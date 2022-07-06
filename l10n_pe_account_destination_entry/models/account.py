# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    debit_target_account_id = fields.Many2one(comodel_name="account.account", string="Debit target account")
    credit_target_account_id = fields.Many2one(comodel_name="account.account", string="Credit target account")
    target_journal_id = fields.Many2one(comodel_name="account.journal", string="Target journal")
    target_account = fields.Boolean(string="Has target account", default=False)
