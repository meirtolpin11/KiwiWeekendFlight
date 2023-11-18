import os
import json
import config
import helpers
import airports
import requests
import database as db
from peewee import JOIN
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Create a Jinja2 environment and specify the template directory
env = Environment(loader=FileSystemLoader("telegram/jinja"))


def generate_cheapest_flights(scan_timestamp: int, one_per_city: bool = True):
    cheapest_flights_query = db.cheapest_flights_by_source_dest(
        db.WeekendFlights, scan_timestamp, one_per_city
    )

    title = "<b>\N{airplane} Cheapest Flights - \N{airplane}</b>\n"
    body = generate_message_refactored(cheapest_flights_query)
    return "\n".join([title, body])


def publish_special_date_report(special_dates, chat_id, scan_timestamp):
    # generate all hashes of the relevant dates -
    hashes_list = []
    for special_date in special_dates:
        hashes_list.append(str(hash(json.dumps(special_date))))

    special_dates_query = db.ConfigToFlightMap.select(
        db.ConfigToFlightMap.flight_id.alias("outbound_flight")
    ).where(
        (db.ConfigToFlightMap.config_hash << hashes_list)
        & (db.ConfigToFlightMap.scan_date == scan_timestamp)
    )

    cheapest_flights_report = generate_message_refactored(special_dates_query)
    if config.publish:
        status_code = send_message_to_chat(cheapest_flights_report, chat_id)

    return cheapest_flights_report


def publish_default_report(
    chat_id, date_from, date_to, scan_timestamp, one_per_city: bool = True
):
    total_report = []

    cheapest_flights_report = generate_cheapest_flights(scan_timestamp)
    if config.publish:
        send_message_to_chat(cheapest_flights_report, chat_id)
    total_report.append(cheapest_flights_report)

    # Cheap flights by Months
    current_month = date_from.month
    number_of_months = date_to.month - current_month
    if number_of_months < 0:
        number_of_months += 12

    # to do: make this parameterized
    for i in range(number_of_months + 1):
        message = generate_report_per_month(current_month, scan_timestamp)

        if not message:
            current_month += 1
            continue

        # send the message and the query
        if all([config.publish, message]):
            send_message_to_chat(message, chat_id)

        total_report.append(message)
        current_month += 1

    cheapest_holidays_report = generate_holidays_report(scan_timestamp)

    if cheapest_holidays_report:
        if config.publish:
            send_message_to_chat(cheapest_holidays_report, chat_id)
        total_report.append(cheapest_holidays_report)

    return total_report


def generate_holidays_report(scan_timestamp):
    # we need a new query here
    cheapest_flights_query = db.cheapest_flights_by_source_dest(
        db.HolidayFlights, scan_timestamp
    )

    title = "<b>\N{airplane} Holiday Flights - \N{airplane}</b>\n"
    body = generate_message_refactored(cheapest_flights_query)
    if len(body.strip()) == 0:
        return None
    return "\n".join([title, body])


def generate_report_per_month(month: int, scan_timestamp: int):
    month = month if month <= 12 else month % 12
    month_name = datetime.strptime(str(month), "%m").strftime("%B")

    month_query = (
        db.WeekendFlights.select()
        .where(
            (db.WeekendFlights.month == month)
            & (db.WeekendFlights.scan_date == scan_timestamp)
        )
        .group_by(db.WeekendFlights.dest, db.WeekendFlights.source)
        .order_by(db.WeekendFlights.discounted_price)
    )

    if not month_query.count():
        return None

    # generate bot message per month
    title = (
        f"<b>\N{airplane} Cheapest Flights <i>({month_name})</i> - \N{airplane}</b>\n"
    )
    body = generate_message_refactored(month_query)

    if len(body.strip()) == 0:
        return None

    return "\n".join([title, body])


