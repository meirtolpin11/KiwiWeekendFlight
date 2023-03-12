import requests
import datetime


def get_flight_information_tlv(flight_number, destination_city, airline_code, departure_date):
	r = requests.get('https://www.iaa.gov.il/airports/ben-gurion/flight-board/?flightType=arrivals')
	print(r.text)
	data = {
	    'g-recaptcha-response': '',
	    'FlightType': 'Outgoing',
	    'AirportId': 'LLBG',
	    'UICulture': 'he-IL',
	    'City': destination_city.upper(),
	    'Country': '',
	    'AirlineCompany': airline_code.upper(),
	    'FromDate': departure_date.strftime("%d/%m/%Y").replace('/0', '/'),
	    'ToDate': departure_date.strftime("%d/%m/%Y").replace('/0', '/'),
	    'ufprt': '',
	}
	print(data)
	r = requests.post('https://www.iaa.gov.il/umbraco/surface/FlightBoardSurface/Search', data = data)
	print(r.text)
	for flight in r.json()['Flights']:
		if flight_number.lower() == flight['Flight'].replace(' ','').lower():
			return flight

	return None



departure_date = datetime.datetime(year=2023, month=6, day=15)
print(get_flight_information_tlv("w62326", "budapest", "w6", departure_date))