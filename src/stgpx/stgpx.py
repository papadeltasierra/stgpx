"""STGPX - Sports-Tracker Downloader"""

import sys
from argparse import Namespace, ArgumentParser
from typing import List
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from random import random

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
    parser.add_argument(
        "-m",
        "--mode",
        action="store",
        help="Operation mode",
        required=True,
        choices=["list", "download"],
    )

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
        prefs = {"download.default_directory": "c:\\temp\\gpx"}
        # options.add_argument("headless")
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
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
        passwordField = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Password']")
            )
        )

        usernameField.send_keys(args.username)
        passwordField.send_keys(args.password)

        facebookSpan = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//span[text()='Login with Facebook']",
                )
            )
        )
        # Login seems to be flakey so loop it and try three times!
        attempts = 0
        while True:
            log.debug("Clicking on the login button")
            logInButton = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Login']"))
            )
            logInButton.send_keys(Keys.ENTER)
            sleep(1)

            try:
                facebookSpan = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//span[text()='Login with Facebook']",
                        )
                    )
                )
                log.debug("Facebook buttont is visible.")
            except Exception as ee:
                log.debug("Login appears to have succeeded")
                # No oops so assume we are OK.
                break

            log.debug("Login failed, retrying...")
            usernameField.clear()
            passwordField.clear()
            usernameField.send_keys(args.username)
            passwordField.send_keys(args.password)
            attempts += 1
            if attempts > 5:
                log.error("Failed to login after 5 attempts.")
                raise Exception("Failed to login after 5 attempts.")
            sleep(1 + random() * 2)

    try:
        # Confirm that we see the "Dashboard" element.
        log.debug("Checking if logged in")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@ng-show='loggedInUser']"))
        )
        amLoggedIn = True
        # Now do the activity requested.
        if args.mode == "list":
            log.info("Listing activities...")

        elif args.mode == "download":
            log.info("Downloading activities...")

            log.debug("Check if Menu visible")
            try:
                menuButton = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[@class='nav-menu-toggle']")
                    )
                )
                menuButton.click()
            except:
                log.debug("Menu button not found, assuming already open.")

            log.debug("Go to dashboard")
            dashboardHyperlink = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Dashboard']"))
            )
            dashboardHyperlink.click()

            log.debug("Goto 'My Workouts'")
            myWorkoutsSpan = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='My workouts']"))
            )
            myWorkoutsSpan.click()

            log.debug("listing workouts")
            # Get all elements of type li and class "workout-item"
            workoutItems = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//li[@class='workout-item']")
                )
            )

            log.debug("download file for workouts")
            for workoutItem in workoutItems:
                log.debug("Clicking on workout item")
                # Click on the workoutItem to open the workout.
                feedCardHref = workoutItem.find_element(
                    By.XPATH, "//a[@class='feed-card__link']"
                )
                feedCardHref.click()

                # Wait for and then click on the 'Edit' button.
                log.debug("Click on the Edit button")
                editButton = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Edit']"))
                )
                editButton.click()

                # Wait for and then click on the 'Export' button.  We do not get the
                # file save dialog in test-mode.
                log.debug("Clicking on the 'Export' button")
                exportButton = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Export']"))
                )
                exportButton.click()

                # We dno't seem able to catch the "Cancel" button so we just
                # send the ESC key.
                log.debug("Using ESC to exit the dialog")
                actions = ActionChains(driver)
                actions.send_keys(Keys.ESCAPE).perform()

                log.debug("Check if Menu visible")
                try:
                    menuButton = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[@class='nav-menu-toggle']")
                        )
                    )
                    menuButton.click()
                except:
                    log.debug("Menu button not found, assuming already open.")

                # Click on Dashboard again to get back to the list...
                log.debug("Go to dashboard")
                dashboardHyperlink = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[text()='Dashboard']"))
                )
                dashboardHyperlink.click()

    except:
        log.exception("Exception: ")
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
