"""calendar_updater.py
Performs the main calendar syncing"""
import calendar
import datetime
import json
from configparser import ConfigParser
from notion_api.api_client import Notion
from icalendar import Calendar, Event
import os, logging, file_utilities, pytz

def run():
    """Runs the calendar updater."""
    # Set up logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Starting calendar syncing...")
    logger.info("Reading configuration file...")
    # Read configuration
    config = file_utilities.read_config()
    NOTION_CONFIGURATION = config["notion"]
    GENERAL_SETTINGS = config["general"]
    # Get main details
    NOTION_TOKEN = NOTION_CONFIGURATION["token"]
    NOTION_DATABASE_ID = NOTION_CONFIGURATION["database_id"]
    DEFAULT_TIMEZONE = GENERAL_SETTINGS["default_timezone"]
    # Get data keys
    NOTION_DATA_KEYS = NOTION_CONFIGURATION["keys"]
    NOTION_TITLE_KEY = NOTION_DATA_KEYS["title"]
    NOTION_DATE_KEY = NOTION_DATA_KEYS["date"]
    NOTION_CALENDAR_KEY = NOTION_DATA_KEYS["calendar"]
    NOTION_DESCRIPTION_KEY = NOTION_DATA_KEYS.get("description") # (description key is an optional setting)
    # Get calendar mappings
    NOTION_CALENDAR_SETTINGS = NOTION_CONFIGURATION["calendars"]
    NOTION_CALENDAR_MAPPINGS = NOTION_CALENDAR_SETTINGS["mappings"]
    # Create mapping calendar ID --> icalendar.Calendar() object
    calendar_mappings = {}
    for calendar_id, calendar_information in NOTION_CALENDAR_MAPPINGS.items():
        new_calendar = Calendar()
        # Set required attributes
        new_calendar.add("prodid", "-//sotpotatis//NotionToIcal//")
        new_calendar.add("version", "2.0")
        # Get or generate a UID for the calendar
        new_calendar.add("uid", file_utilities.get_uid(calendar_id))
        # Add optional calendar parameters
        optional_calendar_parameters = ["name", "description"]
        for optional_calendar_parameter in optional_calendar_parameters:
            if optional_calendar_parameter in calendar_information:
                new_calendar.add(optional_calendar_parameter, calendar_information[optional_calendar_parameter])
        calendar_mappings[calendar_id] = new_calendar
    logger.info("✅ Configuration file read.")
    # Set up API
    notion = Notion(NOTION_TOKEN)
    UTC = pytz.timezone("UTC") # Timezones are converted to UTC to avoid confusions in calendar apps
    # Get database
    logger.info("Retrieving database...")
    database_content = notion.get_database(NOTION_DATABASE_ID)
    logger.info("Database retrieved.")
    logger.debug(f"Database content: {database_content}")
    # Iterate over every object in the database and create a calendar
    for entry in database_content:
        logger.debug(f"Parsing entry {entry}...")
        if entry["object"] == "page":
            properties = entry["properties"]
            # Grab details
            entry_title = notion.extract_text_from_database_entry(properties[NOTION_TITLE_KEY])
            entry_description = None
            if NOTION_DESCRIPTION_KEY is not None:
                entry_description = notion.extract_text_from_database_entry(properties[NOTION_DESCRIPTION_KEY])
            entry_date = properties[NOTION_DATE_KEY]["date"]
            entry_calendar = notion.extract_text_from_database_entry(properties[NOTION_CALENDAR_KEY], "id")
            # Validate that required keys are present
            required_entries_validation = [entry_value is not None for entry_value in [entry_title, entry_date, entry_calendar]]
            required_entries_valid = all(required_entries_validation)
            if not required_entries_valid:
                logger.warning("Missing required entries for a page. Skipping...")
                logger.debug(f"(entry validations are: {required_entries_validation})")
                continue
            # Check if calendar exists
            if entry_calendar in NOTION_CALENDAR_MAPPINGS:
                entry_ical_target = entry_calendar
            else:
                logger.warning(f"No calendar key exists for {entry_calendar}. Fallback will be used.")
                entry_ical_target = NOTION_CALENDAR_MAPPINGS[NOTION_CALENDAR_SETTINGS["fallback"]]
            # Check and handle date
            entry_start_date = entry_date["start"]
            entry_end_date = entry_date["end"]
            timezone = entry_date["time_zone"]
            # Get page URL and ID
            page_url = entry["url"]
            page_id = entry["id"]
            # Add all the details
            new_event = Event()
            new_event.add("summary", entry_title)
            # Add a "dtstamp" parameter used for caching etc.
            # Note that this parameter is updated every time the file is written.
            # See https://bugzilla.mozilla.org/show_bug.cgi?id=303663
            now_utc = datetime.datetime.now().astimezone(pytz.UTC)
            new_event.add("dtstamp", now_utc)
            new_event.add("last-modified", now_utc)
            if entry_description is not None:
                new_event.add("comment", entry_description)
            if entry_start_date == entry_end_date is None:
                logger.warning(f"Skipping an event that is missing a start and end date. ({entry_title})...")
                continue
            if entry_start_date is not None:
                entry_start_date = datetime.datetime.fromisoformat(entry_start_date).astimezone(UTC)
                new_event.add("dtstart", entry_start_date)
            if entry_end_date is not None:
                entry_end_date = datetime.datetime.fromisoformat(entry_end_date).astimezone(UTC)
                new_event.add("dtend", entry_end_date)
            # Get a unique UID for the event
            event_uid = file_utilities.get_uid(page_id)
            new_event.add("uid", event_uid)
            # Finally, some added things are not automatically converted to iCal (which is weird).
            # I created a quick for loop to do the conversion manually:
            final_event = Event()
            for entry, value in new_event.items():
                final_event[entry] = new_event[entry].to_ical()
            new_event = final_event
            calendar_mappings[entry_ical_target].add_component(new_event)
    logger.info("Writing updated calendars...")
    for calendar_id, calendar_object in calendar_mappings.items():
        calendar_target_file = NOTION_CALENDAR_MAPPINGS[calendar_id]["ics_file"]
        file_utilities.write_ical(calendar_target_file, calendar_object.to_ical())
        logger.info(f"Calendar {calendar_target_file} saved.")
    # Do some UID-related cleaning (see file_utilities.py file)
    file_utilities.perform_uid_file_cleaning()
    file_utilities.update_uid_file_counter()


if __name__ == "__main__":
    run()