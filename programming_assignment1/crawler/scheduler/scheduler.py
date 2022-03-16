from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
from url_normalize import url_normalize
import logging
import socket
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

        self.ips = {}
        self.last_request = {}
        self.crawler_delays = {}

        wait_between_consecutive_requests = self.configuration.get('wait_between_consecutive_requests', 5)
        self.wait_between_consecutive_requests = timedelta(seconds=wait_between_consecutive_requests)
    
    def get_wait_time(self, domain):
        return self.crawler_delays.get(domain, self.wait_between_consecutive_requests)
    
    def get_server_ip(self, hostname):
        try:
            ip_address = socket.gethostbyname(hostname)
            logging.info('Performing DNS request for %s, IP: %s', hostname, ip_address)
            return ip_address
        except Exception as e:
            logging.exception(e)
            return None
    
    def get_robots_parser(self, url):
        url_parts = urlparse(url)

        domain = url_parts.hostname
        if domain in self.robots:
            return self.robots[domain]
        
        robots_url = f'{url_parts.scheme}://{domain}/robots.txt'
        logging.info('Fetching "robots.txt" from: %s', robots_url)
        parser = RobotFileParser(robots_url)
        parser.read()

        self.robots[domain] = parser

        # If crawler delay option is set in the "robots.txt" file, store it into
        # [crawler_delays] cache and use it when checking if the URL can
        # actually be fetched.
        crawler_delay = parser.crawl_delay(self.user_agent)
        if crawler_delay is not None:
            self.crawler_delays[domain] = timedelta(seconds=crawler_delay)

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
        
        # Ignore links that are not inside our allowed domains
        is_domain_allowed = False
        for allowed_domain in self.allowed_domains:
            if url_parts.hostname.endswith(allowed_domain):
                is_domain_allowed = True
                break
        
        if not is_domain_allowed:
            logging.debug('Domain not allowed: %s', url_parts.hostname)
            return True
        
        # Check if we are even allowed to visit the url using the
        # "robots.txt" file.
        robots_parser = self.get_robots_parser(url)
        if not robots_parser.can_fetch(self.user_agent, url):
            logging.debug('Site disallowed: %s', url)
            return True
        
        return False

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

        for index, url in enumerate(self.queue):

            # Get IP address from the URL - either perform a DNS query or read it
            # from cache.
            url_parts = urlparse(url)
            if url_parts.hostname in self.ips:
                ip_address = self.ips[url_parts.hostname]
            else:
                ip_address = self.get_server_ip(url_parts.hostname)
                self.ips[url_parts.hostname] = ip_address
            
            # Check if enough time has passed between two consecutive requests to
            # the same server.
            if ip_address not in self.last_request:
                # We haven't made any requests to this server yet. We can perform
                # our first request now.
                self.last_request[ip_address] = datetime.now()
                return self.queue.pop(index)
            else:
                last_request_time = self.last_request[ip_address]
                time_passed = datetime.now() - last_request_time

                wait_between_consecutive_requests = self.get_wait_time(url_parts.hostname)
                if time_passed > wait_between_consecutive_requests:
                    self.last_request[ip_address] = datetime.now()
                    return self.queue.pop(index)
        
        return None

    def normalize_url(self, url):
        normalized_url = url_normalize(url)
        final_url, _ = urldefrag(normalized_url)
        return final_url

    def canonicalize_url(self, base_url, relative_url):
        absolute_url = urljoin(base_url, relative_url)
        normalized_url = url_normalize(absolute_url)
        final_url, _ = urldefrag(normalized_url)
        return final_url