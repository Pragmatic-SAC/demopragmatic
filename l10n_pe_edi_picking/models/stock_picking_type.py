# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'


    is_electronic = fields.Boolean(string='Is Electronic')

    gre_sequence_id = fields.Many2one(comodel_name='ir.sequence', string='Secuence for Referral Guide')

    reason_for_transfer = fields.Many2one(comodel_name='pragmatic.transportation.reason.catalog.20',
                                          string='Default Reason for transfer')

    transport_mode = fields.Many2one(comodel_name='pragmatic.transport.mode.catalog.18',
                                     string='Default Transport mode')

    who_received = fields.Boolean(string="Print PDF Who received?")
