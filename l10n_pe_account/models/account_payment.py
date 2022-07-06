# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    detraction = fields.Boolean(string="Is Detraction Payment", default=False)
    detraction_date = fields.Date(string="Detraction Date Payment")
    detraction_number = fields.Char(string="Detraction Number Payment")
