import config
import helpers


class WizzAir():
    @staticmethod
    def calculate_discount_price(price, is_round=True):
        members_discount = helpers.convert_currency_api(20 if is_round else 10, "EUR", "ILS")
        if price >= helpers.convert_currency_api(40 if is_round else 20, "EUR", "ILS"):
            # Ticket price should be more then 19.99 EUR in every direction
            return price - members_discount
        return round(price)

    @staticmethod
    def generate_link(fly_from, fly_to, date_to, date_from=None, is_round=True):
        if is_round:
            wizz_round_url = f'https://wizzair.com/en-gb#/booking/select-flight/{fly_from}/{fly_to}/{date_to.strftime("%Y-%m-%d")}/{date_from.strftime("%Y-%m-%d")}/1/0/0/null'
            return wizz_round_url

        wizz_oneway_url = f'https://wizzair.com/en-gb#/booking/select-flight/{fly_from}/{fly_to}/{date_to.strftime("%Y-%m-%d")}/null/1/0/0/null'
        return wizz_oneway_url
