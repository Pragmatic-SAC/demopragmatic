# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_detraction = fields.Boolean(string="Is detraction", related="company_id.is_detraction",
                                   readonly=False)

    detraction_amount = fields.Float(string="Detraction Mount", related="company_id.detraction_amount",
                                    readonly=False)
