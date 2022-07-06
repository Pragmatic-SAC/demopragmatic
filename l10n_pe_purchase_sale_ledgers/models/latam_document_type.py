# -*- coding: utf-8 -*-
# © 2020 PRAGMATIC PERU
from odoo import api, fields, models


class L10nLatamDocumentType(models.Model):
    _inherit = "l10n_latam.document.type"

    tax_decrease = fields.Boolean(string="Tax decrease", default=False)

    show_book = fields.Boolean(string="Show in Account Book", default=False)
