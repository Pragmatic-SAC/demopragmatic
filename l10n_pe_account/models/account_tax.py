# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_type_purchase = fields.Selection(selection=[
        ('grav', 'Gravada'),
        ('grav_no_grav', 'Gravada y No Gravada'),
        ('no_grav', 'No Gravada'),
        ('excento', 'Excento'), ], string="Type Tax Purchase")
