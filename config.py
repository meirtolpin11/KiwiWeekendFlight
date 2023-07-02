import os
import json
import logging

API_KEY = ""
URL = "https://tequila-api.kiwi.com/v2/search"
HEADERS = {"accept": "application/json", "apikey": API_KEY}

AWS_BUCKET_NAME = None
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
AWS_CONFIG_FILE_NAME = "config.json"
AWS_TEST_CONFIG_FILE_NAME = "config_test.json"

TELEGRAM_BOTS = {"default": {"token": "", "chats": {"all": -1}}}

MONTHS_TO_SCAN = 5

SPECIAL_DESTINATIONS = [
    "HU",  # Hungary
    "IT",  # Italy
    "DE",  # Germany
    "CZ",  # Czech Republic
    "FR",  # France
    "GR",  # Greece
    "BG",  # Bulgaria
    "RO",  # Romania
    "BE",  # Belgium
    "PL",  # Poland
    "NL",  # Netherlands
    "ES",  # Spain
    "SP",  # Serbia
]

WEEKEND_START = 4
WEEKEND_END = 7

KIWI_API_PARAMS = {
    "fly_from": "TLV",
    "fly_to": "",
    "date_from": "",
    "date_to": "",
    "return_from": "",
    "return_to": "",
    "nights_in_dst_from": "",
    "nights_in_dst_to": "",
    "flight_type": "round",
    "one_for_city": False,
    "max_stopovers": 0,
    "price_to": "",
    "curr": "ILS",
    "ret_from_diff_airport": 0,
}
DEFAULT_NIGHTS_IN_DST_FROM = 2
DEFAULT_NIGHTS_IN_DST_TO = 5

tmp_folder = "/tmp"


def init_config():
    global API_KEY
    global HEADERS
    global TELEGRAM_BOTS
    global AWS_BUCKET_NAME
    global AWS_ACCESS_KEY_ID
    global AWS_SECRET_ACCESS_KEY

    # load the config from the environment variable
    API_KEY = os.getenv("KIWI_API_KEY").strip()
    HEADERS["apikey"] = API_KEY
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    try:
        TELEGRAM_BOTS = {
            "default": {
                "token": os.getenv("TELEGRAM_BOT_TOKEN").strip(),
                "chats": {"all": [os.getenv("TELEGRAM_CHAT_ID").strip(), "all", 500]},
            }
        }

        # configure additional chats
        additional_chats = os.getenv("ADDITIONAL_CHAT_IDS")

        # separate chat names from chat ids
        additional_chats = additional_chats.split("|")
        for chat in additional_chats:
            chat_name = chat.split(";")[0]
            chat_id = chat.split(";")[1]
            max_price = int(chat.split(";")[2]) if chat.split(";")[2] else 0
            TELEGRAM_BOTS["default"]["chats"][chat_name] = [chat_id, chat_name.upper(), max_price]

    except Exception:
        logging.error("Unable to load configuration from ENV variables")


def load_config_from_file(file_path: str):
    global DEFAULT_NIGHTS_IN_DST_FROM
    global DEFAULT_NIGHTS_IN_DST_TO
    global SPECIAL_DESTINATIONS
    global TELEGRAM_BOTS
    global MONTHS_TO_SCAN
    global WEEKEND_START
    global WEEKEND_END
    with open(file_path) as f:
        data = json.loads(f.read())

        # update values in case there is a special config in the json file
        TELEGRAM_BOTS = data.get("bots", TELEGRAM_BOTS)
        MONTHS_TO_SCAN = data.get("months_to_scan", MONTHS_TO_SCAN)
        WEEKEND_START = data.get("weekend_start", WEEKEND_START)
        WEEKEND_END = data.get("weekend_end", WEEKEND_END)
        DEFAULT_NIGHTS_IN_DST_FROM = data.get('nights_in_dst_from', DEFAULT_NIGHTS_IN_DST_FROM)
        DEFAULT_NIGHTS_IN_DST_TO = data.get('nights_in_dst_to', DEFAULT_NIGHTS_IN_DST_TO)
        SPECIAL_DESTINATIONS = data.get("special_destinations", SPECIAL_DESTINATIONS)




