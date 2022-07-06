# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    rate_exchange = fields.Float(string="Type Exchange", digits=(12, 3), store=True)
    rate = fields.Float(string="Rate", digits=(12, 10), compute="_compute_rate", store=True)

    @api.depends("rate_exchange")
    def _compute_rate(self):
        for curreny_rate in self:
            if curreny_rate.rate_exchange > 0:
                curreny_rate.rate = (1 / curreny_rate.rate_exchange)
