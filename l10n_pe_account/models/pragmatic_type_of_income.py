# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PragmaticTypeIncomeTable31(models.Model):
    _name = "pragmatic.type.income.table.31"
    _description = "Sunat table 31 - Type Of Income"
    _inherit = "pragmatic.table.tmpl"

    code_ocde = fields.Char(string="Code OCDE")
