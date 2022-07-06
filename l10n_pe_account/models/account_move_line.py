# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
from datetime import datetime

_TAXES_FREE = [
    '21',
    '31'
]


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def get_account_incomes(self):
        return self.mov

    price_unit_free = fields.Float(string='Reference Price Free', digits='Product Price')

    price_ref = fields.Float(string='Unit Price', digits='Product Price')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountMoveLine, self)._onchange_product_id()
        if self.move_id.move_type in ['out_invoice', 'out_refund', 'in_refund']:
            self.update({'price_ref': self.price_unit})
        return res

    @api.onchange('product_uom_id')
    def _onchange_uom_id(self):
        res = super(AccountMoveLine, self)._onchange_uom_id()
        if self.move_id.move_type in ['out_invoice', 'out_refund', 'in_refund']:
            self.update({'price_ref': self.price_unit})
        return res

    @api.onchange('price_ref', 'l10n_pe_edi_affectation_reason')
    def _onchange_price_ref(self):
        self.set_price_unit_by_tag()

    def set_price_unit_by_tag(self):
        if self.price_ref and self.l10n_pe_edi_affectation_reason:
            if self.l10n_pe_edi_affectation_reason in _TAXES_FREE:
                self.price_unit_free = self.price_ref
                self.price_unit = 0.00
            else:
                self.price_unit = self.price_ref
