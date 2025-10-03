

RAKUTEN_AI_BASE_URL = "xxx"
RAKUTEN_AI_GATEWAY_KEY = "xxx"
RAKUTEN_AI_MODEL = "gpt-4o-mini"

# Server configuration
HOST = "127.0.0.1"
PORT = 8000
DEBUG = True

# Retrieval configuration
XML_FILE_PATH = "hemant.xml"  # legacy single-file mode
PRE_XML_FILE_PATH = "pre.xml"
POST_XML_FILE_PATH = "post.xml"
MAX_SNIPPETS = 8
MAX_TOKENS_PER_SNIPPET = 1600  # characters per snippet
MAX_FULL_CONTEXT_CHARS = 1500000  # increase cap to reduce truncation risk
RETRIEVAL_TAGS_OF_INTEREST = {
    "ENBFunction",
    "EUtranCellFDD",
    "RadioObj",
    "RadioBand",
    "RadioCarrier",
    "NBIOTService",
    "MIB",
    "IRAT",
    "UEUplinkPowerControl",
}


