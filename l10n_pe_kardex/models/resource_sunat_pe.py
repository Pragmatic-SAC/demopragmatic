# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PragmaticTypeOperationTable12(models.Model):
    _inherit = 'pragmatic.type.operation.table.12'

    cost_adjustment = fields.Boolean(string="Cost adjustment", default=False)
