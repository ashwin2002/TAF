import copy
import logging
import time
import traceback
from BucketLib.BucketOperations import BucketHelper
from BucketLib.MemcachedOperations import MemcachedHelper
from membase.api.exception import FailoverFailedException, \
    ServerUnavailableException, BucketFlushFailed
from membase.api.rest_client import RestConnection
from testconstants import MIN_KV_QUOTA, INDEX_QUOTA, FTS_QUOTA, CBAS_QUOTA
"""
from java.util.concurrent import Callable, TimeUnit, CancellationException, \
    TimeoutException
"""

CHECK_FLAG = False

PENDING = 'PENDING'
EXECUTING = 'EXECUTING'
CHECKING = 'CHECKING'
FINISHED = 'FINISHED'
CANCELLED = 'CANCELLED'


class Task(Callable):
    def __init__(self, name, task_manager):
        self.name = name
        self.thread_name = name
        self.task_manager = task_manager
        self.state = EXECUTING
        self.result = None
        self.future = None
        self.log = logging.getLogger("infra")
        self.test_log = logging.getLogger("test")
        self.log.debug("*** TASK {0} Scheduled...".format(self.name))

    def call(self):
        self.log.debug("*** TASK  {0} in progress...".format(self.name))
        if self.state == PENDING:
            self.state = EXECUTING
            self.future = self.task_manager.schedule(self)
        if self.state == EXECUTING:
            self.execute()
        elif self.state == CHECKING:
            self.check()
        elif self.state != FINISHED:
            raise Exception("Bad State in {0}: {1}".format(self.name,
                                                           self.state))

    def execute(self):
        raise NotImplementedError

    def check(self):
        raise NotImplementedError

    def set_result(self, result):
        self.result = result

    def get_result(self, timeout=None):
        try:
            if timeout:
                self.future.get(timeout, TimeUnit.SECONDS)
            else:
                self.future.get()
            if self.state == FINISHED:
                self.log.debug("*** TASK  {0} Finished...".format(self.name))
                return self.result
        except CancellationException as ex:
            self.state = CANCELLED
            self.result = False
        except TimeoutException as ex:
            self.log.error("Task Timed Out")

    def cancel(self, interrupt_if_running=True):
        check = self.future.cancel(interrupt_if_running)
        if check:
            self.state = CANCELLED
            raise CancellationException
        elif self.future.isDone():
            self.state = FINISHED

    def cancelled(self):
        return self.future.isCancelled()

    def set_unexpected_exception(self, e, suffix=""):
        self.log.error("Unexpected exception [{0}] caught".format(e) + suffix)
        self.log.error(''.join(traceback.format_stack()))

    @staticmethod
    def wait_until(value_getter, condition, timeout_secs=-1):
        """
        Repeatedly calls value_getter returning the value when it
        satisfies condition. Calls to value getter back off exponentially.
        Useful if you simply want to synchronously wait for a condition to be
        satisfied.

        :param value_getter: no-arg function that gets a value
        :param condition: single-arg function that tests the value
        :param timeout_secs: number of seconds after which to timeout; if negative
                             waits forever; default is to wait forever
        :return: the value returned by value_getter
        :raises: TimeoutError if the operation times out before
                 getting a value that satisfies condition
        """
        start_time = time.time()
        stop_time = start_time + max(timeout_secs, 0)
        interval = 0.01
        attempt = 0
        value = value_getter()
        while not condition(value):
            now = time.time()
            if timeout_secs < 0 or now < stop_time:
                time.sleep(2**attempt * interval)
                attempt += 1
                value = value_getter()
            else:
                raise TimeoutException(
                    'Timed out after {0} seconds and {1} attempts' .format(
                        now - start_time, attempt))
        return value


