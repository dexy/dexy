from kaa import imlib2
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import sys

def run():
    url = sys.argv[1]
    filename = sys.argv[2]

    delay = 2

    if len(sys.argv) > 3:
        crop_width = sys.argv[3]
        crop_height = sys.argv[4]
    else:
        crop_width = 850
        crop_height = 150

    def crop_image(filename, region_width, region_height, x=0, y=0):
        image = imlib2.open(filename)
        image = image.crop((x, y), (region_width, region_height))
        image.save(filename)

    browser = webdriver.Firefox()
    browser.get(url)
    time.sleep(delay)
    browser.save_screenshot(filename)
    #crop_image(filename, crop_width, crop_height)
    browser.close()
