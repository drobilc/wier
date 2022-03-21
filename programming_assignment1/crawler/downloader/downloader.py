import datetime
from selenium import webdriver
import selenium.common.exceptions as selenium_exceptions
import urllib.error as urllib_exceptions
import ssl
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import logging
import threading

from urllib.parse import urljoin, urlparse
from .duplicateDetector import *
from downloader.robots import *
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.firefox.options import Options
import hashlib
import os
import requests
import urllib.error
from socket import timeout
import sys
import time

"""
sys.setrecursionlimit(1500)


def processSeedPages(seed_urls, db_connection):
    for seed in seed_urls:
        if checkForDuplicateSEED(seed, db_connection) or checkForDuplicateFRONTIER(seed, db_connection):
            continue

        response_robots, sitemap, delay = getResponseRobots(seed, db_connection)

        site_id = add_site(seed, response_robots, sitemap, delay, db_connection)
        page_id = add_page(seed, site_id, db_connection)


def processCurrentPage(current_page, db_connection, driver):
    html_content = status_code = content_type = None
    url = "http://" + current_page[3]

    html_content, status_code, content_type = getContent(url, driver)

    if html_content is not None and status_code is not None:
        # 1. PAGE TYPE IS HTML
        if content_type is not None and 'html' in content_type:
            # 1.1 hash and search duplicates
            pretty_content = html_content.prettify()
            hashed_content = hashlib.md5(pretty_content.encode()).hexdigest()
            duplicate = checkForDuplicateHTML(current_page[0], hashed_content, db_connection)

            # 1.2 check if page is accessible
            if status_code >= 400:
                updatePageAsInaccessible(current_page[0], status_code, "HTML", db_connection)
                print("Inaccessible: ", status_code, url, current_page[0])
            else:
                # 1.3 if page is not duplicate - crawl it 
                if not duplicate:
                    fetchData(html_content, current_page, db_connection)
                    updatePageAsHTML(current_page[0], status_code,pretty_content, hashed_content, db_connection)
                else:
                    print("Duplicate: ", current_page[3], duplicate[0])
                    updatePageAsDuplicate(current_page[0], status_code,duplicate, db_connection)
        # 2. PAGE TYPE IS NOT HTML
        else:
            updatePageAsNotHTML(current_page[0], status_code, db_connection)
            print("Not HTML: ", current_page[3])
    else:
        updatePageAsInaccessible(current_page[0], status_code, None, db_connection)
        print("Not a page: ", current_page[3], current_page[0])


def getContent(url, driver):
    soup = status_code = content_type = None
    try:
        time.sleep(6)
        response = requests.get(url, data={'key': 'value'})
        status_code = response.status_code
        content_type = response.headers['Content-Type']
    except Exception as e:
        print("Getting status code led to", e)
        return soup, status_code, content_type
    
    now = datetime.now()
    access_time = now.strftime("%Y-%m-%d %H:%M:%S'")
    print("ACCESS 1:", url, access_time)

    try:
        time.sleep(6)
        driver.get(url)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")
    except Exception as error:
        print("Fetching page with Selenium led to", error)

    now = datetime.now()
    access_time = now.strftime("%Y-%m-%d %H:%M:%S'")
    print("ACCESS 2:", url, access_time)

    return soup, status_code, content_type


"""    
class Downloader(threading.Thread):

    def __init__(self, configuration, scheduler, storage):
        # Because the downloader will be running as a thread, we need to
        # initialize the parent Thread object first. We use the daemon=True so
        # that when the main thread exits, all Downloader threads are destroyed
        # too.
        threading.Thread.__init__(self, daemon=True)

        self.configuration = configuration

        self.scheduler = scheduler
        self.storage = storage

        # Initialize Selenium webdriver with Firefox browser
        driver_path = configuration.get('driver_path')
        
        browser_options = Options()
        browser_options.accept_insecure_certs = True
        
        # Set user agent for the browser
        user_agent = configuration.get('user_agent')
        browser_options.add_argument(f'user-agent={user_agent}')

        # Hide browser if the headless key is set in configuration
        browser_options.headless = self.configuration.get('headless', True)

        self.driver = webdriver.Firefox(executable_path=driver_path, options=browser_options)

        # Read timeout from configuratinon
        self.timeout = configuration.get('page_load_timeout')

    def download_site(self, url):
        if url is None: return None
        self.driver.get(url)
        self.driver.set_page_load_timeout(self.timeout)
        return self.driver.page_source
    
    def parse_html(self, content):
        # Maybe we should parse HTML using the 'html5lib' parser which is more
        # lenient, but slower.
        html = BeautifulSoup(content, 'html.parser')
        return html
    
    def extract_links(self, current_url, html):
        hyperlinks = html.find_all('a')
        
        urls = []
        for hyperlink in hyperlinks:
            relative_url = hyperlink.get('href')
            if relative_url is not None:
                # The site can contain relative urls, the scheduler will convert
                # those urls to their absolute value.
                url = self.scheduler.canonicalize_url(current_url, relative_url)
                urls.append(url)
        
        return urls

    def main_loop(self):
        while self.scheduler.has_next():
            try:
                # Get the next url from scheduler
                url = self.scheduler.next()

                if url is None:
                    continue
                
                logging.info('Fetching: %s', url)
                
                # Try to read the website and parse its html.
                content = self.download_site(url)
                html = self.parse_html(content)

                # TODO: Store the page source in database.
                # self.storage.save(url, html)

                # Get a list of links from page and add pass them on to the
                # scheduler.
                urls = self.extract_links(url, html)
                self.scheduler.enqueue(urls)
            except selenium_exceptions.TimeoutException as e:
                logging.error('Timeout exception: %s', url)
            except ssl.SSLError as e:
                logging.error('SSL exception: %s', url)
            except urllib_exceptions.URLError as e:
                logging.error('SSL handshake exception: %s', url)
            except Exception as e:
                # Don't stop if an error occurs.
                logging.exception(e)
    
    def run(self):
        logging.info('Starting thread %s', self.name)

        # Start the main loop, which will grab URL from scheduler, fetch sites
        # and add more URLs into scheduler. The function will exit when there is
        # no more URLs in queue.
        self.main_loop()

        # Before the thread finishes, we need to close our driver.
        self.driver.close()
