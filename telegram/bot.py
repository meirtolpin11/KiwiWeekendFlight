import os
import config
import helpers
import airports
import requests
import database as db
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Create a Jinja2 environment and specify the template directory
env = Environment(loader=FileSystemLoader("telegram/jinja"))


def generate_cheapest_flights(scan_timestamp):
    cheapest_flights_query = db.prepare_flights_per_city(
        scan_timestamp, where=db.Flights.holiday_name == ""
    )
    output_path = os.path.join(config.tmp_folder, "cheapest.csv")
    helpers.dump_csv(cheapest_flights_query, output_path)

    title = "<b>\N{airplane} Cheapest Flights - \N{airplane}</b>\n"
    body = generate_message(cheapest_flights_query)
    return "\n".join([title, body]), output_path


def publish_special_date_report(chat_id, scan_timestamp):
    special_dates = db.get_special_date_flights(scan_timestamp)
    cheapest_flights_report = generate_message(special_dates)
    if config.publish:
        status_code = send_message_to_chat(cheapest_flights_report, chat_id)

    return cheapest_flights_report


def publish_default_report(
    chat_id,
    date_from,
    date_to,
    scan_timestamp,
    query_function=db.prepare_flights_per_city,
    **query_params,
):
    total_report = []

    cheapest_flights_report, output_path = generate_cheapest_flights(scan_timestamp)
    if config.publish:
        send_message_to_chat(cheapest_flights_report, chat_id)
        send_file_to_chat(output_path, "", chat_id)
    total_report.append(cheapest_flights_report)

    # Cheap flights by Months
    current_month = date_from.month
    number_of_months = date_to.month - current_month
    if number_of_months < 0:
        number_of_months += 12

    # to do: make this parameterized
    for i in range(number_of_months + 1):
        message, output_path = generate_report_per_month(
            current_month, scan_timestamp, query_function, **query_params
        )

        if not message:
            current_month += 1
            continue

        # send the message and the query
        if all([config.publish, message, output_path]):
            send_message_to_chat(message, chat_id)
            send_file_to_chat(output_path, "", chat_id)

        total_report.append(message)
        current_month += 1

    cheapest_holidays_report, output_path = generate_holidays_report(scan_timestamp)

    if cheapest_holidays_report:
        if config.publish:
            send_message_to_chat(cheapest_holidays_report, chat_id)
            send_file_to_chat(output_path, "", chat_id)
        total_report.append(cheapest_holidays_report)

    return total_report


def generate_holidays_report(scan_timestamp):
    # we need a new query here
    cheapest_flights_query = db.prepare_flights_per_city(
        scan_timestamp, where=db.Flights.holiday_name != ""
    )
    output_path = os.path.join(config.tmp_folder, "holidays.csv")
    helpers.dump_csv(cheapest_flights_query, output_path)

    title = "<b>\N{airplane} Holiday Flights - \N{airplane}</b>\n"
    body = generate_message(cheapest_flights_query)
    if len(body.strip()) == 0:
        return None, None
    return "\n".join([title, body]), output_path


def generate_report_per_month(
    month, scan_timestamp, query_function=db.prepare_flights_per_city, **query_params
):
    if month > 12:
        month %= 12

    # query the cheapest flights by month
    # TODO: verify
    if "where" in query_params:
        where_clause = {
            "where": query_params["where"]
            & (db.Flights.month == month)
            & (db.Flights.holiday_name == "")
        }
        month_query = query_function(scan_timestamp, **where_clause)
    else:
        month_query = query_function(
            scan_timestamp,
            where=(db.Flights.month == month) & (db.Flights.holiday_name == ""),
            **query_params,
        )

    if len(month_query) == 0:
        return None, None

    output_file = os.path.join(
        config.tmp_folder, f"{datetime.strptime(str(month), '%m').strftime('%B')}.csv"
    )
    # dump the query output to the reports folder
    helpers.dump_csv(month_query, output_file)

    # generate bot message per month
    title = f"<b>\N{airplane} Cheapest Flights <i>({datetime.strptime(str(month), '%m').strftime('%B')})</i> - \N{airplane}</b>\n"
    body = generate_message(month_query)

    if len(body.strip()) == 0:
        return None, None

    return "\n".join([title, body]), output_file


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
