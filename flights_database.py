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

db.create_tables([Flights, IATA])