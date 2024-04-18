"""Slack notifier"""
import json
import sys
import os
import datetime

import logging

import requests

LIMIT = 2900
POST_TIMEOUT = 10  # sec
_logger = logging.getLogger(__name__)

LEVELS = {
        'info': {
            'level': 'INFO',
            'text_icon': ':large_blue_circle:',
            'text_icon_teams': '&#x2139;&#xFE0F;',
            'icon_emoji': 'information_source:',
            },
        'warning': {
            'level': 'WARNING',
            'text_icon': ':large_yellow_circle:',
            'text_icon_teams': '&#128310;',
            'icon_emoji': ':warning:',
            },
        'error': {
            'level': 'ERROR',
            'text_icon': ':red_circle:',
            'text_icon_teams': '&#128308;',
            'icon_emoji': ':red_circle:',
            }
        }


class SlackNotifier:
    """
    simple class for sending logger like notifications to Slack channel
    need to generate url address in "incoming WebHooks app"

    :param url: url address generated from incoming webHooks app
    :param url_teams: url address generated from teams incoming webhooks
    :param name: use __name__ method
    :param username: name of user who "sending" the message (use project name or leave empty)
    """

    def __init__(self, url: str, url_teams: str = None, name: str = None, username: str = None):

        self.url = url
        self.url_teams = url_teams
        self.body = ''
        self.body_teams = ''

        if username is None:
            self.username = os.path.basename(__file__)
        else:
            self.username = username

        if name is None:
            self.name = __name__
        else:
            self.name = name

    def set_body(self, level: str, text: str, echo: [str, list] = None) -> json:
        """sets body for message based on level"""

        level_text = LEVELS[level]['level']
        text_icon = LEVELS[level]['text_icon']
        text_icon_teams = LEVELS[level]['text_icon_teams']
        icon_emoji = LEVELS[level]['icon_emoji']
        date = datetime.datetime.now()

        text = (text[:LIMIT] + '..') if len(text) > LIMIT else text

        if echo is not None:
            if isinstance(echo, list):
                echo = ' '.join([f'@{x}' for x in echo])
            else:
                echo = f'@{echo}'
        else:
            echo = ''

        body = {
            "username": self.username,
            "icon_emoji": icon_emoji,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{text_icon} {date} [{self.name}]  {level_text}: {echo} {text}"
                    }
                }
            ]
        }

        body_teams = {'text': f"{text_icon_teams} {date} [{self.name}]  {level_text}:  {text}"}

        return body, body_teams

    def info(self, text: str, teams: bool = False, echo: [str, list] = None) -> None:
        """info level mess format"""
        level = 'info'

        self.body, self.body_teams = self.set_body(level, text, echo)
        self.send_message(teams)

    def error(self, text: str, teams: bool = False, echo: [str, list] = None) -> None:
        """error level mess format"""
        level = 'error'

        self.body, self.body_teams = self.set_body(level, text, echo)
        self.send_message(teams)

    def warning(self, text: str, teams: bool = False, echo: [str, list] = None) -> None:
        """warning level mess format"""
        level = 'warning'

        self.body, self.body_teams = self.set_body(level, text, echo)
        self.send_message(teams)

    def send_message(self, teams: bool) -> None:
        """sends wrap up message"""
        byte_length = str(sys.getsizeof(self.body))
        byte_length_teams = str(sys.getsizeof(self.body_teams))
        headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
        headers_teams = {'Content-Type': "application/json", 'Content-Length': byte_length_teams}

        send_to_slack = requests.post(self.url,
                                      data=json.dumps(self.body),
                                      headers=headers,
                                      timeout=POST_TIMEOUT
                                      )

        if send_to_slack.status_code != 200:
            _logger.error('Slack bot unreachable, status code - slack: %s',
                          send_to_slack.status_code)

        if teams:
            send_to_teams = requests.post(self.url_teams,
                                          data=json.dumps(self.body_teams),
                                          headers=headers_teams,
                                          timeout=POST_TIMEOUT
                                          )

            if send_to_teams.status_code != 200:
                _logger.error('Slack bot unreachable, status code - teams: %s',
                              send_to_teams.status_code)
