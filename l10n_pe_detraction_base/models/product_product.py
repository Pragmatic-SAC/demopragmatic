# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_detraction = fields.Boolean(string="Is Detraction")

    detraction_type = fields.Many2one(comodel_name="pragmatic.catalog.54", string="Detraction Type")

    detraction_percent = fields.Float(related="detraction_type.percent", string="Percent Detraction", readonly=True)

    @api.onchange("detraction_type")
    def _onchange_detraction_type(self):
        if self.detraction_type.id:
            self.l10n_pe_withhold_code = self.detraction_type.code
            self.l10n_pe_withhold_percentage = self.detraction_type.percent
