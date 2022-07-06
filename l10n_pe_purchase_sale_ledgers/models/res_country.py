# -*- coding: utf-8 -*-
# © 2020 INTITEC PERU
from odoo import api, fields, models


class ResCountry(models.Model):
    _inherit = "res.country"

    code_sunat = fields.Char(string='Code Sunat')
