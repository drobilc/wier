from .base_extractor import BaseExtractor
from lxml import etree

class RTVSloXPathExtractor(BaseExtractor):

    def extract_title(self, tree):
        return tree.xpath('//header/h1/text()')[0]
    
    def extract_author(self, tree):
        return tree.xpath('//*[@id="main-container"]/div[3]/div/header/div[3]/div[1]/strong/text()')[0]

    def extract_data(self, content):
        html_parser = etree.HTMLParser()
        dom_tree = etree.fromstring(content, html_parser)
        
        return {
            'title': self.extract_title(dom_tree),
            'author': self.extract_author(dom_tree),
        }

class OverstockXPathExtractor(BaseExtractor):

    def extract_data(self, content):
        html_parser = etree.HTMLParser()
        dom_tree = etree.fromstring(content, html_parser)
        
        return {}