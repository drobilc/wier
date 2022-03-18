from selenium import webdriver
import selenium.common.exceptions as selenium_exceptions
import urllib.error as urllib_exceptions
import ssl
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import logging
import threading

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

                # Store the page source in database.
                self.storage.save(url, html)

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