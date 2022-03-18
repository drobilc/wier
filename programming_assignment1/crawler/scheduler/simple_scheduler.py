import queue
from urllib.parse import urljoin, urldefrag, urlparse
from url_normalize import url_normalize
from datetime import datetime, timedelta
import logging

class Scheduler(queue.Queue):

    def __init__(self, configuration, repository):
        super().__init__()
        
        self.configuration = configuration
        self.repository = repository

        initial_urls = self.configuration.get('initial_urls')
        initial_domains = map(lambda url: urlparse(url).hostname, initial_urls)
        self.allowed_domains = list(initial_domains)
    
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