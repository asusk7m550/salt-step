import sys, os, re
import unittest
import json
from unittest import mock

sys.path.append(os.getcwd())
from salt import SaltApiNodeStepPlugin
from salt import SaltTargettingMismatchException


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
    def test_submit_job(self, mock_post):
        mock_post.return_value.status_code = 202
        mock_post.return_value.json.return_value = {"return": [{
            "jid": self.OUTPUT_JID,
            "minions": [
                self.PARAM_MINION_NAME,
                ]
            }],
            "_links": {
                "jobs": [{"href": "/jobs/"+self.OUTPUT_JID}]
            }
        }

        result = self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, self.PARAM_FUNCTION)

        self.assertEqual(result, self.OUTPUT_JID)
        mock_post.assert_called_once_with(
            self.PARAM_ENDPOINT+'/minions',
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps({
                "fun": self.PARAM_FUNCTION,
                "tgt": self.PARAM_MINION_NAME,
            })
        )

    @mock.patch('requests.post')
    def test_submit_job_with_args(self, mock_post):
        mock_post.return_value.status_code = 202
        mock_post.return_value.json.return_value = {"return": [{
            "jid": self.OUTPUT_JID,
            "minions": [
                self.PARAM_MINION_NAME,
                ]
            }],
            "_links": {
                "jobs": [{"href": "/jobs/"+self.OUTPUT_JID}]
            }
        }

        arg1 = "sdf%33&"
        arg2 = "adsf asdf"
        function = f"{self.PARAM_FUNCTION} \"{arg1}\" \"{arg2}\""

        result = self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, function)

        self.assertEqual(result, self.OUTPUT_JID)
        mock_post.assert_called_once_with(
            self.PARAM_ENDPOINT+'/minions',
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps({
                "fun": self.PARAM_FUNCTION,
                "tgt": self.PARAM_MINION_NAME,
                "arg": [arg1, arg2],
            })
        )

    @mock.patch('requests.post')
    def test_submit_job_response_code_error(self, mock_post):
        mock_post.return_value.status_code = 307
        mock_post.return_value.json.return_value = {}

        with self.assertRaises(Exception):
            self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, self.PARAM_FUNCTION)

    @mock.patch('requests.post')
    def test_submit_job_no_minions_matched(self, mock_post):
        mock_post.return_value.status_code = 202
        mock_post.return_value.json.return_value = {"return": [{
            }],
            "_links": {
                "jobs": []
            }
        }

        with self.assertRaises(SaltTargettingMismatchException):
            self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, self.PARAM_FUNCTION)

    @mock.patch('requests.post')
    def test_submit_job_minion_count_mismatch(self, mock_post):
        mock_post.return_value.status_code = 202
        mock_post.return_value.json.return_value = {"return": [{
            "jid": self.OUTPUT_JID,
            "minions": [
                "foo",
                "bar"
                ]
            }],
            "_links": {
                "jobs": [{"href": "/jobs/"+self.OUTPUT_JID}]
            }
        }

        with self.assertRaises(SaltTargettingMismatchException):
            self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, self.PARAM_FUNCTION)

    @mock.patch('requests.post')
    def test_submit_job_minion_id_mismatch(self, mock_post):
        mock_post.return_value.status_code = 202
        mock_post.return_value.json.return_value = {"return": [{
            "jid": self.OUTPUT_JID,
            "minions": [
                "someotherhost"
                ]
            }],
            "_links": {
                "jobs": [{"href": "/jobs/"+self.OUTPUT_JID}]
            }
        }

        with self.assertRaises(SaltTargettingMismatchException):
            self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, self.PARAM_FUNCTION)

    @mock.patch('requests.post')
    def test_submit_job_hides_secure_options(self, mock_post):

        secret = ("greatgooglymoogly5f5DEyIKEyde\n"
                  "wjXpeCuqX89nAaGwjSphBZsjlQldheNDra1+FqOJfBaKK3Zr1FKe5mr1si\n\n"
                  "QCqCM11FLV2/jdMS/c7aMwfhBvapN2Rh76LBRysm\n\n"
                  "LV0prx1jqbdb8/UyxTyMlfJpRtn09wy+rL\n\n"
                  "f6qGO+Srwiy5/7lgNFJ7t3xT1w5NA==\n")
        secure_options = {"foo": secret}

        mock_post.return_value.status_code = 202
        mock_post.return_value.json.return_value = {"return": [{
            "jid": self.OUTPUT_JID,
            "minions": [
                self.PARAM_MINION_NAME,
                ]
            }],
            "_links": {
                "jobs": [{"href": "/jobs/"+self.OUTPUT_JID}]
            }
        }

        command = "cmd.run"
        function = f"{command} 'echo {secret}'"

        with self.assertLogs(level='DEBUG') as cm:

            result = self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, function, secure_options=secure_options)

            data = json.dumps({
                "fun": command,
                "tgt": self.PARAM_MINION_NAME,
                "arg": ["echo ****"],
            })

            for line in cm.output:

                match = re.match(r'DEBUG:salt:Submitting job with arguments \[(.*)\]', line)
                if match is not None:
                    self.assertEqual(data.replace('"', "'"), match[1])

        self.assertEqual(result, self.OUTPUT_JID)
        mock_post.assert_called_once_with(
            self.PARAM_ENDPOINT+'/minions',
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps({
                "fun": command,
                "tgt": self.PARAM_MINION_NAME,
                "arg": [f"echo {secret}"],
            })
        )

    @mock.patch.dict(os.environ, {"RD_SECUREOPTION_foo": "bar"})
    def test_extract_secure_data(self):

        result = self.plugin.extract_secure_data()
        self.assertEqual(result, {"foo":  "bar"})

    def test_extract_secure_data_no_secure_options(self):

        result = self.plugin.extract_secure_data()
        self.assertEqual(result, {})

    @mock.patch('requests.post')
    def test_assert_that_submit_salt_job_attempted_successfully(self, mock_post):

        mock_post.return_value.status_code = 202
        mock_post.return_value.json.return_value = {"return": [{
            "jid": self.OUTPUT_JID,
            "minions": [
                self.PARAM_MINION_NAME,
                ]
            }],
            "_links": {
                "jobs": [{"href": "/jobs/"+self.OUTPUT_JID}]
            }
        }

        self.plugin.submit_job(self.AUTH_TOKEN, self.PARAM_MINION_NAME, self.PARAM_FUNCTION)

        mock_post.assert_called_once_with(
            self.PARAM_ENDPOINT+'/minions',
            headers={"X-Auth-Token": self.AUTH_TOKEN, "Accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps({
                "fun": self.PARAM_FUNCTION,
                "tgt": self.PARAM_MINION_NAME,
            })
        )
