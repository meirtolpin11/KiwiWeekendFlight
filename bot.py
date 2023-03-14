import requests
import airlines
import airport_information

TOKEN = ""
CHAT_ID = ""

def generate_message(query):
	message = ""
	for flight in query:
		message += f"\n<b>{flight.fly_to.split('/')[1]}</b> <i>({flight.fly_to.split('/')[0]})</i>\n "
		 
		if flight.departure_to.month == flight.arrival_from.month:
			message += f"\N{calendar} \t<b>{flight.departure_to.strftime('%d/%m %H:%M ')}-{flight.arrival_from.strftime(' %d/%m %H:%M')}</b> "
		else:
			message += f"\N{calendar} \t<b>{flight.departure_to.strftime('%d/%m %H:%M ')}-{flight.arrival_from.strftime(' %d/%m %H:%M')}</b> "

		message += f"<i>({flight.departure_to.strftime('%a')} - {flight.arrival_from.strftime('%a')})</i> \N{calendar}\n "

		check_confirmed = airport_information.get_flight_information_tlv(flight.flight_numbers.split(',')[0], flight.fly_to.split('/')[1], flight.departure_to)
		if check_confirmed:
			message += f"\N{white heavy check mark} Flight - {flight.flight_numbers.split(',')[0]} confirmed \N{white heavy check mark}\n"
		else:
			message += f"\N{cross mark} Flight - MAYBE {flight.flight_numbers.split(',')[0]} not confirmed \N{cross mark}\n"


		if flight.price == flight.discount_price:
			message += f"\t\N{money bag} <b>{flight.price} nis</b> \N{money bag}\n"
		else:
			message += f"\t\N{money bag} <b>{flight.price} nis, <i>Members: {flight.discount_price} nis</i></b> \N{money bag}\n"

		message += airlines.generate_airline_link(flight)

	return message

def send_message_to_chat(message_to_send, chat_id = CHAT_ID):
	global TOKEN

	data = {"chat_id": chat_id, "text": message_to_send, "parse_mode": "HTML"}
	url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
	
	return requests.post(url, data=data).json()

def send_file_to_chat(filename, caption, chat_id = CHAT_ID):
	global TOKEN

	url = f'https://api.telegram.org/bot{TOKEN}/sendDocument'

	data = {"chat_id": chat_id, "caption": caption}
	file_handle = open(filename, 'rb')

	resp = requests.post(url, data = data, files={"document": file_handle})

	return resp.json()

 
