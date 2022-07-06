# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResCompany(models.Model):
    _inherit = "res.company"

    is_detraction = fields.Boolean(string="Is detraction")

    detraction_amount = fields.Float(string="Detraction Mount")
