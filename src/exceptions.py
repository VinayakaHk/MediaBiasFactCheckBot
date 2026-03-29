import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger("MediaBiasBot")

def print_exception():
    logger.exception("Exception occurred")
