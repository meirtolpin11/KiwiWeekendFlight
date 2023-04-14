import argparse
import os
import config
import logging
from engine import kiwi
import database as db
from telegram import bot
from datetime import datetime, timedelta


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(r'--print', dest='print', action='store_true', help='print output to the terminal (not in AWS)')
    parser.add_argument(r'--publish', dest='publish', action='store_true', help='publish report to telegram')
    parser.add_argument(r'-from', dest='from_date', help='scan start date (DD-MM-YY)')
    parser.add_argument(r'-to', dest='to_date', help='scan end date (DD-MM-YY)')
    parser.add_argument(r'-price', dest='price', help='max ticket price (nis)', default=500)
    parser.add_argument(r'-airline', dest='airline', help='airline name', default=None)

    args = parser.parse_args()

    return args


def create_env():
    try:
        os.mkdir(os.path.join(config.tmp_folder, "reports"))
    except Exception as e:
        logging.error(e)


def main():
    args = parse_args()
    config.init_config()
    create_env()

    if args.from_date and args.to_date:
        date_from = datetime.strptime(args.from_date, "%d-%m-%y")
        date_to = datetime.strptime(args.to_date, "%d-%m-%y")
    else:
        date_from = datetime.now()
        date_to = date_from + timedelta(days=config.MONTHS_TO_SCAN * 30)

    for chat_name, details in config.TELEGRAM_BOTS['default']['chats'].items():
        chat_id, max_price = details
        max_price = max_price if max_price > args.price else args.price
        fly_to = ','.join(config.SPECIAL_DESTINATIONS) if chat_name == 'all' else chat_name.upper()
        scan_timestamp = int(datetime.timestamp(datetime.now()))
        kiwi.generate_weekend_flights(date_from, date_to, fly_to=fly_to, price_to=max_price, scan_timestamp=scan_timestamp)
        kiwi.generate_holidays_flights(date_from, date_to, fly_to=fly_to, price_to=max_price, scan_timestamp=scan_timestamp)
        config.publish = args.publish

        if chat_name != 'all':
            report = bot.publish_default_report(chat_id, scan_timestamp, query_function=db.prepare_single_destination_flights)
        else:
            report = bot.publish_default_report(chat_id, scan_timestamp)

        if args.print:
            print(report)


if __name__ == '__main__':
    main()
