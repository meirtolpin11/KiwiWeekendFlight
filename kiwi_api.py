import requests
import urllib
import csv
import json
from datetime import datetime, timedelta, date
from peewee import *
import flights_database as db

API_KEY = ""
URL = "https://tequila-api.kiwi.com/v2/search"
HEADERS = {
	"accept": "application/json",
	"apikey": API_KEY
}

IATA_CODES_CACHE = {}

SPECIAL_DESTINATION = [
	"HU", 
	"IT", 
	"DE",
	"CZ",
	"FR",
	"GR",
	"BG",
	"RO",
	"BE",
	"PL",
	"UK",
	"NL",
	"ES"
]

# load kiwi api key from seperate file (for security reasons)
def load_config(path = "config.json.private"):
	global API_KEY
	data = json.load(open(path))

	API_KEY = data['kiwi_api']
	HEADERS['apikey'] = API_KEY

def dump_csv(query, file_or_name, include_header=True, close_file=True,
             append=False, csv_writer=None):
    """
    Create a CSV dump of a query.
    """

    fh = open(file_or_name, append and 'a' or 'w', encoding='utf-8', newline='')

    writer = csv_writer or csv.writer(
        fh,
        delimiter=',',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL)

    if include_header:
        writer.writerow([header.name for header in query.selected_columns])

    for row in query.tuples().iterator():
    	writer.writerow(row)

    if close_file:
        fh.close()

    return fh

def search_for_flight(search_params):

	response = requests.get(f"{URL}", params=search_params, headers=HEADERS)
	return response.json()

def daterange(date1, date2):
	for n in range(int ((date2 - date1).days)+1):
		yield date1 + timedelta(n)

def get_weekends(start_dt, end_dt):
	weekend_days = [4,7]
	weekends = []
	pair = ["", ""]

	for dt in daterange(start_dt, end_dt):
		if dt.isoweekday() in weekend_days:
			if dt.isoweekday() == weekend_days[0]:
				pair[0] = dt.strftime("%Y-%m-%d")
			else:
				pair[1] = dt.strftime("%Y-%m-%d")
				weekends.append(pair)
				pair = ["", ""]

	return weekends

def get_airline_name(iata_code):

	resp = db.IATA.select(db.IATA.airline).where(db.IATA.code == iata_code).execute() 
	if len(resp) > 0:
		return resp[0].airline

	url = "https://iata-and-icao-codes.p.rapidapi.com/airline"

	querystring = {"iata_code":iata_code}

	headers = {
		"X-RapidAPI-Key": "6c7d471d8bmsh3830faf947c0858p12e8ddjsn6ec3222ee5be",
		"X-RapidAPI-Host": "iata-and-icao-codes.p.rapidapi.com"
	}

	response = requests.request("GET", url, headers=headers, params=querystring)

	db.IATA(airline=response.json()[0]["name"], code=iata_code).save()
	return response.json()[0]["name"]

def calculate_days_off(departure, arrival):
	days_off = 0

	if departure.isoweekday() == 4 and departure.hour < 19:
		days_off += 1

	if arrival.isoweekday() == 7 and arrival.hour > 10:
		days_off += 1

	return days_off

def search_flights(date_from, date_to, fly_to = "", output_file = "flights_output.csv"):

	date_of_scan = datetime.now()
	# default search params - should be changed
	params = {
		"fly_from": "TLV",
		"fly_to": fly_to,
		"date_from": "",
		"date_to": "",
		"return_from": "",
		"return_to": "",
		"nights_in_dst_from": 2,
		"nights_in_dst_to": 5,
		"flight_type": "round",
		"one_for_city": False,
		"max_stopovers": 0,
		"price_to": 400,
		"curr": "ILS",
		"ret_from_diff_airport": 0
	}

	weekend_dates = get_weekends(date_from, date_to)

	for weekend in weekend_dates:
		print(weekend)
		params["date_from"] = params["return_from"] = weekend[0]
		params["date_to"] = params["return_to"] = weekend[1]

		flights = search_for_flight(params)

		# flights data
		try:
			flights_data = flights["data"]
		except:
			print(flights)
			continue

		for flight in flights_data:

			# parse the relevant flight information
			source = f"{flight['countryFrom']['name']}/{flight['cityFrom'] }/{flight['flyFrom']}"
			dest = f"{flight['countryTo']['name']}/{flight['cityTo']}/{flight['flyTo']}"
			price = int(flight['price'])
			airlines = ','.join(set([get_airline_name(airline) for airline in flight['airlines']]))

			# datetime files 
			source_departure = datetime.strptime(flight['route'][0]['local_departure'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			dest_arrival = datetime.strptime(flight['route'][0]['local_arrival'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			dest_departure = datetime.strptime(flight['route'][1]['local_departure'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			source_arrival = datetime.strptime(flight['route'][1]['local_arrival'], r"%Y-%m-%dT%H:%M:%S.%fZ")

			# caclulate how many days off the work are needed
			days_off = calculate_days_off(source_departure, source_arrival)

			db_flight = db.Flights(fly_from = source, fly_to = dest, price = price, nights = int(flight['nightsInDest']), airlines = airlines, departure_to =  source_departure, days_off = days_off,  arrival_to = dest_arrival, departure_from = dest_departure, arrival_from = source_arrival, date_of_scan = date_of_scan, month = source_departure.month)

			db_flight.save()
				
def create_report():

	cheapest_flights_query = db.prepare_query_cheapest_flights_per_city()
	dump_csv(cheapest_flights_query, "reports/cheapest.csv")

	current_month = datetime.now().month
	for i in range(4):
		if current_month > 12:
			current_month -= 12

		month_query = db.prepare_query_cheapest_flights_per_month(current_month)
		dump_csv(month_query, f"reports/{current_month}.csv")

		current_month += 1 

def main():
	date_from = datetime.now()
	date_to = datetime(2022, 12, 30)
	
	# search_flights(date_from, date_to)

	# # search for special destinations
	# search_flights(date_from, date_to, fly_to = ','.join(SPECIAL_DESTINATION))

	create_report()

if __name__ == '__main__':
	load_config()
	main()