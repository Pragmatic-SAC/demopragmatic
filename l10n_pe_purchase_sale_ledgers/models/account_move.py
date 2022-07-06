# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    show_book = fields.Boolean(string="Show in Account Book", default=True)

    @api.onchange("l10n_latam_document_type_id")
    def _pgonchange_l10n_latam_document_type_id(self):
        super(AccountMove, self)._pgonchange_l10n_latam_document_type_id()
        self.show_book = self.l10n_latam_document_type_id.show_book

    def _get_payment_detraction_JSON_values(self):
        self.ensure_one()
        reconciled_vals = {}
        for partial, amount, counterpart_line in self._get_reconciled_invoices_partials():
            if counterpart_line.payment_id.detraction:
                reconciled_vals = {
                    'payment_id': counterpart_line.payment_id.id,
                    'detraction_date': counterpart_line.payment_id.detraction_date.strftime("%d/%m/%Y"),
                    'detraction_number': counterpart_line.payment_id.detraction_number
                }
        return reconciled_vals
