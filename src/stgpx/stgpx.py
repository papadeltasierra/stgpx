"""STGPX - Sports-Tracker Downloader"""

import sys
from argparse import Namespace, ArgumentParser
from typing import List
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    parser.add_argument("-m", "--mode", action="store", help="Operation mode")

    loginGroup = parser.add_argument_group("login", "Login to Sports-Tracker")
    loginGroup.add_argument(
        "-u", "--username", action="store", help="Username for Sports-Tracker"
    )
    loginGroup.add_argument(
        "-p", "--password", action="store", help="Password for Sports-Tracker"
    )

    browserGroup = parser.add_mutually_exclusive_group(required=False)
    browserGroup.add_argument(
        "--chrome", action="store_true", help="Use Chrome WebDriver"
    )
    browserGroup.add_argument("--edge", action="store_true", help="Use Edge WebDriver")
    browserGroup.add_argument(
        "--firefox", action="store_true", help="Use Filefox WebDriver"
    )
    browserGroup.add_argument(
        "--safari", action="store_true", help="Use Safari WebDriver"
    )

    args: Namespace = parser.parse_args(argv)

    if args.username and not args.password:
        parser.error("Password required when username is specified.")
    if args.password and not args.username:
        parser.error("Username required when password is specified.")

    if not args.chrome and not args.edge and not args.firefox and not args.safari:
        parser.error("A WebDriver must be specified.")

    return args


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
    """Main function to execute the script."""
    amLoggedIn = False

    args: Namespace = argparse(argv)
    setLogging(args)

    # Connect to the Selenium WebBrowser
    log.info("Connecting to the WebBrowser...")
    if args.chrome:
        log.info("Using Chrome WebDriver")
        options = webdriver.chrome.options.Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome()
    elif args.edge:
        log.info("Using Edge WebDriver")
        driver = webdriver.Chrome()
    elif args.firefox:
        log.info("Using Firefox WebDriver")
        driver = webdriver.Chrome()
    elif args.safari:
        log.info("Using Safari WebDriver")
        driver = webdriver.Safari()
    else:
        log.error(
            "No WebDriver specified. Please specify one of: --chrome, --edge, --firefox, --safari"
        )
        return 1

    # Opening the Sports-Tracker website
    log.info("Opening Sports-Tracker website...")
    driver.get("https://www.sports-tracker.com/")

    # Optionally login to the Sports-Tracker website
    if args.username:
        log.info("Logging in to Sports-Tracker...")
        log.debug("Declining cookies")
        # We have to wait for the cookies banner to appear.
        declineCookies = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(),'Decline All')]")
            )
        )
        # declineCookies = driver.find_element("xpath", "//button[text()='Decline All']")
        declineCookies.click()
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located(declineCookies)
        )
        log.debug("Finding the login button")
        logInButton = driver.find_element("xpath", "//button[text()='Login']")
        logInButton.click()
        log.debug("Enter username and password")
        usernameField = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Email or username']")
            )
        )
        passwordField = driver.find_element("xpath", "//input[@placeholder='Password']")
        usernameField.send_keys(args.username)
        passwordField.send_keys(args.password)
        log.debug("Pressing the login button")
        logInButton = driver.find_element("xpath", "//input[@value='Login']")
        logInButton.click()
        amLoggedIn = True

    try:
        # Confirm that we see the "Dashboard" element.
        log.debug("Checking if logged in")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@ng-show='loggedInUser']"))
        )
        # Now do the activity requested.
        if args.mode == "list":
            log.info("Listing activities...")

        elif args.mode == "download":
            log.info("Downloading activities...")

    except:
        log.error("An error occurred during the operation.")

    finally:
        # Optionally logout from the website.
        if args.username and amLoggedIn:
            log.info("Logging out from Sports-Tracker...")
            loggedInUser = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@ng-show='loggedInUser']")
                )
            )
            loggedInUser.click()
            logOutButton = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Log out']"))
            )
            logOutButton.click()

        log.info("Closing the WebBrowser...")
        driver.quit()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
