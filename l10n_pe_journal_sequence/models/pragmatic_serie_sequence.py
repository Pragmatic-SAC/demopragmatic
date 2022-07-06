# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PragmaticSequenceJournal(models.Model):
    _name = "pragmatic.serie.sequence"
    _description = "Serie Sequence"

    sequence = fields.Integer(string="Sequence")

    name = fields.Char(string="Name")

    sequence_id = fields.Many2one(comodel_name="ir.sequence", string="Entry Sequence", copy=False)

    sequence_number_next = fields.Integer(string="Next Number", related="sequence_id.number_next_actual",
                                          readonly=False)

    user_ids = fields.Many2many(comodel_name="res.users", string="Responsable")

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    type = fields.Selection(selection=[("manual", "Manual"), ("electronic", "Electronic")], string="Type")

    active = fields.Boolean(string="Active", default=True)

    @api.model
    def get_sequence_by_user(self, user_id):
        pg_series = self.search([('user_ids', '=', user_id.ids), ('company_id', '=', self.env.company.id)])
        return pg_series
