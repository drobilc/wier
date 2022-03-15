from downloader import Downloader
from scheduler import Scheduler
from storage import Storage

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
    
    def run(self):
        # TODO: Spawn multiple downloaders using threads
        downloader = Downloader(self.configuration, self.scheduler, self.storage)
        downloader.run()