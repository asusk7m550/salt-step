import sys, os
import unittest
from unittest.mock import MagicMock
from unittest import mock

sys.path.append(os.getcwd())
from contents.salt import SaltApiNodeStepPlugin
from contents.salt import SaltApiException


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
        self.client = MagicMock()
        self.plugin.timer = MagicMock()

    @mock.patch('requests.get')
    def test_extract_output_for_jid(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"return": [{
            self.PARAM_MINION_NAME: self.HOST_RESPONSE
        }]}

        result = self.plugin.extract_output_for_jid(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)

        self.assertEqual(result, self.HOST_RESPONSE)
        mock_get.assert_called_once_with(
            self.PARAM_ENDPOINT+'/jobs/'+self.OUTPUT_JID,
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json"}
        )

    @mock.patch('requests.get')
    def test_extract_output_for_jid_bad_response(self, mock_get):
        mock_get.return_value.status_code = 500
        mock_get.return_value.json.return_value = {}

        result = self.plugin.extract_output_for_jid(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)

        self.assertIsNone(result)
        mock_get.assert_called_once_with(
            self.PARAM_ENDPOINT+'/jobs/'+self.OUTPUT_JID,
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json"}
        )

    @mock.patch('requests.get')
    def test_extract_output_for_jid_host_empty_response(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"return": [{
            self.PARAM_MINION_NAME: ""
        }]}

        result = self.plugin.extract_output_for_jid(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)

        self.assertEqual(result, "")
        mock_get.assert_called_once_with(
            self.PARAM_ENDPOINT+'/jobs/'+self.OUTPUT_JID,
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json"}
        )

    @mock.patch('requests.get')
    def test_extract_output_for_jid_no_response(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"return": [{}]}

        result = self.plugin.extract_output_for_jid(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)

        self.assertIsNone(result)
        mock_get.assert_called_once_with(
            self.PARAM_ENDPOINT+'/jobs/'+self.OUTPUT_JID,
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json"}
        )

    @mock.patch('requests.get')
    def test_extract_output_for_jid_multiple_responses(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"return": [{}, {}]}

        with self.assertRaises(SaltApiException):
            self.plugin.extract_output_for_jid(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)

        mock_get.assert_called_once_with(
            self.PARAM_ENDPOINT+'/jobs/'+self.OUTPUT_JID,
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json"}
        )
