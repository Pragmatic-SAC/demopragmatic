# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class StockPicking(models.Model):
    _inherit = "stock.picking.type"

    type_transactions_allowed = fields.Many2many(comodel_name="pragmatic.type.operation.table.12",
                                                 string="Sunat Type transactions", copy=False,
                                                 help="Type transaction allowed")
