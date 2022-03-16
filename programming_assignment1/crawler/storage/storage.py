class Storage(object):

    def __init__(self):
        self.already_visited = []

    def save(self, url, html):
        self.already_visited.append(url)

    def contains_url(self, url):
        return url in self.already_visited