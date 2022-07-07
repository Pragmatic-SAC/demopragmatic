# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TransportUnit(models.Model):
    _name = 'transport.unit'
    _description = 'Transport units'

    partner_id = fields.Many2one(comodel_name='res.partner',string='Transport')
    name = fields.Char(string='Name')
    model = fields.Char(string='Model')
    license_plate = fields.Char(string='License Plate')
    second_license_plate = fields.Char(string='Second License Plate')
    unit_active = fields.Boolean(string='Active',default=True)