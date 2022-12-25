from peewee import *

db = SqliteDatabase('flights.db')

class Flights(Model):
	fly_from = CharField()
	fly_to = CharField()
	nights = IntegerField()
	days_off = IntegerField()
	price = IntegerField()
	airlines = CharField()
	departure_to = DateTimeField()
	arrival_to = DateTimeField()
	departure_from = DateTimeField()
	arrival_from = DateTimeField()
	link_to = CharField()
	link_from = CharField()
	month = IntegerField()
	date_of_scan = DateTimeField()


	class Meta:
		database = db

class IATA(Model):
	code = CharField()
	airline = CharField()

	class Meta:
		database = db

def prepare_query_cheapest_flights_per_city():

	last_scan_data = Flights.select(fn.Max(Flights.date_of_scan).alias('date_of_scan')).execute()

	# query the cheapest flights per city
	flights = Flights.select(Flights.fly_to, fn.Min(Flights.price).alias("price"), Flights.airlines, Flights.nights,\
	 Flights.days_off, Flights.departure_to,\
	 Flights.arrival_to, Flights.departure_from, Flights.arrival_from, \
	 Flights.link_to, Flights.link_from).where(Flights.date_of_scan == last_scan_data[0].date_of_scan).group_by(Flights.fly_to).order_by(Flights.price)
	
	return flights

def prepare_query_cheapest_flights_per_month(month_number):

	last_scan_data = Flights.select(fn.Max(Flights.date_of_scan).alias('date_of_scan')).execute()
	
	flights = Flights.select(Flights.fly_to, fn.Min(Flights.price).alias("price"), Flights.airlines, Flights.nights,\
	 Flights.days_off, Flights.departure_to,\
	 Flights.arrival_to, Flights.departure_from, Flights.arrival_from, \
	 Flights.link_to, Flights.link_from).where((Flights.month == month_number) & (Flights.date_of_scan == last_scan_data[0].date_of_scan)).group_by(Flights.fly_to).order_by(Flights.price)

	return flights

def prepare_query_price_drop():

	subquery1 = Flights.select(Flights.fly_from, Flights.fly_to, Flights.departure_to, Flights.arrival_from, \
				fn.Min(Flights.price).alias("min_price"), \
				fn.Max(Flights.price).alias("max_price")).group_by(Flights.fly_from, Flights.fly_to, \
				Flights.departure_to, Flights.arrival_from)

	subquery2 = Flights.select(subquery1.c.fly_to, subquery1.c.fly_from, \
		subquery1.c.departure_to, subquery1.c.arrival_from, \
		subquery1.c.min_price).from_(subquery1).where(subquery1.c.min_price != subquery1.c.max_price)

	subquery3 = Flights.select(fn.Max(Flights.date_of_scan).alias('date'))


	subquery4 = Flights.select(Flights.fly_from, Flights.fly_to, Flights.departure_to, \
		Flights.arrival_to, Flights.departure_from, Flights.arrival_from, Flights.airlines, Flights.price, \
		Flights.date_of_scan, Flights.link_to, Flights.link_from).join(subquery2, on=( (subquery2.c.fly_to == Flights.fly_to) & \
		(subquery2.c.fly_from == Flights.fly_from) & \
		(subquery2.c.min_price == Flights.price))).where(Flights.date_of_scan == subquery3[0].date)

	return subquery4

db.create_tables([Flights, IATA])