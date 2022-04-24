from .base_extractor import BaseExtractor
from lxml import etree
from os.path import join
import glob

class RTVSloXPathExtractor(BaseExtractor):
    
    def extract_author(self, tree):
        return tree.xpath('//div[@class="author-name"]/text()')[0]
    
    def extract_published_time(self, tree):
        return tree.xpath('//div[@class="publish-meta"]/text()')[0].strip()
    
    def extract_title(self, tree):
        return tree.xpath('//header/h1/text()')[0]
    
    def extract_subtitle(self, tree):
        return tree.xpath('//header//div[@class="subtitle"]/text()')[0]
    
    def extract_lead(self, tree):
        return tree.xpath('//p[@class="lead"]/text()')[0]
    
    def extract_body(self, tree):
        all_text = tree.xpath('//div[@class="article-body"]//*[not(name()="script")]/text()')
        return ' '.join([text.strip() for text in all_text]).strip()

    def extract_data(self, content):
        html_parser = etree.HTMLParser()
        dom_tree = etree.fromstring(content, html_parser)
        
        return {
            'title': self.extract_title(dom_tree),
            'subtitle': self.extract_subtitle(dom_tree),
            'lead': self.extract_lead(dom_tree),
            'content': self.extract_body(dom_tree),
            'author': self.extract_author(dom_tree),
            'published_time': self.extract_published_time(dom_tree),
        }

class OverstockXPathExtractor(BaseExtractor):

    def extract(self):
        input_folder = self.configuration.input_folder

        # Find all HTML files inside input folder
        glob_pathname = join(input_folder, '*.html')
        html_files = glob.glob(glob_pathname)

        results = []

        # Open each file and extract data
        for filename in html_files:
            with open(filename, 'r') as html_file:
                try:
                    file_content = html_file.read()
                    result = self.extract_data(file_content)
                    results.append(result)
                except Exception as exception:
                    print(exception)
        
        return results
    
    def extract_title(self, tree):
        return tree.xpath('/tr/td[2]/a/b/text()')[0]
    
    def extract_list_price(self, tree):
        return tree.xpath('/tr/td[2]/table//table/tbody/tr[1]/td[2]/s/text()')[0]
    
    def extract_price(self, tree):
        return tree.xpath('/tr/td[2]/table//table/tbody/tr[2]/td[2]/span/b/text()')[0]
    
    def extract_saving(self, tree):
        saving = tree.xpath('/tr/td[2]/table//table/tbody/tr[3]/td[2]/span/text()')[0]
        saving_price, saving_percent, *_ = saving.split(' ')
        saving_percent = saving_percent.replace('(', '').replace(')', '')
        return saving_price, saving_percent
    
    def extract_content(self, tree):
        all_text = tree.xpath('/tr//span[@class="normal"]//text()')
        return ' '.join([text.strip() for text in all_text]).strip()

    def extract_item(self, tree):
        saving, saving_percent = self.extract_saving(tree)
        return {
            'title': self.extract_title(tree),
            'list_price': self.extract_list_price(tree),
            'price': self.extract_price(tree),
            'saving': saving,
            'saving_percent': saving_percent,
            'content': self.extract_content(tree),
        }

    def extract_items(self, tree):
        items = tree.xpath('/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr')
        result = []
        for item in items:
            try:
                root = etree.fromstring(etree.tostring(item))
                result.append(self.extract_item(root))
            except:
                pass
        return result

    def extract_data(self, content):
        html_parser = etree.HTMLParser()
        dom_tree = etree.fromstring(content, html_parser)
        
        return {
            'items': self.extract_items(dom_tree)
        }

class BolhaXPathExtractor(BaseExtractor):
    
    def extract_title(self, tree):
        return tree.xpath('/li//h3[@class="entity-title"]/a/text()')[0].strip()
    
    def extract_price(self, tree):
        return tree.xpath('/li//li[@class="price-item"]/strong/text()')[0].strip()
    
    def extract_location(self, tree):
        return tree.xpath('/li//div[@class="entity-description-main"]/text()')[1].strip()
    
    def extract_time(self, tree):
        time = tree.xpath('/li//time/text()')[0].strip()
        if time.endswith('.'):
            return time[:-1]
        return time 
    
    def extract_item(self, tree):
        return {
            'title': self.extract_title(tree),
            'price': self.extract_price(tree),
            'location': self.extract_location(tree),
            'date_posted': self.extract_time(tree),
        }

    def extract_items(self, tree):
        items = tree.xpath('//ul[@class="EntityList-items"]/li')
        result = []
        for item in items:
            try:
                root = etree.fromstring(etree.tostring(item))
                result.append(self.extract_item(root))
            except Exception as e:
                pass
        return result

    def extract_data(self, content):
        html_parser = etree.HTMLParser()
        dom_tree = etree.fromstring(content, html_parser)
        
        return {
            'items': self.extract_items(dom_tree)
        }