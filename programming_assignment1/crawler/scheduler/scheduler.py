from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging

class Scheduler(object):

    def __init__(self, configuration, repository):
        self.configuration = configuration
        self.repository = repository

        self.queue = []

        self.user_agent = self.configuration.get('user_agent')

        # A mapping between domains and RobotFileParser objects that we can use
        # to query for allowed or disallowed URL's.
        self.robots = {}
    
    def get_robots_parser(self, url):
        url_parts = urlparse(url)

        domain = url_parts.hostname
        if domain in self.robots:
            return self.robots[domain]
        
        robots_url = f'{url_parts.scheme}://{domain}/robots.txt'
        logging.debug('Getting "robots.txt" from: %s', robots_url)
        parser = RobotFileParser(robots_url)
        parser.read()

        self.robots[domain] = parser
        return parser

    def enqueue(self, urls):
        for url in urls:

            # Check if the URL has already been visited using data from our
            # repository.
            if self.repository.contains_url(url):
                logging.debug('Site already downloaded: %s', url)
                continue

            # Check if we are even allowed to visit the url using the
            # "robots.txt" file.
            robots_parser = self.get_robots_parser(url)
            if not robots_parser.can_fetch(self.user_agent, url):
                logging.debug('Site disallowed: %s', url)
                continue

            self.queue.append(url)
    
    def has_next(self):
        return len(self.queue) > 0
    
    def next(self):
        if len(self.queue) <= 0:
            return None
        
        return self.queue.pop(0)
    
    def canonicalize_url(self, base_url, relative_url):
        return urljoin(base_url, relative_url)