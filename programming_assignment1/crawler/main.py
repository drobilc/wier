import yaml
import argparse

def run_crawler(configuration):
    # Read data from configuration
    initial_urls = configuration.get('initial_urls', [])

    user_agent = configuration.get('user_agent')
    assert user_agent is not None

    # TODO: Actually start the crawler
    print(configuration)

def main():

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
            print(exception)

if __name__ == '__main__':
    main()