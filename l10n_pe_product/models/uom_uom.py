# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class UomUom(models.Model):
    _inherit = "uom.uom"

    l10n_pe_edi_measure_unit_code = fields.Char(string="Measure unit code",
                                                help="Unit code that relates to a product in order to identify what measure unit it uses, the possible values"
                                                     " that you can use here can be found in this URL",
                                                related="sunat_unit_measure.code", readonly=True)

    sunat_unit_measure = fields.Many2one(comodel_name="pragmatic.unit.measurement.table.6",
                                         string="Sunat Unit of Measure")
