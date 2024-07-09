#!/usr/bin/python3

import requests
import json
import logging
from urllib.parse import urlparse

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
