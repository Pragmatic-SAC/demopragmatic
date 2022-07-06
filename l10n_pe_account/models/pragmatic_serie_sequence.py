# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class PragmaticSerieSequence(models.Model):
    _inherit = "pragmatic.serie.sequence"

    establishment = fields.Many2one(comodel_name="pragmatic.establishment", string="Establishment")

    type_document = fields.Many2one(comodel_name="l10n_latam.document.type", string="Type Document")

    @api.model
    def get_sequence_by_user_establishment_vals(self, user_id, establishment, type_document, company_id, journal):
        domain = []
        if user_id:
            domain.append(('user_ids', 'in', [user_id]))
        if company_id:
            domain.append(('company_id', '=', company_id))
        if establishment:
            domain.append(('establishment', '=', establishment))
        if type_document:
            domain.append(('type_document', '=', type_document))
        if journal:
            journal_id = self.env['account.journal'].browse(journal)
            _type = 'electronic' if journal_id.edi_format_ids.ids else 'manual'
            domain.append(('type', '=', _type))
        pg_series = self.search(domain)
        return pg_series

    @api.model
    def get_sequence_by_user_establishment(self, user_id, establishment, type_document, company_id, journal_id):
        domain = []
        if user_id.id:
            domain.append(('user_ids', 'in', user_id.ids))
        if company_id.id:
            domain.append(('company_id', '=', company_id.id))
        if establishment.id:
            domain.append(('establishment', '=', establishment.id))
        if type_document.id:
            domain.append(('type_document', '=', type_document.id))
        if journal_id.id:
            _type = 'electronic' if journal_id.edi_format_ids.ids else 'manual'
            domain.append(('type', '=', _type))
        pg_series = self.search(domain)
        return pg_series
