# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_referral_guide_line(self):
        vals = {
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_code': self.product_id.default_code,
            'unit_of_measurement': self.product_id.uom_id.id,
            'quantity': self.quantity_done,
            'weight': self.product_id.weight,
            'total_weight': self.quantity_done * self.product_id.weight
        }
        return vals
