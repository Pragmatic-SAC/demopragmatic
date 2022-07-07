# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_referrals = fields.One2many(comodel_name='picking.referral.guide', string='Referral Guide',
                                        inverse_name='picking_id')

    referral_count = fields.Integer(string='Referral Guides Count', store=True, compute='_compute_referral_count')

    @api.depends('picking_referrals')
    def _compute_referral_count(self):
        for stock in self:
            stock.referral_count = len(stock.picking_referrals.ids or [])

    def _get_addressee_origin(self):
        partner_id = False
        origin_id = False
        if self.picking_type_id.code in ['incoming', 'internal']:
            partner_id = self.company_id.partner_id
            origin_id = self.partner_id.parent_id if self.partner_id.parent_id.id else self.partner_id
        elif self.picking_type_id.code in ['outgoing']:
            partner_id = self.partner_id.parent_id if self.partner_id.parent_id.id else self.partner_id
            origin_id = self.company_id.partner_id
        return partner_id, origin_id

    def _prepare_referral_guide(self):
        lines_vals = []
        for line in self.move_ids_without_package:
            lines_vals.append([0, 0, line._prepare_referral_guide_line()])
        addressee_id, origin_id = self._get_addressee_origin()
        if not addressee_id:
            raise UserError(_('Recipient not found'))
        if not origin_id:
            raise UserError(_('Issuer not found'))
        dates_default = datetime.datetime.now()
        vals = {
            'picking_id': self.id,
            'referral_lines': lines_vals,
            'addressee_id': addressee_id.id,
            'origin_id': origin_id.id,
            'establishment': self.location_id.establishment.id,
            'transport_mode': self.picking_type_id.transport_mode.id,
            'reason_for_transfer': self.picking_type_id.reason_for_transfer.id,
            'description': self.picking_type_id.reason_for_transfer.name,
            'issuing_date': dates_default,
            'transfer_date': dates_default,
            'delivery_date': dates_default,
            'destination_addresses_id': addressee_id.id,
            'origin_addresses_id': origin_id.id
        }
        return vals

    def _create_referral_guide(self):
        REFERRAL_ENV = self.env["picking.referral.guide"]
        vals = self._prepare_referral_guide()
        referral = REFERRAL_ENV.create(vals)
        self.write({'picking_referrals': [(4, referral.id)]})

    def create_referral_guide(self):
        for picking in self:
            picking._create_referral_guide()

    def show_referral_guide(self):
        ctx = dict(self.env.context or {})
        return {
            'res_model': 'picking.referral.guide',
            'type': 'ir.actions.act_window',
            'name': _("Referral Guides"),
            'domain': [('id', 'in', self.picking_referrals.ids)],
            'view_mode': 'tree,form',
        }
