from peewee import *

db = SqliteDatabase('/tmp/flights.db')


class Flights(Model):
    fly_from = CharField()
    fly_to = CharField()
    nights = IntegerField()
    days_off = IntegerField()
    price = IntegerField()
    discount_price = IntegerField()
    airlines = CharField()
    flight_numbers = CharField()
    departure_to = DateTimeField()
    arrival_to = DateTimeField()
    departure_from = DateTimeField()
    arrival_from = DateTimeField()
    link_to = CharField()
    link_from = CharField()
    month = IntegerField()
    date_of_scan = DateTimeField()
    holiday_name = CharField()

    class Meta:
        database = db


class IATA(Model):
    code = CharField()
    airline = CharField()

    class Meta:
        database = db


def prepare_flights_per_city(scan_timestamp, **query_params):
    user_where_cause = query_params["where"] if "where" in query_params else True

    # query the cheapest flights per city
    flights = Flights.select(Flights.fly_to, Flights.fly_from, fn.Min(Flights.price).alias("price"),
                             Flights.discount_price, Flights.airlines, Flights.flight_numbers, Flights.nights,
                             Flights.days_off, Flights.departure_to,
                             Flights.arrival_to, Flights.departure_from, Flights.arrival_from,
                             Flights.link_to, Flights.link_from, Flights.holiday_name). \
        where(user_where_cause & (Flights.date_of_scan == scan_timestamp)). \
        group_by(Flights.fly_to, Flights.fly_from). \
        order_by(Flights.price)

    return flights


def prepare_single_destination_flights(scan_timestamp, **query_params):
    user_where_cause = query_params["where"] if "where" in query_params else True

    flights = Flights.select(Flights.fly_from, Flights.fly_to, Flights.price, Flights.discount_price, Flights.airlines,
                             Flights.flight_numbers, Flights.nights,
                             Flights.days_off, Flights.departure_to,
                             Flights.arrival_to, Flights.departure_from, Flights.arrival_from,
                             Flights.link_to, Flights.link_from, Flights.holiday_name).\
        where((Flights.date_of_scan == scan_timestamp) & user_where_cause).\
        order_by(Flights.price)

    flights = flights.limit(5)

    return flights


db.create_tables([Flights, IATA])
