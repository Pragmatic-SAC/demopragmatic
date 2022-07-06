# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
from datetime import datetime

_TAXES_FREE = [
    '21',
    '31'
]


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_draft_edi(self):
        for invoice in self:
            invoice.write({'state': 'draft'})

    def get_type_operation(self):
        type_operation = self.env['pragmatic.type.operation.catalog.51'].search(
            [('code', '=', self.l10n_pe_edi_operation_type)], limit=1)
        if type_operation.message_report:
            return [True, type_operation.message_report]
        return [False]

    datetime_emision = fields.Datetime(string='Date Emission')

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        for move in self:
            if move.move_account_tax_free.id:
                move.move_account_tax_free.button_draft()
                move.move_account_tax_free.button_cancel()
        return res

    line_free_ids = fields.Many2many(comodel_name='account.move.line', relation='account_free_line',
                                     string='Account Lines Free', compute='_compute_line_free_ids', store=True)

    @api.depends('move_account_tax_free.line_ids')
    def _compute_line_free_ids(self):
        for move in self:
            move.line_free_ids = move.move_account_tax_free.line_ids

    def get_amount_free_tax(self):
        return sum(line.price_unit_free * line.quantity for line in
                   self.invoice_line_ids.filtered(lambda l: l.l10n_pe_edi_affectation_reason in _TAXES_FREE))

    def _prepare_tax_free_lines(self):
        amount_total = 0.0
        tax_ids = False
        line_default = False
        line_taxfree = []
        for line in self.invoice_line_ids.filtered(lambda l: l.l10n_pe_edi_affectation_reason in _TAXES_FREE):
            amount_total += line.price_unit_free
            tax_ids = line.tax_ids
            line_default = line
        _price_tax = 0.00
        _price_total = 0.00
        _price_subtotal = 0.00
        _account_line_free = False
        if line_default:
            amounts = line_default._get_price_total_and_subtotal(price_unit=amount_total, taxes=tax_ids)
            _price_total = amounts['price_total']
            _price_subtotal = amounts['price_subtotal']
            _price_tax = amounts['price_total'] - amounts['price_subtotal']
            _account_line_free = line_default.account_id
        # INCOME
        _account_tax = tax_ids[0].invoice_repartition_line_ids.filtered(lambda r: r.account_id.id)[0].account_id
        _debit_price_total = 0.00
        _credit_price_total = 0.00
        # Account of Client - Price total
        if self.move_type == 'out_invoice':
            _debit_price_total = _price_total
        if self.move_type == 'out_refund':
            _credit_price_total = _price_total
        line_taxfree.append((0, 0, {
            'name': self.name,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'debit': _debit_price_total,
            'credit': _credit_price_total
        }))
        # Account line of invoice - Price Subtotal
        _debit_price_subtotal = 0.00
        _credit_price_subtotal = 0.00
        # Account of Client - Price total
        if self.move_type == 'out_invoice':
            _credit_price_subtotal = _price_subtotal
        if self.move_type == 'out_refund':
            _debit_price_subtotal = _price_subtotal
        line_taxfree.append((0, 0, {
            'name': self.name,
            'account_id': _account_line_free.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'debit': _debit_price_subtotal,
            'credit': _credit_price_subtotal
        }))
        # Account line of tax - Price IGV
        _debit_price_tax = 0.00
        _credit_price_tax = 0.00
        # Account of Client - Price total
        if self.move_type == 'out_invoice':
            _credit_price_tax = _price_tax
        if self.move_type == 'out_refund':
            _debit_price_tax = _price_tax
        line_taxfree.append((0, 0, {
            'name': self.name,
            'account_id': _account_tax.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'debit': _debit_price_tax,
            'credit': _credit_price_tax
        }))
        # REVERSE ACCOUNT
        # Account of partner
        _debit_re_price_total = 0.00
        _credit_re_price_total = 0.00
        # Account of Client - Price total
        if self.move_type == 'out_invoice':
            _credit_re_price_total = _price_total
        if self.move_type == 'out_refund':
            _debit_re_price_total = _price_total

        line_taxfree.append((0, 0, {
            'name': 'Reverso %s' % self.name,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'debit': _debit_re_price_total,
            'credit': _credit_re_price_total
        }))
        # Account line of invoice - Price Subtotal
        _debit_re_price_subtotal = 0.00
        _credit_re_price_subtotal = 0.00
        # Account of Client - Price total
        if self.move_type == 'out_invoice':
            _debit_re_price_subtotal = _price_subtotal
        if self.move_type == 'out_refund':
            _credit_re_price_subtotal = _price_subtotal
        line_taxfree.append((0, 0, {
            'name': 'Reverso %s' % self.name,
            'account_id': _account_line_free.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'debit': _debit_re_price_subtotal,
            'credit': _credit_re_price_subtotal
        }))
        # Account line of configuration company - Price IGV
        _debit_re_price_tax = 0.00
        _credit_re_price_tax = 0.00
        # Account of Client - Price total
        if self.move_type == 'out_invoice':
            _debit_re_price_tax = _price_tax
        if self.move_type == 'out_refund':
            _credit_re_price_tax = _price_tax
        line_taxfree.append((0, 0, {
            'name': 'Reverso %s' % self.name,
            'account_id': self.company_id.account_free_reverse.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'debit': _debit_re_price_tax,
            'credit': _credit_re_price_tax
        }))
        return line_taxfree

    move_account_tax_free = fields.Many2one(comodel_name='account.move', string='Account Move Free Tax', copy=False)

    def _prepare_account_tax_free(self):
        lines = self._prepare_tax_free_lines()
        vals = {
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'date': self.date,
            'journal_id': self.company_id.journal_free.id,
            'currency_id': self.currency_id.id,
            'line_ids': lines,
            'move_type': 'entry'
        }
        return vals

    def has_tax_free(self):
        invoice_line_ids = self.invoice_line_ids.filtered(lambda l: l.l10n_pe_edi_affectation_reason in _TAXES_FREE)
        return True if len(invoice_line_ids.ids) > 0 else False

    def create_account_move_freetax(self):
        if self.has_tax_free() and self.move_type in ['out_invoice', 'out_refund']:
            vals = self._prepare_account_tax_free()
            accont_move_free = self.create(vals)
            accont_move_free.action_post()
            self.move_account_tax_free = accont_move_free.id

    def get_name_report_fe(self):
        _name = "{ruc}-{name}".format(ruc=self.company_id.vat, name=self.name)
        return _name

    guide_number = fields.Char(string="Guide Number")

    def has_account_banks(self):
        account_banks = self.env["res.partner.bank"].search(
            [('company_id', '=', self.company_id.id), ('show_in_invoice', '=', True)])
        return True if account_banks.ids else False

    def get_account_banks(self):
        account_banks = self.env["res.partner.bank"].search(
            [('company_id', '=', self.company_id.id), ('show_in_invoice', '=', True)])
        return account_banks

    @api.depends('move_type', 'company_id', 'serie_id')
    def _compute_l10n_pe_edi_is_required(self):
        for move in self:
            move.l10n_pe_edi_is_required = move.country_code == 'PE' \
                                           and move.is_sale_document() and move.journal_id.l10n_latam_use_documents \
                                           and move.serie_id.type == 'electronic' \
                                           and not move.l10n_pe_edi_cancel_cdr_number

    def validate_length_correlative(self):
        length_minimal = (self.l10n_latam_document_type_id.length or [])
        if length_minimal > 0:
            correlative_length = len(self.correlative or [])
            if correlative_length != length_minimal:
                raise UserError(_("Correlative no have the correct length."))

    def validate_duplicate_document(self):
        document = self.search([('partner_id', '=', self.partner_id.id), ('serie_code', '=', self.serie_code),
                                ('correlative', '=', self.correlative), ('id', '!=', self.id)])
        if document.id:
            raise UserError(_("The document is registered."))

    serie_code = fields.Char(string="Serie")

    correlative = fields.Char(string="Correlative")

    edit_serie_code = fields.Selection(selection=[('readonly', 'Readonly'), ('editable', 'Editable')],
                                       string="Edit Serie Code", compute="_compute_edit_serie_code")

    initial_charge = fields.Boolean(string="Initial Charge", default=False)

    serie_filter = fields.Many2many(comodel_name="pragmatic.serie.sequence",
                                    compute="_compute_serie_filter_establishment")

    document_type_filter = fields.Many2many(comodel_name="l10n_latam.document.type",
                                            compute="_compute_filter_document_type_filter")

    @api.depends("partner_id")
    def _compute_filter_document_type_filter(self):
        for move in self:
            move.document_type_filter = [
                (6, False, move.partner_id.l10n_latam_identification_type_id.invoice_type_allowed.ids)]

    establish_filter = fields.Many2many(comodel_name="pragmatic.establishment",
                                        compute="_compute_establishment_filter")

    @api.depends("company_id")
    def _compute_establishment_filter(self):
        for move in self:
            establishments = self.env["pragmatic.establishment"].search([('company_id', '=', move.company_id.id)])
            move.establish_filter = [(6, False, establishments.ids)]

    @api.onchange("journal_id")
    def _pg_onchange_journal_id(self):
        self.update({"serie_id": False})

    @api.onchange("partner_id")
    def _pg_onchange_partner(self):
        if self.move_type in ["out_invoice", "out_refund"]:
            if self.partner_id.id:
                invoice_type_allowed = self.partner_id.l10n_latam_identification_type_id.invoice_type_allowed
                if invoice_type_allowed.ids:
                    self.update({"l10n_latam_document_type_id": invoice_type_allowed.ids[0]})
                    self._pgonchange_l10n_latam_document_type_id()
                else:
                    self.update({"l10n_latam_document_type_id": False, "establishment": False, "serie_id": False})
            else:
                self.update({"l10n_latam_document_type_id": False, "establishment": False, "serie_id": False})

    @api.onchange("l10n_latam_document_type_id")
    def _pgonchange_l10n_latam_document_type_id(self):
        if self.move_type in ["out_invoice", "out_refund"]:
            series = self.env["pragmatic.serie.sequence"].get_sequence_by_user_establishment(self.user_id,
                                                                                             self.establishment,
                                                                                             self.l10n_latam_document_type_id,
                                                                                             self.company_id,
                                                                                             self.journal_id)
            if series.ids:
                self.update({"establishment": series[0].establishment.id})

            else:
                self.update({"establishment": False})
        self._pg_l10n_change_establishment()

    @api.onchange("establishment")
    def _pg_l10n_change_establishment(self):
        if self.move_type in ["out_invoice", "out_refund"]:
            series = self.env["pragmatic.serie.sequence"].get_sequence_by_user_establishment(self.user_id,
                                                                                             self.establishment,
                                                                                             self.l10n_latam_document_type_id,
                                                                                             self.company_id,
                                                                                             self.journal_id)
            if series.ids:
                self.update({"serie_id": series[0].id})
                self._pgonchange_serie_id()
            else:
                self.update({"serie_id": False})

    @api.onchange("serie_id")
    def _pgonchange_serie_id(self):
        if self.move_type in ["out_invoice", "out_refund"]:
            if self.journal_id.id and self.l10n_latam_document_type_id.id:
                sequence = False
                if self.move_type in ["out_invoice", "out_refund"]:
                    sequence = self.serie_id.sequence_id
                elif self.move_type in ["in_invoice", "in_refund"]:
                    sequence = self.journal_id.sequence_journal_id
                if sequence.id:
                    self.l10n_latam_document_number = "%s" % sequence.prefix
                    self.serie_code = "%s" % sequence.prefix
                else:
                    self.serie_code = False

    @api.depends("establishment", "partner_id", "l10n_latam_document_type_id", "company_id", "journal_id")
    def _compute_serie_filter_establishment(self):
        for move in self:
            if move.move_type in ["out_invoice", "out_refund"]:
                series = self.env["pragmatic.serie.sequence"].get_sequence_by_user_establishment(self.env.user,
                                                                                                 move.establishment,
                                                                                                 move.l10n_latam_document_type_id,
                                                                                                 move.company_id,
                                                                                                 move.journal_id)

                move.serie_filter = [(6, False, series.ids)]
            else:
                move.serie_filter = [(6, False, [])]

    @api.depends('posted_before', 'state', 'serie_id', 'date', 'initial_charge', 'serie_code', 'correlative')
    def _compute_name(self):
        for move in self:
            if not move.serie_id.sequence_id.id:
                return super(AccountMove, self)._compute_name()
            sequence_id = move._get_sequence()
            if not sequence_id:
                raise UserError('Please define a sequence on your journal.')
            if not move.sequence_generated and move.state in ['draft', 'cancel'] and not move.initial_charge:
                move.name = '/'
            elif not move.sequence_generated and move.state not in ['draft', 'cancel'] and not move.initial_charge:
                move.name = sequence_id.with_context(
                    {'ir_sequence_date': move.invoice_date, 'bypass_constrains': True}).next_by_id(
                    sequence_date=move.invoice_date)
                move.sequence_generated = True
            elif move.initial_charge:
                move.name = "{0}-{1}".format(move.serie_code, move.correlative)
                move.sequence_generated = True

    @api.depends("state", "move_type")
    def _compute_edit_serie_code(self):
        for move in self:
            if move.move_type in ["out_refund", "out_invoice"]:
                move.edit_serie_code = "readonly"
            elif move.move_type in ["in_refund", "in_invoice"]:
                if move.state in ["draft"]:
                    move.edit_serie_code = "editable"
                else:
                    move.edit_serie_code = "readonly"
            else:
                move.edit_serie_code = "readonly"

    exchange_rate = fields.Float(string="Exchange Rate", store=True, compute="_compute_exchange_rate",
                                 digits="Exchange Rate")

    def _validate_fields_for_edi(self):
        for line in self.invoice_line_ids:
            if line.l10n_pe_edi_affectation_reason in _TAXES_FREE and line.price_ref <= 0:
                raise UserError(_('Please enter a reference price.'))

    def action_post(self):
        response = super(AccountMove, self).action_post()
        if self.move_type in ["in_refund", "in_invoice"]:
            self.validate_length_correlative()
            self.validate_duplicate_document()
        elif self.move_type in ["out_refund", "out_invoice"]:
            self._validate_fields_for_edi()
            self.assign_serie_correlative()
            self.create_account_move_freetax()
        return response

    def assign_serie_correlative(self):
        self.datetime_emision = datetime.now()
        if self.name:
            if '-' in self.name:
                _name = self.name.split("-")
                self.serie_code = _name[0]
                self.correlative = _name[1]

    type_of_income = fields.Many2one(comodel_name="pragmatic.type.income.table.31", string="Type of Income")

    nc_nd_latam_document_type_id = fields.Many2one(comodel_name="l10n_latam.document.type", string="Ref. Document Type")

    nc_nd_date_emision = fields.Date(string="Ref. Date")

    nc_nd_serie_code = fields.Char(string="Ref. Serie")

    nc_nd_correlative = fields.Char(string="Ref. Correlative")

    establishment = fields.Many2one(comodel_name="pragmatic.establishment", string="Establishment")

    type_document_code = fields.Char(string="Code type document", related="l10n_latam_document_type_id.code",
                                     copy=False, readonly=False)

    edit_correlative = fields.Boolean(string="Edit Correlative", copy=False)

    can_edit_correlative = fields.Selection(selection=[('readonly', 'Readonly'), ('editable', 'Editable')],
                                            string="Edit Correlative", store=True,
                                            compute="_compute_can_edit_correlative")

    @api.depends("move_type", "edit_correlative", "state")
    def _compute_can_edit_correlative(self):
        for move in self:
            if move.move_type in ["out_invoice", "out_refund"]:
                can_edit = "readonly" if not move.edit_correlative else "editable"
            else:
                can_edit = "readonly" if not move.edit_correlative and move.state not in ["draft"] else "editable"
            move.can_edit_correlative = can_edit

    def _reverse_moves(self, default_values_list=None, cancel=False):
        for move, default_values in zip(self, default_values_list):
            _values = {
                'nc_nd_latam_document_type_id': move.l10n_latam_document_type_id.id,
                'nc_nd_date_emision': move.invoice_date,
                'nc_nd_serie_code': move.serie_code,
                'nc_nd_correlative': move.correlative
            }
            invoice_type_allowed = move.partner_id.l10n_latam_identification_type_id.invoice_type_allowed
            if invoice_type_allowed.ids:
                if move.move_type == 'out_invoice':
                    invoice_type_allowed = invoice_type_allowed.filtered(lambda inv: inv.code == '07')
                    if invoice_type_allowed.ids:
                        _values['l10n_latam_document_type_id'] = invoice_type_allowed.ids[0]
                        series = self.env["pragmatic.serie.sequence"] \
                            .get_sequence_by_user_establishment_vals(move.invoice_user_id.id,
                                                                     False,
                                                                     _values['l10n_latam_document_type_id'],
                                                                     move.company_id.id,
                                                                     move.journal_id.id)
                        if series.ids:
                            _values['establishment'] = series[0].establishment.id
                            _values['serie_id'] = series[0].id
                            _values['serie_code'] = series[0].sequence_id.prefix
            default_values.update(_values)
        response = super(AccountMove, self)._reverse_moves(default_values_list, cancel)
        return response

    @api.depends("currency_id", "date", "company_id")
    def _compute_exchange_rate(self):
        for account in self:
            account_date = account.date or fields.Datetime.now()
            account_rate = self.env["res.currency"]._get_conversion_rate(account.company_id.currency_id,
                                                                         account.currency_id,
                                                                         account.company_id, account_date)
            if account_rate > 0:
                account_rate = 1 / account_rate
            else:
                account_rate = 1
            account.exchange_rate = account_rate
