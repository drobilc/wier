import yaml
import argparse
import logging
from crawler import Crawler
import time

def run_crawler(configuration):
    # Create a new crawler object with the configuration and start it. The
    # crawler will spawn multiple Downloader threads.
    crawler = Crawler(configuration)
    crawler.run()

    # The crawler will spawn multiple Downloader threads in daemon mode. Because
    # the main thread will have nothing to do after that, the main thread will
    # exit, and the crawler will stop.
    # Run an infinite loop that does nothing.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info('The crawler has been interrupted')
    finally:
        crawler.stop()

def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start web crawler.')
    parser.add_argument(
        '--configuration',
        dest='configuration_file',
        help='Web crawler configuration file (default: configuration.yaml)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='If set, the crawler will output DEBUG information'
    )
    arguments = parser.parse_args()

    # Configure logger
    logging_level = logging.DEBUG if arguments.verbose else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s %(levelname)s %(threadName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

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