import yaml
import argparse
import logging
from crawler import Crawler

def run_crawler(configuration):
    # Create a new crawler object with the configuration and start it. The
    # crawler will spawn multiple Downloader threads.
    crawler = Crawler(configuration)
    crawler.run()

def main():

    # Configure logger
    logging.basicConfig(level=logging.INFO)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start web crawler.')
    parser.add_argument(
        '--configuration',
        dest='configuration_file',
        help='Web crawler configuration file (default: configuration.yaml)'
    )
    arguments = parser.parse_args()

    # Open YAML configuration file
    with open(arguments.configuration_file, "r") as configuration_file:
        try:

            # Read configuration from file
            configuration = yaml.safe_load(configuration_file)

            # Start the crawler
            run_crawler(configuration)

        except yaml.YAMLError as exception:
            logging.exception(exception)

if __name__ == '__main__':
    main()