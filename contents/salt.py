#!/usr/bin/python3

import requests
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


class SaltApiNodeStepPlugin(object):

    def __init__(self, endpoint=None, username=None, password=None, eauth='auto'):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.eauth = eauth

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
