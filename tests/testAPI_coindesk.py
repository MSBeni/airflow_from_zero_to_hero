import requests

from datetime import datetime

def extract_from_api():
    data = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')

    js_data = data.json()
    price_date = js_data['time']['updated']  # May 15, 2022 16:29:00 UTC
    newDate = datetime.strptime(price_date, '%B %d, %Y %H:%M:%S %Z')

    print(newDate)

extract_from_api()
