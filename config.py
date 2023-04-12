import os

API_KEY = ""
URL = "https://tequila-api.kiwi.com/v2/search"
HEADERS = {
    "accept": "application/json",
    "apikey": API_KEY
}

TELEGRAM_BOTS = {
    'default': {
        'token': '',
        'chats': {
            'all': -1
        }
    }
}

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
    "SP"  # Serbia
]

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
    "ret_from_diff_airport": 0
}

tmp_folder = "/tmp"
NUM_OF_MONTHS = 5


def init_config():
    global API_KEY
    global HEADERS
    global TELEGRAM_BOTS

    # load the config from the environment variable
    API_KEY = os.getenv('KIWI_API_KEY').strip()
    HEADERS['apikey'] = API_KEY

    TELEGRAM_BOTS = {
        'default': {
            'token': os.getenv('TELEGRAM_BOT_TOKEN').strip(),
            'chats': {
                'all': [os.getenv('TELEGRAM_CHAT_ID').strip(), 500]
            }
        }
    }

    # configure additional chats
    additional_chats = os.getenv('ADDITIONAL_CHAT_IDS')

    # separate chat names from chat ids
    additional_chats = additional_chats.split('|')
    for chat in additional_chats:
        chat_name = chat.split(';')[0]
        chat_id = chat.split(';')[1]
        max_price = int(chat.split(';')[2]) if chat.split(';')[2] else 0
        TELEGRAM_BOTS['default']['chats'][chat_name] = [chat_id, max_price]

