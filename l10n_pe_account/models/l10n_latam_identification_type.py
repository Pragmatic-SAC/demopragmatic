# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression

class L10nLatamIdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'

    invoice_type_allowed = fields.Many2many(comodel_name="l10n_latam.document.type", string="Type document allowed")
    placeholder = fields.Char(string="Size of Length")
