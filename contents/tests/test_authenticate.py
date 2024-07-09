import sys, os, time
import unittest
import json
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

        self.plugin = SaltApiNodeStepPlugin(self.PARAM_ENDPOINT, self.PARAM_USER, self.PARAM_PASSWORD, self.PARAM_EAUTH)

    @mock.patch('requests.post')
    def test_authenticate_with_ok_response_code(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"return": [{
            "token": self.AUTH_TOKEN,
            "start": time.time(),
            "expire": time.time()+(12*60*60),
            "user": self.PARAM_USER,
            "eauth": self.PARAM_EAUTH,
            "perms": [
                "grains.*",
                "status.*",
                "sys.*",
                "test.*"
            ]
        }]}

        result = self.plugin.authenticate()
        self.assertEqual(result, self.AUTH_TOKEN)
        mock_post.assert_called_once_with(
            self.PARAM_ENDPOINT+'/login',
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps({
                "username": self.PARAM_USER,
                "password": self.PARAM_PASSWORD,
                "eauth": self.PARAM_EAUTH,
            })
        )

    @mock.patch('requests.post')
    def test_authenticate_failure(self, mock_post):
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {}

        result = self.plugin.authenticate()
        self.assertIsNone(result)

    @mock.patch('requests.post')
    def test_authentication_failure_on_internal_server_error(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.json.return_value = {}

        with self.assertRaises(Exception):
            self.plugin.authenticate()
