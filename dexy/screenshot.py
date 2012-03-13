try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
except ImportError:
    raise Exception("You must have python-selenium installed to take screenshots. Try 'pip install selenium'.")
from kaa import imlib2
from modargs import args
import time
import sys

PROG = 'screenshot'
MOD = sys.modules[__name__]

def run():
    args.parse_and_run_command(sys.argv[1:], MOD, default_command='screenshot')

def screenshot_command(
        url = None, # the URL to take a screenshot of
        filename = None, # the filename to save screenshot to (can be png or pdf)
        croph = -1, # height to crop image to
        cropw = -1, # width to crop image to
        scalew = -1, # width to scape image to (height calculated automatically)
        delay = 2, # The time to delay after loading the url before taking screenshot (to let page finish)
        loginpass = "",
        loginpassid = "user_pass", # dom id of input for password
        loginsubmit = "wp-submit", # dom id of submit button
        loginurl = "", # if set, page to access first to log in to
        loginuser = "",
        loginuserid = "user_login", # dom id of input for username
        logindelay = 2 # time to wait to make sure login has succeeded
        ):

    def crop_image(filename, region_width, region_height, x=0, y=0):
        image = imlib2.open(filename)
        image = image.crop((x, y), (region_width, region_height))
        image.save(filename)

    def scape_image(filename, width):
        image = imlib2.open(filename)
        image = image.scale((width, -1))
        image.save(filename)

    def login_to_site():
        browser.get(loginurl)

        username_element = browser.find_element_by_id(loginuserid)
        username_element.send_keys(loginuser)

        password_element = browser.find_element_by_id(loginpassid)
        password_element.send_keys(loginpass)

        submit_element = browser.find_element_by_id(loginsubmit)
        submit_element.click()
        time.sleep(logindelay)

    browser = webdriver.Firefox()

    if len(loginurl) > 0:
        login_to_site()

    browser.get(url)
    time.sleep(delay)
    browser.save_screenshot(filename)
    if croph > 0:
        crop_image(filename, cropw, croph)
    if scalew > 0:
        scape_image(filename, scalew)

    browser.close()

def help_command(on=False):
    args.help_command(PROG, MOD, 'screenshot', on)
