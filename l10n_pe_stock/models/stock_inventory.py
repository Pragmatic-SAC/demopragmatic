# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    type_transaction = fields.Many2one(comodel_name="pragmatic.type.operation.table.12",
                                       string="Sunat Type Transaction")
