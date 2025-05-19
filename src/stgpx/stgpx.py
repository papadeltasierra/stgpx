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
import re
import os

log = logging.getLogger(__name__)

# Login is flakey so we try a few times.
LOGIN_ATTEMPTS = 5

# Timeout intervals intervals.
COOKIES_BANNER_TIMEOUT = 10
LOGIN_FAILED_TIMEOUT = 10
LOGIN_BUTTON_TIMEOUT = 10
USERNAME_PASSWORD_TIMEOUT = 10
USER_LOGGED_IN_TIMEOUT = 10
MENU_TIMEOUT = 10
DASHBOARD_TIMEOUT = 10
WORKOUTS_TIMEOUT = 10
WORKOUT_ITEMS_TIMEOUT = 10
MORE_ACTIVITIES_TIMEOUT = 10
ACTIVITY_LOAD_TIMEOUT = 40
EXPORT_TIMEOUT = 10

# Duplicate files regex.
DUPLICATE_FILES_REGEX = re.compile(r"^.*\(\d+\)\.gpx$")


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

    outputGroup = parser.add_argument_group("output", "Output options")
    outputGroup.add_argument(
        "-o", "--output", action="store", help="Downloaded files output directory"
    )
    outputGroup.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="Clean duplicated files from output directory after downloading",
    )

    args: Namespace = parser.parse_args(argv)

    if args.username and not args.password:
        parser.error("Password required when username is specified.")
    if args.password and not args.username:
        parser.error("Username required when password is specified.")

    if not args.chrome and not args.edge and not args.firefox and not args.safari:
        parser.error("A WebDriver must be specified.")

    if args.clean and not args.output:
        parser.error("Output directory required when cleaning duplicate files.")

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
    if args.verbose >= 2:
        consoleHandler.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        consoleHandler.setLevel(logging.INFO)
    else:
        consoleHandler.setLevel(logging.WARNING)


