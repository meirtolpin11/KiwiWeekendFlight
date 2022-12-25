import flights_database as db
import requests
import json


AIRLINES_DATA = json.loads(open("airlines.json").read())

def get_airline_name(iata_code):

	try: 
		# resp = db.IATA.select(db.IATA.airline).where(db.IATA.code == iata_code).execute() 
		# if len(resp) > 0:
		# 	return resp[0].airline

		# url = "https://iata-and-icao-codes.p.rapidapi.com/airline"

		# querystring = {"iata_code":iata_code}

		# headers = {
		# 	"X-RapidAPI-Key": "6c7d471d8bmsh3830faf947c0858p12e8ddjsn6ec3222ee5be",
		# 	"X-RapidAPI-Host": "iata-and-icao-codes.p.rapidapi.com"
		# }

		# response = requests.request("GET", url, headers=headers, params=querystring)

		# print(response.json())

		# db.IATA(airline=response.json()[0]["name"], code=iata_code).save()
		# return response.json()[0]["name"]
		
		return AIRLINES_DATA[iata_code]["name"]
	except Exception as e:
		print(e.message)
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
