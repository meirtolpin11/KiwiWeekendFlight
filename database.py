from peewee import *
from typing import Type

db = SqliteDatabase("/tmp/flights.db")


class DirectFlight(Model):
    source = CharField()
    dest = CharField()
    airline = CharField()
    price = IntegerField()
    discounted_price = IntegerField()
    flight_number = CharField()
    link = CharField()
    departure_time = DateTimeField()
    landing_time = DateTimeField()
    scan_date = DateTimeField()
    next_flight = IntegerField(null=True)
    round_flight = IntegerField(null=True)

    class Meta:
        database = db
        constraints = [
            SQL("FOREIGN KEY(next_flight) REFERENCES DirectFlight(id)"),
            SQL("FOREIGN KEY(round_flight) REFERENCES DirectFlight(id)"),
        ]


class ConfigToFlightMap(Model):
    config_hash = CharField()
    flight_id = IntegerField()
    scan_date = CharField()

    class Meta:
        database = db
        constraints = [
            SQL("FOREIGN KEY(flight_id) REFERENCES DirectFlight(id)"),
        ]


class WeekendFlights(Model):
    month = IntegerField()
    source = CharField()
    dest = CharField()
    outbound_flight = CharField()
    scan_date = DateTimeField()
    discounted_price = IntegerField()

    class Meta:
        database = db


class HolidayFlights(WeekendFlights):
    holiday_name = CharField()


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


def cheapest_flights_by_source_dest(
    table: Type[WeekendFlights],
    scan_timestamp: int,
    one_per_city: bool = True,
    limit: int = 5,
):
    query = table.select().where((table.scan_date == scan_timestamp))
    if one_per_city:
        return (
            query.group_by(table.dest, table.source)
            .order_by(table.discounted_price)
            .limit(limit)
        )
    else:
        return query.order_by(table.discounted_price)


db.create_tables([ConfigToFlightMap, DirectFlight, WeekendFlights, HolidayFlights])
