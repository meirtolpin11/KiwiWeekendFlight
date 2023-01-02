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
import argparse
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

NUM_OF_MONTHS = 5

SPECIAL_DESTINATION = [
	"HU", # Hungary
	"IT", # Italy
	"DE", # Germany
	"CZ", # Czech Republic
	"FR", # France 
	"GR", # Greece
	"BG", # Bulgaria
	"RO", # Romania
	"BE", # Belgium
	"PL", # Poland
	"NL", # Netherlands
	"ES", # Spain
	"SP" # Serbia
]

SPECIAL_CHATS = {
	"HU": ""
}


SCAN_DATE = None
FLY_FROM = 'TLV'

# load kiwi api key from seperate file (for security reasons)
def load_config(path = "config.json.private"):
	global API_KEY
	global HEADERS

	with open(path) as config:
		data = json.load(config)

		API_KEY = data['kiwi_api']
		HEADERS['apikey'] = API_KEY

		# update other files config
		bot.TOKEN = data['bot_token']
		bot.CHAT_ID = data['chat_id']
		SPECIAL_CHATS["HU"] = data['budapest_chat_id']
		SPECIAL_CHATS["CZ"] = data['czech_chat_id']
		airlines.CURRENCY_API_TOKEN = data['currency_convert_api']

def query_flight_kiwi(search_params):

	response = requests.get(f"{URL}", params=search_params, headers=HEADERS)
	return response.json()

