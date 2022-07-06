# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from . import pe_exchange_rate
import datetime
import pytz

_URL_SBS_DEFAULT = "https://www.sbs.gob.pe/app/pp/SISTIP_PORTAL/Paginas/Publicacion/TipoCambioPromedio.aspx"
_URL_SUNAT_DEFAULT = "https://www.sunat.gob.pe/a/txt/tipoCambio.txt"

TYPES = [('purchase', _('Purchase')), ('sale', _('Sale'))]
FROM_TYPES = [('sbs', _('SBS')), ('sunat', _('SUNAT'))]

import logging

_logger = logging.getLogger(__name__)


class Currency(models.Model):
    _inherit = "res.currency"
    _description = "Currency"

    from_type = fields.Selection(FROM_TYPES, string='Origin', default='sunat')

    type = fields.Selection(TYPES, string='Type', default='sale')

    def get_url_service(self, from_url):
        _identity = 'exchange.{from_url}.url'.format(from_url=from_url)
        get_param = self.env['ir.config_parameter'].sudo().get_param
        url = get_param(_identity, _URL_SBS_DEFAULT)
        return url

    def action_exchange_rate_sale(self, company):
        rec = self
        if rec.type == "sale":
            success, date_exchange, exchange_rate = pe_exchange_rate.exchange_rate_sale(
                rec.get_url_service(rec.from_type), rec.from_type)
            _logger.info("success")
            _logger.info(success)
            _logger.info("date_exchange")
            _logger.info(exchange_rate)
            _logger.info("exchange_rate")
            _logger.info(success)
            local_pytz = pytz.timezone(company.partner_id.tz)
            time_created_day = datetime.datetime.now(local_pytz)
            if success:
                if date_exchange.date() == time_created_day.date():
                    currency_rates = rec._pg_get_rates(company, date_exchange)
                    rate_id = currency_rates.get(rec.id, False)
                    if rate_id:
                        rate_currency = self.env["res.currency.rate"].browse(int(rate_id))
                        if rate_currency.name == date_exchange.date():
                            rate_currency.write({
                                "rate_exchange": exchange_rate
                            })
                        else:
                            self.env["res.currency.rate"].create({
                                'currency_id': rec.id,
                                'name': date_exchange.date(),
                                'rate_exchange': exchange_rate,
                                'company_id': company.id
                            })
                    else:
                        self.env["res.currency.rate"].create({
                            'currency_id': rec.id,
                            'name': date_exchange.date(),
                            'rate_exchange': exchange_rate,
                            'company_id': company.id
                        })

    def action_exchange_rate_purchase(self, company):
        for rec in self.search([('active', '=', True), ('name', '=', 'USD')]):
            if rec.type == "purchase" and rec.symbol.upper() == "$":
                success, date_exchange, exchange_rate = pe_exchange_rate.exchange_rate_purchase(
                    rec.get_url_service(rec.from_type), rec.from_type)
                local_pytz = pytz.timezone(company.partner_id.tz)
                time_created_day = datetime.datetime.now(local_pytz)
                if success:
                    if date_exchange.date() == time_created_day.date():
                        currency_rates = rec._pg_get_rates(company, date_exchange)
                        rate_id = currency_rates.get(rec.id, False)
                        if rate_id:
                            rate_currency = self.env["res.currency.rate"].browse(int(rate_id))
                            if rate_currency.name == date_exchange.date():
                                rate_currency.write({
                                    "rate_exchange": exchange_rate
                                })
                            else:
                                self.env["res.currency.rate"].create({
                                    'currency_id': rec.id,
                                    'name': date_exchange.date(),
                                    'rate_exchange': exchange_rate
                                })
                        else:
                            self.env["res.currency.rate"].create({
                                'currency_id': rec.id,
                                'name': date_exchange.date(),
                                'rate_exchange': exchange_rate
                            })

    @api.model
    def get_pe_exchange_rate(self):
        self = self.sudo()
        country_pe = self.env.ref('base.pe')
        _logger.info("get_pe_exchange_rate")
        _logger.info(country_pe.id)
        companies = self.env['res.company'].search([('country_id', '=', country_pe.id)])
        _logger.info("companies")
        _logger.info(companies)
        currency_usd = self.search([('active', '=', True), ('name', '=', 'USD')], limit=1)
        for company in companies:
            is_updated = currency_usd.is_updated(company)
            _logger.info("is_updated")
            _logger.info(is_updated)
            if not is_updated:
                currency_usd.action_exchange_rate_sale(company)
                currency_usd.action_exchange_rate_purchase(company)
        return True

    def get_exchange_rate(self):
        for rec in self:
            rec.get_pe_exchange_rate()

    def is_updated(self, company):
        local_pytz = pytz.timezone(company.partner_id.tz)
        time_created_day = datetime.datetime.now(local_pytz)
        _logger.info("time_created_day")
        _logger.info(time_created_day.date())
        currency_rates = self._pg_get_rates(company, time_created_day.date())
        rate_id = currency_rates.get(self.id, False)
        if rate_id:
            rate_currency = self.env["res.currency.rate"].browse(int(rate_id))
            _logger.info("rate_currency")
            _logger.info(rate_currency)
            _logger.info("rate_currency.name")
            _logger.info(rate_currency.name)
            if rate_currency.name == time_created_day.date():
                return True
        return False

    def _pg_get_rates(self, company, date):
        if not self.ids:
            return {}
        self.env['res.currency.rate'].flush(['rate', 'currency_id', 'company_id', 'name'])
        query = """SELECT c.id,
                          COALESCE((SELECT r.id FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 0) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company.id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        return currency_rates


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"
    _description = "Currency Rate"

    type = fields.Selection(related="currency_id.type", store=True)
