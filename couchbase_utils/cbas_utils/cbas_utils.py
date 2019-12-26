"""
Created on Nov 15, 2017

@author: riteshagarwal
"""

import json
import logging
import threading
import time
from threading import Thread

from CbasLib.CBASOperations import CBASHelper
from remote.remote_util import RemoteMachineShellConnection


class CbasUtil:
    def __init__(self, master, cbas_node):
        self.log = logging.getLogger("test")
        self.cbas_node = cbas_node
        self.master = master
        self.cbas_helper = CBASHelper(master, cbas_node)

    def execute_statement_on_cbas_util(self, statement, mode=None, rest=None,
                                       timeout=120, client_context_id=None,
                                       username=None, password=None,
                                       analytics_timeout=120,
                                       time_out_unit="s"):
        """
        Executes a statement on CBAS using the REST API using REST Client
        """
        pretty = "true"
        try:
            self.log.debug("Running query on cbas: %s" % statement)
            response = self.cbas_helper.execute_statement_on_cbas(
                statement, mode, pretty, timeout, client_context_id,
                username, password,
                analytics_timeout=analytics_timeout,
                time_out_unit=time_out_unit)
            if type(response) == str:
                response = json.loads(response)
            if "errors" in response:
                errors = response["errors"]
                if type(errors) == str:
                    errors = json.loads(errors)
            else:
                errors = None

            if "results" in response:
                results = response["results"]
                if type(results) == str:
                    results = json.loads(results)
            else:
                results = None

            if "handle" in response:
                handle = response["handle"]
            else:
                handle = None

            if "metrics" in response:
                metrics = response["metrics"]
                if type(metrics) == str:
                    metrics = json.loads(metrics)
            else:
                metrics = None

            return response["status"], metrics, errors, results, handle

        except Exception as e:
            raise Exception(str(e))

    def execute_parameter_statement_on_cbas_util(self, statement, mode=None,
                                                 rest=None, timeout=120,
                                                 client_context_id=None,
                                                 username=None, password=None,
                                                 analytics_timeout=120,
                                                 parameters=[]):
        """
        Executes a statement on CBAS using the REST API using REST Client
        """
        pretty = "true"
        try:
            self.log.debug("Running query on cbas: %s" % statement)
            response = self.cbas_helper.execute_parameter_statement_on_cbas(
                statement, mode, pretty, timeout, client_context_id,
                username, password,
                analytics_timeout=analytics_timeout, parameters=parameters)
            if type(response) == str:
                response = json.loads(response)
            if "errors" in response:
                errors = response["errors"]
                if type(errors) == str:
                    errors = json.loads(errors)
            else:
                errors = None

            if "results" in response:
                results = response["results"]
                if type(results) == str:
                    results = json.loads(results, parse_int=int)
            else:
                results = None

            if "handle" in response:
                handle = response["handle"]
            else:
                handle = None

            if "metrics" in response:
                metrics = response["metrics"]
                if type(metrics) == str:
                    metrics = json.loads(metrics)
            else:
                metrics = None

            return response["status"], metrics, errors, results, handle

        except Exception, e:
            raise Exception(str(e))

    def create_dataverse_on_cbas(self, dataverse_name=None,
                                 username=None,
                                 password=None,
                                 validate_error_msg=False,
                                 expected_error=None,
                                 expected_error_code=None):

        if dataverse_name == "Default" or dataverse_name is None:
            cmd = "create dataverse Default;"
        else:
            cmd = "create dataverse %s" % dataverse_name

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error,
                                                   expected_error_code)
        else:
            if status != "success":
                return False
            else:
                return True

    def drop_dataverse_on_cbas(self, dataverse_name=None,
                               username=None,
                               password=None,
                               validate_error_msg=False,
                               expected_error=None,
                               expected_error_code=None):
        if dataverse_name:
            cmd = "drop dataverse %s;" % dataverse_name
        else:
            cmd = "drop dataverse Default;"

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error,
                                                   expected_error_code)
        else:
            if status != "success":
                return False
            else:
                return True

    def create_link_on_cbas(self, link_name=None,
                            ip_address=None,
                            username=None,
                            password=None,
                            validate_error_msg=False,
                            expected_error=None,
                            expected_error_code=None):

        if link_name == "Local" or link_name is None:
            cmd = "create link Local;"
        else:
            cmd = "create link %s WITH {'nodes': %s, 'user': %s, 'password': %s}"\
                  % (link_name, ip_address, username, password)

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error,
                                                   expected_error_code)
        else:
            if status != "success":
                return False
            else:
                return True

    def drop_link_on_cbas(self, link_name=None,
                          username=None,
                          password=None,
                          validate_error_msg=False,
                          expected_error=None,
                          expected_error_code=None):
        if link_name:
            cmd = "drop link %s;" % link_name
        else:
            cmd = "drop link Local;"

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error,
                                                   expected_error_code)
        else:
            if status != "success":
                return False
            else:
                return True

    def create_dataset_on_bucket(self, cbas_bucket_name, cbas_dataset_name,
                                 where_field=None, where_value=None,
                                 validate_error_msg=False, username=None,
                                 password=None, expected_error=None):
        """
        Creates a shadow dataset on a CBAS bucket
        """
        cbas_bucket_name = "`"+cbas_bucket_name+"`"
        cmd_create_dataset = "create dataset {0} on {1};".format(
            cbas_dataset_name, cbas_bucket_name)
        if where_field and where_value:
            cmd_create_dataset = \
                "create dataset {0} on {1} WHERE `{2}`=\"{3}\";" \
                .format(cbas_dataset_name, cbas_bucket_name,
                        where_field, where_value)
        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd_create_dataset,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error)
        else:
            if status != "success":
                return False
            else:
                return True

    def create_dataset_on_bucket_merge_policy(
            self, cbas_bucket_name, cbas_dataset_name,
            where_field=None,
            where_value=None,
            validate_error_msg=False,
            username=None,
            password=None,
            expected_error=None,
            merge_policy="no-merge",
            max_mergable_component_size=16384,
            max_tolerance_component_count=2):
        """
        Creates a shadow dataset on a CBAS bucket
        """
        if merge_policy == "no-merge":
            cmd_create_dataset = 'create dataset %s with { "merge-policy": {"name": "%s"}} on %s;'\
            % (cbas_dataset_name, merge_policy, cbas_bucket_name)
            if where_field and where_value:
                cmd_create_dataset = 'create dataset %s with { "merge-policy": {"name": "%s" }} on %s WHERE `%s`=\"%s\";'%(
                    cbas_dataset_name, merge_policy, cbas_bucket_name, where_field, where_value)
        else:
            cmd_create_dataset = 'create dataset %s with { "merge-policy": {"name": "%s", "parameters": {"max-mergable-component-size": %s, "max-tolerance-component-count": %s}}} on %s;'\
            %(cbas_dataset_name, merge_policy, max_mergable_component_size, max_tolerance_component_count, cbas_bucket_name)
            if where_field and where_value:
                cmd_create_dataset = 'create dataset %s with { "merge-policy": {"name": "%s", "parameters": {"max-mergable-component-size": %s,"max-tolerance-component-count": %s}}} on %s WHERE `%s`=\"%s\";'%(
                                        cbas_dataset_name, merge_policy,
                                        max_mergable_component_size, max_tolerance_component_count,
                                        cbas_bucket_name, where_field, where_value)

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd_create_dataset,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error)
        else:
            if status != "success":
                return False
            else:
                return True

    def connect_link(self, link_name="Local",
                     validate_error_msg=False,
                     with_force=False,
                     username=None,
                     password=None,
                     expected_error=None,
                     expected_error_code=None):
        """
        Connects to a Link
        """
        cmd_connect_bucket = "connect link %s" % link_name

        if with_force is True:
            cmd_connect_bucket += " with {'force':true}"

        retry_attempt = 5
        connect_bucket_failed = True
        while connect_bucket_failed and retry_attempt > 0:
            status, metrics, errors, results, _ = \
                self.execute_statement_on_cbas_util(cmd_connect_bucket,
                                                    username=username,
                                                    password=password)

            if errors:
                # Below errors are to be fixed in Alice, until they are fixed retry is only option
                actual_error = errors[0]["msg"]
                if "Failover response The vbucket belongs to another server" in actual_error or "Bucket configuration doesn't contain a vbucket map" in actual_error:
                    retry_attempt -= 1
                    time.sleep(10)
                    self.log.debug("Retrying connecting of bucket")
                else:
                    self.log.debug("Not a vbucket error, so don't retry")
                    connect_bucket_failed = False
            else:
                connect_bucket_failed = False
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error,
                                                   expected_error_code)
        else:
            if status != "success":
                return False
            else:
                return True

    def disconnect_link(self, link_name="Local",
                        disconnect_if_connected=False,
                        validate_error_msg=False,
                        username=None,
                        password=None,
                        expected_error=None,
                        expected_error_code=None):
        """
        Disconnects from a CBAS bucket
        """
        if disconnect_if_connected:
            cmd_disconnect_link = 'disconnect link %s if connected;' \
                                  % link_name
        else:
            cmd_disconnect_link = 'disconnect link %s;' % link_name

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd_disconnect_link,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error,
                                                   expected_error_code)
        else:
            if status != "success":
                return False
            else:
                return True

    def connect_to_bucket(self, cbas_bucket_name=None, cb_bucket_password=None,
                          validate_error_msg=False,
                          cb_bucket_username="Administrator",
                          username=None, password=None, expected_error=None):
        """
        Connects to a CBAS bucket
        """
        cmd_connect_bucket = "connect link Local;"

        retry_attempt = 5
        connect_bucket_failed = True
        while connect_bucket_failed and retry_attempt > 0:
            status, metrics, errors, results, _ = \
                self.execute_statement_on_cbas_util(cmd_connect_bucket,
                                                    username=username,
                                                    password=password)

            if errors:
                # Below errors are to be fixed in Alice, until they are fixed retry is only option
                actual_error = errors[0]["msg"]
                if "Failover response The vbucket belongs to another server" \
                        in actual_error \
                        or "Bucket configuration doesn't contain a vbucket map" in actual_error:
                    retry_attempt -= 1
                    time.sleep(10)
                    self.log.debug("Retrying connecting of bucket")
                else:
                    self.log.debug("Not a vbucket error, so don't retry")
                    connect_bucket_failed = False
            else:
                connect_bucket_failed = False
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error)
        else:
            if status != "success":
                return False
            else:
                return True

    def disconnect_from_bucket(self, cbas_bucket_name=None,
                               disconnect_if_connected=False,
                               validate_error_msg=False, username=None,
                               password=None, expected_error=None):
        """
        Disconnects from a CBAS bucket
        """

        cmd_disconnect_bucket = 'disconnect link Local;'
        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd_disconnect_bucket,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error)
        else:
            if status != "success":
                return False
            else:
                return True

    def drop_dataset(self, cbas_dataset_name, validate_error_msg=False,
                     username=None, password=None, expected_error=None):
        """
        Drop dataset from CBAS
        """
        cmd_drop_dataset = "drop dataset {0};".format(cbas_dataset_name)
        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(cmd_drop_dataset,
                                                username=username,
                                                password=password)
        if validate_error_msg:
            return self.validate_error_in_response(status, errors,
                                                   expected_error)
        else:
            if status != "success":
                return False
            else:
                return True

    def drop_cbas_bucket(self, cbas_bucket_name, validate_error_msg=False,
                         username=None, password=None, expected_error=None):
        """
        Drop a CBAS bucket
        """
        return True

    def wait_for_ingestion_complete(self, cbas_dataset_names, num_items,
                                    timeout=300):

        total_items = 0
        for ds_name in cbas_dataset_names:
            total_items += self.get_num_items_in_cbas_dataset(ds_name)[0]

        counter = 0
        while timeout > counter:
            self.log.debug("Total items in CB Bucket to be ingested "
                           "in CBAS datasets %s"
                           % num_items)
            if num_items == total_items:
                self.log.debug("Data ingestion completed in %s seconds."
                               % counter)
                return True
            else:
                time.sleep(2)
                total_items = 0
                for ds_name in cbas_dataset_names:
                    total_items += self.get_num_items_in_cbas_dataset(ds_name)[0]
                counter += 2

        return False

    def get_num_items_in_cbas_dataset(self, dataset_name, timeout=300,
                                      analytics_timeout=300):
        """
        Gets the count of docs in the cbas dataset
        """
        total_items = -1
        mutated_items = -1
        cmd_get_num_items = "select count(*) from %s;" % dataset_name
        cmd_get_num_mutated_items = "select count(*) from %s where mutated>0;"\
                                    % dataset_name

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(
                cmd_get_num_items,
                timeout=timeout,
                analytics_timeout=analytics_timeout)
        if status != "success":
            self.log.error("Query failed")
        else:
            self.log.debug("No. of items in CBAS dataset {0} : {1}"
                           .format(dataset_name, results[0]['$1']))
            total_items = results[0]['$1']

        status, metrics, errors, results, _ = \
            self.execute_statement_on_cbas_util(
                cmd_get_num_mutated_items,
                timeout=timeout,
                analytics_timeout=analytics_timeout)
        if status != "success":
            self.log.error("Query failed")
        else:
            self.log.debug("No. of items mutated in CBAS dataset {0}: {1}"
                           .format(dataset_name, results[0]['$1']))
            mutated_items = results[0]['$1']

        return total_items, mutated_items

    def validate_cbas_dataset_items_count(self, dataset_name, expected_count,
                                          expected_mutated_count=0,
                                          num_tries=12,
                                          timeout=300,
                                          analytics_timeout=300):
        """
        Compares the count of CBAS dataset total
        and mutated items with the expected values.
        """
        count, mutated_count = self.get_num_items_in_cbas_dataset(
            dataset_name,
            timeout=timeout,
            analytics_timeout=analytics_timeout)
        tries = num_tries
        if expected_mutated_count:
            while (count != expected_count
                   or mutated_count != expected_mutated_count) and tries > 0:
                time.sleep(10)
                count, mutated_count = self.get_num_items_in_cbas_dataset(
                    dataset_name,
                    timeout=timeout,
                    analytics_timeout=analytics_timeout)
                tries -= 1
        else :
            while count != expected_count and tries > 0:
                time.sleep(10)
                count, mutated_count = self.get_num_items_in_cbas_dataset(
                    dataset_name,
                    timeout=timeout,
                    analytics_timeout=analytics_timeout)
                tries -= 1

        self.log.debug("Expected Count: %s, Actual Count: %s"
                       % (expected_count, count))
        self.log.debug("Expected Mutated Count: %s, Actual Mutated Count: %s"
                       % (expected_mutated_count, mutated_count))

        if count != expected_count:
            return False
        elif mutated_count == expected_mutated_count:
            return True
        else:
            return False

    def delete_request(self, client_context_id, username=None, password=None):
        """
        Deletes a request from CBAS
        """
        try:
            if client_context_id is None:
                payload = "client_context_id=None"
            else:
                payload = "client_context_id=" + client_context_id

            status = self.cbas_helper.delete_active_request_on_cbas(payload,
                                                                    username,
                                                                    password)
            self.log.info(status)
            return status
        except Exception, e:
            raise Exception(str(e))

    def retrieve_request_status_using_handle(self, server, handle, shell=None):
        """
        Retrieves status of a request from /analytics/status endpoint
        """
        if not shell:
            shell = RemoteMachineShellConnection(server)

        output, error = shell.execute_command(
            """curl -g -v {0} -u {1}:{2}"""
            .format(handle,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))

        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)

        if not shell:
            shell.disconnect()

        status = ""
        handle = ""
        if 'status' in response:
            status = response['status']
        if 'handle' in response:
            handle = response['handle']

        self.log.debug("status=%s, handle=%s" % (status, handle))
        return status, handle

    def retrieve_result_using_handle(self, server, handle):
        """
        Retrieves result from the /analytics/results endpoint
        """
        shell = RemoteMachineShellConnection(server)

        output, error = shell.execute_command(
            """curl -g -v {0} -u {1}:{2}"""
            .format(handle,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))

        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)
        shell.disconnect()

        return response

    def convert_execution_time_into_ms(self, execution_time):
        """
        Converts the execution time into ms
        """
        import re
        match = re.match(r"([0-9]+.[0-9]+)([a-zA-Z]+)", execution_time, re.I)
        if match:
            items = match.groups()

            if items[1] == "s":
                return float(items[0])*1000
            if items[1] == "ms":
                return float(items[0])
            if items[1] == "m":
                return float(items[0])*1000*60
            if items[1] == "h":
                return float(items[0])*1000*60*60
        else:
            return None

    def validate_error_in_response(self, status, errors, expected_error=None,
                                   expected_error_code=None):
        """
        Validates the error response against the expected one.
        """
        if status != "success":
            actual_error = errors[0]["msg"]
            if expected_error not in actual_error:
                self.log.debug("Error message mismatch. Expected: %s, got: %s"
                               % (expected_error, actual_error))
                return False
            self.log.debug("Error message matched. Expected: %s, got: %s"
                           % (expected_error, actual_error))
            if expected_error_code is not None:
                if expected_error_code != errors[0]["code"]:
                    self.log.debug("Error code mismatch. Expected: %s, got: %s"
                                   % (expected_error_code, errors[0]["code"]))
                    return False
                self.log.info("Error code matched. Expected: %s, got: %s"
                              % (expected_error_code, errors[0]["code"]))
            return True
        return False

    def async_query_execute(self, statement, mode, num_queries):
        """
        Asynchronously run queries
        """
        self.log.deebug("Executing %s queries concurrently", num_queries)

        cbas_base_url = "http://{0}:8095/analytics/service" \
                        .format(self.cbas_node.ip)

        pretty = "true"
        tasks = []
        for count in range(0, num_queries):
            tasks.append(self.cluster.async_cbas_query_execute(self.master,
                                                               self.cbas_node,
                                                               cbas_base_url,
                                                               statement,
                                                               mode,
                                                               pretty))
        return tasks

    def _run_concurrent_queries(self, query, mode, num_queries, rest=None,
                                batch_size=100, timeout=300,
                                analytics_timeout=300):
        self.failed_count = 0
        self.success_count = 0
        self.rejected_count = 0
        self.error_count = 0
        self.cancel_count = 0
        self.timeout_count = 0
        self.handles = []
        self.concurrent_batch_size = batch_size
        # Run queries concurrently
        self.log.debug("Running queries concurrently now...")
        threads = []
        if rest:
            self.cbas_util = rest
        for i in range(0, num_queries):
            threads.append(Thread(target=self._run_query,
                                  name="query_thread_{0}".format(i),
                                  args=(query, mode, rest, False, 0, timeout,
                                        analytics_timeout)))
        i = 0
        for thread in threads:
            # Send requests in batches, and sleep for 5 seconds before sending another batch of queries.
            i += 1
            if i % self.concurrent_batch_size == 0:
                self.log.debug("Submitted {0} queries".format(i))
                time.sleep(5)
            thread.start()
        for thread in threads:
            thread.join()

        self.log.debug("%s queries submitted, %s failed, %s passed, "
                       "%s rejected, %s cancelled, %s timeout"
                       % (num_queries, self.failed_count, self.success_count,
                          self.rejected_count, self.cancel_count,
                          self.timeout_count))
        if self.failed_count+self.error_count != 0:
            raise Exception("Queries Failed:%s , Queries Error Out:%s"
                            % (self.failed_count, self.error_count))
        return self.handles

    def _run_query(self, query, mode, rest=None, validate_item_count=False,
                   expected_count=0, timeout=300, analytics_timeout=300):
        # Execute query (with sleep induced)
        name = threading.currentThread().getName()
        client_context_id = name
        if rest:
            self.cbas_util = rest
        try:
            status, metrics, errors, results, handle = \
                self.execute_statement_on_cbas_util(
                    query, mode=mode, rest=rest, timeout=timeout,
                    client_context_id=client_context_id,
                    analytics_timeout=analytics_timeout)
            # Validate if the status of the request is success, and if the count matches num_items
            if mode == "immediate":
                if status == "success":
                    if validate_item_count:
                        if results[0]['$1'] != expected_count:
                            self.log.warn("Query result: %s", results[0]['$1'])
                            self.log.error("*** Thread %s: failure ***", name)
                            self.failed_count += 1
                        else:
                            self.log.debug("--- Thread %s: success ---", name)
                            self.success_count += 1
                    else:
                        self.log.debug("--- Thread %s: success ---", name)
                        self.success_count += 1
                else:
                    self.log.warn("Status = %s", status)
                    self.log.error("*** Thread %s: failure ***", name)
                    self.failed_count += 1
            elif mode == "async":
                if status == "running" and handle:
                    self.log.debug("--- Thread %s: success ---", name)
                    print(handle)
                    self.handles.append(handle)
                    self.success_count += 1
                else:
                    self.log.warn("Status = %s", status)
                    self.log.error("*** Thread %s: failure ***", name)
                    self.failed_count += 1
            elif mode == "deferred":
                if status == "success" and handle:
                    self.log.debug("--- Thread %s: success ---", name)
                    self.handles.append(handle)
                    self.success_count += 1
                else:
                    self.log.warn("Status = %s", status)
                    self.log.error("*** Thread %s: failure ***", name)
                    self.failed_count += 1
            elif mode is None:
                if status == "success":
                    self.log.debug("--- Thread %s: success ---", name)
                    self.success_count += 1
                else:
                    self.log.warn("Status = %s", status)
                    self.log.error("*** Thread %s: failure ***", name)
                    self.failed_count += 1

        except Exception, e:
            if str(e) == "Request Rejected":
                self.log.debug("Error 503 : Request Rejected")
                self.rejected_count += 1
            elif str(e) == "Request TimeoutException":
                self.log.debug("Request TimeoutException")
                self.timeout_count += 1
            elif str(e) == "Request RuntimeException":
                self.log.debug("Request RuntimeException")
                self.timeout_count += 1
            elif str(e) == "Request RequestCancelledException":
                self.log.debug("Request RequestCancelledException")
                self.cancel_count += 1
            elif str(e) == "CouchbaseException":
                self.log.debug("General CouchbaseException")
                self.rejected_count += 1
            elif str(e) == "Capacity cannot meet job requirement":
                self.log.debug(
                    "Error 500 : Capacity cannot meet job requirement")
                self.rejected_count += 1
            else:
                self.error_count +=1
                self.log.error(str(e))

    def verify_index_created(self, index_name, index_fields, dataset):
        result = True

        statement = "select * from Metadata.`Index` where DatasetName='{0}' and IsPrimary=False"\
                    .format(dataset)
        status, metrics, errors, content, _ = \
            self.execute_statement_on_cbas_util(statement)
        if status != "success":
            result = False
            self.log.debug("Index not created. Metadata query status = %s",
                           status)
        else:
            index_found = False
            for index in content:
                if index["Index"]["IndexName"] == index_name:
                    index_found = True
                    field_names = []
                    for index_field in index_fields:
                        if "meta()".lower() in index_field:
                            field_names.append(index_field.split(".")[1])
                        else:
                            field_names.append(str(index_field.split(":")[0]))
                            field_names.sort()
                    self.log.debug(field_names)
                    actual_field_names = []
                    for index_field in index["Index"]["SearchKey"]:
                        if type(index_field) is list:
                            index_field = ".".join(index_field)
                        actual_field_names.append(str(index_field))
                        actual_field_names.sort()

                    actual_field_names.sort()
                    self.log.debug(actual_field_names)
                    if field_names != actual_field_names:
                        result = False
                        self.log.debug("Index fields not correct")
                    break
            result &= index_found
        return result, content

    def retrieve_cc_ip(self,shell=None):

        if not shell:
            shell = RemoteMachineShellConnection(self.cbas_node)
        url = self.cbas_helper.cbas_base_url + "/analytics/cluster"
        output, error = shell.execute_command(
            """curl -g -v {0} -u {1}:{2}"""
            .format(url,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))

        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)

        if not shell:
            shell.disconnect()

        cc_node_id = ""
        cc_node_ip = ""
        cc_node_config_url = None
        if 'ccNodeId' in response:
            cc_node_id = response['ccNodeId']
        if 'nodes' in response:
            nodes = response['nodes']
            for node in nodes:
                if node["nodeId"] == cc_node_id:
                    cc_node_config_url = node['configUri']
                    cc_node_ip = node['nodeName'][:-5]
                    break

        self.log.debug("cc_config_urls=%s, ccNodeId=%s, ccNodeIP=%s"
                       % (cc_node_config_url, cc_node_id, cc_node_ip))
        return cc_node_ip

    def retrieve_nodes_config(self, only_cc_node_url=True, shell=None):
        """
        Retrieves status of a request from /analytics/status endpoint
        """
        if not shell:
            shell = RemoteMachineShellConnection(self.cbas_node)
        url = self.cbas_helper.cbas_base_url + "/analytics/cluster"
        output, error = shell.execute_command(
            """curl -g -v {0} -u {1}:{2}"""
            .format(url,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))

        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)

        if not shell:
            shell.disconnect()

        cc_node_id = ""
        nodes = None
        cc_node_config_url=None
        if 'ccNodeId' in response:
            cc_node_id = response['ccNodeId']
        if 'nodes' in response:
            nodes = response['nodes']
            for node in nodes:
                if only_cc_node_url and node["nodeId"] == cc_node_id:
                    cc_node_config_url = node['configUri']
                    break

        self.log.debug("cc_config_urls=%s, ccNodeId=%s"
                       % (cc_node_config_url, cc_node_id))
        self.log.debug("Nodes: %s" % nodes)
        return nodes, cc_node_id, cc_node_config_url

    def fetch_analytics_cluster_response(self, shell=None):
        """
        Retrieves response from /analytics/status endpoint
        """
        if not shell:
            shell = RemoteMachineShellConnection(self.cbas_node)
        url = self.cbas_helper.cbas_base_url + "/analytics/cluster"
        output, error = shell.execute_command(
            "curl -g -v {0} -u {1}:{2}"
            .format(url,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))
        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)
        return response

    def retrieve_analyticsHttpAdminListen_address_port(self, node_config_url,
                                                       shell=None):
        """
        Retrieves status of a request from /analytics/status endpoint
        """
        if not shell:
            shell = RemoteMachineShellConnection(self.cbas_node)
        output, error = shell.execute_command(
            """curl -g -v {0} -u {1}:{2}"""
            .format(node_config_url,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))

        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)

        if not shell:
            shell.disconnect()

        analytics_http_admin_listen_addr = None
        analytics_http_admin_listen_port = None

        if 'analyticsHttpAdminListenAddress' in response:
            analytics_http_admin_listen_addr = \
                response['analyticsHttpAdminPublicAddress']
            if analytics_http_admin_listen_addr.find(":") != -1:
                analytics_http_admin_listen_addr = \
                    '['+analytics_http_admin_listen_addr+']'
        if 'analyticsHttpAdminListenPort' in response:
            analytics_http_admin_listen_port = \
                response['analyticsHttpAdminPublicPort']

        return analytics_http_admin_listen_addr,\
               analytics_http_admin_listen_port

    def retrive_replica_from_storage_data(self,
                                          analytics_http_admin_listen_addr,
                                          analytics_http_admin_listen_port,
                                          shell=None):
        url = "http://{0}:{1}/analytics/node/storage" \
              .format(analytics_http_admin_listen_addr,
                      analytics_http_admin_listen_port)

        if not shell:
            shell = RemoteMachineShellConnection(self.cbas_node)
        output, error = shell.execute_command(
            """curl -g -v {0} -u {1}:{2}"""
            .format(url,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))

        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)
        self.log.debug("Api %s: %s" % (url, response))

        if not shell:
            shell.disconnect()

        for partition in response:
            if 'replicas' in partition and len(partition['replicas']) > 0:
                return partition['replicas']
        return []

    def get_replicas_info(self, shell=None):
        cc__metadata_replicas_info = []
        start_time = time.time()
        cc_node_id = None
        nodes = []
        while (not cc_node_id or not nodes) and start_time + 60 > time.time():
            nodes, cc_node_id, cc_config_url = \
                self.retrieve_nodes_config(shell)
        if cc_config_url:
            address, port = \
                self.retrieve_analyticsHttpAdminListen_address_port(
                    cc_config_url, shell)
            cc__metadata_replicas_info = \
                self.retrive_replica_from_storage_data(address, port, shell)

        return cc__metadata_replicas_info

    def get_num_partitions(self, shell=None):
        partitons = dict()
        nodes, cc_node_id, cc_config_url = \
            self.retrieve_nodes_config(shell=shell)
        for node in nodes:
            address, port = \
                self.retrieve_analyticsHttpAdminListen_address_port(
                    node['configUri'], shell)
            partitons[node['nodeName']] = \
                self.retrieve_number_of_partitions(address, port, shell)

        return partitons

    def retrieve_number_of_partitions(self, analytics_http_admin_listen_addr,
                                      analytics_http_admin_listen_port,
                                      shell=None):
        url = "http://{0}:{1}/analytics/node/storage" \
            .format(analytics_http_admin_listen_addr,
                    analytics_http_admin_listen_port)

        if not shell:
            shell = RemoteMachineShellConnection(self.cbas_node)
        output, error = shell.execute_command(
            """curl -g -v {0} -u {1}:{2}"""
            .format(url,
                    self.cbas_node.rest_username,
                    self.cbas_node.rest_password))

        response = ""
        for line in output:
            response = response + line
        if response:
            response = json.loads(response)
        self.log.debug("Api %s: %s" % (url, response))

        if not shell:
            shell.disconnect()

        return len(response)

    def set_log_level_on_cbas(self, log_level_dict, timeout=120, username=None,
                              password=None):

        payload = ""
        for component, level in log_level_dict.items():
            payload += '{ "level": "' + level + '", "name": "' + component + '" },'
        payload = payload.rstrip(",")
        params = '{ "loggers": [ ' + payload + ' ] }'
        status, content, response = \
            self.cbas_helper.operation_log_level_on_cbas(
                method="PUT", params=params,
                logger_name=None,
                timeout=timeout, username=username,
                password=password)
        return status, content, response

    def set_specific_log_level_on_cbas(self, logger_name, log_level,
                                       timeout=120, username=None,
                                       password=None):
        status, content, response = \
            self.cbas_helper.operation_log_level_on_cbas(
                method="PUT", params=None,
                logger_name=logger_name, log_level=log_level,
                timeout=timeout, username=username,
                password=password)
        return status, content, response

    def get_log_level_on_cbas(self, timeout=120, username=None, password=None):
        status, content, response = \
            self.cbas_helper.operation_log_level_on_cbas(
                method="GET", params="",
                logger_name=None,
                timeout=timeout,
                username=username, password=password)
        return status, content, response

    def get_specific_cbas_log_level(self, logger_name, timeout=120,
                                    username=None, password=None):
        status, content, response = \
            self.cbas_helper.operation_log_level_on_cbas(
                method="GET", params=None,
                logger_name=logger_name,
                timeout=timeout,
                username=username, password=password)
        return status, content, response

    def delete_all_loggers_on_cbas(self, timeout=120, username=None,
                                   password=None):
        status, content, response = \
            self.cbas_helper.operation_log_level_on_cbas(
                method="DELETE", params="",
                logger_name=None,
                timeout=timeout,
                username=username, password=password)
        return status, content, response

    def delete_specific_cbas_log_level(self, logger_name, timeout=120,
                                       username=None, password=None):
        status, content, response = \
            self.cbas_helper.operation_log_level_on_cbas(
                method="DELETE", params=None,
                logger_name=logger_name,
                timeout=timeout,
                username=username, password=password)
        return status, content, response

    def update_config_on_cbas(self, config_name=None, config_value=None,
                              username=None, password=None):
        if config_name and config_value:
            params = '{"' + config_name + '":' + str(config_value) + '}'
        else:
            raise ValueError("Missing config name and/or config value")
        status, content, response = self.cbas_helper.operation_config_on_cbas(
            method="PUT", params=params,
            username=username, password=password)
        return status, content, response

    def fetch_config_on_cbas(self, config_name=None, config_value=None,
                             username=None, password=None):
        status, content, response = \
            self.cbas_helper.operation_config_on_cbas(method="GET",
                                                      username=username,
                                                      password=password)
        return status, content, response

    def fetch_cbas_stats(self, username=None, password=None):
        status, content, response = self.cbas_helper.fetch_cbas_stats(
            username=username, password=password)
        return status, content, response

    def log_concurrent_query_outcome(self, node_in_test, handles):
        run_count = 0
        fail_count = 0
        success_count = 0
        aborted_count = 0
        shell = RemoteMachineShellConnection(node_in_test)
        for handle in handles:
            status, hand = self.retrieve_request_status_using_handle(
                node_in_test, handle, shell)
            if status == "running":
                run_count += 1
                self.log.debug("query with handle %s is running." % handle)
            elif status == "failed":
                fail_count += 1
                self.log.debug("query with handle %s is failed." % handle)
            elif status == "success":
                success_count += 1
                self.log.debug("query with handle %s is successful." % handle)
            else:
                aborted_count += 1
                self.log.debug("Queued job is deleted: %s" % status)

        self.log.debug("%s queued jobs are Running." % run_count)
        self.log.debug("%s queued jobs are Failed." % fail_count)
        self.log.debug("%s queued jobs are Successful." % success_count)
        self.log.debug("%s queued jobs are Aborted." % aborted_count)

    def update_service_parameter_configuration_on_cbas(self, config_map=None,
                                                       username=None,
                                                       password=None):
        if config_map:
            params = json.dumps(config_map)
        else:
            raise ValueError("Missing config map")
        status, content, response = \
            self.cbas_helper.operation_service_parameters_configuration_cbas(
                method="PUT", params=params,
                username=username, password=password)
        return status, content, response

    def fetch_service_parameter_configuration_on_cbas(self, username=None,
                                                      password=None):
        status, content, response = \
            self.cbas_helper.operation_service_parameters_configuration_cbas(
                method="GET", username=username, password=password)
        return status, content, response

    def update_node_parameter_configuration_on_cbas(self, config_map=None,
                                                    username=None,
                                                    password=None):
        if config_map:
            params = json.dumps(config_map)
        else:
            raise ValueError("Missing config map")
        status, content, response = \
            self.cbas_helper.operation_node_parameters_configuration_cbas(
                method="PUT", params=params,
                username=username, password=password)
        return status, content, response

    def fetch_node_parameter_configuration_on_cbas(self, username=None,
                                                   password=None):
        status, content, response = \
            self.cbas_helper.operation_node_parameters_configuration_cbas(
                method="GET", username=username, password=password)
        return status, content, response

    def restart_analytics_cluster_uri(self, username=None, password=None):
        status, content, response = \
            self.cbas_helper.restart_analytics_cluster_uri(username=username,
                                                           password=password)
        return status, content, response

    def restart_analytics_node_uri(self, node_id, port=8095,
                                   username=None, password=None):
        status, content, response = \
            self.cbas_helper.restart_analytics_node_uri(node_id, port,
                                                        username=username,
                                                        password=password)
        return status, content, response

    def fetch_bucket_state_on_cbas(self):
        status, content, response = \
            self.cbas_helper.fetch_bucket_state_on_cbas(method="GET",
                                                        username=None,
                                                        password=None)
        return status, content, response

    def fetch_pending_mutation_on_cbas_node(self, node_ip, port=9110,
                                            username=None, password=None):
        status, content, response = \
            self.cbas_helper.fetch_pending_mutation_on_cbas_node(
                node_ip, port, method="GET",
                username=username, password=password)
        return status, content, response

    def fetch_pending_mutation_on_cbas_cluster(self, port=9110,
                                               username=None, password=None):
        status, content, response = \
            self.cbas_helper.fetch_pending_mutation_on_cbas_cluster(
                port, method="GET", username=username, password=password)
        return status, content, response

    def fetch_dcp_state_on_cbas(self, data_set, data_verse="Default",
                                username=None, password=None):
        if not data_set:
            raise ValueError("dataset is required field")
        status, content, response = self.cbas_helper.fetch_dcp_state_on_cbas(
            data_set, method="GET", dataverse=data_verse,
            username=username, password=password)
        return status, content, response

    def get_analytics_diagnostics(self, cbas_node, timeout=120):
        response = self.cbas_helper.get_analytics_diagnostics(cbas_node,
                                                              timeout=timeout)
        return response
