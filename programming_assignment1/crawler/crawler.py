from downloader import Downloader
from scheduler import Scheduler
from storage import Storage
import logging

class Crawler(object):

    def __init__(self, configuration):
        self.configuration = configuration

        # Create only one repository (Storage object) and only one frontier
        # manager (Scheduler object) and use them when constructing multiple
        # downloader threads.
        self.storage = Storage(self.configuration)
        self.scheduler = Scheduler(self.configuration, self.storage)

        # Read initial seed URL's from configuration and add them to the crawler
        # queue.
        initial_urls = configuration.get('initial_urls', [])
        self.scheduler.enqueue(initial_urls)

        # A list of threads that are used to crawl the web.
        self.threads = []
        
    def run(self):
        number_of_workers = self.configuration.get('number_of_workers', 1)
        logging.info('Spawning %d workers', number_of_workers)

        for _ in range(number_of_workers):
            downloader = Downloader(self.configuration, self.scheduler, self.storage)
            self.threads.append(downloader)
            downloader.start()
    
    def stop(self):
        logging.info('Stopping crawler')

        # Disconnect from the database
        self.storage.disconnect()
        logging.info('Disconnected from database')

        # Backup frontier data into some file
        self.scheduler.stop()
        logging.info('Saved frontier data to file')