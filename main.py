import argparse
import os
import config
import helpers
import tempfile
import logging
import database as db
import telegram.interactive_bot as interactive_bot
from engine import kiwi
from telegram import bot
from datetime import datetime, timedelta


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        r"--print",
        dest="print",
        action="store_true",
        help="print output to the terminal (not in AWS)",
    )
    parser.add_argument(
        r"--publish",
        dest="publish",
        action="store_true",
        help="publish report to telegram",
    )
    parser.add_argument(
        r"--dest",
        dest="dest",
        help="destination, can be 2 letter countries,"
        ' or 3 letter airports. seperated with ","',
    )
    parser.add_argument(
        r"--from-date", dest="from_date", help="scan start date (DD-MM-YY)"
    )
    parser.add_argument(r"--to-date", dest="to_date", help="scan end date (DD-MM-YY)")
    parser.add_argument(
        r"--price", dest="price", help="max ticket price (nis)", default=500
    )
    parser.add_argument(r"--airline", dest="airline", help="airline name", default=None)
    parser.add_argument(
        r"--chat-id", dest="chat_id", help="telegram chat id to send the result to"
    )
    parser.add_argument(r"--bot", action="store_true")
    parser.add_argument(r"--config_from_file", help="load config from provided file", default="")
    parser.add_argument(r"--aws_config", help="load config from aws s3", default=False, action="store_true")
    parser.add_argument(r"--aws_test_config", help="use config_test.json from s3", default=False, action="store_true")

    args = parser.parse_args()

    return args


def create_env():
    try:
        os.mkdir(os.path.join(config.tmp_folder, "reports"))
    except Exception as e:
        logging.error(e)


def handle_destination(
    fly_to, date_from, date_to, max_price, chat_id, single_dest=False, details=None
):
    scan_timestamp = int(datetime.timestamp(datetime.now()))
    kiwi.generate_weekend_flights(
        date_from,
        date_to,
        fly_to=fly_to,
        price_to=max_price,
        scan_timestamp=scan_timestamp,
        details=details
    )
    kiwi.generate_holidays_flights(
        date_from,
        date_to,
        fly_to=fly_to,
        price_to=max_price,
        scan_timestamp=scan_timestamp,
    )

    if single_dest:
        report = bot.publish_default_report(
            chat_id,
            date_from,
            date_to,
            scan_timestamp,
            query_function=db.prepare_single_destination_flights,
        )
    else:
        report = bot.publish_default_report(chat_id, date_from, date_to, scan_timestamp)

    if config.print:
        print(report)


def main():
    args = parse_args()

    # load config from env variables
    config.init_config()
    if path := args.config_from_file:
        config.load_config_from_file(path)
    if args.aws_config:
        with tempfile.NamedTemporaryFile(mode="wb") as t:
            if args.aws_test_config:
                config_content = helpers.download_config_from_s3(test_config=True)
            else:
                config_content = helpers.download_config_from_s3()
            t.write(config_content)
            t.flush()
            config.load_config_from_file(t.file.name)

    config.publish = args.publish
    config.print = args.print
    create_env()

    if args.bot:
        interactive_bot.run()
        return

    if args.from_date and args.to_date:
        date_from = datetime.strptime(args.from_date, "%d-%m-%y")
        date_to = datetime.strptime(args.to_date, "%d-%m-%y")
    else:
        date_from = datetime.now()
        date_to = date_from + timedelta(days=config.MONTHS_TO_SCAN * 30)

    if args.dest:
        fly_to = args.dest.upper()
        chat_id = (
            args.chat_id
            if args.chat_id
            else config.TELEGRAM_BOTS["default"]["chats"]["all"][0]
        )
        max_price = (
            int(args.price)
            if args.price
            else config.TELEGRAM_BOTS["default"]["chats"]["all"][2]
        )

        handle_destination(
            fly_to, date_from, date_to, max_price, chat_id, single_dest=True
        )
    else:
        # iterate over the default configuration
        for chat_name, details in config.TELEGRAM_BOTS["default"]["chats"].items():
            chat_id, destinations, max_price, _, _, _, _ = details
            max_price = max_price if max_price > args.price else args.price
            fly_to = (
                ",".join(config.SPECIAL_DESTINATIONS)
                if destinations == "all"
                else ",".join(destinations)
            )

            handle_destination(
                fly_to,
                date_from,
                date_to,
                max_price,
                chat_id,
                single_dest=(chat_name != "all"),
                details=details
            )


if __name__ == "__main__":
    main()