class NodeInitializeTask(Task):
    def __init__(self, server, task_manager, disabled_consistent_view=None,
                 rebalanceIndexWaitingDisabled=None,
                 rebalanceIndexPausingDisabled=None,
                 maxParallelIndexers=None,
                 maxParallelReplicaIndexers=None,
                 port=None, quota_percent=None,
                 index_quota_percent=None,
                 services=None, gsi_type='forestdb'):
        Task.__init__(self, name="node_init_task", task_manager=task_manager)
        self.server = server
        self.port = port or server.port
        self.quota = 0
        self.index_quota = 0
        self.index_quota_percent = index_quota_percent
        self.quota_percent = quota_percent
        self.disable_consistent_view = disabled_consistent_view
        self.rebalanceIndexWaitingDisabled = rebalanceIndexWaitingDisabled
        self.rebalanceIndexPausingDisabled = rebalanceIndexPausingDisabled
        self.maxParallelIndexers = maxParallelIndexers
        self.maxParallelReplicaIndexers = maxParallelReplicaIndexers
        self.services = services
        self.gsi_type = gsi_type

    def execute(self):
        try:
            rest = RestConnection(self.server)
        except ServerUnavailableException as error:
            self.state = FINISHED
            self. set_unexpected_exception(error)
            return
        info = Task.wait_until(lambda: rest.get_nodes_self(),
                               lambda x: x.memoryTotal > 0, 10)
        self.test_log.debug("server: %s, nodes/self: %s", self.server, info.__dict__)

        username = self.server.rest_username
        password = self.server.rest_password

        if int(info.port) in range(9091, 9991):
            self.state = FINISHED
            self.set_result(True)
            return

        self.quota = int(info.mcdMemoryReserved * 2 / 3)
        if self.index_quota_percent:
            self.index_quota = int((info.mcdMemoryReserved * 2 / 3) *
                                   self.index_quota_percent / 100)
            rest.set_service_memoryQuota(
                service='indexMemoryQuota',
                username=username,
                password=password,
                memoryQuota=self.index_quota)
        if self.quota_percent:
            self.quota = int(info.mcdMemoryReserved * self.quota_percent / 100)

        """ Adjust KV RAM to correct value when there is INDEX
            and FTS services added to node from Watson  """
        index_quota = INDEX_QUOTA
        kv_quota = int(info.mcdMemoryReserved * 2 / 3)
        if self.index_quota_percent:
            index_quota = self.index_quota
        if not self.quota_percent:
            set_services = copy.deepcopy(self.services)
            if set_services is None:
                set_services = ["kv"]
#             info = rest.get_nodes_self()
#             cb_version = info.version[:5]
#             if cb_version in COUCHBASE_FROM_VERSION_4:
            if "index" in set_services:
                self.test_log.debug("Quota for index service will be %s MB"
                                    % index_quota)
                kv_quota -= index_quota
                self.test_log.debug("Set index quota to node %s "
                                    % self.server.ip)
                rest.set_service_memoryQuota(
                    service='indexMemoryQuota', memoryQuota=index_quota)
            if "fts" in set_services:
                self.test_log.debug("Quota for fts service will be %s MB"
                                    % FTS_QUOTA)
                kv_quota -= FTS_QUOTA
                self.test_log.debug("Set both index and fts quota at node %s"
                                    % self.server.ip)
                rest.set_service_memoryQuota(
                    service='ftsMemoryQuota', memoryQuota=FTS_QUOTA)
            if "cbas" in set_services:
                self.test_log.debug("Quota for cbas service will be %s MB"
                                    % CBAS_QUOTA)
                kv_quota -= CBAS_QUOTA
                rest.set_service_memoryQuota(
                    service="cbasMemoryQuota", memoryQuota=CBAS_QUOTA)
            if kv_quota < MIN_KV_QUOTA:
                raise Exception(
                    "KV RAM needs to be more than %s MB"
                    " at node  %s" %
                    (MIN_KV_QUOTA, self.server.ip))
            if kv_quota < int(self.quota):
                self.quota = kv_quota

        rest.init_cluster_memoryQuota(username, password, self.quota)
        rest.set_indexer_storage_mode(username, password, self.gsi_type)

        if self.services:
            status = rest.init_node_services(
                username=username,
                password=password,
                port=self.port,
                hostname=self.server.ip,
                services=self.services)
            if not status:
                self.state = FINISHED
                self. set_unexpected_exception(
                    Exception(
                        'unable to set services for server %s' %
                        (self.server.ip)))
                return
        if self.disable_consistent_view is not None:
            rest.set_reb_cons_view(self.disable_consistent_view)
        if self.rebalanceIndexWaitingDisabled is not None:
            rest.set_reb_index_waiting(self.rebalanceIndexWaitingDisabled)
        if self.rebalanceIndexPausingDisabled is not None:
            rest.set_rebalance_index_pausing(
                self.rebalanceIndexPausingDisabled)
        if self.maxParallelIndexers is not None:
            rest.set_max_parallel_indexers(self.maxParallelIndexers)
        if self.maxParallelReplicaIndexers is not None:
            rest.set_max_parallel_replica_indexers(
                self.maxParallelReplicaIndexers)

        rest.init_cluster(username, password, self.port)
        self.server.port = self.port
        try:
            rest = RestConnection(self.server)
        except ServerUnavailableException as error:
            self.state = FINISHED
            self. set_unexpected_exception(error)
            return
        info = rest.get_nodes_self()

        if info is None:
            self.state = FINISHED
            self. set_unexpected_exception(
                Exception(
                    'unable to get information on a server %s, it is available?' %
                    (self.server.ip)))
            return
        self.state = CHECKING
        self.call()

    def check(self):
        self.state = FINISHED
        self.set_result(self.quota)


