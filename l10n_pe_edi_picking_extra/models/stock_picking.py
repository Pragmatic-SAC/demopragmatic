# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_referral_guide(self):
        vals = super(StockPicking, self)._prepare_referral_guide()
        invoices = self.env['picking.referral.guide'].get_invoices(self)
        if len(invoices) > 0:
            vals['invoice_id'] = invoices[0]
        return vals
