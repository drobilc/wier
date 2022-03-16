from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
from url_normalize import url_normalize
import logging

class Scheduler(object):

    def __init__(self, configuration, repository):
        self.configuration = configuration
        self.repository = repository

        self.queue = []

        self.user_agent = self.configuration.get('user_agent')

        initial_urls = self.configuration.get('initial_urls')
        initial_domains = map(lambda url: urlparse(url).hostname, initial_urls)
        self.allowed_domains = list(initial_domains)

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

        # If there is a sitemap inside the "robots.txt" file, add it to queue
        # and our crawler will extract all links.
        sitemaps = parser.site_maps()
        if sitemaps is not None:
            self.enqueue(sitemaps)

        return parser

    def should_skip(self, url):
        # Check if the URL has already been visited using data from our
        # repository.
        if self.repository.contains_url(url):
            logging.debug('Site already downloaded: %s', url)
            return True

        url_parts = urlparse(url)

        # Ignore links that are not http or https
        if url_parts.scheme not in ['http', 'https']:
            logging.debug('Incorrect scheme: %s', url_parts.scheme)
            return True

        # Check if we are even allowed to visit the url using the
        # "robots.txt" file.
        robots_parser = self.get_robots_parser(url)
        if not robots_parser.can_fetch(self.user_agent, url):
            logging.debug('Site disallowed: %s', url)
            return True
        
        # Ignore links that are not inside our allowed domains
        for allowed_domain in self.allowed_domains:
            if url_parts.hostname.endswith(allowed_domain):
                return False

        logging.debug('Domain not allowed: %s', url_parts.hostname)
        return True

    def enqueue(self, urls):
        for dirty_url in urls:
            # First, canonicalize the URL address
            url = self.normalize_url(dirty_url)
            
            if self.should_skip(url):
                continue
            
            self.queue.append(url)
    
    def has_next(self):
        return len(self.queue) > 0
    
    def next(self):
        if len(self.queue) <= 0:
            return None
        
        return self.queue.pop(0)

    def normalize_url(self, url):
        normalized_url = url_normalize(url)
        final_url, _ = urldefrag(normalized_url)
        return final_url

    def canonicalize_url(self, base_url, relative_url):
        absolute_url = urljoin(base_url, relative_url)
        normalized_url = url_normalize(absolute_url)
        final_url, _ = urldefrag(normalized_url)
        return final_url