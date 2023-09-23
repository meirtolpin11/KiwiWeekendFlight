import copy
import config
import helpers
import logging
import airlines
import holidays
import requests
import database as db
from datetime import datetime, timedelta


# noinspection PyBroadException
def query_flight_kiwi(search_params):
    try:
        response = requests.get(
            config.URL, params=search_params, headers=config.HEADERS
        )
        return response.json()
    except Exception as e:
        return -1


def get_date(flight, field):
    return datetime.strptime(flight[field], r"%Y-%m-%dT%H:%M:%S.%fZ")


def generate_holidays_flights(
    date_from: datetime,
    date_to: datetime,
    fly_to: str,
    price_to: int = 1000,
    nights_in_dst_from: int = 1,
    nights_in_dst_to: int = 10,
    country="IL",
    scan_timestamp=None,
) -> None:
    country_holidays = holidays.country_holidays(country, years=date_to.year)

    holiday_start = None
    prev_holiday = None
    prev_holiday_name = None
    for _holiday in country_holidays.items():
        if not (date_from.date() < _holiday[0] < date_to.date()):
            continue

        if not prev_holiday:
            holiday_start = _holiday
            prev_holiday = _holiday
            prev_holiday_name = _holiday[1].split("-")[0]

        elif (_holiday[0] - prev_holiday[0]).days != 1:
            generate_flights(
                holiday_start[0] - timedelta(days=1),
                prev_holiday[0] + timedelta(days=1),
                fly_to,
                price_to,
                nights_in_dst_from,
                nights_in_dst_to,
                scan_timestamp,
                holiday_name=prev_holiday_name,
            )

            holiday_start = _holiday
            prev_holiday = _holiday
            prev_holiday_name = _holiday[1].split("-")[0]

        else:
            prev_holiday = _holiday


def generate_special_date(
    special_date,
    scan_timestamp: int = int(datetime.timestamp(datetime.now())),
):
    kiwi_api_params = prepare_kiwi_api(**special_date)

    flights = query_flight_kiwi(kiwi_api_params)
    if flights == -1:
        return

    # flights data
    try:
        flights_data = flights["data"]
    except Exception as e:
        logging.error(f"failed to fetch flight from kiwi api, error:{e}")
        logging.error(flights)
        return

    for flight in flights_data:
        parse_and_save_flight(flight, scan_timestamp, special_date=True)


def generate_weekend_flights(
    date_from: datetime,
    date_to: datetime,
    fly_to: str,
    price_to: int = 500,
    nights_in_dst_from: int = config.DEFAULT_NIGHTS_IN_DST_FROM,
    nights_in_dst_to: int = config.DEFAULT_NIGHTS_IN_DST_TO,
    scan_timestamp=None,
    details=None,
):
    weekend_dates = helpers.get_weekends(date_from, date_to, details)

    if details:
        nights_in_dst_from = nights_in_dst_from if details[5] == -1 else details[5]
        nights_in_dst_to = nights_in_dst_to if details[6] == -1 else details[6]

    for weekend_id, weekend in enumerate(weekend_dates):
        generate_flights(
            weekend[0],
            weekend[1],
            fly_to,
            price_to,
            nights_in_dst_from,
            nights_in_dst_to,
            scan_timestamp,
        )


def prepare_kiwi_api(**kwargs):
    # get a local copy of the api params dict
    kiwi_api_params = copy.deepcopy(config.KIWI_API_PARAMS)
    for key, value in kwargs.items():
        if type(value) == datetime:
            value = value.strftime("%Y-%m-%d")
        kiwi_api_params[key] = value

    return kiwi_api_params


def get_airline_links(flight, is_round=True):
    airlines_list = [
        airlines.get_airline_name(route["airline"]) for route in flight["route"]
    ]

    links = ["", ""]
    if len(set(airlines_list)) == 1:
        if hasattr(airlines, airlines_list[i].lower().replace(" ", "_")):
            airline_class = getattr(airlines, airlines_list[0].lower().replace(" ", "_"))
            if airline_class:
                links[0] = airline_class.generate_link(
                    flight["flyFrom"],
                    flight["flyTo"],
                    get_date(flight["route"][0], "local_departure"),
                    get_date(flight["route"][1], "local_departure") if is_round else None,
                    is_round=is_round
                )
                if is_round:
                    links[1] = links[0]
    else:
        for i in range(2):
            # generate separate links for every flight
            # TODO: check kiwi api about fly from and to in a route
            if hasattr(airlines, airlines_list[i].lower().replace(" ", "_")):
                airline_class = getattr(
                    airlines, airlines_list[i].lower().replace(" ", "_")
                )
                links[i] = airline_class.generate_link(
                    flight["route"][i]["flyFrom"],
                    flight["route"][i]["flyTo"],
                    get_date(flight["route"][i], "local_departure"),
                    is_round=False,
                )

    return links


