import argparse
from os.path import join
import glob

class BaseExtractor(object):

    def __init__(self):
        pass

    def parse_arguments(self, arguments):
        parser = argparse.ArgumentParser()
        parser.add_argument('input_folder')
        self.add_arguments(parser)
        arguments, _ = parser.parse_known_args(arguments)
        self.configuration = arguments
    
    def extract(self):
        input_folder = self.configuration.input_folder

        # Find all HTML files inside input folder
        glob_pathname = join(input_folder, '*.html')
        html_files = glob.glob(glob_pathname)

        results = []

        # Open each file and extract data
        for filename in html_files:
            with open(filename, 'r', encoding='utf-8') as html_file:
                try:
                    file_content = html_file.read()
                    result = self.extract_data(file_content)
                    results.append(result)
                except Exception as exception:
                    print(exception)
        
        return results
    
    def add_arguments(self, parser):
        pass
    
    def extract_data(self, content):
        return {}