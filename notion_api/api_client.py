"""notion.py
An API client to interface with Notion."""
import logging
from typing import Optional, List

import requests


class Notion:
    def __init__(self, authorization_token:str, notion_api_version:str="2022-06-28"):
        """:param authorization_token: The token used for authenticating with Notion.

        :param notion_api_version: API version to use. Note! This code was written for the default (2022-06-28).
        Other configurations might return weird results."""
        self.authorization_token = authorization_token
        self.notion_api_version = notion_api_version
        self.logger = logging.getLogger(__name__)

    def authorized_request(self, request_method, api_method, request_parameters:Optional[dict]=None, expected_status_codes:Optional[List[int]]=None,paginated:bool=False, previous_data:Optional[List]=None):
        """Sends an authorized request to Notion

        :param request_method: The request method (GET, POST, etc.)

        :param api_method: API path to request relative to the API url.

        :param request_parameters: Any other kwargs to pass to the request.request function."""
        if request_parameters is None:
            request_parameters = {}
        if expected_status_codes is None:
            expected_status_codes = [200]
        if "headers" not in request_parameters:
            request_parameters["headers"] = {}
        # Add access token and Notion version
        request_parameters["headers"].update({
            "Authorization": f"Bearer {self.authorization_token}",
            "Notion-Version": self.notion_api_version
        })
        # Add other info
        request_url = "https://api.notion.com/v1/" + api_method.strip("/")
        request_parameters.update(
            {
                "url": request_url,
                "method": request_method
            }
        )
        # Send request
        self.logger.debug(f"Sending request with parameters {request_parameters} to Notion...")
        request = requests.request(**request_parameters)
        self.logger.info("Request sent.")
        if request.status_code not in expected_status_codes:
            raise Exception(f"Notion API returned an unexpected status code: {request.status_code}. Response: {request.text}.")
        else:
            self.logger.debug("Request vas valid. Returning JSON...")
            request_json = request.json()
            # Handle pagination if needed
            if paginated and request_json["has_more"]:
                self.logger.debug("Retrieving next page...")
                if "params" not in request_parameters:
                    request_parameters["params"] = {}
                request_parameters["params"]["start_cursor"] = request_json["next_cursor"]
                return self.authorized_request(request_method, api_method, request_parameters, expected_status_codes, paginated)
            return request_json if not paginated else request_json["results"]

    def get_database(self, database_id:str) -> dict:
        """Gets a Notion database ID and returns the database content.

        :param database_id: The ID of the database."""
        response = self.authorized_request("POST", f"/databases/{database_id}/query", paginated=True)
        return response

    def extract_text_from_database_entry(self, database_entry:dict, return_type:Optional[str]=None)->Optional[str]:
        """Gets the of a certain Notion database entry. Note that this is a simplified
        function and probably needs to be modified for more complex use cases.
        Note: for multi selects, only the first value is returned.

        :param item: The item to extract text from.

        :param return_type: "text" to return the text, "id" to return the ID. Default if unset is "text"."""
        if return_type is None:
            return_type = "text"
        entry_data = database_entry[database_entry["type"]]
        # Check whether to return text or ID of entry
        if return_type == "text":
            if len(entry_data) == 0: # No data --> Return None
                return None
            elif database_entry["type"] == "title":
                return entry_data[0]["plain_text"]
            elif database_entry["type"] == "multi_select":
                return entry_data[0]["name"]
            elif database_entry["type"] == "text":
                return entry_data[0]["plain_text"]
        elif return_type == "id":
            if isinstance(entry_data, list):
                if len(entry_data) == 0:  # No data --> Return None
                    return None
                return entry_data[0]["id"]
            else:
                return entry_data["id"]