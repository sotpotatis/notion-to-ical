"""file_utilities.py
The project uses files for configuring the behavior of the code,
storing calendars, etc. This is a little helper library to help out with it."""
import json
import os, logging
import random
import string
from typing import List

import toml

logger = logging.getLogger(__name__)
# Basic paths
SCRIPT_PATH = os.path.realpath(__file__)
SCRIPT_DIRECTORY = os.path.dirname(SCRIPT_PATH)
DATA_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "data")
CONFIG_PATH = os.path.join(SCRIPT_DIRECTORY, "config.toml")
UID_MAPPINGS_PATH = os.path.join(DATA_DIRECTORY, ".notion_to_ical_uids")
ICAL_DIRECTORY = os.path.join(DATA_DIRECTORY, "icals")
if not os.path.exists(DATA_DIRECTORY):
    logger.info("Creating data directory...")
    os.mkdir(DATA_DIRECTORY)
    logger.info("Data directory created.")
if not os.path.exists(ICAL_DIRECTORY):
    logger.info("Creating directory for storing generated Icals...")
    os.mkdir(ICAL_DIRECTORY)
# Utility functions


def read_config()->dict:
    """Reads and returns the configuration file.

    :returns The content of the configuration file as a dictionary."""
    return toml.loads(open(CONFIG_PATH, encoding="UTF-8").read())


def write_ical(ical_name:str, content) -> None:
    """Writes to an iCal calendar file.

    :param ical_name: The name of the file to write to.

    :param content: The content to write."""
    if not ical_name.endswith(".ics"): # Add file ending if missing
        ical_name += ".ics"
    with open(os.path.join(ICAL_DIRECTORY, ical_name), "wb") as ical_file:
        ical_file.write(content)
    logger.debug(f"Wrote content to ical file {ical_file}.")


# iCal calendars and events should have a UID.
# Previously, you could just throw in a hostname or something, but as said on this
# website: https://icalendar.org/New-Properties-for-iCalendar-RFC-7986/5-3-uid-property.html
# this is no longer recommended practise.
# Therefore, I implemented a .uid_mappings file to map Notion IDs to a UID.
def read_uid_file()->dict:
    """Reads the UID file and returns its mappings as a dictionary.

    :returns UIDs mapped to IDs in a dictionary."""
    return json.loads(open(UID_MAPPINGS_PATH, "r", encoding="UTF-8").read())

def write_uid_file_content(uid_mappings:dict)->None:
    """Writes UIDs mapped to IDs to the UID file.

    :param uid_mappings: UID mappings to write."""
    with open(UID_MAPPINGS_PATH, "w", encoding="UTF-8") as uid_mappings_file:
        uid_mappings_file.write(json.dumps(uid_mappings))

def perform_uid_file_cleaning():
    """Cleans the UID file for old entries."""
    config = read_config()
    # In the UID file, there is a tracking variable named "last_accessed_at".
    # It is an integer. There is also a counter variable in the UID file that counts
    # how many times the scripts have been run. By configuring a delete_old_events_after,
    # it is set how much smaller the counter variable in a UID can be compared to how often
    # the script is ran before a new ID is assigned.
    clean_uid_every = config["general"].get("cleaning_factor", 20) # (default if unset is 20)
    uids = read_uid_file()
    new_uids = uids
    access_counter = uids["counter"]
    for uid, uid_data in uids["mappings"].items():
        if uid_data["last_accessed_at"] < access_counter - clean_uid_every:
            logger.debug(f"Performing housekeeping: deleting {uid} from UID file...")
            del new_uids["mappings"][uid]
    write_uid_file_content(new_uids)

def generate_unique_uid(previous_uids:List[str]):
    """Generates a unique UID.

    :param previous_uids: Any previous UIDs that should not be generaated."""
    while True:
        # Sorry, I just had to make a fun one liner :P
        generated_id = "".join(["".join([random.choice(string.ascii_letters) for i in range(16)]) + "-"
                               for i in range(4)]).strip("-")
        if generated_id not in previous_uids:
            break
    return generated_id

def get_uid(id:str)->str:
    """Gets the UID for a certain ID. The UID will be created if not exists.

    :param id: A unique ID to map to a corresponding ID."""
    uid_file_content = read_uid_file()
    uid_mappings = uid_file_content["mappings"]
    previous_uids = [previous_mapping["uid"] for previous_mapping in uid_mappings.values()]
    if id in uid_file_content["mappings"]:
        uid_data = uid_mappings[id]
    else:
        # Create new UID and add to the file
        uid_data = {
            "uid": generate_unique_uid(previous_uids),
            "last_accessed_at": None
        }
        uid_file_content["mappings"][id] = uid_data
    # Update counter variable (see above for more information)
    uid_data["last_accessed_at"] = uid_file_content["counter"]
    write_uid_file_content(uid_file_content)
    return uid_data["uid"]

def update_uid_file_counter()->None:
    """Updates the counter in the UID file. See above for more information."""
    uid_file_content = read_uid_file()
    uid_file_content["counter"] += 1
    write_uid_file_content(uid_file_content)
    logger.debug("Updated UID file counter.")

if not os.path.exists(UID_MAPPINGS_PATH):
    logger.info("Creating file for UID mappings...")
    write_uid_file_content({
        "mappings": {},
        "counter": 0
    })
    logger.info("UID mappings file created.")