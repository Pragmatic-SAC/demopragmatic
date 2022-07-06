# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PragmaticTypeOperationCatalog51(models.Model):
    _name = "pragmatic.type.operation.catalog.51"
    _description = "Sunat Catalog 51 - Type Of Operation"
    _inherit = "pragmatic.table.tmpl"

    message_report = fields.Text(string="Message To Report")
