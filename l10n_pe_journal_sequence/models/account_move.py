# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    sequence_generated = fields.Boolean(string="Sequence Generated", copy=False)

    serie_id = fields.Many2one(comodel_name="pragmatic.serie.sequence", string="Serie")

    serie_filter = fields.Many2many(comodel_name="pragmatic.serie.sequence", compute="_compute_serie_filter")

    @api.depends("user_id")
    def _compute_serie_filter(self):
        for move in self:
            series = self.env["pragmatic.serie.sequence"].get_sequence_by_user(move.user_id)
            move.serie_filter = [(6, False, series.ids)]

    def button_draft(self):
        for move in self:
            move.sequence_generated = True
        super(AccountMove, self).button_draft()

    @api.depends('posted_before', 'state', 'serie_id', 'date', 'move_type')
    def _compute_name(self):
        for move in self:
            sequence_id = move._get_sequence()
            if not sequence_id:
                return super(AccountMove, self)._compute_name()
            if not sequence_id:
                raise UserError('Please define a sequence')
            if not move.sequence_generated and move.state in ['draft', 'cancel']:
                move.name = '/'
            elif not move.sequence_generated and move.state not in ['draft', 'cancel']:
                move.name = sequence_id.with_context(
                    {'ir_sequence_date': move.invoice_date, 'bypass_constrains': True}).next_by_id(
                    sequence_date=move.date)
                move.sequence_generated = True

    def _get_sequence(self):
        self.ensure_one()
        if self.move_type in ["in_invoice", "in_refund", "in_receipt", "entry"]:
            return self.journal_id.sequence_journal_id
        elif self.move_type in ["out_invoice", "out_refund"]:
            return self.serie_id.sequence_id
        return False
