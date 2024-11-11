import time
import logging
from src.core.Server.server import Server
from src.core.Queue.event_queue import EventQueue


def setup_logging():
    """Setup root logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main():
    setup_logging()
    logger = logging.getLogger("ServerMain")

    try:
        queue = EventQueue()
        server = Server("localhost", 5000, queue)
        server.start_server()
        logger.info("Server started on localhost:5000")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            server.stop_server()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
