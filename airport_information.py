import requests
import logging
from seleniumwire import webdriver
from time import sleep

IAA_HEADERS = None


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


'''

import datetime
from airport_information import * 

get_flight_information_tlv('w62326', 'budapest', datetime.datetime(2023,6,15))

'''


def get_flight_information_tlv(flight_number, destination_city, departure_date):
    global IAA_HEADERS

    if not IAA_HEADERS:
        IAA_HEADERS = get_iaa_headers()

    data = {
        'g-recaptcha-response': '',
        'FlightType': 'Outgoing',
        'AirportId': 'LLBG',
        'UICulture': 'he-IL',
        'City': destination_city.upper(),
        'Country': '',
        'AirlineCompany': '',
        'FromDate': departure_date.strftime("%d/%m/%Y").replace('/0', '/'),
        'ToDate': departure_date.strftime("%d/%m/%Y").replace('/0', '/'),
        'ufprt': '',
    }

    error_counter = 0
    while error_counter <= 10:
        r = requests.post('https://www.iaa.gov.il/umbraco/surface/FlightBoardSurface/Search', data=data,
                          headers=IAA_HEADERS)
        print(r.text)
        try:
            r.json()
            if len(r.json()['Flights']) == 0:
                error_counter += 1
                continue
        except:
            IAA_HEADERS = get_iaa_headers()

            error_counter += 1
            continue

        for flight in r.json()['Flights']:
            if flight_number.lower() == flight['Flight'].replace(' ', '').lower():
                return flight
        break

    return None
