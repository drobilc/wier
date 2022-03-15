from scheduler import Scheduler
from storage import Storage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class Downloader(object):

    def __init__(self, configuration, scheduler, storage):
        self.configuration = configuration

        self.scheduler = scheduler
        self.storage = storage

        # Read data from configuration
        initial_urls = configuration.get('initial_urls', [])
        self.scheduler.enqueue(initial_urls)

        # Initialize Selenium webdriver with Google Chrome browser
        driver_path = configuration.get('driver_path')
        
        browser_options = Options()
        
        # Set user agent for the browser
        user_agent = configuration.get('user_agent')
        browser_options.add_argument(f'user-agent={user_agent}')

        self.driver = webdriver.Chrome(driver_path, options=browser_options)

        # TODO: Hide the browser
        # browser_options.add_argument("--headless")

        # TODO: Read timeout from configuratinon
        self.timeout = 5
        

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

    def run(self):
        while self.scheduler.has_next():
            try:
                # Get the next url from scheduler
                url = self.scheduler.next()
                
                # Try to read the website and parse its html.
                content = self.download_site(url)
                html = self.parse_html(content)

                # Store the page source in database.
                self.storage.save(url, html)

                # Get a list of links from page and add pass them on to the
                # scheduler.
                urls = self.extract_links(url, html)
                self.scheduler.enqueue(urls)
            except Exception as e:
                # Don't stop if an error occurs.
                # TODO: Use logger library to log errors
                print(e)