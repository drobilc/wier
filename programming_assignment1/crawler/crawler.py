from downloader import Downloader
from scheduler import Scheduler
from storage import Storage
import threading


class Crawler(object):

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