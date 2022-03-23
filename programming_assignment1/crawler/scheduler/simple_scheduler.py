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

        initial_urls = self.configuration.get('initial_urls')
        initial_domains = map(lambda url: urlparse(url).hostname, initial_urls)
        self.allowed_domains = list(initial_domains)

        self.user_agent = self.configuration.get('user_agent')

        # Currently locked IP addresses - the ones that the threads must not
        # access to.
        self.locked_ips = {}

        # A mapping between domains and RobotFileParser objects that we can use
        # to query for allowed or disallowed URL's.
        self.robots = {}
        self.crawler_delays = {}

        # The last access time for a specified IP address.
        self.access_times = {}

        # The IP addresses for domains.
        self.domain_ips = {}

        # Load fontier from file
        try:
            with open('frontier.p', 'rb') as input_file:
                access_times, queue = pickle.load(input_file)
                self.access_times = access_times
                self.queue = queue
                for ip in self.queue:
                    self.locked_ips[ip] = False
                logging.info('Frontier loaded from file')
        except Exception:
            logging.info('No saved frontier')

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

    def site_allowed(self, url):
        url_parts = urlparse(url)
        if url_parts.scheme not in ['http', 'https']:
            return False
        
        for allowed_domain in self.allowed_domains:
            if url_parts.hostname.endswith(allowed_domain):
                return True
        
        return False

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
            pickle.dump((self.access_times, self.queue), output_file)
    
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
        
        if ip_address not in self.locked_ips:
            self.locked_ips[ip_address] = False
        
        self.queue[ip_address].append(url)
    
    def mark_done(self, url):
        with self.mutex:
            url_parts = urlparse(url)

            domain = url_parts.hostname
            ip_address = self.get_ip(domain)

            self.locked_ips[ip_address] = False
            self.access_times[ip_address] = datetime.now()
    
    # Get an item from the queue
    def _get(self):
        # First, find all queues that are not empty.
        non_empty_queues = dict(filter(lambda item: len(item[1]) > 0, self.queue.items()))

        # There are no more items
        if len(non_empty_queues) <= 0:
            return None, None
        
        unlocked_ips = list(map(lambda item: item[0], filter(lambda item: not item[1], self.locked_ips.items())))
        queues = dict(filter(lambda item: item[0] in unlocked_ips, non_empty_queues.items()))

        if len(queues) <= 0:
            return None, None
        
        # Find the IP that was marked as accessed least recently.
        least_recently_downloaded = min(queues.items(), key=lambda item: self.access_times[item[0]])
        ip_address, queue = least_recently_downloaded
        access_time = self.access_times[ip_address]

        # Check if at least maximum_waiting_time has passed between accessing
        # this domain.
        domains = filter(lambda item: item[1] == ip_address, self.domain_ips.items())
        waiting_times = list(map(lambda item: self.get_wait_time(item[0]), domains))
        maximum_waiting_time = max(waiting_times) if len(waiting_times) > 0 else self.wait_between_consecutive_requests

        time_difference = datetime.now() - access_time
        if time_difference < maximum_waiting_time:
            return None, time_difference
        
        # Enough time has passed.
        
        # Mark the IP address as locked - it will only be unlocked after
        # self.mark_done is called.
        self.locked_ips[ip_address] = True

        url = queue.popleft()
        while self.should_skip(url):
            url = queue.popleft()
        
        return url, None