# -*- coding: utf-8 -*-

import base64
from requests.exceptions import InvalidSchema, InvalidURL
from lxml.objectify import fromstring
from copy import deepcopy
from lxml import etree
from odoo.addons.iap.tools.iap_tools import iap_jsonrpc
from odoo.exceptions import AccessError
from odoo.tools import html_escape
from odoo import models, fields, api, _, _lt
import logging

_logger = logging.getLogger(__name__)


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    @api.model
    def _l10n_pe_edi_get_general_error_messages(self):
        response = super(AccountEdiFormat, self)._l10n_pe_edi_get_general_error_messages()
        if 'L10NPE12' not in response:
            response['L10NPE12'] = _lt(
                "An error occurred while querying the CDR, the server did not respond, please check in a few seconds..")
        return response

    # TODO Fixme - after update GRA TAX from original branch odoo
    def _l10n_pe_edi_get_edi_values(self, invoice):
        self.ensure_one()

        def format_float(amount, precision=2):
            ''' Helper to format monetary amount as a string with 2 decimal places. '''
            if amount is None or amount is False:
                return None
            return '%.*f' % (precision, amount)

        def unit_amount(amount, quantity):
            ''' Helper to divide amount by quantity by taking care about float division by zero. '''
            if quantity:
                return invoice.currency_id.round(amount / quantity)
            else:
                return 0.0

        def unit_amount_real(amount, quantity):
            ''' Helper to divide amount by quantity by taking care about float division by zero. '''
            if quantity:
                return round((amount / quantity), 10)
            else:
                return 0.0

        spot = invoice._l10n_pe_edi_get_spot()
        invoice_date_due_vals_list = []
        first_time = True
        for rec_line in invoice.line_ids.filtered(lambda l: l.account_internal_type == 'receivable'):
            amount = rec_line.amount_currency
            if spot and first_time:
                amount -= spot['spot_amount']
            first_time = False
            invoice_date_due_vals_list.append({'amount': rec_line.move_id.currency_id.round(amount),
                                               'currency_name': rec_line.move_id.currency_id.name,
                                               'date_maturity': rec_line.date_maturity})

        values = {
            'record': invoice,
            'spot': invoice._l10n_pe_edi_get_spot(),
            'is_refund': invoice.move_type in ('out_refund', 'in_refund'),
            'PaymentMeansID': invoice._l10n_pe_edi_get_payment_means(),
            'invoice_date_due_vals': invoice.line_ids.filtered(lambda l: l.account_internal_type == 'receivable'),
            'invoice_date_due_vals_list': invoice_date_due_vals_list,
            'invoice_lines_vals': [],
            'certificate_date': invoice.invoice_date,
            'format_float': format_float,
            'total_after_spot': 0.0,
            'tax_details': {
                'total_excluded': 0.0,
                'total_included': 0.0,
                'total_taxes': 0.0,
            },
        }
        if invoice.datetime_emision:
            values['certificate_time'] = invoice.datetime_emision.strftime('%H:%M:%S')
        tax_details = values['tax_details']

        # Invoice lines.
        tax_res_grouped = {}
        invoice_lines = invoice.invoice_line_ids.filtered(lambda line: not line.display_type)
        for i, line in enumerate(invoice_lines, start=1):
            price_unit_wo_discount = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)

            taxes_res = line.tax_ids.compute_all(
                price_unit_wo_discount,
                currency=line.currency_id,
                quantity=line.quantity,
                product=line.product_id,
                partner=line.partner_id,
                is_refund=invoice.move_type in ('out_refund', 'in_refund'),
            )

            taxes_res.update({
                'unit_total_included': unit_amount(taxes_res['total_included'], line.quantity),
                'unit_total_excluded': unit_amount_real(taxes_res['total_excluded'], line.quantity),
                'price_unit_type_code': '01' if not line.currency_id.is_zero(price_unit_wo_discount) else '02',
            })

            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.description == 'GRA':
                    tax_res['base'] = line.price_unit_free * line.quantity
                tax_res.update({
                    'tax_amount': tax.amount,
                    'tax_amount_type': tax.amount_type,
                    'price_unit_type_code': '01' if not line.currency_id.is_zero(tax_res['amount']) else '02',
                    'l10n_pe_edi_tax_code': tax.l10n_pe_edi_tax_code,
                    'l10n_pe_edi_group_code': tax.tax_group_id.l10n_pe_edi_code,
                    'l10n_pe_edi_international_code': tax.l10n_pe_edi_international_code,
                })

                tuple_key = (
                    tax_res['l10n_pe_edi_group_code'],
                    tax_res['l10n_pe_edi_international_code'],
                    tax_res['l10n_pe_edi_tax_code'],
                )

                tax_res_grouped.setdefault(tuple_key, {
                    'base': 0.0,
                    'amount': 0.0,
                    'l10n_pe_edi_group_code': tax_res['l10n_pe_edi_group_code'],
                    'l10n_pe_edi_international_code': tax_res['l10n_pe_edi_international_code'],
                    'l10n_pe_edi_tax_code': tax_res['l10n_pe_edi_tax_code'],
                })
                tax_res_grouped[tuple_key]['base'] += tax_res['base']
                tax_res_grouped[tuple_key]['amount'] += tax_res['amount']
                if tax.description == 'GRA':
                    tax_details['total_excluded'] += 0.00
                    tax_details['total_included'] += 0.00
                else:
                    tax_details['total_excluded'] += tax_res['base']
                    tax_details['total_included'] += tax_res['base'] + tax_res['amount']
                tax_details['total_taxes'] += tax_res['amount']

                if tax.description == 'GRA':
                    taxes_res['unit_total_included'] = line.price_unit_free

                values['invoice_lines_vals'].append({
                    'index': i,
                    'line': line,
                    'tax_details': taxes_res,
                })

        values['tax_details']['grouped_taxes'] = list(tax_res_grouped.values())
        if spot:
            values['total_after_spot'] = tax_details['total_included'] - spot['spot_amount']
        else:
            values['total_after_spot'] = tax_details['total_included']
        return values
