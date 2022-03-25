from selenium import webdriver
import selenium.common.exceptions as selenium_exceptions
import requests.exceptions as requests_exceptions
import urllib.error as urllib_exceptions
import ssl
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import logging
import threading
from urllib.parse import urlparse
from .duplicateDetector import *
from downloader.robots import *
import requests
import time
import pathlib
import urllib3

urllib3.disable_warnings()

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
        browser_options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(executable_path=driver_path, options=browser_options)

        # Read timeout from configuratinon
        self.timeout = configuration.get('page_load_timeout')

    def download_site(self, url):
        """
            Fetch the site and return its content and server response code. If
            page has binary content, a tuple (None, None) will be returned.
        """
        if url is None:
            return None, None
        
        # Don't verify certificates, because this greatly reduces the total
        # number of downloaded pages.
        response = requests.head(url, allow_redirects=True, verify=False)

        # We have allowed redirects, so the response object contains redirection
        # history. If it is empty, no redirection has happened.
        redirection_urls = [item.url for item in response.history] + [response.url]
        if len(redirection_urls) >= 2:
            # A redirection has happened, add redirection url to database
            for i in range(1, len(redirection_urls)):
                from_url = redirection_urls[i - 1]
                to_url = redirection_urls[i]
                self.storage.save_redirection(from_url, to_url)
        
        # If we have been redirected to another page, the response.url will
        # point to that page. As we don't want to repeat all the redirections,
        # we can crawl this url with our web driver.
        url = response.url
        
        # Check if content type is 'text/html' or any other text type.
        content_type = response.headers.get('Content-Type')
        if content_type is not None:
            content_type = content_type.lower()
            if 'text' not in content_type:
                extensions = {
                    'application/pdf': 'PDF',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
                }
                # This is a binary file, store this data in database.
                extension = extensions.get(content_type)
                if extension is not None:
                    self.storage.save_page_data(url, extension)
                return None, None
        
        status_code = response.status_code

        # Wait before performing another request to the same URL with our
        # driver.
        time.sleep(5)

        self.driver.set_page_load_timeout(self.timeout)
        self.driver.delete_all_cookies()
        self.driver.get(url)
        return self.driver.page_source, status_code
    
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
    
    def extract_images(self, current_url, html):
        images = html.find_all('img')
        
        image_urls = []
        for image in images:
            image_url = image.get('src')
            if image_url is not None:
                absolute_url = self.scheduler.canonicalize_url(current_url, image_url)

                url_parts = urlparse(absolute_url)

                # Skip images with no scheme (svg and base64 encoded images)
                if url_parts.hostname is None:
                    continue
                
                path = pathlib.Path(url_parts.path)
                image_urls.append((absolute_url, path.suffix))
        
        return image_urls

    def sort_urls(self, urls):
        binary_file_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx']
        skip_file_extensions = ['.gif', '.jpg', '.jpeg', '.png', '.bmp', '.svg', '.zip', '.xls', '.xlsx']

        page_urls = []
        binary_file_urls = []

        for url in urls:
            url_parts = urlparse(url)

            if not self.scheduler.site_allowed(url):
                continue
            
            file_extension = pathlib.Path(url_parts.path).suffix
            extension = file_extension.lower()
            
            # If the filename contains a file extension from
            # [skip_file_extensions] list, skip it as we don't need to insert it
            # into database or add it to frontier.
            if extension in skip_file_extensions:
                continue

            if extension in binary_file_extensions:
                clean_extension = extension.removeprefix('.')
                binary_file_urls.append((url, clean_extension))
            else:
                page_urls.append(url)
        
        return page_urls, binary_file_urls

    def main_loop(self):
        while True:
            try:
                # Get the next url from scheduler
                url, wait_for = self.scheduler.next()

                if wait_for is not None:
                    sleep_for = wait_for.total_seconds()
                    if sleep_for > 0:
                        time.sleep(sleep_for)
                
                if url is None:
                    continue
                
                url_parts = urlparse(url)
                logging.info('[%s] Fetching: %s', url_parts.hostname, url)

                # Try to read the website and parse its html.
                content, response_code = self.download_site(url)
                if content is None:
                    continue

                html = self.parse_html(content)
                page_content = str(html.prettify())

                # Check if page is a duplicate. If it is, add a new DUPLICATE
                # entry to database.
                duplicate_page_id = self.storage.check_if_duplicate(page_content)
                if duplicate_page_id is not None:
                    self.storage.save_duplicate(duplicate_page_id, url)
                    continue

                # Store the page source in database.
                page_id = self.storage.save_page(url, str(page_content), response_code=response_code, update=True)

                # Get a list of links from page and add pass them on to the
                # scheduler.
                urls = self.extract_links(url, html)

                image_urls = self.extract_images(url, html)
                for image_url, file_extension in image_urls:
                    self.storage.save_image(page_id, image_url, file_extension)

                # Filter out the urls that most likely point to a website and
                # links that point to a binary file.
                page_urls, binary_file_urls = self.sort_urls(urls)

                for binary_file_url, extension in binary_file_urls:
                    self.storage.save_page_data(binary_file_url, extension)

                self.scheduler.enqueue(page_urls)
            except requests_exceptions.Timeout:
                logging.error('Requests timeout exception: %s', url)
                # Insert URL back into the frontier
                self.scheduler.enqueue([ url ])
            except requests_exceptions.RequestException as e:
                logging.error('Requests exception: %s', url)
                logging.exception(e)
            except selenium_exceptions.TimeoutException as e:
                logging.error('Timeout exception: %s', url)
                # Insert URL back into the frontier
                self.scheduler.enqueue([ url ])
            except selenium_exceptions.WebDriverException as e:
                logging.error('WebDriver exception: %s', url)
            except ssl.SSLError as e:
                logging.error('SSL exception: %s', url)
            except urllib_exceptions.URLError as e:
                logging.error('SSL handshake exception: %s', url)
            except Exception as e:
                # Don't stop if an error occurs.
                logging.exception(e)
            finally:
                # This block will be executed even if we have called continue
                # inside the loop.
                if url is not None:
                    self.scheduler.mark_done(url)
    
    def run(self):
        logging.info('Starting thread %s', self.name)

        # Start the main loop, which will grab URL from scheduler, fetch sites
        # and add more URLs into scheduler. The function will exit when there is
        # no more URLs in queue.
        self.main_loop()

        # Before the thread finishes, we need to close our driver.
        self.driver.close()