def main(argv: List[str]):
    """Main function to execute the script."""
    amLoggedIn = False

    args: Namespace = argparse(argv)
    setLogging(args)

    # Connect to the Selenium WebBrowser
    log.info("Connecting to the WebBrowser...")
    if args.chrome:
        log.info("Using Chrome WebDriver...")
        options = webdriver.chrome.options.Options()
        # options.add_argument("headless")
        # Suppress off 'Tensor' message.
        options.add_argument("--log-level=1")
        # Suppress 'DevTools listening' message.
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if args.output:
            prefs = {"download.default_directory": args.output}
            options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
    elif args.edge:
        log.info("Using Edge WebDriver...")
        driver = webdriver.Chrome()
    elif args.firefox:
        log.info("Using Firefox WebDriver...")
        driver = webdriver.Chrome()
    elif args.safari:
        log.info("Using Safari WebDriver...")
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
        declineCookies = WebDriverWait(driver, COOKIES_BANNER_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(),'Decline All')]")
            )
        )
        declineCookies.click()
        WebDriverWait(driver, COOKIES_BANNER_TIMEOUT).until(
            EC.invisibility_of_element_located(declineCookies)
        )
        log.debug("Finding the login button")
        logInButton = driver.find_element("xpath", "//button[text()='Login']")
        logInButton.click()

        log.debug("Enter username and password")
        usernameField = WebDriverWait(driver, USERNAME_PASSWORD_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Email or username']")
            )
        )
        passwordField = WebDriverWait(driver, USERNAME_PASSWORD_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Password']")
            )
        )

        # WebDriverWait(driver, LOGIN_FAILED_TIMEOUT).until(
        #     EC.presence_of_element_located(
        #         (
        #             By.XPATH,
        #             "//span[text()='Login with Facebook']",
        #         )
        #     )
        # )

        # Login seems to be flakey so loop it and try three times!
        attempts = 0
        while True:
            log.debug("Sending username and password")
            usernameField.clear()
            usernameField.send_keys(args.username)
            sleep(0.5 + random() * 0.5)
            passwordField.clear()
            passwordField.send_keys(args.password)

            log.debug("Clicking on the login button")
            # Randomise the wait before clicking the login button.
            sleep(0.5 + random() * 1)

            logInButton = WebDriverWait(driver, LOGIN_BUTTON_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Login']"))
            )
            logInButton.send_keys(Keys.ENTER)

            # We have to wait for the login dialog to disappear before we test
            # to see if login was successful.
            sleep(2)

            try:
                log.debug("Checking if logged in")
                WebDriverWait(driver, USER_LOGGED_IN_TIMEOUT).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[@ng-show='loggedInUser']")
                    )
                )
                log.info("Login was successful...")
                break
                # WebDriverWait(driver, LOGIN_FAILED_TIMEOUT).until(
                #     EC.presence_of_element_located(
                #         (
                #             By.XPATH,
                #             "//span[text()='Login with Facebook']",
                #         )
                #     )
                # )
                # log.debug("Facebook button is visible.")

            except Exception as ee:
                # No logged in user so we failed.
                pass

            log.debug("Login failed, retrying...")
            attempts += 1
            if attempts > LOGIN_ATTEMPTS:
                log.error("Failed to login after %d attempts.", LOGIN_ATTEMPTS)
                raise Exception("Failed to login after %d attempts." % LOGIN_ATTEMPTS)

    try:
        # Confirm that we see the "Dashboard" element.
        amLoggedIn = True
        # Now do the activity requested.
        if args.mode == "list":
            log.info("Listing activities...")

        elif args.mode == "download":
            log.info("'Download activities' requested...")
            log.debug("Check if Menu visible")
            try:
                menuButton = WebDriverWait(driver, MENU_TIMEOUT).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[@class='nav-menu-toggle']")
                    )
                )
                menuButton.click()
            except:
                log.debug("Menu button not found, assuming already open.")

            log.debug("Go to dashboard")
            dashboardHyperlink = WebDriverWait(driver, DASHBOARD_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Dashboard']"))
            )
            dashboardHyperlink.click()

            log.debug("Goto 'My Workouts'")
            myWorkoutsSpan = WebDriverWait(driver, WORKOUTS_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='My workouts']"))
            )
            myWorkoutsSpan.click()

            # Repeatedly click on "Load more activities" until we have them all.
            log.info("Loading all activities...")
            while True:
                try:
                    loadMoreSpan = WebDriverWait(driver, MORE_ACTIVITIES_TIMEOUT).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[text()='Load more activities']")
                        )
                    )
                    loadMoreSpan.click()
                except:
                    # Assume we have found them all now.
                    break

            log.debug("listing workouts")
            # Get all elements of type li and class "workout-item"
            workoutItems = WebDriverWait(driver, WORKOUT_ITEMS_TIMEOUT).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//li[@class='workout-item']")
                )
            )

            # Find the hrefs to each workout and convert to absolute URLs.
            workoutAbsUrls = []

            log.info("Downloading %d activities...", len(workoutItems))
            for workoutItem in workoutItems:
                log.debug("Clicking on workout item")
                # Click on the workoutItem to open the workout.
                feedCardHref = workoutItem.find_element(
                    By.XPATH, ".//a[@class='feed-card__link']"
                )
                workoutAbsUrls.append(feedCardHref.get_attribute("href"))

            for workoutAbsUrl in workoutAbsUrls:
                # Wait for and then click on the 'Edit' button.
                log.debug("Click on the Edit button")
                print(".", end="", file=sys.stderr, flush=True)
                driver.get(workoutAbsUrl)

                editButton = WebDriverWait(driver, ACTIVITY_LOAD_TIMEOUT).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Edit']"))
                )
                editButton.click()

                # Wait for and then click on the 'Export' button.  We do not get the
                # file save dialog in test-mode.
                log.debug("Clicking on the 'Export' button")
                exportButton = WebDriverWait(driver, EXPORT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Export']"))
                )
                exportButton.click()

                # We don't seem able to catch the "Cancel" button so we just
                # send the ESC key.
                log.debug("Using ESC to exit the dialog")
                actions = ActionChains(driver)
                actions.send_keys(Keys.ESCAPE).perform()

                log.debug("Check if Menu visible")
                try:
                    menuButton = WebDriverWait(driver, MENU_TIMEOUT).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[@class='nav-menu-toggle']")
                        )
                    )
                    menuButton.click()
                except:
                    log.debug("Menu button not found, assuming already open.")

                # Click on Dashboard again to get back to the list...
                log.debug("Go to dashboard")
                dashboardHyperlink = WebDriverWait(driver, DASHBOARD_TIMEOUT).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[text()='Dashboard']"))
                )
                dashboardHyperlink.click()

            # Done downloading; print final "\n" to make it look nice.
            print("", file=sys.stderr, flush=True)

            if args.output and args.clean:
                log.info("Cleaning up duplicate files...")
                (_, _, filenames) = os.walk(args.output)
                for filename in filenames:
                    if DUPLICATE_FILES_REGEX.match(filename):
                        log.debug("Deleting duplicate file: %s", filename)
                        os.remove(os.path.join(args.output, filename))

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
