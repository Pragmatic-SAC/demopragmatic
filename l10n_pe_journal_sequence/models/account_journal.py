# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    sequence_journal_id = fields.Many2one(comodel_name="ir.sequence", string="Sequence")
