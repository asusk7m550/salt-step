import sys, os
import unittest
from requests.exceptions import ConnectionError
from unittest import mock

sys.path.append(os.getcwd())
from contents.salt import SaltApiNodeStepPlugin


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

    @mock.patch('requests.post')
    def test_logout(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}

        result = self.plugin.logoutQuietly(self.AUTH_TOKEN)

        self.assertIsNone(result)
        mock_post.assert_called_once_with(
            self.PARAM_ENDPOINT+'/logout',
            headers={"X-Auth-Token": self.AUTH_TOKEN}
        )

    @mock.patch('requests.post')
    def test_logout_throws_IOException_remains_quiet(self, mock_post):
        mock_post.side_effect = ConnectionError('test ConnectionError')

        result = self.plugin.logoutQuietly(self.AUTH_TOKEN)

        self.assertIsNone(result)

    @mock.patch('requests.post')
    def test_logout_throws_interrupted_exception_remains_quiet(self, mock_post):
        mock_post.side_effect = InterruptedError('test InterruptedError')

        result = self.plugin.logoutQuietly(self.AUTH_TOKEN)

        self.assertIsNone(result)
