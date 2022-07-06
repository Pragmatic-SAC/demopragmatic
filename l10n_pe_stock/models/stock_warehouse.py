# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    establishment = fields.Many2one(comodel_name="pragmatic.establishment",
                                    string="Establishment")
