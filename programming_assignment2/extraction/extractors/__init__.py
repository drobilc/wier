from .regex_extractor import RegexExtractor
from .xpath_extractor import XPathExtractor
from .automatic_extractor import AutomaticExtractor

EXTRACTORS = {
    'regex': RegexExtractor,
    'xpath': XPathExtractor,
    'automatic': AutomaticExtractor,
}