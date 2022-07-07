# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResDriver(models.Model):
    _name = 'res.driver'
    _description = 'Drivers'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Transport')
    name = fields.Char(string='Name')
    type_document = fields.Many2one(comodel_name='l10n_latam.identification.type', string='Type Document')
    number_document = fields.Char(string='Number Document')
    license = fields.Char(string='License')
    driver_active = fields.Boolean(string='Active', default=True)