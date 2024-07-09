import sys, os
import unittest
from unittest.mock import MagicMock
from unittest import mock

sys.path.append(os.getcwd())
from contents.salt import SaltApiNodeStepPlugin
from contents.salt import NodeStepException, SaltStepValidationException, SaltApiException, SaltTargettingMismatchException

from requests.exceptions import HTTPError


class SaltApiNodeStepPluginTest(unittest.TestCase):

    def setUp(self):
        self.pluginContext = MagicMock()
        self.configuration = MagicMock()
        self.node = MagicMock()
        self.client = MagicMock()
        self.AUTH_TOKEN = 'auth_token'
        self.OUTPUT_JID = 'output_jid'
        self.PARAM_MINION_NAME = 'minion_name'
        self.HOST_RESPONSE = 'host_response'
        self.PARAM_FUNCTION = 'function'
        self.returnHandlerRegistry = MagicMock()
        self.returnHandler = MagicMock()
        self.pluginLogger = MagicMock()
        self.latestCapability = MagicMock()
        self.dataContext = {}

        self.PARAM_ENDPOINT = "https://localhost"
        self.PARAM_EAUTH = "pam"
        self.PARAM_USER = "user"
        self.PARAM_PASSWORD = "password&!@$*"

        self.plugin = SaltApiNodeStepPlugin(self.PARAM_ENDPOINT, self.PARAM_USER, self.PARAM_PASSWORD, self.PARAM_EAUTH)
        self.plugin.authenticate = MagicMock()
        self.plugin.submit_job = MagicMock()
        self.plugin.wait_for_jid_response = MagicMock()
        self.plugin.extract_output_for_jid = MagicMock()
        self.plugin.logoutQuietly = MagicMock()

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
        }
    )
    def test_execute_with_authentication_failure(self):
        self.plugin.authenticate.return_value = None
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response.return_value = self.HOST_RESPONSE
        self.plugin.extract_output_for_jid.return_value = MagicMock(exit_code=0, stdout=[], stderr=[])

        with self.assertRaises(NodeStepException) as context:
            self.plugin.execute_node_step()

        self.assertEqual(context.exception.failure_reason, 'AUTHENTICATION_FAILURE')

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
        }
    )
    def test_execute_with_validation_failure(self):
        e = SaltStepValidationException("some property", "Some message", 'ARGUMENTS_INVALID', self.node.nodename)
        self.plugin.validate = MagicMock()
        self.plugin.validate.side_effect = e

        with self.assertRaises(SaltStepValidationException) as context:
            self.plugin.execute_node_step()

        self.assertIs(context.exception, e)

    def test_execute_with_data_context_missing(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response = MagicMock(return_value=self.HOST_RESPONSE)
        self.plugin.extract_output_for_jid.return_value = MagicMock(exit_code=0, stdout=[], stderr=[])

        self.dataContext.clear()

        with self.assertRaises(NodeStepException) as context:
            self.plugin.execute_node_step()

        self.assertEqual(context.exception.failure_reason, 'ARGUMENTS_MISSING')

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
            "RD_NODE_NAME": "minion_name",
        }
    )
    def test_execute_invokes_with_correct_capability(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response = MagicMock(return_value=self.HOST_RESPONSE)
        self.plugin.extract_output_for_jid.return_value = MagicMock(exit_code=0, stdout=[], stderr=[])

        self.plugin.execute_node_step()

        self.plugin.authenticate.assert_called_once_with()

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
            "RD_NODE_NAME": "minion_name",
        }
    )
    def test_execute_invokes_with_correct_secure_options(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response.return_value = self.HOST_RESPONSE
        self.plugin.extract_output_for_jid.return_value = MagicMock(exit_code=0, stdout=[], stderr=[])

        secure_options = set()
        self.plugin.extract_secure_data = MagicMock()
        self.plugin.extract_secure_data.return_value = secure_options

        self.plugin.execute_node_step()

        self.plugin.submit_job.assert_called_once_with(self.AUTH_TOKEN, self.PARAM_MINION_NAME, 'test.ping', secure_options)

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
            "RD_NODE_NAME": "minion_name",
        }
    )
    def test_execute_invokes_logout(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response.return_value = self.HOST_RESPONSE
        self.plugin.extract_output_for_jid.return_value = MagicMock(exit_code=0, stdout=[], stderr=[])

        self.plugin.execute_node_step()

        self.plugin.logoutQuietly.assert_called_once_with(self.AUTH_TOKEN)

    """
    TODO: fix test for logging and return handler
    def test_execute_makes_log_wrapper_available(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response.return_value = self.HOST_RESPONSE
        self.plugin.extract_output_for_jid.return_value = MagicMock(exit_code=0, stdout=[], stderr=[])

        self.plugin.execute_node_step()

        self.plugin.setLogWrapper.assert_called_once_with(self.pluginLogger)

    def test_set_log_wrapper(self):
        self.plugin.setLogWrapper(self.pluginLogger)
        self.assertIsNotNone(self.plugin.logWrapper)
        self.assertIs(self.pluginLogger, self.plugin.logWrapper.getUnderlyingLogger())

    def test_execute_with_successful_exit_code(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response.return_value = self.HOST_RESPONSE

        output1 = "line 1 of output"
        output2 = "line 2 of output"
        error1 = "line 1 of error"
        error2 = "line 2 of error"

        response = MagicMock(exit_code=0, stdout=[output1, output2], stderr=[error1, error2])
        self.plugin.extract_output_for_jid.return_value = response

        self.plugin.execute_node_step()

        self.returnHandlerRegistry.getHandlerFor.assert_called_once_with(self.PARAM_FUNCTION, self.plugin.defaultReturnHandler)
        self.returnHandler.extract_output_for_jid.assert_called_once_with(self.HOST_RESPONSE)

        self.plugin.log.info.assert_any_call(output1)
        self.plugin.log.info.assert_any_call(output2)
        self.plugin.log.error.assert_any_call(error1)
        self.plugin.log.error.assert_any_call(error2)

    def test_execute_with_unsuccessful_exit_code(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response.return_value = self.HOST_RESPONSE

        output1 = "line 1 of output"
        output2 = "line 2 of output"
        error1 = "line 1 of error"
        error2 = "line 2 of error"

        response = MagicMock(exit_code=1, stdout=[output1, output2], stderr=[error1, error2])
        self.plugin.extract_output_for_jid.return_value = response

        with self.assertRaises(NodeStepException) as context:
            self.plugin.execute_node_step()

        self.assertEqual(context.exception.failure_reason, 'EXIT_CODE')

        self.returnHandlerRegistry.getHandlerFor.assert_called_once_with(self.PARAM_FUNCTION, self.plugin.defaultReturnHandler)
        self.returnHandler.extract_output_for_jid.assert_called_once_with(self.HOST_RESPONSE)

        self.plugin.log.info.assert_any_call(output1)
        self.plugin.log.info.assert_any_call(output2)
        self.plugin.log.error.assert_any_call(error1)
        self.plugin.log.error.assert_any_call(error2)

    def test_execute_with_salt_response_parse_exception(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.return_value = self.OUTPUT_JID
        self.plugin.wait_for_jid_response.return_value = self.HOST_RESPONSE

        pe = SaltReturnResponseParseException("message")
        self.returnHandler.extract_output_for_jid.side_effect = pe

        with self.assertRaises(NodeStepException) as context:
            self.plugin.execute_node_step()

        self.assertEqual(context.exception.failure_reason, 'SALT_API_FAILURE')
        self.assertIs(context.exception.__cause__, pe)

        self.returnHandlerRegistry.getHandlerFor.assert_called_once_with(self.PARAM_FUNCTION, self.plugin.defaultReturnHandler)
        self.returnHandler.extract_output_for_jid.assert_called_once_with(self.HOST_RESPONSE)
    """

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
            "RD_NODE_NAME": "minion_name",
        }
    )
    def test_execute_with_salt_api_exception(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.side_effect = SaltApiException("Some message")

        with self.assertRaises(NodeStepException) as context:
            self.plugin.execute_node_step()

        self.assertEqual(context.exception.failure_reason, 'SALT_API_FAILURE')

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
            "RD_NODE_NAME": "minion_name",
        }
    )
    def test_execute_with_salt_targetting_exception(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.side_effect = SaltTargettingMismatchException("Some message")

        with self.assertRaises(NodeStepException) as context:
            self.plugin.execute_node_step()

        self.assertEqual(context.exception.failure_reason, 'SALT_TARGET_MISMATCH')

    @mock.patch.dict(os.environ, {
            "RD_OPTION_SALT_API_EAUTH": "pam",
            "RD_OPTION_SALT_USER": "user",
            "RD_OPTION_SALT_PASSWORD": "password&!@$*",
            "RD_OPTION_SALT_API_END_POINT": "https://localhost",
            "RD_CONFIG_FUNCTION": "test.ping",
            "RD_NODE_NAME": "minion_name",
        }
    )
    def test_execute_with_http_exception(self):
        self.plugin.authenticate.return_value = self.AUTH_TOKEN
        self.plugin.submit_job.side_effect = HTTPError("Some message")

        with self.assertRaises(NodeStepException) as context:
            self.plugin.execute_node_step()

        self.assertEqual(context.exception.failure_reason, 'COMMUNICATION_FAILURE')
