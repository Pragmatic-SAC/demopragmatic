# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PragmaticCatalog54(models.Model):
    _name = "pragmatic.catalog.54"
    _description = "Sunat Catalog 54 - Goods and services codes subject to detraction"
    _inherit = "pragmatic.table.tmpl"

    percent = fields.Float(string="Percent")
