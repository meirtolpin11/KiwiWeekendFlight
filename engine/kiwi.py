import json
import copy
import config
import helpers
import logging
import airlines
import holidays
import requests
import database as db
from typing import Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Holiday:
    start: Tuple[datetime, str]
    end: Tuple[datetime, str]
    name: str


# noinspection PyBroadException
def query_flight_kiwi(search_params):
    try:
        return requests.get(
            config.URL, params=search_params, headers=config.HEADERS
        ).json()
    except Exception:
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

    holiday = None
    for _holiday in country_holidays.items():
        if not holiday:
            holiday = Holiday(_holiday, _holiday, _holiday[1].split("-")[0])  # type: ignore

        elif (_holiday[0] - holiday.end[0]).days != 1:
            generate_flights(
                holiday.start[0] - timedelta(days=1),
                holiday.end[0] + timedelta(days=1),
                fly_to,
                price_to,
                nights_in_dst_from,
                nights_in_dst_to,
                scan_timestamp,
                holiday_name=holiday.name,
            )
            holiday = Holiday(_holiday, _holiday, _holiday[1].split("-")[0])
            if not (date_from.date() < _holiday[0] < date_to.date()):
                logging.info(
                    f"Stopping holiday generation - out of range - {holiday.name}"
                )
                break
        else:
            holiday.end = _holiday


def generate_special_date(
    special_date,
    scan_timestamp: int = int(datetime.timestamp(datetime.now())),
):
    kiwi_api_params = prepare_kiwi_api(**special_date)

    flights = query_flight_kiwi(kiwi_api_params)
    if flights == -1:
        logging.error("Unable to fetch flights from KIWI")
        return

    try:
        flights_data = flights["data"]
    except Exception as e:
        logging.error(f"failed to fetch flight from kiwi api, error:{e}")
        logging.error(flights)
        return

    for flight in flights_data:
        parse_and_save_custom_search(
            flight, scan_timestamp, str(hash(json.dumps(special_date)))
        )


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
        if hasattr(airlines, airlines_list[0].lower().replace(" ", "_")):
            airline_class = getattr(
                airlines, airlines_list[0].lower().replace(" ", "_")
            )
            if airline_class:
                links[0] = airline_class.generate_link(
                    flight["flyFrom"],
                    flight["flyTo"],
                    get_date(flight["route"][0], "local_departure"),
                    get_date(flight["route"][1], "local_departure")
                    if is_round
                    else None,
                    is_round=is_round,
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


def parse_and_save_direct_flights(flight, scan_date):
    is_round = True if len(flight["route"]) == 2 else False

    # parse the relevant flight information
    source = f"{flight['countryFrom']['name']}/{flight['cityFrom']}/{flight['flyFrom']}"
    dest = f"{flight['countryTo']['name']}/{flight['cityTo']}/{flight['flyTo']}"
    price = int(flight["price"]) - 25  # usually their price is around 25 NIS higher

    airlines_list = [
        airlines.get_airline_name(route["airline"]) for route in flight["route"]
    ]

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
                discount_price = airline_class.calculate_discount_price(
                    price, is_round=is_round
                )

    links = get_airline_links(flight, is_round)

    # store flight numbers
    flight_numbers = [
        direction["airline"] + str(direction["flight_no"])
        for direction in flight["route"]
    ]

    outbound_flight = db.DirectFlight(
        source=source,
        dest=dest,
        airline=airlines_list[0],
        flight_number=flight_numbers[0],
        price=price,
        discounted_price=discount_price,
        link=links[0],
        departure_time=get_date(flight["route"][0], "local_departure"),
        landing_time=get_date(flight["route"][0], "local_arrival"),
        scan_date=scan_date,
    )

    inbound_flight = None
    if is_round:
        inbound_flight = db.DirectFlight(
            source=dest,
            dest=source,
            airline=airlines_list[1],
            flight_number=flight_numbers[1],
            price=price,
            discounted_price=discount_price,
            link=links[1],
            departure_time=get_date(flight["route"][1], "local_departure"),
            landing_time=get_date(flight["route"][1], "local_arrival"),
            scan_date=scan_date,
        )

    if inbound_flight:
        inbound_flight.save()
        outbound_flight.round_flight = inbound_flight.id

    outbound_flight.save()

    return outbound_flight, inbound_flight


def parse_and_save_monthly_flight(flight, scan_timestamp, holiday_name=""):
    outbound_flight, inbound_flight = parse_and_save_direct_flights(
        flight, scan_timestamp
    )

    db_table = db.HolidayFlights if holiday_name else db.WeekendFlights
    additional_keys = {"holiday_name": holiday_name} if holiday_name else {}

    monthly_flight = db_table(
        month=outbound_flight.departure_time.month,
        source=outbound_flight.source,
        dest=outbound_flight.dest,
        outbound_flight=outbound_flight.id,
        scan_date=scan_timestamp,
        discounted_price=outbound_flight.discounted_price,
        **additional_keys,
    )

    monthly_flight.save()


def parse_and_save_custom_search(flight, scan_timestamp, config_hash: str):
    outbound_flight, _ = parse_and_save_direct_flights(flight, scan_timestamp)
    db.ConfigToFlightMap(
        config_hash=config_hash, flight_id=outbound_flight.id, scan_date=scan_timestamp
    ).save()


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
    if not all([date_to, date_from]):
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
        parse_and_save_monthly_flight(flight, scan_timestamp, holiday_name=holiday_name)
