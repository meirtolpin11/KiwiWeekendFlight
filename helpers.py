from datetime import timedelta
import csv

def daterange(date1, date2):
	for n in range(int ((date2 - date1).days)+1):
		yield date1 + timedelta(n)

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