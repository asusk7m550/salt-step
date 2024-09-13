import sys, os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.getcwd())
from salt import SaltApiNodeStepPlugin


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

    def test_wait_for_jid_submit_response(self):
        # Mocking extract_output_for_jid method
        call_count = 2

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count -= 1
            return self.HOST_RESPONSE if call_count == 0 else None

        self.plugin.extract_output_for_jid = MagicMock(side_effect=side_effect)

        result = self.plugin.wait_for_jid_response(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)

        self.assertEqual(result, self.HOST_RESPONSE)

        # Verifying interactions
        self.assertEqual(self.plugin.extract_output_for_jid.call_count, 2)
        self.plugin.timer.wait_for_next.assert_called_once()

    def test_wait_for_jid_response_interrupted(self):
        # Mocking extract_output_for_jid method
        self.plugin.extract_output_for_jid = MagicMock(return_value=None)

        # Mocking timer to throw an exception
        def side_effect():
            raise InterruptedError()

        self.plugin.timer.wait_for_next = MagicMock(side_effect=side_effect)

        # Calling the method under test
        with self.assertRaises(InterruptedError):
            self.plugin.wait_for_jid_response(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)

        # Verifying interactions
        self.plugin.extract_output_for_jid.assert_called_once_with(self.AUTH_TOKEN, self.OUTPUT_JID, self.PARAM_MINION_NAME)
