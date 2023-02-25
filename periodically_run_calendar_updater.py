"""periodically_run_calendar_updater.py
A very simple script to run the calendar updater on a certain time interval."""
import file_utilities, logging, calendar_updater, time
from healthchecks.api_client import HealthChecks
logger = logging.getLogger(__name__)
CONFIG = file_utilities.read_config()
if "periodic_runner" not in CONFIG:
    logger.critical("Missing configuration entry for periodic runner.")
    exit(1)
# Load config
PERIODIC_RUNNER_CONFIG = CONFIG["periodic_runner"]
RUN_EVERY = PERIODIC_RUNNER_CONFIG["run_every"] # How often to run the sync in minutes
RUN_EVERY_SECONDS = RUN_EVERY * 60 # Convert from seconds to minutes
HEALTHCHECKS_URL = PERIODIC_RUNNER_CONFIG.get("healthchecks_url", None) # Optional Healthckecks URL
HEALTHCHECKS_UUID = PERIODIC_RUNNER_CONFIG.get("healthchecks_uuid", None) # Optional Healthckecks URL
healthchecks_active = HEALTHCHECKS_UUID is not None
healthchecks_client = None
if healthchecks_active:
    healthchecks_client = HealthChecks(HEALTHCHECKS_UUID, HEALTHCHECKS_URL)

while True:
    try:
        if healthchecks_active:
            healthchecks_client.signal_start()
        calendar_updater.run()
        logger.info("Successfully ran calendar update.")
        if healthchecks_active:
            healthchecks_client.signal_success()
    except Exception as e:
        logger.critical(f"Something went wrong in the calendar updater script! Will retry after the next interation. Exception was: {e}", exc_info=True)
    logger.info(f"Waiting {RUN_EVERY} minutes until next iCal update...")
    time.sleep(RUN_EVERY_SECONDS)