def get_flight_confirmation_status(outbound_flight):
    # generate flight confirmation line
    if hasattr(airports, outbound_flight.source.split("/")[2].lower()):
        airport_helper = getattr(airports, outbound_flight.source.split("/")[2].lower())
        try:
            if config.CHECK_FLIGHT_CONFIRMATION:
                is_flight_confirmed = airport_helper.get_flight_confirmation(
                    outbound_flight.flight_number, outbound_flight.dest
                )
            else:
                is_flight_confirmed = -2
        except Exception:
            is_flight_confirmed = -2
    else:
        is_flight_confirmed = -1

    return is_flight_confirmed


def generate_message_refactored(flights):
    # Load the template from the file
    template = env.get_template("flight.jinja2")

    message = []
    for flight in flights:
        outbound_flight = db.DirectFlight.select().where(
            db.DirectFlight.id == flight.outbound_flight
        )[0]

        inbound_flight = None
        if getattr(outbound_flight, "round_flight", False):
            inbound_flight = db.DirectFlight.select().where(
                db.DirectFlight.id == outbound_flight.round_flight
            )[0]

        message += [
            template.render(
                fly_from=outbound_flight.source,
                fly_to=outbound_flight.dest,
                holiday=getattr(flight, "holiday_name", None),
                round=getattr(outbound_flight, "round_flight", False),
                takeoff_to=outbound_flight.departure_time,
                landing_back=getattr(inbound_flight, "landing_time", ""),
                landing_to=outbound_flight.landing_time,
                flight_confirmed=get_flight_confirmation_status(outbound_flight),
                flight_numbers=[
                    outbound_flight.flight_number,
                    getattr(
                        inbound_flight, "flight_number", outbound_flight.flight_number
                    ),
                ],
                price=outbound_flight.price,
                discounted_price=outbound_flight.discounted_price,
                airlines=[
                    outbound_flight.airline,
                    getattr(inbound_flight, "airline", outbound_flight.airline),
                ],
                link_to=outbound_flight.link,
                link_from=getattr(inbound_flight, "link", ""),
            ).strip()
        ]

    return "\n\n".join(message)


def generate_message(query):
    # Load the template from the file
    template = env.get_template("flight.jinja2")

    # TODO: use jinja template
    message = []
    for flight in query:
        # generate flight confirmation line
        if hasattr(airports, flight.fly_from.split("/")[2].lower()):
            airport_helper = getattr(airports, flight.fly_from.split("/")[2].lower())
            try:
                if config.CHECK_FLIGHT_CONFIRMATION:
                    is_flight_confirmed = airport_helper.get_flight_confirmation(
                        flight.flight_numbers.split(",")[0], flight.departure_to
                    )
                else:
                    is_flight_confirmed = -2
            except Exception:
                is_flight_confirmed = -2
        else:
            is_flight_confirmed = -1

        message += [
            template.render(
                fly_from=flight.fly_from,
                fly_to=flight.fly_to,
                holiday=flight.holiday_name,
                round=bool(flight.arrival_from),
                takeoff_to=flight.departure_to,
                landing_back=flight.arrival_from,
                landing_to=flight.arrival_to,
                flight_confirmed=is_flight_confirmed,
                flight_numbers=flight.flight_numbers,
                price=flight.price,
                discounted_price=flight.discount_price,
                airlines=flight.airlines.split(","),
                link_to=flight.link_to,
                link_from=flight.link_from,
            ).strip()
        ]

    return "\n\n".join(message)


def send_message_to_chat(message_to_send, chat_id):
    data = {"chat_id": chat_id, "text": message_to_send, "parse_mode": "HTML"}
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOTS['default']['token']}/sendMessage"

    return requests.post(url, data=data).json()


def send_file_to_chat(filename, caption, chat_id):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOTS['default']['token']}/sendDocument"

    data = {"chat_id": chat_id, "caption": caption}
    file_handle = open(filename, "rb")

    resp = requests.post(url, data=data, files={"document": file_handle})

    return resp.json()
