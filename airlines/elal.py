# noinspection PyUnboundLocalVariable
class Elal:

    @staticmethod
    def generate_link(fly_from, fly_to, date_to, date_from=None, is_round=True):
        if is_round:
            elal_round_url = f"https://booking.elal.com/booking/flights?SYSTEMID=1&LANG=EN&" \
                                f"agentPCCode=SKY&agentName=skyscanner" \
                                f"&adults=1&children=0&infants=0&cabin=Economy" \
                                f"&origin={fly_from}&destination={fly_to}&" \
                                f"departDay={date_to.day}&departMonth={date_to.month}&departYear={date_to.year}" \
                                f"&journeyType=1&" \
                                f"returnFrom={fly_from}&returnTo={fly_to}&" \
                                f"returnDay={date_from.day}&returnMonth={date_from.month}&returnYear={date_from.year}"
            return elal_round_url

        elal_oneway_url = f"https://booking.elal.com/booking/flights?SYSTEMID=1&LANG=EN&" \
                         f"agentPCCode=SKY&agentName=skyscanner" \
                         f"&adults=1&children=0&infants=0&cabin=Economy" \
                         f"&origin={fly_from}&destination={fly_to}&" \
                         f"departDay={date_to.day}&departMonth={date_to.month}&departYear={date_to.year}" \
                         f"&journeyType=0"
        return elal_oneway_url
