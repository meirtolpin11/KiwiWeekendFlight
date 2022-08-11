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

	# query the cheapest flights per city
	flights = Flights.select(Flights.fly_to, fn.Min(Flights.price).alias("price"), Flights.nights,\
	 Flights.days_off, Flights.departure_to,\
	 Flights.arrival_from).group_by(Flights.fly_to).order_by(Flights.price)
	
	return flights

def prepare_query_cheapest_flights_per_month(month_number):
	
	flights = Flights.select(Flights.fly_to, fn.Min(Flights.price).alias("price"), Flights.nights,\
	 Flights.days_off, Flights.departure_to,\
	 Flights.arrival_from).where(Flights.month == month_number).group_by(Flights.fly_to).order_by(Flights.price)

	return flights

def preprae_query_price_drop():

	subquery1 = Flights.select(Flights.fly_from, Flights.fly_to, Flights.departure_to, Flights.arrival_from, \
				fn.Min(Flights.price).alias("min_price"), \
				fn.Max(Flights.price).alias("max_price")).group_by(Flights.fly_from, Flights.fly_to, \
				Flights.departure_to, Flights.arrival_from)

	subquery2 = Flights.select(subquery1.c.fly_to, subquery1.c.fly_from, \
		subquery1.c.departure_to, subquery1.c.arrival_from, \
		subquery1.c.min_price).from_(subquery1).where(subquery1.c.min_price != subquery1.c.max_price)

	subquery3 = Flights.select(fn.Max(Flights.date_of_scan).alias('date'))


	subquery4 = Flights.select(Flights.fly_from, Flights.fly_to, Flights.departure_to, Flights.arrival_from, Flights.price, \
		Flights.date_of_scan).join(subquery2, on=( (subquery2.c.fly_to == Flights.fly_to) & \
		(subquery2.c.fly_from == Flights.fly_from) & \
		(subquery2.c.min_price == Flights.price))).where(Flights.date_of_scan == subquery3[0].date)

	return subquery4

db.create_tables([Flights, IATA])