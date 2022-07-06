# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    journal_free = fields.Many2one(comodel_name='account.journal', string='Journal Free Tax')

    account_free_reverse = fields.Many2one(comodel_name='account.account', string='Account Free Tax')
