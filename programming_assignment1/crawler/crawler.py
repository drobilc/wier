from downloader import Downloader
from scheduler import Scheduler
from storage.storage import *
import threading
import sys
import time
from crawler.downloader.downloader import *
from selenium.webdriver.firefox.options import Options


# user-agent=fri-wier-DOMACI_NJOKI
"""
lock = threading.Lock()

class Crawler(threading.Thread):

    def __init__(self, threadID, db_connection):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.db_connection = db_connection
        print(f"Web Crawler worker {self.threadID} has Started")

    def run(self):
        try:
            options = Options()
            options.headless = True
            options.add_argument("--user-agent=fri-wier-DOMACI_NJOKI")
            driver = webdriver.Firefox(executable_path=os.path.abspath(
                "./crawler/downloader/geckodriver.exe"), options=options)
            driver.set_page_load_timeout(12)
        except Exception as error:
            print("Running Selenium led to", error)

    current_page = None
    while True:
        with lock:
            current_page = getFromFrontier(self.db_connection)
            print("Current page in FRONTIER: ", current_page[3], current_page[0], self.threadID)

        if current_page is not None:
            processCurrentPage(current_page, self.db_connection, driver)
        else:
            driver.close()
            break
    print(self.threadID, " worker finnished!")


def initiateCrawler(number_of_workers):
    current_page, db_connection = add_site(SEED_URLS)

    if not current_page:
        processSeedPages(SEED_URLS, db_connection)

    # CHANGE ACCESSED_TIME TO NULL IF FINNISHED = FALSE --> RESET FRONTIER AFTER STOPPING THE CRAWLER
    reset = True
    while reset == True:
        reset = resetFrontier(db_connection)
    
    all_threads = []
    for i in range(number_of_workers):
        thread = current_thread(i, db_connection)
        all_threads.append(thread)
        thread.start()

    for t in all_threads:
        t.join()
    print("All threads have finnished!")
    closeconnectiontodatabase()


if __name__ == '__main__':
    number_of_workers = int(sys.argv[1])

    initiateCrawler(number_of_workers)



"""
def __init__(self, configuration):
    self.configuration = configuration

    # Create only one repository (Storage object) and only one frontier
    # manager (Scheduler object) and use them when constructing multiple
    # downloader threads.
    self.storage = Storage()
    self.scheduler = Scheduler(self.configuration, self.storage)

    # Read initial seed URL's from configuration and add them to the crawler
    # queue.
    initial_urls = configuration.get('initial_urls', [])
    self.scheduler.enqueue(initial_urls)

    # A list of threads that are used to crawl the web.
    self.threads = []
    
def run(self):
    number_of_workers = self.configuration.get('number_of_workers', 1)

    for _ in range(number_of_workers):
        downloader = Downloader(self.configuration, self.scheduler, self.storage)
        self.threads.append(downloader)
        downloader.start()