def parse_and_save_flight(flight, scan_timestamp, special_date=False, holiday_name=""):
    is_round = True if len(flight["route"]) == 2 else False

    # parse the relevant flight information
    source = f"{flight['countryFrom']['name']}/{flight['cityFrom']}/{flight['flyFrom']}"
    dest = f"{flight['countryTo']['name']}/{flight['cityTo']}/{flight['flyTo']}"
    price = int(flight["price"]) - 25 # usually their price is around 25 NIS higher

    airlines_list = [
        airlines.get_airline_name(route["airline"]) for route in flight["route"]
    ]

    airline_class = None
    discount_price = price

    # get discount price is available
    if len(set(airlines_list)) == 1:
        # check that there is an airline class
        if hasattr(airlines, airlines_list[0].lower().replace(" ", "_")):
            airline_class = getattr(
                airlines, airlines_list[0].lower().replace(" ", "_")
            )
            # check there is a discount calculation function
            if hasattr(airline_class, "calculate_discount_price"):
                discount_price = airline_class.calculate_discount_price(price, is_round=is_round)

    links = get_airline_links(flight, is_round)

    # store flight numbers
    flight_numbers = ",".join(
        [
            direction["airline"] + str(direction["flight_no"])
            for direction in flight["route"]
        ]
    )

    # calculate how many days off the work are needed
    if is_round:
        days_off = helpers.calculate_days_off(
            get_date(flight["route"][0], "local_departure"),
            get_date(flight["route"][1], "local_arrival"),
        )
    else:
        days_off = 0

    # insert the flight into the database
    db_flight = db.Flights(
        fly_from=source,
        fly_to=dest,
        price=price,
        discount_price=discount_price,
        nights=int(flight["nightsInDest"]) if is_round else 0,
        airlines=",".join(airlines_list),
        departure_to=get_date(flight["route"][0], "local_departure"),
        departure_from=get_date(flight["route"][1], "local_departure")
        if is_round
        else "",
        arrival_to=get_date(flight["route"][0], "local_arrival"),
        arrival_from=get_date(flight["route"][1], "local_arrival") if is_round else "",
        month=get_date(flight["route"][0], "local_departure").month,
        days_off=days_off,
        date_of_scan=scan_timestamp,
        link_to=links[0],
        link_from=links[1],
        weekend_id=-1,  # TODO: update weekend id
        flight_numbers=flight_numbers,
        holiday_name=holiday_name,
        special_date=special_date,
    )
    db_flight.save()


def generate_flights(
    date_from: datetime,
    date_to: datetime,
    fly_to: str,
    price_to: int = 500,
    nights_in_dst_from: int = config.DEFAULT_NIGHTS_IN_DST_FROM,
    nights_in_dst_to: int = config.DEFAULT_NIGHTS_IN_DST_TO,
    scan_timestamp: int = int(datetime.timestamp(datetime.now())),
    holiday_name="",
):
    if date_to is None or date_from is None:
        return

    kiwi_api_params = prepare_kiwi_api(
        fly_to=fly_to,
        price_to=price_to,
        date_from=date_from,
        return_from=date_from,
        date_to=date_to,
        return_to=date_to,
        nights_in_dst_from=nights_in_dst_from,
        nights_in_dst_to=nights_in_dst_to,
    )

    flights = query_flight_kiwi(kiwi_api_params)
    if flights == -1:
        return

    # flights data
    try:
        flights_data = flights["data"]
    except Exception as e:
        logging.error(f"failed to fetch flight from kiwi api, error:{e}")
        logging.error(flights)
        return

    for flight in flights_data:
        # parse the relevant flight information
        parse_and_save_flight(
            flight, scan_timestamp, special_date=False, holiday_name=holiday_name
        )
