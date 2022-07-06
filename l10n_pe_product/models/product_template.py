# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    type_existence = fields.Many2one(comodel_name="pragmatic.type.existence.table.5", string="Sunat Type Existence")
