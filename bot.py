import requests


TOKEN = ""
CHAT_ID = ""

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

