# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class StockLocation(models.Model):
    _inherit = "stock.location"

    establishment = fields.Many2one(comodel_name="pragmatic.establishment", string="Establishment")
