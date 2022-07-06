# -*- coding: utf-8 -*-
# © 2020 INTITEC PERU
from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_plastic = fields.Boolean(string='ICBPer', default=False)
