import json
from .wizzair import WizzAir as wizz_air
from .ryanair import Ryanair as ryanair
from .elal import Elal as el_al_israel_airlines

airlines_date = json.loads(open("airlines/airlines.json").read())


def get_airline_name(airline_iata_code):
    try:
        return airlines_date[airline_iata_code]["name"]
    except Exception as e:
        print(e)
        return iata_code