class FailoverTask(Task):
    def __init__(
            self,
            servers,
            task_manager,
            to_failover=[],
            wait_for_pending=0,
            graceful=False,
            use_hostnames=False):
        Task.__init__(self, "failover_task", task_manager)
        self.servers = servers
        self.to_failover = to_failover
        self.graceful = graceful
        self.wait_for_pending = wait_for_pending
        self.use_hostnames = use_hostnames

    def execute(self):
        try:
            self._failover_nodes(self.task_manager)
            self.test_log.debug("{0} seconds sleep after failover for nodes to go pending...."
                                .format(self.wait_for_pending))
            time.sleep(self.wait_for_pending)
            self.state = FINISHED
            self.set_result(True)

        except FailoverFailedException as e:
            self.state = FINISHED
            self. set_unexpected_exception(e)

        except Exception as e:
            self.state = FINISHED
            self.set_unexpected_exception(e)

    def _failover_nodes(self, task_manager):
        rest = RestConnection(self.servers[0])
        # call REST fail_over for the nodes to be failed over
        for server in self.to_failover:
            for node in rest.node_statuses():
                if (server.hostname if self.use_hostnames else server.ip) == node.ip and int(
                        server.port) == int(node.port):
                    self.test_log.debug(
                        "Failing over {0}:{1} with graceful={2}"
                        .format(node.ip, node.port, self.graceful))
                    rest.fail_over(node.id, self.graceful)


class BucketFlushTask(Task):
    def __init__(self, server, task_manager, bucket="default"):
        Task.__init__(self, "bucket_flush_task", task_manager)
        self.server = server
        self.bucket = bucket
        if isinstance(bucket, Bucket):
            self.bucket = bucket.name

    def execute(self):
        try:
            rest = BucketHelper(self.server)
            if rest.flush_bucket(self.bucket):
                self.state = CHECKING
                self.task_manager.schedule(self)
            else:
                self.state = FINISHED
                self.set_result(False)

        except BucketFlushFailed as e:
            self.state = FINISHED
            self. set_unexpected_exception(e)

        except Exception as e:
            self.state = FINISHED
            self.set_unexpected_exception(e)

    def check(self):
        try:
            # check if after flush the vbuckets are ready
            if MemcachedHelper.wait_for_vbuckets_ready_state(
                    self.server, self.bucket):
                self.set_result(True)
            else:
                self.test_log.error(
                    "Unable to reach bucket {0} on server {1} after flush"
                    .format(self.bucket, self.server))
                self.set_result(False)
            self.state = FINISHED
        except Exception as e:
            self.state = FINISHED
            self.set_unexpected_exception(e)
