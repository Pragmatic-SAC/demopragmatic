# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class StockPicking(models.Model):
    _inherit = "stock.scrap"

    type_transaction = fields.Many2one(comodel_name="pragmatic.type.operation.table.12",
                                       string="Sunat Type Transaction")
