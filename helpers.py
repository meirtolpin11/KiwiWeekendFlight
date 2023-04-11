import csv
import config
import requests
from datetime import datetime, timedelta

CACHED_RATES = {}

def get_weekends(start_dt, end_dt):
	weekend_days = [4,7]
	weekends = []
	pair = ["", ""]

	for dt in daterange(start_dt, end_dt):
		if dt.isoweekday() in weekend_days:
			if dt.isoweekday() == weekend_days[0]:
				pair[0] = dt.strftime("%Y-%m-%d")
			else:
				pair[1] = dt.strftime("%Y-%m-%d")
				weekends.append(pair)
				pair = ["", ""]

	return weekends

# TODO: refactor
def daterange(date1, date2):
	for n in range(int((date2 - date1).days)+1):
		yield date1 + timedelta(n)


def convert_currency_api(amount, from_currency, to_currency):
	if f"{from_currency}:{to_currency}" not in CACHED_RATES.keys():
		url = f"https://open.er-api.com/v6/latest/{from_currency.upper()}"

		response = requests.get(url)
		result = response.json()

		CACHED_RATES[f"{from_currency}:{to_currency}"] = result
	else:
		result = CACHED_RATES[f"{from_currency}:{to_currency}"]

	try:
		return int(int(amount) * result["rates"][to_currency.upper()])
	except Exception as e:
		print(f"Error while fetching currency info {e}")
		# TODO: fix this shit
		if from_currency.lower() == "eur":
			return int(int(amount) * 3.74)
		else:
			return 0

def calculate_days_off(departure, arrival):
	days_off = 0

	if departure.isoweekday() == 4 and departure.hour < 19:
		days_off += 1

	if arrival.isoweekday() == 7 and arrival.hour > 10:
		days_off += 1

	elif arrival.isoweekday() == 1:
		days_off += 1

	return days_off

def dump_csv(query, file_or_name, include_header=True, close_file=True,
			 append=False, csv_writer=None):
	"""
	Create a CSV dump of a query.
	"""

	fh = open(file_or_name, append and 'a' or 'w', encoding='utf-8', newline='')

	writer = csv_writer or csv.writer(
		fh,
		delimiter=',',
		quotechar='"',
		quoting=csv.QUOTE_MINIMAL)

	if include_header:
		writer.writerow([header.name for header in query.selected_columns])

	for row in query.tuples().iterator():
		writer.writerow(row)

	if close_file:
		fh.close()

	return fh