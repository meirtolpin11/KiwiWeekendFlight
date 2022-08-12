


def get_ryanair_link(fly_from, fly_to, date_to, date_from, isround=True):
	ryanair_round_url = f'https://www.ryanair.com/us/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut={date_to.strftime("%Y-%m-%d")}&dateIn={date_from.strftime("%Y-%m-%d")}&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata={fly_from}&destinationIata={fly_to}&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate={date_to.strftime("%Y-%m-%d")}&tpEndDate={date_from.strftime("%Y-%m-%d")}&tpDiscount=0&tpPromoCode=&tpOriginIata={fly_from}&tpDestinationIata={fly_to}'

	ryanair_oneway_url = f'https://www.ryanair.com/us/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut={date_to.strftime("%Y-%m-%d")}&dateIn=&isConnectedFlight=false&discount=0&isReturn=false&promoCode=&originIata={fly_from}&destinationIata={fly_to}&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate={date_to.strftime("%Y-%m-%d")}&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata={fly_from}&tpDestinationIata={fly_to}'	

	if isround:
		return ryanair_round_url

	return ryanair_oneway_url

def get_wizzair_link(fly_from, fly_to, date_to, date_from, isround=True):
	wizz_round_url = f'https://wizzair.com/#/booking/select-flight/{fly_from}/{fly_to}/{date_to.strftime("%Y-%m-%d")}/{date_from.strftime("%Y-%m-%d")}/1/0/0/null'

	wizz_oneway_url = f'https://wizzair.com/#/booking/select-flight/{fly_from}/{fly_to}/{date_to.strftime("%Y-%m-%d")}/null/1/0/0/null'

	if isround:
		return wizz_round_url

	return wizz_oneway_url


airlines_dict = {
	'ryanair': get_ryanair_link,
	'wizz air': get_wizzair_link
}