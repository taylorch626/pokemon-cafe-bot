#!/usr/bin/env bash

import os
import requests

# PUSHOVER_API_ENDPOINT: str = "https://api.pushover.net/1/messages.json"
# API_HEADERS: dict = {"Content-Type": "application/json"}
# PUSH_TOKEN: str = os.getenv("PUSHOVER_PUSH_TOKEN", None)
# PUSH_USER: str = os.getenv("PUSHOVER_PUSH_USER", None)
    
class PushoverNotifications:
    """
    Push Notifications via Pushover + a Logging Handler
    """

    def __init__(self,
        # level: Optional[int] = logging.INFO,
        ):
        """
        Instantiate with a Requests Session
        """
        self.session = requests.Session()
        self.api_endpoint = "https://api.pushover.net/1/messages.json"
        self.session.headers.update({"Content-Type": "application/json"})
        # self.pushover_user = 'u1snc8q7r1pphnqy2rynp436h4pdfu'  # TODO: fix this so it's not hardcoded
        self.pushover_user = os.getenv("PUSHOVER_PUSH_USER", None)
        if self.pushover_user in [None, ""]:
            raise EnvironmentError("Pushover user not found!")
        self.pushover_user_2 = os.getenv("PUSHOVER_PUSH_USER_2", None)
        if self.pushover_user in [None, ""]:
            raise EnvironmentError("2nd Pushover user not found!")
        #self.pushover_token = 'a2sczq9yobu7w6pxpuc4941rriy7t7'  # TODO: fix this so it's not hardcoded
        self.pushover_token = os.getenv("PUSHOVER_PUSH_TOKEN", None)
        if self.pushover_token in [None, ""]:
            raise EnvironmentError('Pushover token not found!')

    def send_message(self, message: str, **kwargs) -> requests.Response:
        """
        Send a message via Pushover - if environment variables are configured

        Parameters
        ----------
        message: str

        Returns
        -------
        requests.Response
        """
        response = self.session.post(
            url=self.api_endpoint,
            params=dict(
                token=self.pushover_token,
                user=self.pushover_user,
                message=message,
                **kwargs,
            ),
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as he:
            raise ConnectionError(response.text) from he
            
        response_2 = self.session.post(
            url=self.api_endpoint,
            params=dict(
                token=self.pushover_token,
                user=self.pushover_user_2,
                message=message,
                **kwargs,
            ),
        )
        try:
            response_2.raise_for_status()
        except requests.HTTPError as he:
            raise ConnectionError(response_2.text) from he
        return (response, response_2)
        
# pusher = PushoverNotifications()
# message = ''.join(['• 0 openings for 9-30\n', '• 5 openings for 10-1\n', '• 2 openings for 10-3\n'])
# message = '\u2022 Longer message\nwith other types of\ncharacters'
# pusher.send_message(title='Opening(s) Found!', message=message, priority=1)
# pusher.send_message(message='Test message', priority=1)
