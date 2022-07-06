# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    show_in_invoice = fields.Boolean(string="Show in Invoice")

    abbreviation = fields.Char(string="Abbreviation")
