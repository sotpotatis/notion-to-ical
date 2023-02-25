"""api_client.py
Healthchecks API client. Healthchecks(.io) is a service that I have used
a lot for tracking the status of my scripts. It's a simple API,
but here is an API client to use it."""
import requests
from typing import Optional


class HealthChecks():
    def __init__(self, check_uuid:str, base_url:Optional[str]=None):
        """Initializes a Healthchecks API client.

        :param check_uuid: The UUID of the check.

        :param base_url: The server to report to. Defaults to https://hc-ping.com
        if unset."""
        if base_url is None:
            base_url = "https://hc-ping.com"
        self.base_url = base_url.strip("/")
        self.check_uuid = check_uuid

    def generate_url(self, additions:Optional[str]=None):
        """Generates a URL to ping with.

        :param additions: Any things to add at the end of the URL."""
        if additions is None:
            additions = ""
        return self.base_url + "/" + self.check_uuid + additions

    def signal_success(self):
        """Sends a simple ping/success request."""
        requests.post(self.generate_url())

    def signal_start(self):
        """Signals that a job has started."""
        requests.post(self.generate_url("/start"))

    def signal_fail(self):
        """Signals that a job has failed."""
        requests.post(self.generate_url("/fail"))

    def report_exit_code(self, exit_code:int):
        """Reports the exit code to Healthchecks.

        :param exit_code: The exit code to report-"""
        requests.post(self.generate_url(f"/{exit_code}"))
