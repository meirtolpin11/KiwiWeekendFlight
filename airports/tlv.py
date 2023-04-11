import requests
import logging
from time import sleep
from seleniumwire import webdriver

IAA_HEADERS = None
CACHE = {}


def get_iaa_headers():
    logging.info(r'getting a cookie for iaa.gov.il')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(r'--headless')
    chrome_options.add_argument(r'--no-sandbox')
    chrome_options.add_argument(r'--single-process')
    chrome_options.add_argument(r'--disable-dev-shm-usage')

    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(r'https://iaa.gov.il')
    sleep(2)
    driver.get(r'https://www.iaa.gov.il/airports/ben-gurion/flight-board/?flightType=arrivals')

    headers = None
    for requests in driver.requests[::-1]:
        if 'iaa.gov.il' in requests.url:
            if 'cookie' in requests.headers:
                if 'visid_incap_' in requests.headers['cookie'] and 'incap_ses_' in requests.headers['cookie']:
                    headers = {}
                    headers['cookie'] = requests.headers['cookie']
                    headers['user-agent'] = requests.headers['user-agent']
                    break

    driver.close()
    driver.quit()
    return headers


def get_flight_confirmation(flight_number, departure_date):
    global IAA_HEADERS
    global CACHE

    if not IAA_HEADERS:
        IAA_HEADERS = get_iaa_headers()

    if departure_date.strftime("%d/%m/%Y").replace('/0', '/') in CACHE:
        for flight in CACHE[departure_date.strftime("%d/%m/%Y").replace('/0', '/')]['Flights']:
            if flight_number.lower() == flight['Flight'].replace(' ', '').lower():
                return flight
        return -1

    data = {
        'g-recaptcha-response': '',
        'FlightType': 'Outgoing',
        'AirportId': 'LLBG',
        'UICulture': 'he-IL',
        'City': '',
        'Country': '',
        'AirlineCompany': '',
        'FromDate': departure_date.strftime("%d/%m/%Y").replace('/0', '/'),
        'ToDate': departure_date.strftime("%d/%m/%Y").replace('/0', '/'),
        'ufprt': '',
    }
    max_error_counter = 2
    error_counter = 0

    # we try up to 10 times to get a valid response
    while error_counter <= max_error_counter:
        r = requests.post('https://www.iaa.gov.il/umbraco/surface/FlightBoardSurface/Search', data=data,
                          headers=IAA_HEADERS)

        # noinspection PyBroadException
        try:
            iaa_flights = r.json()
            if len(iaa_flights['Flights']) == 0:
                IAA_HEADERS = get_iaa_headers()
                sleep(2)
                error_counter += 1

                if error_counter >= max_error_counter:
                    # return status that no flight are returned
                    return -2

                # try to fetch again
                continue
        except Exception as e:
            IAA_HEADERS = get_iaa_headers()
            error_counter += 1
            continue

        CACHE[departure_date.strftime("%d/%m/%Y").replace('/0', '/')] = iaa_flights

        # try to find the valid flight
        for flight in iaa_flights['Flights']:
            if flight_number.lower() == flight['Flight'].replace(' ', '').lower():
                return flight

        return -1

    return -3
