# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class AccountMove(models.Model):
    _inherit = "account.move"

    detraction_percent = fields.Float(string="Detraction Percent", store=True,
                                      compute="_compute_detraction")

    detraction_code = fields.Char(string="Detraction Code", store=True,
                                  compute="_compute_detraction")

    detraction_amount = fields.Monetary(string="Monto de detraccion", store=True,
                                        compute="_compute_detraction")

    @api.depends("invoice_line_ids", "amount_total", "currency_id", "l10n_latam_document_type_id", "move_type")
    def _compute_detraction(self):
        for move in self:
            move.detraction_code = False
            move.detraction_percent = 0.00
            move.detraction_amount = 0.00
            detracions = {}
            have_igv = False
            for line in move.invoice_line_ids:
                for tax in line.tax_ids:
                    if tax.l10n_pe_edi_tax_code in ["1000"]:
                        have_igv = True
            for product in move.invoice_line_ids.mapped('product_id'):
                if product.is_detraction:
                    detracions[product.detraction_type.percent] = product
            detraction_mount = move.currency_id.compute(move.amount_total, move.company_id.currency_id)
            if len(detracions) > 0 and have_igv and move.company_id.is_detraction \
                    and detraction_mount >= move.company_id.detraction_amount \
                    and move.l10n_latam_document_type_id.code == '01':
                product = detracions[max(detracions)]
                move.detraction_percent = product.detraction_type.percent
                move.detraction_code = product.detraction_type.code
                detraction_amount = (move.detraction_percent / 100) * move.amount_total
                if move.move_type not in ["in_invoice"]:
                    move.detraction_amount = detraction_amount
                else:
                    detraction_amount = int(round((move.detraction_percent / 100) * move.amount_total))
                    move.detraction_amount = float(detraction_amount)
