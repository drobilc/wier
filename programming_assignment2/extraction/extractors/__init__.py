from .regex_extractor import RegexExtractor
from .xpath_extractor import *
from .automatic_extractor import AutomaticExtractor

EXTRACTORS = {
    'regex': RegexExtractor,
    'xpath-rtvslo': RTVSloXPathExtractor,
    'xpath-overstock': OverstockXPathExtractor,
    'automatic': AutomaticExtractor,
}