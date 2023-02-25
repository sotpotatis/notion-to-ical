"""server.py
A simple server that hosts the calendars."""
import os

import file_utilities, logging
from flask import Flask, request, Response, send_from_directory
from http import HTTPStatus
logger = logging.getLogger(__name__)
# Read configuration
config = file_utilities.read_config()
SERVER_CONFIGURATION = config["server"]
ENABLE_SERVER = SERVER_CONFIGURATION["enabled"]
RUN_DEBUG = SERVER_CONFIGURATION["debug"]
CALENDAR_URL = SERVER_CONFIGURATION["calendar_url"]
AUTHENTICATION_CONFIGURATION = SERVER_CONFIGURATION["authentication"]
AUTHENTICATION_ENABLED = AUTHENTICATION_CONFIGURATION["enabled"]
AUTHENTICATION_KEY = AUTHENTICATION_CONFIGURATION["key"]
DEFAULT_AUTHENTICATION_KEY = "super_secret_key_here" # The default until a key is set by the user
def create_app()->Flask:
    """Creates and returns the server application."""
    # Create app
    app = Flask(__name__)
    # Create helper functions
    def validate_authentication(sent_request:request)->tuple:
        """Validates whether a sent request passes the authentication
        needs set up on the server.


        :param sent_request: The request that was sent."""
        if AUTHENTICATION_ENABLED:
            if "key" not in sent_request.args:
                logger.warning(f"Received unauthenticated request from remote address {sent_request.remote_addr}")
                return False, HTTPStatus.FORBIDDEN, "No authentication provided. This incident has been logged."
            elif sent_request.args["key"] != AUTHENTICATION_KEY:
                logger.warning(f"Received invalidly authenticated request from remote address {sent_request.remote_addr}")
                return False, HTTPStatus.FORBIDDEN, "Invalid authentication provided. This incident has been logged."
        # If authentication was valid
        return True, None, None
    # Create routes
    @app.route("/")
    def index():
        """Return "I am a Teapot" on the index page.
        I had to use this somewhere, sometime, and I felt like it here."""
        return Response("""NotionToIcal is active. I'm busy serving calendar requests.
        I'm also a teapot! See https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/418.
        And have a nice day!""", status=HTTPStatus.IM_A_TEAPOT)

    @app.route(CALENDAR_URL)
    def return_calendar(requested_calendar:str):
        """Returns a requested calendar."""
        request_valid, status_code, error_text = validate_authentication(request)
        if not request_valid:
            return Response(error_text, status=status_code)
        logger.info(f"Returning requested calendar {requested_calendar}...")
        if ".ics" not in requested_calendar:
            requested_calendar = requested_calendar + ".ics"
        if requested_calendar not in os.listdir(file_utilities.ICAL_DIRECTORY):
            logger.info("Calendar was not found. Returning 404...")
            return HTTPStatus.NOT_FOUND
        else:
            logger.info("Calendar was found. Returning...")
            return send_from_directory(file_utilities.ICAL_DIRECTORY,
                                       requested_calendar, mimetype="text/calendar")
    # Return the generated app
    return app

if not AUTHENTICATION_ENABLED:
    logger.warning("""You have disabled authentication! This will make ANYONE with the link to your calendar or with some"
                   web scraping interest be able to find and READ all your calendar entries. Make sure that this is the intended
                   behavior. If not, enable authentication in the server configuration file.""")
elif AUTHENTICATION_ENABLED and AUTHENTICATION_KEY == DEFAULT_AUTHENTICATION_KEY:
    logger.critical("""You have authentication enabled for the calendar URL(s), but you have not changed the authentication key.
    You have to change the setting server.authentication.key in order for the server to start.""")
    exit(1)
if RUN_DEBUG:
    logger.info("Running debug server...")
    logger.warning("""The debug server is enabled. This server should only be used 
    locally on your computer and NOT in a production environment. For production environments,
    use a WSGI server (like Gunicorn)""")
    # All debug server parameters are optional and will otherwise be filled out with defaults.
    DEBUG_SERVER_HOST = SERVER_CONFIGURATION.get("debug_server_host", "127.0.0.1")
    DEBUG_SERVER_PORT = SERVER_CONFIGURATION.get("debug_server_port", 80)
    app = create_app()
    app.run(debug=True, host=DEBUG_SERVER_HOST, port=DEBUG_SERVER_PORT)
logger.info("""💅✨The server is ready:) Just run a WSGI server and we'll take it from there.
An example (running with Gunicorn):
gunicorn server:create_app()
""")