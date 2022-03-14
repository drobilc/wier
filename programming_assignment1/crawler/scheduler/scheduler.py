from urllib.parse import urljoin

class Scheduler(object):

    def __init__(self):
        self.queue = []

    def enqueue(self, urls):
        self.queue.extend(urls)
    
    def has_next(self):
        return len(self.queue) > 0
    
    def next(self):
        if len(self.queue) <= 0:
            return None
        
        return self.queue.pop(0)
    
    def canonicalize_url(self, base_url, relative_url):
        return urljoin(base_url, relative_url)