# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)
class ExchangeRatePe:
    def __init__(self):
        pass

    def compute_exchange_rate(self, url, type):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        if soup:
            date_consult = soup.find('input', id="ctl00_cphContent_rdpDate_dateInput")
            date_exchange = date_consult.get('value')
            table = soup.find('table', class_="rgMasterTable")
            table_rows = table.find_all('tr')
            count = 0
            exchanges = []
            for tr in table_rows:
                count = count + 1
                if count > 1:
                    td = tr.find_all('td')
                    list = [i.text.strip() for i in td]
                    exchanges.append({'currency': list[0], 'purchase': list[1], 'sale': list[2]})
            date_exchange = datetime.strptime(date_exchange, "%d/%m/%Y")
            exchange_rate = float(exchanges[0][type])
            return True, date_exchange, exchange_rate
        return False, False, False

    def compute_exchange_rate_sunat(self, url, type):
        response = requests.get(url=url, headers={"content-type": "text"})
        _logger.info("response")
        _logger.info(response)
        if response.status_code == 200:
            res_json = response.text.split("|")
            _logger.info("res_json")
            _logger.info(res_json)
            position_rate = 2 if type == 'sale' else 1
            try:
                date_exchange = datetime.strptime(res_json[0], "%d/%m/%Y")
            except:
                return False, False, False
            exchange_rate = float(res_json[position_rate])
            return True, date_exchange, exchange_rate
        return False, False, False


def exchange_rate_sale(url, from_type):
    if from_type == "sbs":
        return ExchangeRatePe.compute_exchange_rate(self=None, url=url, type="sale")
    else:
        return ExchangeRatePe.compute_exchange_rate_sunat(self=None, url=url, type="sale")


def exchange_rate_purchase(url, from_type):
    if from_type == "sbs":
        return ExchangeRatePe.compute_exchange_rate(self=None, url=url, type="purchase")
    else:
        return ExchangeRatePe.compute_exchange_rate_sunat(self=None, url=url, type="purchase")
