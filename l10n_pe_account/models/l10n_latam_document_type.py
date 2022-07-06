from odoo import fields, models, api


class L10nLatamDocumentType(models.Model):
    _inherit = 'l10n_latam.document.type'

    length = fields.Integer(string="Size of Length")

