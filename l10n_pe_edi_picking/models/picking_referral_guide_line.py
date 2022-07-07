# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReferralGuideLine(models.Model):
    _name = 'picking.referral.guide.line'
    _description = 'Referral Guide Line'

    referral_guide_id = fields.Many2one(comodel_name='picking.referral.guide', ondelete="cascade", required=True)
    name = fields.Char(string='Description')
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    product_code = fields.Char(string='Product Code')
    unit_of_measurement = fields.Many2one(comodel_name='uom.uom', string='Unit of measurement')
    quantity = fields.Float(string='Quantity')
    weight = fields.Float(string='Weight')
    total_weight = fields.Float(string='Total weight')



    @api.onchange("quantity", "weight")
    def onchange_quantity_weight(self):
        if self.quantity:
            self.update({"total_weight": self.weight * self.quantity})

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.update({
                "product_code": self.product_id.default_code,
                "name": self.product_id.name,
                "unit_of_measurement": self.product_id.uom_id.id,
                "weight": self.product_id.weight,
                "total_weight": self.weight * self.quantity
            })
