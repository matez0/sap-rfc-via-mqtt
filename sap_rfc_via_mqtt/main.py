import logging
import signal
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from sap_rfc_via_mqtt.facade import Facade
from sap_rfc_via_mqtt.messaging import MessageAdapter

logger = logging.getLogger(__name__)
logger.propagate = False

logger.info('Starting RFC service...')
facade = Facade()
message_adapter = MessageAdapter(facade)


def signal_handler(sig, frame):
    logger.info('Terminating...')

    message_adapter.close()
    facade.close()

    sys.exit(0)


for sig in [signal.SIGINT, signal.SIGTERM]:
    signal.signal(sig, signal_handler)

signal.pause()
