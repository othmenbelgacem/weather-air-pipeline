import logging

import extract
import load
import transform

logger = logging.getLogger(__name__)


def main():
    extract.main()          # exits with code 1 if extraction fails
    df = transform.run()
    load.load(df)
    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()