import argparse
import pprint
from extractors import *

def run_extraction(arguments, other_arguments):
    # Get extractor class for specified extraction algorithm.
    ExtractorClass = EXTRACTORS[arguments.extraction_algoritm]
 
    # Construct a new extractor object.
    extractor = ExtractorClass()

    # Each parser object can accept additional arguments by overriding the
    # add_arguments method. Parse those arguments now.
    extractor.parse_arguments(other_arguments)

    # Extract information from webpage and print the resulting json.
    result = extractor.extract()
    pprint.pprint(result)

def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start web crawler.')
    parser.add_argument(
        'extraction_algoritm',
        choices=EXTRACTORS.keys(),
        default=list(EXTRACTORS.keys())[0],
        help='Which algorithm to use to extract information from webpages'
    )
    arguments, other_arguments = parser.parse_known_args()

    # Run the extraction
    run_extraction(arguments, other_arguments)

if __name__ == '__main__':
    main()