from .regex_extractor import *
from .xpath_extractor import *
from .automatic_extractor import AutomaticExtractor

EXTRACTORS = {
    'regex-rtvslo': RTVSloRegexExtractor,
    'regex-overstock': OverstockRegexExtractor,
    'regex-avtonet': AvtoNetRegexExtractor,
    'xpath-rtvslo': RTVSloXPathExtractor,
    'xpath-overstock': OverstockXPathExtractor,
    'xpath-bolha': BolhaXPathExtractor,
    'xpath-avtonet': AvtoNetXPathExtractor,
    'automatic': AutomaticExtractor,
}