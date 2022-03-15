from urllib.parse import urljoin

class Scheduler(object):

    def __init__(self, repository):
        self.queue = []
        self.repository = repository

    def enqueue(self, urls):
        # TODO: Use repository to check if the site has already been downloaded.
        for url in urls:
            if not self.repository.contains_url(url):
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