"""STGPX - Spots-Tracker Downloader"""

import sys
from argparse import Namespace, ArgumentParser
from typing import List
import logging

log = logging.getLogger(__name__)


def argparse(argv: List[str]) -> Namespace:
    """Parse command line arguments."""
    parser = ArgumentParser(description="STGPX - Spots-Tracker Downloader")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (up to 3 times)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        default=0,
        help="Increase debugging  (up to 3 times)",
    )
    parser.add_argument("-l", "--logfile", action="store", help="Debug logfile name")
    return parser.parse_args(argv)


def setLogging(args: Namespace) -> None:
    """Enable logging levels."""
    # If a logfile has been defined, create a logger logging to this file and
    # set the level based on the debug flag.
    log.setLevel(logging.DEBUG)
    if args.logfile:
        # Create a logger that logs to a file.
        logfileHandler = logging.FileHandler(args.logfile, mode="w")
        logfileFormatter = logging.Formatter(
            "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
        )
        logfileHandler.setFormatter(logfileFormatter)
        log.addHandler(logfileHandler)
        if args.debug >= 3:
            logfileHandler.setLevel(logging.DEBUG)
        elif args.debug == 2:
            logfileHandler.setLevel(logging.INFO)
        elif args.debug == 1:
            logfileHandler.setLevel(logging.WARNING)
        else:
            logfileHandler.setLevel(logging.ERROR)

    # Set-up logging to console with level based on the verbose flag.
    consoleHandler = logging.StreamHandler()
    consoleFormatter = logging.Formatter("%(message)s")
    consoleHandler.setFormatter(consoleFormatter)
    log.addHandler(consoleHandler)
    if args.verbose >= 3:
        consoleHandler.setLevel(logging.DEBUG)
    elif args.verbose == 2:
        consoleHandler.setLevel(logging.INFO)
    elif args.verbose == 1:
        consoleHandler.setLevel(logging.WARNING)
    else:
        consoleHandler.setLevel(logging.ERROR)


def main(argv: List[str]):
    args: Namespace = argparse(argv)
    setLogging(args)
    log.debug("STGPX - Spots-Tracker Downloader")
    log.warning("A warning")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
