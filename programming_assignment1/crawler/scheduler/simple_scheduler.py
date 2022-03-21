import queue
from urllib.parse import urljoin, urldefrag, urlparse
from url_normalize import url_normalize
from datetime import datetime, timedelta
import logging
import pickle
import socket
from collections import deque
from urllib.robotparser import RobotFileParser

class Scheduler(queue.Queue):

    def __init__(self, configuration, repository):
        super().__init__()
        
        self.configuration = configuration
        self.repository = repository

        # TODO: Load fontier from file
        # with open('frontier.p', 'rb') as input_file:
        #     self.queue = pickle.load(input_file)

        initial_urls = self.configuration.get('initial_urls')
        initial_domains = map(lambda url: urlparse(url).hostname, initial_urls)
        self.allowed_domains = list(initial_domains)

        self.user_agent = self.configuration.get('user_agent')

        # A mapping between domains and RobotFileParser objects that we can use
        # to query for allowed or disallowed URL's.
        self.robots = {}
        self.crawler_delays = {}

        # The last access time for a specified IP address.
        self.access_times = {}

        # The IP addresses for domains.
        self.domain_ips = {}

        wait_between_consecutive_requests = self.configuration.get('wait_between_consecutive_requests', 5)
        self.wait_between_consecutive_requests = timedelta(seconds=wait_between_consecutive_requests)
    
    def get_host_ip(self, host):
        try:
            ip_address = socket.gethostbyname(host)
            logging.info('Performing DNS request for %s, IP: %s', host, ip_address)
            return ip_address
        except Exception as e:
            logging.exception(e)
            return None
    
    def get_ip(self, domain):
        if domain in self.domain_ips:
            return self.domain_ips[domain]
        else:
            ip_address = self.get_host_ip(domain)
            self.domain_ips[domain] = ip_address
            return ip_address
    
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

        return parser

    def get_wait_time(self, domain):
        return self.crawler_delays.get(domain, self.wait_between_consecutive_requests)

    def should_skip(self, url):
        # Check if the URL has already been visited using data from our
        # repository.
        url_parts = urlparse(url)

        if self.repository.contains_page(url_parts.hostname, url):
            logging.debug('Site already downloaded: %s', url)
            return True        

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

    def has_next(self):
        return not self.empty()
    
    def enqueue(self, urls):
        for dirty_url in urls:
            # First, canonicalize the URL address
            url = self.normalize_url(dirty_url)
            
            if self.should_skip(url):
                continue
            
            self.put(url)
    
    def next(self):
        return self.get()
    
    def normalize_url(self, url):
        normalized_url = url_normalize(url)
        final_url, _ = urldefrag(normalized_url)
        return final_url
    
    def canonicalize_url(self, base_url, relative_url):
        absolute_url = urljoin(base_url, relative_url)
        normalized_url = url_normalize(absolute_url)
        final_url, _ = urldefrag(normalized_url)
        return final_url
    
    def stop(self):
        # Store current frontier to a file
        with open('frontier.p', 'wb') as output_file:
            pickle.dump(self.queue, output_file)
    
    def _init(self, maxsize):
        self.queue = {}
    
    def _qsize(self):
        return sum(map(lambda queue: len(queue), self.queue.values()))
    
    # Put a new item in the queue
    def _put(self, url):
        url_parts = urlparse(url)

        domain = url_parts.hostname
        ip_address = self.get_ip(domain)
        if ip_address not in self.queue:
            self.queue[ip_address] = deque()
        
        if ip_address not in self.access_times:
            self.access_times[ip_address] = datetime.now()
        
        self.queue[ip_address].append(url)
    
    # Get an item from the queue
    def _get(self):
        # First, find all queues that are not empty.
        non_empty_queues = dict(filter(lambda item: len(item[1]) > 0, self.queue.items()))

        # There are no more items
        if len(non_empty_queues) <= 0:
            return None

        # Then, find the queue that has the smallest last modified time.
        least_recently_downloaded = min(non_empty_queues.items(), key=lambda item: self.access_times[item[0]])
        ip_address, queue = least_recently_downloaded
        access_time = self.access_times[ip_address]

        url = queue.popleft()
        while self.should_skip(url):
            url = queue.popleft()

        domains = filter(lambda item: item[1] == ip_address, self.domain_ips.items())
        waiting_times = list(map(lambda item: self.get_wait_time(item[0]), domains))
        maximum_waiting_time = max(waiting_times) if len(waiting_times) > 0 else self.wait_between_consecutive_requests

        self.access_times[ip_address] = max(datetime.now(), access_time) + maximum_waiting_time
        
        return (url, access_time)