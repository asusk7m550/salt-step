#!/usr/bin/python3

import sys, os
import requests
import json
import shlex
import logging
from urllib.parse import urlparse

sys.path.append(os.getcwd())
from contents.util.exponential_backoff_timer import ExponentialBackoffTimer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


# define Python user-defined exceptions
class NodeStepException(Exception):
    """
    Represents an exception in the node step.
    """

    def __init__(self, message, failure_reason, nodename):

        self.message = message
        self.failure_reason = failure_reason
        self.nodename = nodename
        super().__init__(self.message)


class SaltTargettingMismatchException(Exception):
    """
    Represents a mismatch between salt was told to target and what salt actually targetted.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SaltApiException(Exception):
    """
    Represents an exception dispatching to salt-api.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SaltApiNodeStepFailureReason(Exception):

    def __init__(self, error_type, message):

        if error_type not in [
            'EXIT_CODE',
            'ARGUMENTS_MISSING',
            'ARGUMENTS_INVALID',
            'AUTHENTICATION_FAILURE',
            'COMMUNICATION_FAILURE',
            'SALT_API_FAILURE',
            'SALT_TARGET_MISMATCH',
            'INTERRUPTED'
        ]:
            raise ValueError('FailureReason %s now known' % error_type)

        self.error_type = error_type
        self.message = message

    def __str__(self):
        return self.error_type + ":" + self.message


class SaltStepValidationException(NodeStepException):
    """
    Represents an exception when validating a field for plugin execution.
    """

    def __init__(self, fieldname, message, failure_reason, nodename):
        self.fieldname = fieldname
        self.message = message
        self.failure_reason = failure_reason
        self.nodename = nodename

    def __dict__(self):
        return {'reason': self.reason, 'fieldname': self.fieldname}


class SaltApiNodeStepPlugin(object):

    def __init__(self, endpoint=None, username=None, password=None, eauth='auto'):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.eauth = eauth
        self.timer = ExponentialBackoffTimer(500, 15000)

    def extract_secure_data(self):
        """
        Return collection of secure data values from data context.
        """

        secureOptions = {}
        for envVariable in os.environ:
            if envVariable[0:16] == 'RD_SECUREOPTION_':
                secureOptions[envVariable[16:]] = os.environ.get(envVariable)

        return secureOptions

    def submit_job(self, authToken, minionId, function, secure_options={}):
        """
        Submits the job to salt-api using the class function and args
        """

        # Parse the function into its arguments
        args = shlex.split(function)
        params = {
            'fun': args[0],
            'tgt': minionId
        }
        printable_params = params.copy()

        # Add the arguments to the params
        for i in range(1, len(args)):
            value = args[i]
            params.setdefault('arg', []).append(value)
            for k, s in secure_options.items():
                value = value.replace(s, "****")
            printable_params.setdefault('arg', []).append(value)

        headers = {
            "X-Auth-Token": authToken,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{self.endpoint}/minions"

        logger.debug("Submitting job with arguments [%s]", printable_params)
        logger.info("Submitting job with salt-api endpoint: [%s]", url)

        response = requests.post(url,
                                 headers=headers,
                                 data=json.dumps(params))

        if response.status_code == 202:

            try:
                minions_size = len(response.json()['return'][0]['minions'])
                minions_output = response.json()['return'][0]['minions']
            except KeyError:
                minions_size = 0
                minions_output = None

            if minions_size != 1:
                raise(SaltTargettingMismatchException("Expected minion delegation count of 1, was %d. Full minion string: (%s)" % (minions_size, minions_output)))

            if minionId not in response.json()['return'][0]['minions']:
                raise(SaltTargettingMismatchException("Minion dispatch mis-match. Expected:%s,  was:%s" % (minionId, minions_output)))

            return response.json()["return"][0]["jid"]
        else:
            raise Exception("Expected response code %d, received %d. %s", 202, response.status_code, response.text())

    def validate(self):

        if not self.endpoint:
            raise SaltApiNodeStepFailureReason('ARGUMENTS_MISSING', 'SALT_API_END_POINT is a required property')

        if not self.function:
            raise SaltApiNodeStepFailureReason('ARGUMENTS_MISSING', 'FUNCTION is a required property')

        if not self.eauth:
            raise SaltApiNodeStepFailureReason('ARGUMENTS_MISSING', 'SALT_API_EAUTH is a required property')

        if not self.username:
            raise SaltApiNodeStepFailureReason('ARGUMENTS_MISSING', 'SALT_USER is a required property')

        if not self.password:
            raise SaltApiNodeStepFailureReason('ARGUMENTS_MISSING', 'SALT_PASSWORD is a required property')

        try:
            parsed_url = urlparse(self.endpoint)
            if parsed_url.scheme not in ['http', 'https']:
                raise SaltStepValidationException('SALT_API_END_POINT', f"{self.endpoint} is not a valid endpoint", 'ARGUMENTS_INVALID', '')
        except Exception:
            raise SaltStepValidationException('SALT_API_END_POINT', f"{self.endpoint} is not a valid endpoint", 'ARGUMENTS_INVALID', '')

    def wait_for_jid_response(self, authToken, jid, minionId):
        jid_resource = f"{self.endpoint}/jobs/{jid}"
        logger.info("Polling for job status with salt-api endpoint: [%s]", jid_resource)
        while True:
            response = self.extract_output_for_jid(authToken, jid, minionId)
            if response is not None:
                return response

            self.timer.wait_for_next()
        pass

    def extract_output_for_jid(self, authToken, jid, minionId):
        """
        Extracts the minion job response by calling the job resource.
        :param authToken: The token of the session
        :param jid: The job id
        :param minionId: The minion id
        :return the host response or null if none is available encoded in json.
        """

        headers = {
            "X-Auth-Token": authToken,
            "Accept": "application/json"
        }

        url = f"{self.endpoint}/jobs/{jid}"

        response = requests.get(url,
                                headers=headers)

        if response.status_code == 200:

            responses = response.json()["return"]

            if len(responses) > 1:
                raise(SaltApiException("Too many responses received: %s" % response.json()))

            elif len(responses) == 1:
                minion_response = responses[0]
                if minionId in minion_response:
                    logger.debug("Received response for jobs/%s = %s", jid, response.json())
                    return minion_response[minionId]

    def authenticate(self):
        """
        Authenticate with the Salt API and store the token
        """

        data = {
            "username": self.username,
            "password": self.password,
            "eauth": self.eauth
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        url = f"{self.endpoint}/login"

        logger.info("Authenticating with salt-api endpoint: [%s]", url)

        response = requests.post(url,
                                 headers=headers,
                                 data=json.dumps(data))

        if response.status_code == 200:
            try:
                token = response.json()["return"][0]["token"]
                return token
            except NameError:
                raise Exception(f"Error fetching token: ${response.text()}")
            except Exception as e:
                print("Error:", e)
                raise Exception(f"Error fetching token: ${response.text()}")
        elif response.status_code == 401:
            return None
        else:
            raise Exception(f"Unexpected failure interacting with salt-api {response.text()}")

    def logoutQuietly(self, authToken):
        """
        Remove or invalidate sessions
        :header authToken: The token of the session
        """

        headers = {
            "X-Auth-Token": authToken,
        }

        url = f"{self.endpoint}/logout"

        logger.info("Logging out with salt-api endpoint: [%s]", url)

        try:
            requests.post(url,
                          headers=headers)
        except requests.exceptions.ConnectionError as e:
            logger.warning("Encountered exception (%s) while trying to logout. Ignoring...", e)
            pass

        except InterruptedError:
            logger.warning("Interrupted while trying to logout.")
