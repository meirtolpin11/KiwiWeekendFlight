import os
import requests
import config
import helpers
import airports
import database as db
from datetime import datetime


def generate_cheapest_flights(scan_timestamp):
    cheapest_flights_query = db.prepare_flights_per_city(scan_timestamp)
    output_path = os.path.join(config.tmp_folder, "cheapest.csv")
    helpers.dump_csv(cheapest_flights_query, output_path)

    title = "<b>\N{airplane} Cheapest Flights - \N{airplane}</b>\n"
    body = generate_message(cheapest_flights_query)
    return "\n".join([title, body]), output_path


def publish_default_report(chat_id, scan_timestamp, query_function=db.prepare_flights_per_city, **query_params):
    total_report = []

    cheapest_flights_report, output_path = generate_cheapest_flights(scan_timestamp)
    if config.publish:
        send_message_to_chat(cheapest_flights_report, chat_id)
        send_file_to_chat(output_path, "", chat_id)
    total_report.append(cheapest_flights_report)

    # Cheap flights by Months
    current_month = datetime.now().month
    for i in range(config.NUM_OF_MONTHS):
        message, output_path = generate_report_per_month(current_month, scan_timestamp, query_function, **query_params)

        # send the message and the query
        if config.publish and message and output_path:
            send_message_to_chat(message, chat_id)
            send_file_to_chat(output_path, "", chat_id)

        total_report.append(message)
        current_month += 1

    return total_report


def generate_report_per_month(month, scan_timestamp, query_function=db.prepare_flights_per_city, **query_params):
    if month > 12:
        month %= 12

    # query the cheapest flights by month
    # TODO: verify
    if "where" in query_params:
        where_clause = {"where": query_params["where"] & (db.Flights.month == month)}
        month_query = query_function(scan_timestamp, **where_clause)
    else:
        month_query = query_function(scan_timestamp, where=db.Flights.month == month, **query_params)

    if len(month_query) == 0:
        return None, None

    output_file = os.path.join(config.tmp_folder, f"{datetime.strptime(str(month), '%m').strftime('%B')}.csv")
    # dump the query output to the reports folder
    helpers.dump_csv(month_query, output_file)

    # generate bot message per month
    title = f"<b>\N{airplane} Cheapest Flights <i>({datetime.strptime(str(month), '%m').strftime('%B')})</i> - \N{airplane}</b>\n"
    body = generate_message(month_query)

    return '\n'.join([title, body]), output_file


def generate_message(query):
    # TODO: use jinja template
    message = []
    for flight in query:
        flight_line = f"\n<b>{flight.fly_to.split('/')[1]}</b> <i>({flight.fly_to.split('/')[0]})</i>"
        message.append(flight_line)

        # generate departure and arrival dates lines
        dates_line = ""
        if flight.departure_to.month == flight.arrival_from.month:
            dates_line += f"\N{calendar} \t<b>{flight.departure_to.strftime('%d/%m %H:%M')} - " \
                          f"{flight.arrival_from.strftime('%d/%m %H:%M')}</b>"
        else:
            dates_line += f"\N{calendar} \t<b>{flight.departure_to.strftime('%d/%m %H:%M')} - " \
                          f"{flight.arrival_from.strftime('%d/%m %H:%M')}</b>"
        dates_line += f"<i>({flight.departure_to.strftime('%a')} - " \
                      f"{flight.arrival_from.strftime('%a')})</i> \N{calendar}"

        message.append(dates_line)

        # generate flight confirmation line
        if hasattr(airports, flight.fly_from.split('/')[2].lower()):
            airport_helper = getattr(airports, flight.fly_from.split('/')[2].lower())
            is_flight_confirmed = airport_helper.get_flight_confirmation(flight.flight_numbers.split(',')[0],
                                                                         flight.departure_to)

            if is_flight_confirmed == -1:
                # if returned -1 that means that flight are found but the flight is missing
                message.append(f"\N{cross mark} Flight - {flight.flight_numbers.split(',')[0]} maybe is not confirmed")
            elif is_flight_confirmed == -2 or is_flight_confirmed == -3:
                # if returned -2 that means that no flight returned from iaa api - can be an error
                pass
            else:
                # flight is found and it's confirmed
                message.append(
                    f"\N{white heavy check mark} Flight - {flight.flight_numbers.split(',')[0]} is confirmed")

        if flight.price == flight.discount_price:
            message.append(f"\t\N{money bag} <b>{flight.price} nis</b> \N{money bag}")
        else:
            message.append(f"\t\N{money bag} <b>{flight.price} nis, " 
                           f"<i>Members: {flight.discount_price} nis</i></b> \N{money bag}")

        # generate airlines and links line
        message += generate_airline_link(flight)
    return '\n'.join(message)


def generate_airline_link(flight):
    message = []

    if flight.airlines.split(',')[0] == flight.airlines.split(',')[1]:
        # in case of the same airline
        if flight.link_to == flight.link_from == "":
            # in case there is no link for this airline
            message.append(f"\t\N{airplane} {flight.airlines.split(',')[0]} \N{airplane}")
        else:
            message.append(
                f"\t\N{airplane} <a href='{flight.link_to}'>{flight.airlines.split(',')[0]}</a> \N{airplane}")
    else:
        # different airlines
        links_line = ""

        # departure leg
        if flight.link_to != "":
            links_line += f"\t\N{airplane} <a href='{flight.link_to}'>{flight.airlines.split(',')[0]}</a>, "
        else:
            links_line += f"\t\N{airplane} {flight.airlines.split(',')[0]}, "

        # arrival leg
        if flight.link_from != "":
            links_line += f"<a href='{flight.link_from}'>{flight.airlines.split(',')[1]}</a> \N{airplane}"
        else:
            links_line += f"{flight.airlines.split(',')[1]} \N{airplane}"

        message.append(links_line)

    return message


def send_message_to_chat(message_to_send, chat_id):
    data = {"chat_id": chat_id, "text": message_to_send, "parse_mode": "HTML"}
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOTS['default']['token']}/sendMessage"

    return requests.post(url, data=data).json()


def send_file_to_chat(filename, caption, chat_id):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOTS['default']['token']}/sendDocument"

    data = {"chat_id": chat_id, "caption": caption}
    file_handle = open(filename, 'rb')

    resp = requests.post(url, data=data, files={"document": file_handle})

    return resp.json()
