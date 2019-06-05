class TableView:
    def __init__(self):
        self.h_sep = "-"
        self.v_sep = None
        self.join_sep = None
        self.r_align = False
        self.headers = list()
        self.rows = list()
        self.set_show_vertical_lines(True)

    def set_show_vertical_lines(self, show_vertical_lines):
        self.v_sep = "|" if show_vertical_lines else ""
        self.join_sep = "+" if show_vertical_lines else " "

    def set_headers(self, headers):
        self.headers = headers

    def add_row(self, row_data):
        self.rows.append(row_data)

    def print_line(self, max_widths):
        row_buffer = ""
        for index, width in enumerate(max_widths):
            line = self.h_sep * (width + len(self.v_sep) + 1)
            last_char = self.join_sep if index == len(max_widths) - 1 else ""
            row_buffer += self.join_sep + line + last_char
        print(row_buffer)

    def print_row(self, row, max_widths):
        row_buffer = ""
        for index, data in enumerate(row):
            v_str = self.v_sep if index == len(row) - 1 else ""
            if self.r_align:
                pass
            else:
                line = "{} {:" + str(max_widths[index]) + "s} {}"
                row_buffer += line.format(self.v_sep, data, v_str)
        print(row_buffer)

    def display(self):
        # Nothing to display if there are no data rows
        if len(self.rows) == 0:
            return

        # Set max_width of each cell using headers
        max_widths = [len(header) for header in self.headers]

        # Update max_widths if header is not defined
        if not max_widths:
            max_widths = [len(item) for item in self.rows[0]]

        # Align cell length with row_data
        for row_data in self.rows:
            for index, item in enumerate(row_data):
                max_widths[index] = max(max_widths[index], len(str(item)))

        # Start printing to console
        if self.headers:
            self.print_line(max_widths)
            self.print_row(self.headers, max_widths)

        self.print_line(max_widths)
        for row in self.rows:
            self.print_row(row, max_widths)
        self.print_line(max_widths)