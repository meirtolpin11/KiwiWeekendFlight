import flights_database as db
import requests
import json
import helpers

AIRLINES_DATA = json.loads(open("airlines.json").read())
CURRENCY_API_TOKEN = None

def calculate_discount_price(str_airlines, price):
	global CURRENCY_API_TOKEN

	airlines = list(set(str_airlines.split(',')))
	
	# diffrent airlines discount price is not supported for now
	if len(airlines) != 1:
		return price

	members_discount = helpers.convert_currency_api(40, "EUR", "ILS")
	if airlines[0].lower() == 'wizz air' and price >= members_discount:
		# Ticket price should be more then 19.99 EUR in every direction
		return price - members_discount

	return price

def get_airline_name(iata_code):

	try: 
		return AIRLINES_DATA[iata_code]["name"]
	except Exception as e:
		print(e)
		return iata_code

def generate_airline_link(flight):
	message = ""
	url_round = None

	if flight.airlines.split(',')[0] == flight.airlines.split(',')[1]:

		if flight.link_to == flight.link_from == "":
			message += f"\t\N{airplane} {flight.airlines.split(',')[0]} \N{airplane}\n"
		else:
			message += f"\t\N{airplane} <a href='{flight.link_to}'>{flight.airlines.split(',')[0]}</a> \N{airplane}\n"

	else:
	
		if flight.link_to != "":
			message += f"\t\N{airplane} <a href='{flight.link_to}'>{flight.airlines.split(',')[0]}</a>, "
		else:
			message += f"\t\N{airplane} {flight.airlines.split(',')[0]}, "

		# direction from
		if flight.link_from != "":
			message += f"<a href='{flight.link_from}'>{flight.airlines.split(',')[1]}</a> \N{airplane}\n"
		else:
			message += f"{flight.airlines.split(',')[1]} \N{airplane}\n"

	return message

def get_ryanair_link(fly_from, fly_to, date_to, date_from, isround=True):
	ryanair_round_url = f'https://www.ryanair.com/us/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut={date_to.strftime("%Y-%m-%d")}&dateIn={date_from.strftime("%Y-%m-%d")}&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata={fly_from}&destinationIata={fly_to}&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate={date_to.strftime("%Y-%m-%d")}&tpEndDate={date_from.strftime("%Y-%m-%d")}&tpDiscount=0&tpPromoCode=&tpOriginIata={fly_from}&tpDestinationIata={fly_to}'

	ryanair_oneway_url = f'https://www.ryanair.com/us/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut={date_to.strftime("%Y-%m-%d")}&dateIn=&isConnectedFlight=false&discount=0&isReturn=false&promoCode=&originIata={fly_from}&destinationIata={fly_to}&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate={date_to.strftime("%Y-%m-%d")}&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata={fly_from}&tpDestinationIata={fly_to}'	

	if isround:
		return ryanair_round_url

	return ryanair_oneway_url

def get_wizzair_link(fly_from, fly_to, date_to, date_from, isround=True):
	wizz_round_url = f'https://wizzair.com/#/booking/select-flight/{fly_from}/{fly_to}/{date_to.strftime("%Y-%m-%d")}/{date_from.strftime("%Y-%m-%d")}/1/0/0/null'

	wizz_oneway_url = f'https://wizzair.com/#/booking/select-flight/{fly_from}/{fly_to}/{date_to.strftime("%Y-%m-%d")}/null/1/0/0/null'

	if isround:
		return wizz_round_url

	return wizz_oneway_url

airlines_dict = {
	'ryanair': get_ryanair_link,
	'wizz air': get_wizzair_link
}
