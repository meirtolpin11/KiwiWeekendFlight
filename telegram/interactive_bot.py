import main
import config
import telebot
import database as db
from engine import kiwi
from telegram import bot as kiwi_bot
from datetime import datetime, timedelta, date
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP


class InteractiveBot:
    def __init__(self):
        config.init_config()
        self.bot_token = config.TELEGRAM_BOTS['default']['token']
        self.chats = {}

    def create_telebot(self):
        bot = telebot.TeleBot(self.bot_token)

        @bot.message_handler(commands=['help', 'start'])
        def send_welcome(message):
            self.chats[message.chat.id] = {}
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
            markup.add(
                telebot.types.KeyboardButton('any'),
            )
            msg = bot.send_message(message.chat.id, text="Where are you flying (Country/Airport code) ?",
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, parse_country)

        @bot.message_handler(commands=['rescan'])
        def rescan(message):
            bot.send_message(message.chat.id, "Scanning Again :)")
            scan(message)

        def parse_country(message):
            self.chats[message.chat.id]['country'] = message.text if message.text != "any" else ""
            calendar, step = DetailedTelegramCalendar(min_date=datetime.now().date()).build()
            self.chats[message.chat.id]['next_func'] = parse_date_from
            bot.send_message(message.chat.id, "Scan From: ")
            bot.send_message(message.chat.id, text="Select Year",
                             reply_markup=calendar)

        @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
        def cal(c):
            result, key, step = DetailedTelegramCalendar(min_date=datetime.now().date()).process(c.data)
            if not result and key:
                bot.edit_message_text(f"Select {LSTEP[step]}",
                                      c.message.chat.id,
                                      c.message.message_id,
                                      reply_markup=key)
            elif result:
                self.chats[c.message.chat.id]['next_func'](c.message, result)

        def parse_date_from(message, result):
            self.chats[message.chat.id]['date_from'] = result
            calendar, step = DetailedTelegramCalendar().build()
            self.chats[message.chat.id]['next_func'] = parse_date_to
            bot.send_message(message.chat.id, "Scan To: ")
            bot.send_message(message.chat.id, text="Select Year",
                             reply_markup=calendar)

        def parse_date_to(message, result):
            self.chats[message.chat.id]['date_to'] = result
            msg = bot.send_message(message.chat.id, text="Min number of nights in destination:")
            bot.register_next_step_handler(msg, parse_min_nights)

        def parse_min_nights(message):
            self.chats[message.chat.id]['min_nights'] = message.text
            msg = bot.send_message(message.chat.id, text="Max number of nights in destination:")
            bot.register_next_step_handler(msg, parse_max_nights)

        def parse_max_nights(message):
            self.chats[message.chat.id]['max_nights'] = message.text
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
            markup.add(
                telebot.types.KeyboardButton('yes'),
                telebot.types.KeyboardButton('no')
            )
            msg = bot.send_message(message.chat.id, text="Fly only weekends?", reply_markup=markup)
            bot.register_next_step_handler(msg, parse_only_weekends)

        def parse_only_weekends(message):
            self.chats[message.chat.id]['only_weekends'] = message.text == "yes"
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
            markup.add(
                telebot.types.KeyboardButton("500"),
                telebot.types.KeyboardButton("1000"),
                telebot.types.KeyboardButton("1500"),
                telebot.types.KeyboardButton("2000"),
            )
            msg = bot.send_message(message.chat.id, text="Max price:",
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, parse_max_price)

        def parse_max_price(message):
            self.chats[message.chat.id]['price_to'] = message.text
            scan(message)

        def get_query_values_from_db(chat_id):

            query_values = db.UserQueryDetails.select().where(db.UserQueryDetails.chat_id == chat_id)
            if len(query_values) == 0:
                return None

            query_values = query_values[0]
            return {
                'country': query_values.fly_to,
                'min_nights': query_values.min_nights,
                'max_nights': query_values.max_nights,
                'date_from': query_values.date_from,
                'date_to': query_values.date_to,
                'price_to': query_values.max_price,
                'only_weekends': query_values.only_weekends,
            }

        def scan(message):
            if message.chat.id in self.chats:
                flight_details = self.chats[message.chat.id]
                db.UserQueryDetails.delete().where(db.UserQueryDetails.chat_id == message.chat.id).execute()
                db.UserQueryDetails(
                    fly_from='IL',
                    fly_to=flight_details['country'],
                    min_nights=flight_details['min_nights'],
                    max_nights=flight_details['max_nights'],
                    date_from=flight_details['date_from'],
                    date_to=flight_details['date_to'],
                    max_price=flight_details['price_to'],
                    only_weekends=flight_details['only_weekends'],
                    chat_id=message.chat.id
                ).save()
            else:
                flight_details = get_query_values_from_db(message.chat.id)
                if not flight_details:
                    bot.send_message(message.chat.id, "No config is found, please type /start :)")
                    return

            # scan flights
            scan_timestamp = int(datetime.timestamp(datetime.now()))
            if flight_details['only_weekends']:
                kiwi.generate_weekend_flights(flight_details['date_from'],
                                              flight_details['date_to'],
                                              fly_to=flight_details['country'], price_to=flight_details['price_to'],
                                              scan_timestamp=scan_timestamp,
                                              nights_in_dst_from=flight_details['min_nights'],
                                              nights_in_dst_to=flight_details['max_nights'])
            else:
                kiwi.generate_flights(flight_details['date_from'].strftime("%Y-%m-%d"),
                                      flight_details['date_to'].strftime("%Y-%m-%d"),
                                      fly_to=flight_details['country'], price_to=flight_details['price_to'],
                                      scan_timestamp=scan_timestamp, nights_in_dst_from=flight_details['min_nights'],
                                      nights_in_dst_to=flight_details['max_nights'])

            config.publish = True
            if len(flight_details['country'].split(',')) == 1:
                kiwi_bot.publish_default_report(message.chat.id, scan_timestamp,
                                                query_function=db.prepare_single_destination_flights)
            else:
                kiwi_bot.publish_default_report(message.chat.id, scan_timestamp)

            bot.send_message(message.chat.id, "You can /rescan with current values, or /start again")

        return bot


def run():
    a = InteractiveBot()
    _bot = a.create_telebot()
    _bot.infinity_polling()
