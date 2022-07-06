# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    journal_free = fields.Many2one(comodel_name='account.journal', string='Journal Free Tax',
                                   related="company_id.journal_free", readonly=False)
    account_free_reverse = fields.Many2one(comodel_name='account.account', string='Account Free Tax',
                                           related="company_id.account_free_reverse", readonly=False)
