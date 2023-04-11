class Ryanair:

    @staticmethod
    def generate_link(fly_from, fly_to, date_to, date_from=None, is_round=True):
        if is_round:
            ryanair_round_url = f'https://www.ryanair.com/us/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=' \
                                f'{date_to.strftime("%Y-%m-%d")}&dateIn={date_from.strftime("%Y-%m-%d")}&' \
                                f'isConnectedFlight=false&isReturn' \
                                f'=true&discount=0&promoCode=&originIata={fly_from}&destinationIata={fly_to}' \
                                f'&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0' \
                                f'&tpStartDate={date_to.strftime("%Y-%m-%d")}&' \
                                f'tpEndDate={date_from.strftime("%Y-%m-%d")}' \
                                f'&tpDiscount=0&tpPromoCode=&tpOriginIata={fly_from}&tpDestinationIata={fly_to}'
            return ryanair_round_url

        ryanair_oneway_url = f'https://www.ryanair.com/us/en/trip/flights/select?adults=1&teens=0&children=0&' \
                             f'infants=0&dateOut={date_to.strftime("%Y-%m-%d")}&dateIn=&' \
                             f'isConnectedFlight=false&discount=0&isReturn=false&promoCode=&' \
                             f'originIata={fly_from}&destinationIata={fly_to}&tpAdults=1&' \
                             f'tpTeens=0&tpChildren=0&tpInfants=0&' \
                             f'tpStartDate={date_to.strftime("%Y-%m-%d")}&tpEndDate=&' \
                             f'tpDiscount=0&tpPromoCode=&tpOriginIata={fly_from}&tpDestinationIata={fly_to}'
        return ryanair_oneway_url
