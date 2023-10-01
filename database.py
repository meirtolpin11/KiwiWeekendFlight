from peewee import *

db = SqliteDatabase("/tmp/flights.db")


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
    special_date = BooleanField(default=False)

    class Meta:
        database = db


class UserQueryDetails(Model):
    fly_from = CharField()
    fly_to = CharField()
    min_nights = IntegerField()
    max_nights = IntegerField()
    date_from = DateTimeField()
    date_to = DateTimeField()
    chat_id = IntegerField()
    max_price = IntegerField()
    only_weekends = BooleanField()

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
    flights = (
        Flights.select(
            Flights.fly_to,
            Flights.fly_from,
            fn.Min(Flights.price).alias("price"),
            Flights.discount_price,
            Flights.airlines,
            Flights.flight_numbers,
            Flights.nights,
            Flights.days_off,
            Flights.departure_to,
            Flights.arrival_to,
            Flights.departure_from,
            Flights.arrival_from,
            Flights.link_to,
            Flights.link_from,
            Flights.holiday_name,
        )
        .where(user_where_cause & (Flights.date_of_scan == scan_timestamp))
        .group_by(Flights.fly_to, Flights.fly_from)
        .order_by(Flights.price)
    )

    return flights


def prepare_single_destination_flights(scan_timestamp, **query_params):
    user_where_cause = query_params["where"] if "where" in query_params else True

    flights = (
        Flights.select(
            Flights.fly_from,
            Flights.fly_to,
            Flights.price,
            Flights.discount_price,
            Flights.airlines,
            Flights.flight_numbers,
            Flights.nights,
            Flights.days_off,
            Flights.departure_to,
            Flights.arrival_to,
            Flights.departure_from,
            Flights.arrival_from,
            Flights.link_to,
            Flights.link_from,
            Flights.holiday_name,
        )
        .where((Flights.date_of_scan == scan_timestamp) & user_where_cause)
        .order_by(Flights.price)
    )

    flights = flights.limit(5)

    return flights


def get_special_date_flights(scan_timestamp):
    flights = (
        Flights.select(
            Flights.fly_from,
            Flights.fly_to,
            Flights.price,
            Flights.discount_price,
            Flights.airlines,
            Flights.flight_numbers,
            Flights.nights,
            Flights.days_off,
            Flights.departure_to,
            Flights.arrival_to,
            Flights.departure_from,
            Flights.arrival_from,
            Flights.link_to,
            Flights.link_from,
            Flights.holiday_name,
        )
        .where(
            (Flights.date_of_scan == scan_timestamp) & (Flights.special_date == True)
        )
    )

    return flights


# def prepare_userquery_flights(chat_id):
#
#     query_details = UserQueryDetails.select().where(UserQueryDetails.chat_id == chat_id)
#     if len(query_details) == 0:
#         return []
#
#     for query in query_details:
#         flights = Flights.select(Flights.fly_from, Flights.fly_to, Flights.price, Flights.discount_price, Flights.airlines,
#                              Flights.flight_numbers, Flights.nights,
#                              Flights.days_off, Flights.departure_to,
#                              Flights.arrival_to, Flights.departure_from, Flights.arrival_from,
#                              Flights.link_to, Flights.link_from, Flights.holiday_name).where(
#             Flights.fly_from == query.fly_from,
#             Flights.fly_to == query.fly_to,
#             query.min_nights <= Flights.nights <= query.max_nights,
#             Flights.departure_to >= query.date_from,
#             Flights.arrival_from <= query.date_to,
#             Flights.price <= query.max_price
#         )


db.create_tables([Flights, IATA, UserQueryDetails])
