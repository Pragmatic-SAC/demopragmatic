from odoo import api, fields, models


class PickingReferralGuide(models.Model):
    _inherit = 'picking.referral.guide'

    invoice_filters = fields.Many2many('account.move', string='Invoice Filter', store=True,
                                       compute='_compute_invoice_filter')

    @api.model
    def get_invoices(self, picking):
        invoices = picking.sale_id.invoice_ids
        return invoices.ids

    @api.depends('picking_id')
    def _compute_invoice_filter(self):
        for referral in self:
            referral.invoice_filters = [(6, 0, self.get_invoices(referral.picking_id))]

    invoice_id = fields.Many2one('account.move', 'Invoice Related')
