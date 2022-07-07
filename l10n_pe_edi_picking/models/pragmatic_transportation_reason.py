# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PragmaticTransportationReasonCatalog20(models.Model):
    _name = "pragmatic.transportation.reason.catalog.20"
    _description = "Sunat catalog 20 - Reason for transfer"
    _inherit = "pragmatic.table.tmpl"

    edit_origin = fields.Boolean(string='Edit Origin Partner', help='True if change Origin Partner')