def scan_all_flights(date_from, date_to, fly_to = "", price_to=400):
	# default search params - should be changed
	kiwi_query_params = {
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

	for weekend_id, weekend in enumerate(weekend_dates):
		kiwi_query_params["date_from"] = kiwi_query_params["return_from"] = weekend[0]
		kiwi_query_params["date_to"] = kiwi_query_params["return_to"] = weekend[1]

		flights = query_flight_kiwi(kiwi_query_params)

		# flights data
		try:
			flights_data = flights["data"]
		except Exception as e:
			logging.error(f"failed to fetch flight from kiwi api, error:{e}")
			continue

		for flight in flights_data:

			# parse the relevant flight information
			source = f"{flight['countryFrom']['name']}/{flight['cityFrom'] }/{flight['flyFrom']}"
			dest = f"{flight['countryTo']['name']}/{flight['cityTo']}/{flight['flyTo']}"
			price = int(flight['price'])

			str_airlines = ','.join([airlines.get_airline_name(route['airline']) for route in flight['route']])

			# calculate discount price per airline
			discount_price = airlines.calculate_discount_price(str_airlines, price)

			# datetime files 
			source_departure = datetime.strptime(flight['route'][0]['local_departure'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			dest_arrival = datetime.strptime(flight['route'][0]['local_arrival'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			dest_departure = datetime.strptime(flight['route'][1]['local_departure'], r"%Y-%m-%dT%H:%M:%S.%fZ")
			source_arrival = datetime.strptime(flight['route'][1]['local_arrival'], r"%Y-%m-%dT%H:%M:%S.%fZ")

			link_to = link_from = ""

			if str_airlines.split(',')[0] == str_airlines.split(',')[1]:
				# if the departure and arrival airline is same
				if str_airlines.split(',')[0].lower() in airlines.airlines_dict.keys():
					link_to = link_from = airlines.airlines_dict[str_airlines.split(',')[0].lower()](flight['flyFrom'], flight['flyTo'], source_departure, dest_departure)

			else:
				# for diffrent departure and arrival airplane 
				if str_airlines.split(',')[0].lower() in airlines.airlines_dict.keys():
					link_to = airlines.airlines_dict[str_airlines.split(',')[0].lower()](flight['flyFrom'], flight['flyTo'], source_departure, dest_departure, isround=False)

				if str_airlines.split(',')[1].lower() in airlines.airlines_dict.keys():
					link_from = airlines.airlines_dict[str_airlines.split(',')[1].lower()](flight['flyFrom'], flight['flyTo'], source_departure, dest_departure, isround=False)
				

			# caclulate how many days off the work are needed
			days_off = helpers.calculate_days_off(source_departure, source_arrival)

			# insert the flight into the database 
			db_flight = db.Flights(fly_from = source, fly_to = dest, price = price, discount_price = discount_price, \
				nights = int(flight['nightsInDest']), airlines = str_airlines, departure_to =  source_departure, \
				days_off = days_off,  arrival_to = dest_arrival, departure_from = dest_departure, \
				arrival_from = source_arrival, date_of_scan = SCAN_DATE, month = source_departure.month, \
				link_to = link_to, link_from = link_from, weekend_id = weekend_id)

			db_flight.save()

def generate_and_send_telegram_report(telegram_chat_id, dont_send=False, query_function=db.prepare_flights_per_city, **query_params):	

	# if required to run without sending report to telegram
	if dont_send:
		return

	cheapest_flights_query = db.prepare_flights_per_city()
	helpers.dump_csv(cheapest_flights_query, "/tmp/reports/cheapest.csv")

	# Total cheapest flights from the last scan 
	message = ""
	message += "<b>\N{airplane} Cheapest Flights - \N{airplane}</b>\n"
	message += bot.generate_message(cheapest_flights_query)

	bot.send_message_to_chat(message, chat_id = telegram_chat_id)
	bot.send_file_to_chat("/tmp/reports/cheapest.csv", "", chat_id = telegram_chat_id)

	# Cheap flights by Months
	current_month = datetime.now().month
	for i in range(NUM_OF_MONTHS):

		# rotate year 
		if current_month > 12:
			current_month -= 12

		# query the cheapest flights by month
		if "where" in query_params:
			where_backup = query_params["where"] 
			query_params["where"] = query_params["where"] & (db.Flights.month  == current_month)
			month_query = query_function(**query_params)
			query_params["where"] = where_backup
		else:
			month_query = query_function(where=db.Flights.month == current_month, **query_params)

		if len(month_query) == 0:
			current_month += 1
			continue

		# dump the query output to the reports folder
		helpers.dump_csv(month_query, f"/tmp/reports/{datetime.strptime(str(current_month), '%m').strftime('%B')}.csv")

		# generate bot message per month
		message = ""
		message += f"<b>\N{airplane} Cheapest Flights <i>({datetime.strptime(str(current_month), '%m').strftime('%B')})</i> - \N{airplane}</b>\n"
		message += bot.generate_message(month_query)

		# send the message and the query
		bot.send_message_to_chat(message, chat_id = telegram_chat_id)
		bot.send_file_to_chat(f"/tmp/reports/{datetime.strptime(str(current_month), '%m').strftime('%B')}.csv", "", chat_id = telegram_chat_id) 

		# continue to the next month
		current_month += 1

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument(r'--local', dest='local', action='store_true', help = 'run a local instance (not in AWS)')
	parser.add_argument(r'--dont-send', dest='dont_send', action='store_true', help = 'don\'t send report to telegram')
	parser.add_argument(r'-from', dest='from_date', help = 'scan start date (DD-MM-YY)')
	parser.add_argument(r'-to', dest='to_date', help = 'scan end date (DD-MM-YY)')
	parser.add_argument(r'-price', dest='price', help = 'max ticket price (nis)', default=500)

	args = parser.parse_args()

	return args

def lambda_handler(event, context):
	global SCAN_DATE

	args = parse_args()

	if not args.local:
		download_from_bucket("flights.db", '/tmp/flight.db')

	load_config("testing_config.json.private")
	#load_config()

	try:
		os.mkdir(r'/tmp/reports')
	except Exception as e:
		logging.error(e)

	SCAN_DATE = datetime.now()

	date_from = datetime.now()
	date_to = date_from + timedelta(days= NUM_OF_MONTHS * 30)
		
	if args.from_date and args.to_date:
		date_from = datetime.strptime(args.from_date, "%d-%m-%y")
		date_to = datetime.strptime(args.to_date, "%d-%m-%y")

	# search for special destinations
	scan_all_flights(date_from, date_to, fly_to = ','.join(SPECIAL_DESTINATION), price_to=args.price)
	# generate telegram report
	generate_and_send_telegram_report(telegram_chat_id = bot.CHAT_ID, dont_send = args.dont_send)

	# update the scan date for a new scan - TODO: scan_id
	SCAN_DATE = datetime.now()
	
	# Generate flights just to Hungary (for Budapest)
	scan_all_flights(date_from, date_to, fly_to = 'HU', price_to=args.price)
	
	# Get only wizzair flights
	generate_and_send_telegram_report(telegram_chat_id = SPECIAL_CHATS["HU"], query_function=db.prepare_cheapest_flights_month,\
	 where=db.Flights.airlines == "Wizz Air,Wizz Air", limit = 6, dont_send = args.dont_send)

	# update the scan date for a new scan - TODO: scan_id
	SCAN_DATE = datetime.now()

	# Generate flights just to Hungary (for Budapest)
	scan_all_flights(date_from, date_to, fly_to = 'CZ', price_to=2500)
	
	# Get only wizzair flights
	generate_and_send_telegram_report(telegram_chat_id = SPECIAL_CHATS["CZ"], query_function=db.prepare_cheapest_flights_month,
						limit = 6, dont_send = args.dont_send)


	if not args.local:
		upload_to_bucket(r'/tmp/flights.db', 'flights.db')

	return{
		'statusCode': 200,
		'body': json.dumps('Success')
	}

if __name__ == '__main__':
	lambda_handler(None, None)