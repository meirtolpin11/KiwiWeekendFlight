import config
import telebot
from engine import kiwi
from datetime import datetime


class IntercativeBot:
    def __init__(self):
        config.init_config()
        self.bot_token = config.TELEGRAM_BOTS['default']['token']
        self.chats = {}

    def create_telebot(self):
        bot = telebot.TeleBot(self.bot_token)

        @bot.message_handler(commands=['help', 'start'])
        def send_welcome(message):
            self.chats[message.chat.id] = {}
            msg = bot.send_message(message.chat.id, text="Where are you flying (2 letter country code) ?")
            bot.register_next_step_handler(msg, parse_country)

        def parse_country(message):
            self.chats[message.chat.id]['country'] = message.text
            msg = bot.send_message(message.chat.id, text="Please enter the date to start the scanning from: dd-mm-yyyy")
            bot.register_next_step_handler(msg, parse_from_date)

        def parse_from_date(message):
            self.chats[message.chat.id]['from_date'] = datetime.strptime(message.text, '%d-%m-%Y')
            msg = bot.send_message(message.chat.id, text="Please enter the date to start the scanning to: dd-mm-yyyy")
            bot.register_next_step_handler(msg, parse_to_date)

        def parse_to_date(message):
            self.chats[message.chat.id]['to_date'] = datetime.strptime(message.text, '%d-%m-%Y')
            msg = bot.send_message(message.chat.id, text="Please enter the min number of nights in destination - ")
            bot.register_next_step_handler(msg, parse_min_nights)

        def parse_min_nights(message):
            self.chats[message.chat.id]['min_nights'] = message.text
            msg = bot.send_message(message.chat.id, text="Please enter the max number of nights in destination - ")
            bot.register_next_step_handler(msg, parse_max_nights)

        def parse_max_nights(message):
            self.chats[message.chat.id]['max_nights'] = message.text
            msg = bot.send_message(message.chat.id, text="Please enter the max price to search for - ")
            bot.register_next_step_handler(msg, parse_max_price)

        def parse_max_price(message):
            self.chats[message.chat.id]['price_to'] = message.text
            flight_details = self.chats[message.chat.id]

            scan_timestamp = int(datetime.timestamp(datetime.now()))
            kiwi.generate_flights(flight_details['from_date'].strftime("%Y-%m-%d"), flight_details['to_date'].strftime("%Y-%m-%d"),
                                  fly_to=flight_details['country'], price_to=flight_details['price_to'],
                                  scan_timestamp=scan_timestamp, nights_in_dst_from=flight_details['min_nights'],
                                  nights_in_dst_to=flight_details['max_nights'])

        return bot


a = IntercativeBot()
_bot = a.create_telebot()
_bot.infinity_polling()
