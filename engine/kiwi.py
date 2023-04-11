import copy
import config
import helpers
import logging
import airlines
import requests
import database as db
from datetime import datetime


# noinspection PyBroadException
def query_flight_kiwi(search_params):
    try:
        response = requests.get(config.URL, params=search_params, headers=config.HEADERS)
        return response.json()
    except Exception as e:
        return -1


def get_date(flight, field):
    return datetime.strptime(flight[field], r"%Y-%m-%dT%H:%M:%S.%fZ")


def generate_weekend_flights(date_from: datetime, date_to: datetime, fly_to: str,
                             price_to: int = 500, nights_in_dst_from: str = 2, nights_in_dst_to: str = 5) -> int:
    scan_timestamp = int(datetime.timestamp(datetime.now()))
    weekend_dates = helpers.get_weekends(date_from, date_to)
    for weekend_id, weekend in enumerate(weekend_dates):
        generate_flights(weekend[0], weekend[1], fly_to, price_to, nights_in_dst_from, nights_in_dst_to, scan_timestamp)
    return scan_timestamp


def prepare_kiwi_api(fly_to, price_to, date_from, date_to, nights_in_dst_from, nights_in_dst_to):
    # get a local copy of the api params dict
    kiwi_api_params = copy.deepcopy(config.KIWI_API_PARAMS)
    kiwi_api_params['fly_to'] = fly_to
    kiwi_api_params['price_to'] = price_to
    kiwi_api_params['date_from'] = date_from
    kiwi_api_params['return_from'] = date_from
    kiwi_api_params['date_to'] = date_to
    kiwi_api_params['return_to'] = date_to
    kiwi_api_params['nights_in_dst_from'] = nights_in_dst_from
    kiwi_api_params['nights_in_dst_to'] = nights_in_dst_to

    return kiwi_api_params


def generate_flights(date_from: datetime, date_to: datetime, fly_to: str,
                     price_to: int = 500, nights_in_dst_from: str = 2, nights_in_dst_to: str = 5,
                     scan_timestamp: int = int(datetime.timestamp(datetime.now()))):
    kiwi_api_params = prepare_kiwi_api(fly_to, price_to, date_from, date_to, nights_in_dst_from, nights_in_dst_to)

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
        source = f"{flight['countryFrom']['name']}/{flight['cityFrom']}/{flight['flyFrom']}"
        dest = f"{flight['countryTo']['name']}/{flight['cityTo']}/{flight['flyTo']}"
        price = int(flight['price'])

        airlines_list = [airlines.get_airline_name(route['airline']) for route in flight['route']]

        airline_class = None
        discount_price = price

        # get discount price is available
        if len(set(airlines_list)) == 1:
            # check that there is an airline class
            if hasattr(airlines, airlines_list[0].lower().replace(' ', '_')):
                airline_class = getattr(airlines, airlines_list[0].lower().replace(' ', '_'))
                # check there is a discount calculation function
                if hasattr(airline_class, "calculate_discount_price"):
                    discount_price = airline_class.calculate_discount_price(price)

        links = ["", ""]

        if len(set(airlines_list)) == 1:
            if airline_class:
                links[0] = links[1] = airline_class.generate_link(flight['flyFrom'],
                                                                  flight['flyTo'],
                                                                  get_date(flight['route'][0], 'local_departure'),
                                                                  get_date(flight['route'][1], 'local_departure'))
        else:
            for i in range(2):
                # generate separate links for every flight
                # TODO: check kiwi api about fly from and to in a route
                if hasattr(airlines, airlines_list[i].lower().replace(' ', '_')):
                    airline_class = getattr(airlines, airlines_list[i].lower().replace(' ', '_'))
                    links[i] = airline_class.generate_link(flight['route'][i]['flyFrom'],
                                                           flight['route'][i]['flyTo'],
                                                           get_date(flight['route'][i], 'local_departure'),
                                                           is_round=False)

        # store flight numbers
        flight_numbers = ','.join(
            [direction['airline'] + str(direction['flight_no']) for direction in flight['route']])

        # calculate how many days off the work are needed
        days_off = helpers.calculate_days_off(get_date(flight['route'][0], 'local_departure'),
                                              get_date(flight['route'][1], 'local_arrival'))

        # insert the flight into the database
        db_flight = db.Flights(fly_from=source, fly_to=dest, price=price, discount_price=discount_price,
                               nights=int(flight['nightsInDest']), airlines=','.join(airlines_list),
                               departure_to=get_date(flight['route'][0], 'local_departure'),
                               departure_from=get_date(flight['route'][1], 'local_departure'),
                               arrival_to=get_date(flight['route'][0], 'local_arrival'),
                               arrival_from=get_date(flight['route'][1], 'local_arrival'),
                               month=get_date(flight['route'][0], 'local_departure').month,
                               days_off=days_off, date_of_scan=scan_timestamp,
                               link_to=links[0], link_from=links[1], weekend_id=-1,  # TODO: update weekend id
                               flight_numbers=flight_numbers)

        db_flight.save()
