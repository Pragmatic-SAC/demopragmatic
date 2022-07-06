# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    detraction = fields.Boolean(string="Is Detraction Payment", default=False)
    detraction_date = fields.Date(string="Detraction Date Payment")
    detraction_number = fields.Char(string="Detraction Number Payment")

    def _create_payment_vals_from_wizard(self):
        response = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        response["detraction"] = self.detraction
        response["detraction_date"] = self.detraction_date
        response["detraction_number"] = self.detraction_number
        return response
