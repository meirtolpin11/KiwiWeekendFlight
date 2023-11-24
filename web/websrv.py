import uvicorn
import calendar
import pycountry
import database as db
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass

app = FastAPI()
country_mapping = {
    country.name.lower(): country.alpha_2.lower() for country in pycountry.countries
}


def month_integer_to_name(month_integer):
    try:
        if month_integer == 0:
            return "Cheapest"
        # Get the English name of the month
        month_name = calendar.month_name[month_integer]
        return month_name
    except (IndexError, ValueError):
        # Handle invalid month integers
        return "Invalid Month"


def generate_flights_list(flights_query):
    flights_list = []
    for flight in flights_query:
        outbound_flight = db.DirectFlight.select().where(
            db.DirectFlight.id == flight.outbound_flight
        )[0]

        inbound_flight = None
        if getattr(outbound_flight, "round_flight", False):
            inbound_flight = db.DirectFlight.select().where(
                db.DirectFlight.id == outbound_flight.round_flight
            )[0]

        flights_list.append(
            {
                "flag": f"https://flagcdn.com/24x18/{country_mapping[outbound_flight.dest.split('/')[0].lower()]}.png",
                "destination": outbound_flight.dest,
                "departureDate": outbound_flight.departure_time.strftime(
                    "%A, %d/%m/%Y %H:%M"
                ),
                "arrivalDate": getattr(inbound_flight, "landing_time", "").strftime(
                    "%A, %d/%m/%Y %H:%M"
                ),
                "price": outbound_flight.price,
                "membersPrice": outbound_flight.discounted_price,
                "airlines": {
                    "departure": [outbound_flight.airline, outbound_flight.link],
                    "arrival": [
                        getattr(inbound_flight, "airline", ""),
                        getattr(inbound_flight, "link", ""),
                    ],
                    "round": [outbound_flight.airline, outbound_flight.link]
                    if outbound_flight.airline == getattr(inbound_flight, "airline")
                    else "",
                },
            }
        )
    return flights_list


@app.get("/get_flights")
def read_root(month: int = 0):
    if month == 0:
        cheapest_flights_query = db.cheapest_flights_by_source_dest(
            db.WeekendFlights, one_per_city=True
        )
    else:
        cheapest_flights_query = (
            db.WeekendFlights.select(
                db.WeekendFlights.id,
                db.WeekendFlights.month,
                db.WeekendFlights.source,
                db.WeekendFlights.dest,
                db.WeekendFlights.outbound_flight,
                db.WeekendFlights.scan_date,
                db.fn.MIN(db.WeekendFlights.discounted_price).alias("discounted_price"),
            )
            .where(
                (db.WeekendFlights.month == month)
                & (
                    db.WeekendFlights.scan_date
                    >= (
                        db.WeekendFlights.select(
                            db.fn.MAX(db.WeekendFlights.scan_date) - 600
                        )
                    )
                )
            )
            .group_by(db.WeekendFlights.dest, db.WeekendFlights.source)
            .order_by(db.SQL("discounted_price"))
        )

    return [month_integer_to_name(month), generate_flights_list(cheapest_flights_query)]


@app.get("/flight/get_available_months")
def get_available_months():
    months = db.WeekendFlights.select(db.fn.DISTINCT(db.WeekendFlights.month)).where(
        db.WeekendFlights.scan_date
        >= (db.WeekendFlights.select(db.fn.MAX(db.WeekendFlights.scan_date) - 600))
    )

    return [0] + [month.month for month in months]


app.mount("/", StaticFiles(directory="web/static", html=True), name="static")

# at last, the bottom of the file/module
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
