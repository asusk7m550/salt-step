class returnHandlerRegistry:
    def __init__(self, fully_qualified_function_name, return_handler):
        """
        Creates a backoff timer using the given delay_step and maximum_delay

        :param delay_step: A multiplier value (in ms) for the amount to sleep for.
        :param maximum_delay: The maximum amount for the sleep value (in ms)
        """
        self.fully_qualified_function_name = fully_qualified_function_name
        self.return_handler = return_handler
        self.output = None
        self.error = None
        self.exit_code = 0

    def extract_response(self, raw_response):

        if self.fully_qualified_function_name == 'cmd.run_all':

            self.output = raw_response['stdout']
            self.error = raw_response['stderr']
            self.exit_code = raw_response['retcode']

        elif self.fully_qualified_function_name == 'cmd.run':

            self.output = raw_response
            self.error = None
            self.exit_code = 0

        elif self.fully_qualified_function_name == 'test.ping':

            self.output = None
            self.error = None
            self.exit_code = 0

    def get_standard_output(self):
        return self.output

    def get_standard_error(self):
        return self.error

    def get_exit_code(self):
        return self.exit_code
