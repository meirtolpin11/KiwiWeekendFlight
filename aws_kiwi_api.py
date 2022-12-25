import requests
import urllib
import json
import bot
import flights_database as db
import airlines
import boto3
import os
import logging
import helpers
from aws_helper import download_from_bucket, upload_to_bucket
from datetime import datetime, timedelta, date
from peewee import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
	"ES",
	"SP"
]

SCAN_DATE = None
FLY_FROM = 'TLV'

# load kiwi api key from seperate file (for security reasons)
def load_config(path = "config.json.private"):
	global API_KEY
	data = json.load(open(path))

	API_KEY = data['kiwi_api']
	HEADERS['apikey'] = API_KEY
	bot.TOKEN = data['bot_token']
	bot.CHAT_ID = data['chat_id']

def query_flight_kiwi(search_params):

	response = requests.get(f"{URL}", params=search_params, headers=HEADERS)
	return response.json()

def search_flights(date_from, date_to, fly_to = "", price_to=400):
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
		"price_to": price_to,
		"curr": "ILS",
		"ret_from_diff_airport": 0
	}

	weekend_dates = helpers.get_weekends(date_from, date_to)

	for weekend in weekend_dates:
		params["date_from"] = params["return_from"] = weekend[0]
		params["date_to"] = params["return_to"] = weekend[1]

		flights = query_flight_kiwi(params)

		# flights data
		try:
			flights_data = flights["data"]
		except:
			continue

		for flight in flights_data:

			# parse the relevant flight information
			source = f"{flight['countryFrom']['name']}/{flight['cityFrom'] }/{flight['flyFrom']}"
			dest = f"{flight['countryTo']['name']}/{flight['cityTo']}/{flight['flyTo']}"
			price = int(flight['price'])

			str_airlines = ','.join([airlines.get_airline_name(route['airline']) for route in flight['route']])

			# datetime files 
			source_departure = datetime.strptime(flight['route'][0]['local_departure'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			dest_arrival = datetime.strptime(flight['route'][0]['local_arrival'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			dest_departure = datetime.strptime(flight['route'][1]['local_departure'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			source_arrival = datetime.strptime(flight['route'][1]['local_arrival'], r"%Y-%m-%dT%H:%M:%S.%fZ")

			link_to = link_from = ""

			if str_airlines.split(',')[0] == str_airlines.split(',')[1]:
				if str_airlines.split(',')[0].lower() in airlines.airlines_dict.keys():
					link_to = link_from = airlines.airlines_dict[str_airlines.split(',')[0].lower()](flight['flyFrom'], flight['flyTo'], source_departure, dest_departure)
			else:
				if str_airlines.split(',')[0].lower() in airlines.airlines_dict.keys():
					link_to = airlines.airlines_dict[str_airlines.split(',')[0].lower()](flight['flyFrom'], flight['flyTo'], source_departure, dest_departure, isround=False)

				if str_airlines.split(',')[1].lower() in airlines.airlines_dict.keys():
					link_from = airlines.airlines_dict[str_airlines.split(',')[1].lower()](flight['flyFrom'], flight['flyTo'], source_departure, dest_departure, isround=False)
				

			# caclulate how many days off the work are needed
			days_off = helpers.calculate_days_off(source_departure, source_arrival)

			db_flight = db.Flights(fly_from = source, fly_to = dest, price = price, nights = int(flight['nightsInDest']), airlines = str_airlines, departure_to =  source_departure, days_off = days_off,  arrival_to = dest_arrival, departure_from = dest_departure, arrival_from = source_arrival, date_of_scan = SCAN_DATE, month = source_departure.month, link_to = link_to, link_from = link_from)

			db_flight.save()

def create_report():
	
	cheapest_flights_query = db.prepare_query_cheapest_flights_per_city()
	helpers.dump_csv(cheapest_flights_query, "reports/cheapest.csv")

	message = ""
	message += "<b>\N{airplane} Cheapest Flights - \N{airplane}</b>\n"
	message += bot.generate_message(cheapest_flights_query)

	bot.send_message_to_chat(message, chat_id = bot.CHAT_ID)
	bot.send_file_to_chat("reports/cheapest.csv", "", chat_id = bot.CHAT_ID)

	current_month = datetime.now().month
	for i in range(5):
		if current_month > 12:
			current_month -= 12

		month_query = db.prepare_query_cheapest_flights_per_month(current_month)
		if len(month_query) == 0:
			current_month += 1
			continue

		helpers.dump_csv(month_query, f"reports/{datetime.strptime(str(current_month), '%m').strftime('%B')}.csv")

		message = ""
		message += f"<b>\N{airplane} Cheapest Flights <i>({datetime.strptime(str(current_month), '%m').strftime('%B')})</i> - \N{airplane}</b>\n"

		message += bot.generate_message(month_query)
		bot.send_message_to_chat(message, chat_id = bot.CHAT_ID)
		bot.send_file_to_chat(f"reports/{datetime.strptime(str(current_month), '%m').strftime('%B')}.csv", "", chat_id = bot.CHAT_ID) 

		current_month += 1

def lambda_handler(event, context):
	global SCAN_DATE

	download_from_bucket("flights.db", '/tmp/flight.db')
	load_config("testing_config.json.private")

	try:
		os.mkdir(r'reports')
	except Exception as e:
		logging.error(e.message)

	SCAN_DATE = datetime.now()

	date_from = datetime.now()
	date_to = date_from + timedelta(days= 5 * 30)
	

	# search for special destinations
	search_flights(date_from, date_to, fly_to = ','.join(SPECIAL_DESTINATION))

	create_report()

	upload_to_bucket(r'/tmp/flights.db', 'flights.db')

	return{
		'statusCode': 200,
		'body': json.dumps('Success')
	}