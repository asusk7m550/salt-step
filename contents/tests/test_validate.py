import sys, os
import unittest

sys.path.append(os.getcwd())
from contents.salt import SaltApiNodeStepPlugin
from contents.salt import SaltStepValidationException


class TestSaltApiNodeStepPlugin(unittest.TestCase):

    def setUp(self):

        self.PARAM_ENDPOINT = "https://localhost"
        self.PARAM_EAUTH = "pam"
        self.PARAM_MINION_NAME = "minion"
        self.PARAM_FUNCTION = "some.function"
        self.PARAM_USER = "user"
        self.PARAM_PASSWORD = "password&!@$*"
        self.AUTH_TOKEN = "123qwe"
        self.OUTPUT_JID = "20130213093536481553"
        self.HOST_RESPONSE = "\"some response\""

        self.plugin = SaltApiNodeStepPlugin(self.PARAM_ENDPOINT, self.PARAM_USER, self.PARAM_PASSWORD)

        self.plugin.function = self.PARAM_FUNCTION
        self.plugin.eauth = self.PARAM_EAUTH

    def test_validate_all_arguments(self):

        self.plugin.function = self.PARAM_FUNCTION
        self.plugin.eauth = self.PARAM_EAUTH

        self.plugin.validate()

    def test_validate_checks_valid_endpoint_http_url(self):

        self.plugin.endpoint = 'http://some.machine.com'

        self.plugin.validate()

    def test_validate_checks_valid_endpoint_https_url(self):

        self.plugin.endpoint = 'https://some.machine.com'

        self.plugin.validate()

    def test_validate_checks_invalid_endpoint_url(self):

        self.plugin.endpoint = 'ftp://some.machine.com'

        with self.assertRaises(SaltStepValidationException) as cm:
            self.plugin.validate()

        self.assertEqual(cm.exception.failure_reason, 'ARGUMENTS_INVALID')
        self.assertEqual(cm.exception.message, 'ftp://some.machine.com is not a valid endpoint')
