# -*- coding: utf-8 -*-
import io
import json
import logging
import datetime
from datetime import timedelta
import calendar
import base64
# from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import config, date_utils, get_lang
from odoo import models, _, api, fields
from . import tools as k_tool

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


class ReportAccountBooks(models.Model):
    _name = 'report.account.books'
    _description = "report of accounting books of purchases and sales non-domiciled subjects"

    @api.model
    def _get_from_date(self):
        date = datetime.date.today()
        start_date = datetime.datetime(date.year, date.month, 1)
        return start_date.date()

    @api.model
    def _get_date_to(self):
        date = datetime.date.today()
        end_date = datetime.datetime(date.year, date.month, calendar.mdays[date.month])
        return end_date.date()

    BOOK_TYPE = [('purchase', _('Purchase')), ('sale', _('Sales')), ('non_domiciled', _('Non-domiciled'))]

    name = fields.Char(string="Name", required=True)
    date_from = fields.Date(string='Date from', default=_get_from_date, required=True, )
    date_to = fields.Date(string='Date to', default=_get_date_to, required=True, )
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id,
                                 string='Company')
    book_type = fields.Selection(BOOK_TYPE, default='purchase', required=True, string='Book Type')

    @api.model
    def _get_report_name(self, options):
        if options['book_type'] == 'sale':
            name_sheet = _('Record sale')
        elif options['book_type'] == 'purchase':
            name_sheet = _('Purchase record')
        elif options['book_type'] == 'non_domiciled':
            name_sheet = _('Registration of purchase subject not domiciled')
        return name_sheet

    def get_header(self, options):
        columns = self._get_columns_name(options)
        return [columns]

    def _get_cell_type_value(self, cell):
        if cell.get('class') == 'number':
            return ('number', cell.get('name', ''))
        elif 'date' not in cell.get('class', '') or not cell.get('name'):
            # cell is not a date
            return ('text', cell.get('name', ''))
        elif isinstance(cell['name'], (float, datetime.date, datetime.datetime)):
            # the date is xlsx compatible
            return ('date', cell['name'])

        try:
            # the date is parsable to a xlsx compatible date
            lg = self.env['res.lang']._lang_get(self.env.user.lang) or get_lang(self.env)
            return ('date', datetime.strptime(cell['name'], lg.date_format))
        except:
            # the date is not parsable thus is returned as text
            return ('text', cell['name'])

    def _get_columns_name(self, options):
        b_type = options["book_type"]
        if b_type == 'sale':
            return k_tool.column_excel_sale()
        if b_type == 'purchase':
            return k_tool.column_excel_purchase()
        if b_type == 'non_domiciled':
            return k_tool.column_excel_non_domiciled()

    def _get_lines(self, options):

        lines = []
        res_company = self.env["res.company"].sudo().browse(
            options["company_id"])
        b_type = options["book_type"]
        if b_type == 'sale':
            types_doc = ["out_invoice", "out_refund"]
            array_values_initial = self.env["account.move"].sudo().search(
                [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
                 ('company_id', '=', res_company['id']), ('state', 'in', ['posted', 'cancel']),
                 ('move_type', 'in', types_doc), ('show_book', '=', True)])
            for invoice in array_values_initial:
                if invoice.correlative and invoice.l10n_latam_document_type_id.show_book:  # and (invoice.it_sunat_state_code is not False):
                    options["count_sale"] = 1
                    date_refund = ""
                    type_refund = ""
                    serie_refund = ""
                    correlative_refund = ""
                    if invoice.reversed_entry_id.date is not False:
                        refund_invoice = invoice.reversed_entry_id.date
                        date_refund = refund_invoice.strftime("%d/%m/%Y")
                        type_refund = invoice.reversed_entry_id.l10n_latam_document_type_id.code or ""
                        serie_refund = "%s" % invoice.reversed_entry_id.serie_code or ""
                        correlative_refund = "%s" % invoice.reversed_entry_id.correlative or ""
                        correlative_refund = correlative_refund.rjust(8, '0')
                        serie_refund = serie_refund.rjust(4, '0')
                    else:
                        if invoice.l10n_latam_document_type_id.code in ['07', '08']:
                            if invoice.nc_nd_latam_document_type_id:
                                refund_invoice = invoice.nc_nd_date_emision
                                date_refund = refund_invoice.strftime("%d/%m/%Y")
                                type_refund = invoice.nc_nd_latam_document_type_id.code or ""
                                serie_refund = invoice.nc_nd_serie_code or ""
                                correlative_refund = invoice.nc_nd_correlative or ""
                    # Base imponible gravada:
                    sum_taxable_base = 0.00
                    # Monto Total del IGV
                    sum_mnt_tot_trb_igv_nac = 0.00
                    # Importe Total de las operaciones exoneradas
                    sum_tot_exo = 0.00
                    sum_tot_inf = 0.00
                    # Monto Total del ISC
                    sum_mnt_tot_trb_isc_nac = 0.00
                    # Otros conceptos
                    sum_tot_otr = 0.00
                    sum_tot_anti = 0.00
                    # Valor facturado exportacion
                    sum_exportacion = 0.00

                    for line in invoice.line_ids:
                        # Igv
                        if line.tax_line_id.id is not False:
                            # MONTO TOTAL DEL IGV
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.debit
                                else:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.credit
                            # MONTO TOTAL DEL ISC
                            if line.tax_line_id.l10n_pe_edi_tax_code == "2000":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.debit
                                else:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.credit
                        # Base imponible
                        if line.tax_ids is not False:
                            for tax in line.tax_ids:
                                if tax.l10n_pe_edi_tax_code == '1000' or tax.l10n_pe_edi_tax_code == '2000':
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_taxable_base = sum_taxable_base + line.debit
                                    else:
                                        if line.quantity > 0:
                                            sum_taxable_base = sum_taxable_base + line.credit
                                            if line.product_id:
                                                if line.product_id.default_code == 'DISC':
                                                    sum_taxable_base = sum_taxable_base - line.debit
                                        else:
                                            sum_taxable_base = sum_taxable_base - line.debit
                                            sum_tot_anti = sum_tot_anti + line.debit
                                if tax.l10n_pe_edi_tax_code == "9997":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_tot_exo = sum_tot_exo + line.debit
                                    else:
                                        sum_tot_exo = sum_tot_exo + line.credit
                                if tax.l10n_pe_edi_tax_code == "9998":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_tot_inf = sum_tot_inf + line.debit
                                    else:
                                        sum_tot_inf = sum_tot_inf + line.credit
                                if tax.l10n_pe_edi_tax_code == "9999":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_tot_otr = sum_tot_otr + line.debit
                                    else:
                                        sum_tot_otr = sum_tot_otr + line.credit
                                if tax.l10n_pe_edi_tax_code == "9995" and tax.l10n_pe_edi_affectation_reason == "40":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_exportacion = sum_exportacion + line.debit
                                    else:
                                        sum_exportacion = sum_exportacion + line.credit
                    name_partner = invoice.partner_id.name or ''
                    taxable_base = sum_taxable_base
                    invoice_kh_importe_total = abs(invoice.amount_total_signed)
                    tot_exportacion = sum_exportacion
                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                        taxable_base = - taxable_base
                        sum_tot_exo = - sum_tot_exo
                        sum_tot_inf = - sum_tot_inf
                        sum_mnt_tot_trb_igv_nac = - sum_mnt_tot_trb_igv_nac
                        sum_mnt_tot_trb_isc_nac = - sum_mnt_tot_trb_isc_nac
                        sum_tot_otr = - sum_tot_otr
                        invoice_kh_importe_total = - invoice_kh_importe_total
                        tot_exportacion = - tot_exportacion

                    if invoice.state == 'cancel':
                        name_partner = 'Anulado'
                        taxable_base = 0.00
                        sum_tot_exo = 0.00
                        sum_tot_inf = 0.00
                        sum_mnt_tot_trb_igv_nac = 0.00
                        sum_mnt_tot_trb_isc_nac = 0.00
                        sum_tot_otr = 0.00
                        invoice_kh_importe_total = 0.00
                        tot_exportacion = 0.00

                    lines.append({
                        "name": invoice.id,
                        "columns": [{"name": invoice.date, 'class': 'date'},
                                    {"name": invoice.invoice_date_due, 'class': 'date'},
                                    {"name": invoice.l10n_latam_document_type_id.code}, {"name": invoice.serie_code},
                                    {"name": invoice.correlative}, {
                                        "name": invoice.partner_id.l10n_latam_identification_type_id.name or ''},
                                    {"name": invoice.partner_id.vat or ''}, {"name": name_partner or ''},
                                    {"name": "{0:.2f}".format(tot_exportacion), 'class': 'number'},
                                    {"name": "{0:.2f}".format(taxable_base), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_tot_exo), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_tot_inf), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_mnt_tot_trb_isc_nac), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_mnt_tot_trb_igv_nac), 'class': 'number'},
                                    {"name": "{0:.2f}".format(0.00), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_tot_otr), 'class': 'number'},
                                    {"name": "{0:.2f}".format(invoice_kh_importe_total), 'class': 'number'},
                                    {"name": invoice.exchange_rate},
                                    {"name": date_refund},
                                    {"name": type_refund},
                                    {"name": serie_refund},
                                    {"name": correlative_refund},
                                    {"name": invoice.state or ''},
                                    ],
                        "id": "invoice" + str(invoice.id),
                        "unfoldable": False,
                        "level": 3
                    })
        if b_type == 'purchase':
            types_doc = ["in_invoice", "in_refund"]
            array_values_initial = self.env["account.move"].sudo().search(
                [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
                 ('company_id', '=', res_company['id']), ('state', 'in', ['posted', 'cancel']),
                 ('move_type', 'in', types_doc), ('partner_id.country_id.code', '=', 'PE'),
                 ('show_book', '=', True)])
            for invoice in array_values_initial:
                # if (
                #         invoice.l10n_latam_document_type_id.code != "02" or invoice.l10n_latam_document_type_id.code == "00" or invoice.l10n_latam_document_type_id.code != "91" or invoice.l10n_latam_document_type_id.code != "97" or invoice.l10n_latam_document_type_id.code != "98") and (
                #         invoice.correlative is not False) and (
                #         invoice.serie_code is not False):
                if (
                        invoice.l10n_latam_document_type_id.code != "02" or invoice.l10n_latam_document_type_id.code == "00" or invoice.l10n_latam_document_type_id.code != "91" or invoice.l10n_latam_document_type_id.code != "97" or invoice.l10n_latam_document_type_id.code != "98") and (
                        invoice.correlative) and (invoice.serie_code) and (
                        invoice.l10n_latam_document_type_id.show_book):
                    options["count_purchase"] = 1
                    date_refund = ""
                    type_refund = ""
                    serie_refund = ""
                    correlative_refund = ""
                    if invoice.reversed_entry_id.invoice_date is not False:
                        refund_invoice = invoice.reversed_entry_id.invoice_date
                        date_refund = refund_invoice.strftime("%d/%m/%Y")
                        type_refund = invoice.reversed_entry_id.l10n_latam_document_type_id.code or ""
                        serie_refund = "%s" % invoice.reversed_entry_id.serie_code or ""
                        correlative_refund = "%s" % invoice.reversed_entry_id.correlative or ""
                        correlative_refund = correlative_refund.rjust(8, '0')
                        serie_refund = serie_refund.rjust(4, '0')
                    else:
                        if invoice.type_document_code in ['07', '08']:
                            if invoice.nc_nd_latam_document_type_id:
                                refund_invoice = invoice.nc_nd_date_emision
                                date_refund = refund_invoice.strftime("%d/%m/%Y")
                                type_refund = invoice.nc_nd_latam_document_type_id.code or ""
                                serie_refund = invoice.nc_nd_serie_code or ""
                                correlative_refund = invoice.nc_nd_correlative or ""
                    # Base imponible
                    sum_taxable_base = 0.00
                    # Monto Total del IGV GRAVADA
                    sum_mnt_tot_trb_igv_nac = 0.00
                    # Monto Total Gravadas y No Gravadas
                    sum_mnt_tot_grav_no_grav = 0.00
                    # Monto Total del IGV GRAVADA Y NO GRAVADA
                    sum_mnt_tot_grav_no_grav_igv = 0.00
                    # Monto Total de no gravadas
                    sum_mnt_tot_no_grav = 0.00
                    # Monto Total de igv no Gravado
                    sum_mnt_tot_no_grav_igv = 0.00
                    # Monto Excento
                    sum_mnt_excento = 0.00
                    # Monto Total del ISC
                    sum_mnt_tot_trb_isc_nac = 0.00

                    for line in invoice.line_ids:
                        # Igv
                        if line.tax_line_id.id is not False:
                            # MONTO TOTAL DEL IGV
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.credit
                                else:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.debit
                            # MONTO GRAVADO Y NO GRAVADO
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "grav_no_grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_grav_no_grav_igv = sum_mnt_tot_grav_no_grav_igv + line.credit
                                else:
                                    sum_mnt_tot_grav_no_grav_igv = sum_mnt_tot_grav_no_grav_igv + line.debit
                            # MONTO  NO GRAVADO
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "no_grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_no_grav_igv = sum_mnt_tot_no_grav_igv + line.credit
                                else:
                                    sum_mnt_tot_no_grav_igv = sum_mnt_tot_no_grav_igv + line.debit
                            # MONTO TOTAL DEL ISC
                            if line.tax_line_id.l10n_pe_edi_tax_code == "2000":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.credit
                                else:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.debit

                        # Base imponible
                        if line.tax_ids is not False:
                            for tax in line.tax_ids:
                                if tax.l10n_pe_edi_tax_code == '1000' and tax.tax_type_purchase == 'grav':
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_taxable_base = sum_taxable_base + line.credit
                                    else:
                                        sum_taxable_base = sum_taxable_base + line.debit
                                # GRAVADA Y NO GRAVADA
                                if tax.tax_type_purchase == "grav_no_grav":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_mnt_tot_grav_no_grav = sum_mnt_tot_grav_no_grav + line.credit
                                    else:
                                        sum_mnt_tot_grav_no_grav = sum_mnt_tot_grav_no_grav + line.debit
                                # NO GRAVADA
                                if tax.tax_type_purchase == "no_grav":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_mnt_tot_no_grav = sum_mnt_tot_no_grav + line.credit
                                    else:
                                        sum_mnt_tot_no_grav = sum_mnt_tot_no_grav + line.debit
                                # EXCENTO
                                if tax.tax_type_purchase == "excento":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_mnt_excento = sum_mnt_excento + line.credit
                                    else:
                                        sum_mnt_excento = sum_mnt_excento + line.debit
                    name_partner = invoice.partner_id.name or ''
                    invoice_kh_importe_total = abs(invoice.amount_total_signed)
                    taxable_base = sum_taxable_base
                    invoice_grav_no_grav = sum_mnt_tot_grav_no_grav
                    invoice_grav_no_grav_igv = sum_mnt_tot_grav_no_grav_igv
                    invoice_no_grav = sum_mnt_tot_no_grav
                    invoice_no_grav_igv = sum_mnt_tot_no_grav_igv
                    invoice_exento = sum_mnt_excento

                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                        taxable_base = - taxable_base
                        sum_mnt_tot_trb_igv_nac = -sum_mnt_tot_trb_igv_nac
                        invoice_grav_no_grav = - invoice_grav_no_grav
                        invoice_grav_no_grav_igv = - invoice_grav_no_grav_igv
                        invoice_no_grav = - invoice_no_grav
                        invoice_no_grav_igv = - invoice_no_grav_igv
                        invoice_exento = - invoice_exento
                        sum_mnt_tot_trb_isc_nac = -sum_mnt_tot_trb_isc_nac
                        invoice_kh_importe_total = - invoice_kh_importe_total

                    if invoice.state == 'cancel':
                        name_partner = 'Anulado'
                        taxable_base = 0.00
                        sum_mnt_tot_trb_igv_nac = 0.00
                        invoice_grav_no_grav = 0.00
                        invoice_grav_no_grav_igv = 0.00
                        invoice_no_grav = 0.00
                        invoice_no_grav_igv = 0.00
                        invoice_exento = 0.00
                        sum_mnt_tot_trb_isc_nac = 0.00
                        invoice_kh_importe_total = 0.00

                    # pago de la detraccion
                    reconciled_vals = invoice._get_payment_detraction_JSON_values()
                    detraccion_fecha_pago = ""
                    detraccion_numero = ""
                    if 'payment_id' in reconciled_vals:
                        detraccion_fecha_pago = reconciled_vals["detraction_date"]
                        detraccion_numero = reconciled_vals["detraction_number"]

                    lines.append({
                        "name": invoice.id,
                        "columns": [{"name": invoice.name or ''},
                                    {"name": invoice.invoice_date, 'class': 'date'},
                                    {"name": invoice.invoice_date_due, 'class': 'date'},
                                    {"name": invoice.l10n_latam_document_type_id.code or ''},
                                    {"name": invoice.serie_code},
                                    {"name": ''},
                                    {"name": invoice.correlative},
                                    {"name": invoice.partner_id.l10n_latam_identification_type_id.name or ''},
                                    {"name": invoice.partner_id.vat or ''}, {"name": name_partner or ''},
                                    {"name": "{0:.2f}".format(taxable_base), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_mnt_tot_trb_igv_nac), 'class': 'number'},
                                    {"name": "{0:.2f}".format(invoice_grav_no_grav), 'class': 'number'},
                                    {"name": "{0:.2f}".format(invoice_grav_no_grav_igv), 'class': 'number'},
                                    {"name": "{0:.2f}".format(invoice_no_grav), 'class': 'number'},
                                    {"name": "{0:.2f}".format(invoice_no_grav_igv), 'class': 'number'},
                                    {"name": "{0:.2f}".format(invoice_exento), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_mnt_tot_trb_isc_nac), 'class': 'number'},
                                    {"name": "{0:.2f}".format(0.00), 'class': 'number'},
                                    {"name": "{0:.2f}".format(0.00), 'class': 'number'},
                                    {"name": "{0:.2f}".format(invoice_kh_importe_total), 'class': 'number'},
                                    {"name": ''},
                                    {"name": detraccion_numero},
                                    {"name": detraccion_fecha_pago},
                                    {"name": invoice.exchange_rate or ''},
                                    {"name": date_refund or ''},
                                    {"name": type_refund or ''},
                                    {"name": serie_refund or ''},
                                    {"name": correlative_refund or ''},
                                    {"name": invoice.state},
                                    ],
                        "id": "invoice" + str(invoice.id),
                        "unfoldable": False,
                        "level": 3
                    })
        if b_type == 'non_domiciled':
            types_doc = ["in_invoice", "in_refund"]
            array_values_initial = self.env["account.move"].sudo().search(
                [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
                 ('company_id', '=', res_company['id']), ('state', 'in', ['posted', 'cancel']),
                 ('move_type', 'in', types_doc), ('partner_id.country_id.code', '!=', 'PE'),
                 ('show_book', '=', True)])
            for invoice in array_values_initial:
                if (
                        invoice.l10n_latam_document_type_id.code == "00" or invoice.l10n_latam_document_type_id.code == "91" or invoice.l10n_latam_document_type_id.code == "97" or invoice.l10n_latam_document_type_id.code == "98" or invoice.l10n_latam_document_type_id.code != "02") and (
                        invoice.correlative) and (invoice.serie_code) and (
                        invoice.l10n_latam_document_type_id.show_book):
                    options["count_purchase_no"] = 1
                    # Monto Total del IGV GRAVADA
                    sum_mnt_tot_trb_igv_nac = 0.00
                    for line in invoice.line_ids:
                        # Igv
                        if line.tax_line_id.id is not False:
                            # MONTO TOTAL DEL IGV
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.credit
                                else:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.debit
                    invoice_it_importe_total = abs(invoice.amount_total_signed)
                    name_partner = invoice.partner_id.name or ''
                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                        invoice_it_importe_total = - invoice_it_importe_total
                        sum_mnt_tot_trb_igv_nac = - sum_mnt_tot_trb_igv_nac
                    if invoice.state == 'cancel':
                        invoice_it_importe_total = 0.00
                        sum_mnt_tot_trb_igv_nac = 0.00
                        name_partner = "Anulado"

                    state = '0'
                    account_period = datetime.datetime.strptime(
                        options["date_to"], "%Y-%m-%d")
                    month = "%02d" % (account_period.month,)
                    date_comprobante = invoice.invoice_date
                    mes_comprobante = str(date_comprobante.year) + "" + str("%02d" % (date_comprobante.month))
                    mes_actual = str(account_period.year) + "" + str(month)
                    if mes_actual != mes_comprobante:
                        state = '9'
                    else:
                        state = '0'
                    lines.append({
                        "name": invoice.id,
                        "columns": [{"name": invoice.invoice_date, 'class': 'date'},
                                    {"name": invoice.l10n_latam_document_type_id.code or ''},
                                    {"name": invoice.serie_code},
                                    {"name": invoice.correlative},
                                    {"name": ''},
                                    {"name": ''},
                                    {"name": ''},
                                    {"name": "{0:.2f}".format(invoice_it_importe_total), 'class': 'number'},
                                    {"name": "{0:.2f}".format(sum_mnt_tot_trb_igv_nac), 'class': 'number'},
                                    {"name": 'PEN'},
                                    {"name": ""},
                                    {"name": invoice.partner_id.country_id.code},
                                    {"name": name_partner or ''},
                                    {"name": invoice.partner_id.street or ""},
                                    {"name": invoice.partner_id.vat or ""},
                                    {"name": invoice.partner_id.sunat_type_agreement.code or ''},
                                    {"name": "{0:.2f}".format(0.00), 'class': 'number'},
                                    {"name": state},
                                    {"name": invoice.state},
                                    ],
                        "id": "invoice" + str(invoice.id),
                        "unfoldable": False,
                        "level": 3
                    })
        return lines

    def get_xlsx(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name(data)[:31])

        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'align': 'center', })
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_1_number = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666',
             'num_format': '#,##0.00'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_number = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666',
             'num_format': '#,##0.00'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_number = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': '#,##0.00'})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        detail_general = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'font_color': '#666666', 'align': 'center'})
        line_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'align': 'start', })
        name_bold = workbook.add_format({'font_name': 'Arial', 'bold': True})

        # Set the first column width to 50
        # sheet.set_column(0, 0, 5)
        if data['book_type'] == 'sale':
            sheet.merge_range('E2:H2', _('SALE'), title_style)
            sheet.merge_range('E3:H3', _('General detail'), detail_general)
            sheet.merge_range('A8:K8', _('SALES REPORT'), line_style)
        elif data['book_type'] == 'purchase':
            sheet.merge_range('E2:H2', _('PURCHASE'), title_style)
            sheet.merge_range('E3:H3', _('General detail'), detail_general)
            sheet.merge_range('A8:K8', _('PURCHASE REPORT'), line_style)
        elif data['book_type'] == 'non_domiciled':
            sheet.merge_range('E2:H2', _('NON DOMICILED'), title_style)
            sheet.merge_range('E3:H3', _('General detail'), detail_general)
            sheet.merge_range('A8:K8', _('NON DOMICILED REPORT'), line_style)

        # company = self.env.user.company_id
        company = self.env["res.company"].sudo().browse(
            data["company_id"])
        image_data = io.BytesIO(base64.b64decode(company.logo))  # to convert it to base64 file
        sheet.insert_image('A3', 'logo', {'image_data': image_data, 'x_scale': 0.2, 'y_scale': 0.2})
        sheet.merge_range('D4:E4', _('Ruc:'), name_bold)
        sheet.merge_range('F4:G4', company.vat)
        sheet.merge_range('D5:E5', _('Address:'), name_bold)
        sheet.merge_range('F5:K5', company.street)
        sheet.merge_range('D6:E6', _('Mail:'), name_bold)
        sheet.merge_range('F6:G6', company.email)
        sheet.merge_range('H4:I4', _('Business name:'), name_bold)
        sheet.merge_range('J4:K4', company.name)
        sheet.merge_range('H6:I6', _('Phone:'), name_bold)
        sheet.merge_range('J6:K6', company.phone)

        sheet.merge_range('A9:C9', _('PERIOD:'), name_bold)
        sheet.merge_range('D9:F9',
                          _("from:") + " " + data['date_from'] + " " + _("to:") + " " + data['date_to'])
        sheet.merge_range('A10:C10', _('RUC:'), name_bold)
        sheet.merge_range('D10:F10', company.vat)
        sheet.merge_range('A11:C11', _('BUSINESS NAME:'), name_bold)
        sheet.merge_range('D11:F11', company.name)
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)
        sheet.set_column('O:O', 15)
        sheet.set_column('P:P', 15)

        y_offset = 13

        for row in self.get_header(data):
            x = 0
            for column in row:
                colspan = column.get('colspan', 1)
                header_label = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                if colspan == 1:
                    sheet.write(y_offset, x, header_label, title_style)
                else:
                    sheet.merge_range(y_offset, x, y_offset, x + colspan - 1, header_label, title_style)
                x += colspan
            y_offset += 1

        lines = self._get_lines(data)
        totales_y = 1
        tot_09, tot_10, tot_11, tot_12, tot_13, tot_14, tot_15, tot_16 = 0, 0, 0, 0, 0, 0, 0, 0
        tot_17, tot_18, tot_19, tot_20, tot_21, tot_22 = 0, 0, 0, 0, 0, 0

        # write all data rows
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
                style_number = level_1_number
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_2_col1_total_style or level_2_col1_style
                style_number = level_2_number
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_3_col1_total_style or level_3_col1_style
                style_number = level_3_number
            else:
                style = default_style
                col1_style = default_col1_style
                style_number = level_3_number

            # write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            totales_y = y + y_offset

            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            elif cell_type == 'number':
                sheet.write_number(y + y_offset, 0, cell_value, level_1_number)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            # write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if data['book_type'] != 'non_domiciled':
                    # if x + lines[y].get('colspan', 1) - 1 == 10:
                    #     tot_11 += float(cell_value)
                    if x + lines[y].get('colspan', 1) - 1 == 11:
                        tot_12 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 12:
                        tot_13 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 13:
                        tot_14 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 14:
                        tot_15 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 15:
                        tot_16 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 16:
                        tot_17 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 17:
                        tot_18 += float(cell_value)
                if data['book_type'] == 'sale':
                    if x + lines[y].get('colspan', 1) - 1 == 9:
                        tot_10 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 10:
                        tot_11 += float(cell_value)
                elif data['book_type'] == 'purchase':
                    if x + lines[y].get('colspan', 1) - 1 == 18:
                        tot_19 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 19:
                        tot_20 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 20:
                        tot_21 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 21:
                        tot_22 += float(cell_value)
                elif data['book_type'] == 'non_domiciled':
                    if x + lines[y].get('colspan', 1) - 1 == 8:
                        tot_09 += float(cell_value)
                    elif x + lines[y].get('colspan', 1) - 1 == 9:
                        tot_10 += float(cell_value)
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                elif cell_type == 'number':
                    sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1) - 1, float(cell_value),
                                       style_number)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)
        cell_format_tot = workbook.add_format({'bold': True, 'font_color': 'black'})
        if len(lines) > 0:
            if data['book_type'] != 'non_domiciled':
                sheet.write_number(totales_y + 1, 11, tot_12, cell_format_tot)
                sheet.write_number(totales_y + 1, 12, tot_13, cell_format_tot)
                sheet.write_number(totales_y + 1, 13, tot_14, cell_format_tot)
                sheet.write_number(totales_y + 1, 14, tot_15, cell_format_tot)
                sheet.write_number(totales_y + 1, 15, tot_16, cell_format_tot)
                sheet.write_number(totales_y + 1, 16, tot_17, cell_format_tot)
                sheet.write_number(totales_y + 1, 17, tot_18, cell_format_tot)
            if data['book_type'] == 'purchase':
                sheet.write_number(totales_y + 1, 18, tot_19, cell_format_tot)
                sheet.write_number(totales_y + 1, 19, tot_20, cell_format_tot)
                sheet.write_number(totales_y + 1, 20, tot_21, cell_format_tot)
                sheet.write_number(totales_y + 1, 21, tot_22, cell_format_tot)
            elif data['book_type'] == 'sale':
                sheet.write_number(totales_y + 1, 9, tot_10, cell_format_tot)
                sheet.write_number(totales_y + 1, 10, tot_11, cell_format_tot)
            elif data['book_type'] == 'non_domiciled':
                sheet.write_number(totales_y + 1, 8, tot_09, cell_format_tot)
                sheet.write_number(totales_y + 1, 9, tot_10, cell_format_tot)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_txt(self, options):
        b_type = options["book_type"]
        content = ""
        moves_json = self.get_moves_json(options)
        if b_type == 'sale':
            for move in moves_json:
                content += "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\r\n" % (
                    move['period'],  # campo 1
                    move['cuo'],  # campo 2
                    move['m_cuo'],  # campo 3
                    move['date_emission'],  # campo 4
                    move['expiration_date'],  # campo 5
                    move['receipt_type'],  # campo 6
                    move['serial_number'],  # campo 7
                    move['payment_number'],  # campo 8
                    move['allows_consolidation'],  # campo 9
                    move['document_type'],  # campo 10
                    move['card_number'],  # campo 11
                    move['business_name'],  # campo 12
                    move['invoiced_value'],  # campo 13
                    move['taxable_base'],  # campo 14
                    move['tax_base_discount'],  # campo 15
                    move['general_sales_tax'],  # campo 16
                    move['general_sales_tax_discount'],  # campo 17
                    move['total_amount_exonerated'],  # campo 18
                    move['total_amount_unaffected'],  # campo 19
                    move['tax_selective'],  # campo 20
                    move['tax_base_taxed'],  # campo 21
                    move['sales_tax'],  # campo 22
                    move['bags_tax'],  # campo 23
                    move['other_concepts'],  # campo 23
                    move['total_amount_payment'],  # campo 24
                    move['currency_code'],  # campo 25
                    move['exchange_rate'],  # campo 26
                    move['date_emission_payment'],  # campo 27
                    move['document_type_payment'],  # campo 28
                    move['serial_number_payment'],  # campo 29
                    move['card_number_payment'],  # campo 30
                    move['contract_identification'],  # campo 31
                    move['type_error'],  # campo 32
                    move['indicator_cancelled_payment'],  # campo 33
                    move['state'],  # campo 34
                    move['fields_free'],  # campo 35
                )
        if b_type == 'purchase':
            for move in moves_json:
                content += "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\r\n" % (
                    move['field_1'],  # campo 1
                    move['field_2'],  # campo 2
                    move['field_3'],  # campo 3
                    move['field_4'],  # campo 4
                    move['field_5'],  # campo 5
                    move['field_6'],  # campo 6
                    move['field_7'],  # campo 7
                    move['field_8'],  # campo 8
                    move['field_9'],  # campo 9
                    move['field_10'],  # campo 10
                    move['field_11'],  # campo 11
                    move['field_12'],  # campo 12
                    move['field_13'],  # campo 13
                    move['field_14'],  # campo 14
                    move['field_15'],  # campo 15
                    move['field_16'],  # campo 16
                    move['field_17'],  # campo 17
                    move['field_18'],  # campo 18
                    move['field_19'],  # campo 19
                    move['field_20'],  # campo 20
                    move['field_21'],  # campo 21
                    move['field_22'],  # campo 22
                    move['field_23'],  # campo 23
                    move['field_24'],  # campo 24
                    move['field_25'],  # campo 25
                    move['field_26'],  # campo 26
                    move['field_27'],  # campo 27
                    move['field_28'],  # campo 28
                    move['field_29'],  # campo 29
                    move['field_30'],  # campo 30
                    move['field_31'],  # campo 31
                    move['field_32'],  # campo 32
                    move['field_33'],  # campo 33
                    move['field_34'],  # campo 34
                    move['field_35'],  # campo 35
                    move['field_36'],  # campo 36
                    move['field_37'],  # campo 37
                    move['field_38'],  # campo 38
                    move['field_39'],  # campo 39
                    move['field_40'],  # campo 40
                    move['field_41'],  # campo 41
                    move['field_42'],  # campo 42
                    move['field_43'],  # campo 43
                )
        if b_type == 'non_domiciled':
            for move in moves_json:
                content += "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\r\n" % (
                    move['field_1'],  # campo 1
                    move['field_2'],  # campo 2
                    move['field_3'],  # campo 3
                    move['field_4'],  # campo 4
                    move['field_5'],  # campo 5
                    move['field_6'],  # campo 6
                    move['field_7'],  # campo 7
                    move['field_8'],  # campo 8
                    move['field_9'],  # campo 9
                    move['field_10'],  # campo 10
                    move['field_11'],  # campo 11
                    move['field_12'],  # campo 12
                    move['field_13'],  # campo 13
                    move['field_14'],  # campo 14
                    move['field_15'],  # campo 15
                    move['field_16'],  # campo 16
                    move['field_17'],  # campo 17
                    move['field_18'],  # campo 18
                    move['field_19'],  # campo 19
                    move['field_20'],  # campo 20
                    move['field_21'],  # campo 21
                    move['field_22'],  # campo 22
                    move['field_23'],  # campo 23
                    move['field_24'],  # campo 24
                    move['field_25'],  # campo 25
                    move['field_26'],  # campo 26
                    move['field_27'],  # campo 27
                    move['field_28'],  # campo 28
                    move['field_29'],  # campo 29
                    move['field_30'],  # campo 30
                    move['field_31'],  # campo 31
                    move['field_32'],  # campo 32
                    move['field_33'],  # campo 33
                    move['field_34'],  # campo 34
                    move['field_35'],  # campo 35
                    move['field_36'],  # campo 36
                    move['field_37'],  # campo 37
                )
        return content

    def get_moves_json(self, options):
        moves_json = []
        res_company = self.env["res.company"].sudo().browse(
            options["company_id"])
        b_type = options["book_type"]
        account_period = datetime.datetime.strptime(
            options["date_to"], "%Y-%m-%d")
        date_emission = ''
        expiration_date = ''
        document_type = '0'
        limit_date = self.env['ir.config_parameter'].sudo().search([('key', '=', 'limit_date_sunat')],
                                                                   limit=1)
        if b_type == 'sale':
            types_doc = ["out_invoice", "out_refund"]
            array_values_initial = self.env["account.move"].sudo().search(
                [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
                 ('company_id', '=', res_company['id']), ('state', 'in', ['posted', 'cancel']),
                 ('move_type', 'in', types_doc), ('show_book', '=', True)])
            for invoice in array_values_initial:
                if invoice.correlative and invoice.l10n_latam_document_type_id.show_book:  # and (invoice.it_sunat_state_code is not False):
                    date_refund = ""
                    type_refund = ""
                    serie_refund = ""
                    correlative_refund = ""
                    if invoice.reversed_entry_id.date is not False:
                        refund_invoice = invoice.reversed_entry_id.date
                        date_refund = refund_invoice.strftime("%d/%m/%Y")
                        type_refund = invoice.reversed_entry_id.l10n_latam_document_type_id.code or ""
                        serie_refund = "%s" % invoice.reversed_entry_id.serie_code or ""
                        correlative_refund = "%s" % invoice.reversed_entry_id.correlative or ""
                        correlative_refund = correlative_refund.rjust(8, '0')
                        serie_refund = serie_refund.rjust(4, '0')
                    else:
                        if invoice.l10n_latam_document_type_id.code in ['07', '08']:
                            if invoice.nc_nd_latam_document_type_id:
                                refund_invoice = invoice.nc_nd_date_emision
                                date_refund = refund_invoice.strftime("%d/%m/%Y")
                                type_refund = invoice.nc_nd_latam_document_type_id.code or ""
                                serie_refund = invoice.nc_nd_serie_code or ""
                                correlative_refund = invoice.nc_nd_correlative or ""

                    if invoice.date:
                        date = invoice.date
                        date_emission = date.strftime("%d/%m/%Y")
                    if invoice.invoice_date_due:
                        date = invoice.invoice_date_due
                        expiration_date = date.strftime("%d/%m/%Y")
                        delta = invoice.invoice_date_due - invoice.date
                        days = int(delta.days)
                        max_days = int(limit_date.value)
                        if days > max_days:
                            new_delta = invoice.invoice_date_due - timedelta(days=days - max_days)
                            expiration_date = new_delta.strftime("%d/%m/%Y")
                    if invoice.partner_id:
                        document_type = invoice.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
                    # Base imponible gravada:
                    sum_taxable_base = 0.00
                    # Monto Total del IGV
                    sum_mnt_tot_trb_igv_nac = 0.00
                    # Importe Total de las operaciones exoneradas
                    sum_tot_exo = 0.00
                    sum_tot_inf = 0.00
                    # Monto Total del ISC
                    sum_mnt_tot_trb_isc_nac = 0.00
                    # Otros conceptos
                    sum_tot_otr = 0.00
                    sum_tot_anti = 0.00
                    # Valor facturado exportacion
                    sum_exportacion = 0.00

                    for line in invoice.line_ids:
                        # Igv
                        if line.tax_line_id.id is not False:
                            # MONTO TOTAL DEL IGV
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.debit
                                else:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.credit
                            # MONTO TOTAL DEL ISC
                            if line.tax_line_id.l10n_pe_edi_tax_code == "2000":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.debit
                                else:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.credit
                        # Base imponible
                        if line.tax_ids is not False:
                            for tax in line.tax_ids:
                                if tax.l10n_pe_edi_tax_code == '1000' or tax.l10n_pe_edi_tax_code == '2000':
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_taxable_base = sum_taxable_base + line.debit
                                    else:
                                        if line.quantity > 0:
                                            sum_taxable_base = sum_taxable_base + line.credit
                                            if line.product_id:
                                                if line.product_id.default_code == 'DISC':
                                                    sum_taxable_base = sum_taxable_base - line.debit
                                        else:
                                            sum_taxable_base = sum_taxable_base - line.debit
                                            sum_tot_anti = sum_tot_anti + line.debit
                                if tax.l10n_pe_edi_tax_code == "9997":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_tot_exo = sum_tot_exo + line.debit
                                    else:
                                        sum_tot_exo = sum_tot_exo + line.credit
                                if tax.l10n_pe_edi_tax_code == "9998":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_tot_inf = sum_tot_inf + line.debit
                                    else:
                                        sum_tot_inf = sum_tot_inf + line.credit
                                if tax.l10n_pe_edi_tax_code == "9999":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_tot_otr = sum_tot_otr + line.debit
                                    else:
                                        sum_tot_otr = sum_tot_otr + line.credit
                                if tax.l10n_pe_edi_tax_code == "9995" and tax.l10n_pe_edi_affectation_reason == "40":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_exportacion = sum_exportacion + line.debit
                                    else:
                                        sum_exportacion = sum_exportacion + line.credit

                    name_partner = invoice.partner_id.name or ''

                    state = '0'
                    month = "%02d" % (account_period.month,)
                    date_comprobante = invoice.invoice_date
                    mes_comprobante = str(date_comprobante.year) + "" + str("%02d" % (date_comprobante.month))
                    mes_actual = str(account_period.year) + "" + str(month)
                    # mes_count = diff_month(account_period, date_comprobante)
                    if invoice.l10n_latam_document_type_id.code in ["02", "03", "10",
                                                                    "22"] and mes_actual == mes_comprobante:
                        state = '0'
                    if invoice.l10n_latam_document_type_id.code in ['01', '03', '07',
                                                                    '08'] and mes_actual == mes_comprobante:
                        state = '1'
                    if invoice.l10n_latam_document_type_id.code in ['01', '07'] and mes_actual != mes_comprobante:
                        state = '8'

                    taxable_base = sum_taxable_base
                    invoice_it_importe_total = abs(invoice.amount_total_signed)
                    tot_exportacion = sum_exportacion
                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                        taxable_base = - taxable_base
                        sum_mnt_tot_trb_igv_nac = - sum_mnt_tot_trb_igv_nac
                        sum_mnt_tot_trb_isc_nac = - sum_mnt_tot_trb_isc_nac
                        invoice_it_importe_total = - invoice_it_importe_total
                        sum_tot_exo = - sum_tot_exo
                        sum_tot_inf = - sum_tot_inf
                        sum_tot_otr = - sum_tot_otr
                        tot_exportacion = - tot_exportacion

                    if invoice.state == 'cancel':
                        state = '2'
                        name_partner = 'Anulado'
                        taxable_base = 0.00
                        sum_mnt_tot_trb_igv_nac = 0.00
                        sum_mnt_tot_trb_isc_nac = 0.00
                        sum_tot_exo = 0.00
                        sum_tot_inf = 0.00
                        sum_tot_otr = 0.00
                        invoice_it_importe_total = 0.00
                        tot_exportacion = 0.00

                    moves_json.append({
                        'period': "%s%s00" % (account_period.year, "%02d" % (account_period.month)),  # campo 1
                        'cuo': invoice.id,  # campo 2
                        'm_cuo': "M" + str(invoice.id) or "00",  # campo 3
                        'date_emission': date_emission,  # campo 4
                        'expiration_date': expiration_date,  # campo 5
                        'receipt_type': invoice.l10n_latam_document_type_id.code or '00',  # campo 6
                        'serial_number': invoice.serie_code or '0',  # campo 7
                        'payment_number': invoice.correlative or '0',  # campo 8
                        'allows_consolidation': '',  # campo 9
                        'document_type': document_type or '0',  # campo 10
                        'card_number': invoice.partner_id.vat or '00000000',  # campo 11
                        'business_name': name_partner or '',  # campo 12
                        'invoiced_value': "%.2f" % round(tot_exportacion, 2),  # campo 13
                        'taxable_base': "%.2f" % round(taxable_base, 2),  # campo 14
                        'tax_base_discount': 0.00,  # campo 15
                        'general_sales_tax': "%.2f" % round(sum_mnt_tot_trb_igv_nac, 2),  # campo 16
                        'general_sales_tax_discount': 0.00,  # campo 17
                        'total_amount_exonerated': "%.2f" % round(sum_tot_exo, 2),  # campo 18
                        'total_amount_unaffected': "%.2f" % round(sum_tot_inf, 2),  # campo 19
                        'tax_selective': "%.2f" % round(sum_mnt_tot_trb_isc_nac, 2),  # campo 20
                        'tax_base_taxed': "%.2f" % round(0, 2),  # campo 21
                        'sales_tax': "%.2f" % round(0, 2),  # campo 22
                        'bags_tax': "%.2f" % round(0, 2),  # campo 23
                        'other_concepts': "%.2f" % round(sum_tot_otr, 2),  # campo 23
                        'total_amount_payment': "%.2f" % round(invoice_it_importe_total, 2),  # campo 24
                        'currency_code': invoice.currency_id.name or 'PEN',  # campo 25
                        'exchange_rate': "%.3f" % invoice.exchange_rate,  # campo 26
                        'date_emission_payment': date_refund,  # campo 27
                        'document_type_payment': type_refund,  # campo 28
                        'serial_number_payment': serie_refund,  # campo 29
                        'card_number_payment': correlative_refund,  # campo 30
                        'contract_identification': '',  # campo 31
                        'type_error': '',  # campo 32
                        'indicator_cancelled_payment': '',  # campo 33
                        'state': state,  # campo 34
                        'fields_free': '',  # campo 35
                    })
        if b_type == 'purchase':
            types_doc = ["in_invoice", "in_refund"]
            array_values_initial = self.env["account.move"].sudo().search(
                [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
                 ('company_id', '=', res_company['id']), ('state', 'in', ['posted', 'cancel']),
                 ('move_type', 'in', types_doc), ('partner_id.country_id.code', '=', 'PE'), ('show_book', '=', True)])
            for invoice in array_values_initial:
                if (
                        invoice.l10n_latam_document_type_id.code != "02" or invoice.l10n_latam_document_type_id.code == "00" or invoice.l10n_latam_document_type_id.code != "91" or invoice.l10n_latam_document_type_id.code != "97" or invoice.l10n_latam_document_type_id.code != "98") and (
                        invoice.correlative) and (invoice.serie_code) and (
                        invoice.l10n_latam_document_type_id.show_book):
                    date_refund = ""
                    type_refund = ""
                    serie_refund = ""
                    correlative_refund = ""
                    if invoice.reversed_entry_id.invoice_date is not False:
                        refund_invoice = invoice.reversed_entry_id.invoice_date
                        date_refund = refund_invoice.strftime("%d/%m/%Y")
                        type_refund = invoice.reversed_entry_id.l10n_latam_document_type_id.code or ""
                        serie_refund = "%s" % invoice.reversed_entry_id.serie_code or ""
                        correlative_refund = "%s" % invoice.reversed_entry_id.correlative or ""
                        correlative_refund = correlative_refund.rjust(8, '0')
                        serie_refund = serie_refund.rjust(4, '0')
                    else:
                        if invoice.l10n_latam_document_type_id.code in ['07', '08']:
                            if invoice.nc_nd_latam_document_type_id:
                                refund_invoice = invoice.nc_nd_date_emision
                                date_refund = refund_invoice.strftime("%d/%m/%Y")
                                type_refund = invoice.nc_nd_latam_document_type_id.code or ""
                                serie_refund = invoice.nc_nd_serie_code or ""
                                correlative_refund = invoice.nc_nd_correlative or ""
                    if invoice.invoice_date:
                        date = invoice.invoice_date
                        date_emission = date.strftime("%d/%m/%Y")
                    if invoice.invoice_date_due:
                        date = invoice.invoice_date_due
                        expiration_date = date.strftime("%d/%m/%Y")
                        delta = invoice.invoice_date_due - invoice.date
                        days = int(delta.days)
                        max_days = int(limit_date.value)
                        if days > max_days:
                            new_delta = invoice.invoice_date_due - timedelta(days=days - max_days)
                            expiration_date = new_delta.strftime("%d/%m/%Y")
                    date_dua = ''
                    if invoice.l10n_latam_document_type_id.code in ['50', '52']:
                        # date_inv = datetime.datetime.strptime(str(invoice.date), "%Y-%m-%d")
                        # date_dua = str(date_inv.year)
                        date_inv = invoice.date
                        date_dua = date_inv.strftime('%Y')
                    if invoice.partner_id:
                        document_type = invoice.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code

                    # Base imponible
                    sum_taxable_base = 0.00
                    # Monto Total del IGV GRAVADA
                    sum_mnt_tot_trb_igv_nac = 0.00
                    # Monto Total Gravadas y No Gravadas
                    sum_mnt_tot_grav_no_grav = 0.00
                    # Monto Total del IGV GRAVADA Y NO GRAVADA
                    sum_mnt_tot_grav_no_grav_igv = 0.00
                    # Monto Total de no gravadas
                    sum_mnt_tot_no_grav = 0.00
                    # Monto Total de igv no Gravado
                    sum_mnt_tot_no_grav_igv = 0.00
                    # Monto Excento
                    sum_mnt_excento = 0.00
                    # Monto Total del ISC
                    sum_mnt_tot_trb_isc_nac = 0.00
                    otros_impuestos_22 = 0.00
                    otros_impuestos_23 = 0.00

                    for line in invoice.line_ids:
                        # Igv
                        if line.tax_line_id.id is not False:
                            # MONTO TOTAL DEL IGV
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.credit
                                else:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.debit
                            # MONTO GRAVADO Y NO GRAVADO
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "grav_no_grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_grav_no_grav_igv = sum_mnt_tot_grav_no_grav_igv + line.credit
                                else:
                                    sum_mnt_tot_grav_no_grav_igv = sum_mnt_tot_grav_no_grav_igv + line.debit
                            # MONTO  NO GRAVADO
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "no_grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_no_grav_igv = sum_mnt_tot_no_grav_igv + line.credit
                                else:
                                    sum_mnt_tot_no_grav_igv = sum_mnt_tot_no_grav_igv + line.debit
                            # MONTO TOTAL DEL ISC
                            if line.tax_line_id.l10n_pe_edi_tax_code == "2000":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.credit
                                else:
                                    sum_mnt_tot_trb_isc_nac = sum_mnt_tot_trb_isc_nac + line.debit

                        # Base imponible
                        if line.tax_ids is not False:
                            for tax in line.tax_ids:
                                if tax.l10n_pe_edi_tax_code == '1000' and tax.tax_type_purchase == 'grav':
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_taxable_base = sum_taxable_base + line.credit
                                    else:
                                        sum_taxable_base = sum_taxable_base + line.debit

                                if tax.l10n_pe_edi_tax_code == '9999' and not tax.tax_plastic:
                                    otros_impuestos_23 = otros_impuestos_23 + line.price_total
                                if tax.l10n_pe_edi_tax_code == '9999' and tax.tax_plastic:
                                    otros_impuestos_22 = otros_impuestos_22 + line.price_total

                                # GRAVADA Y NO GRAVADA
                                if tax.tax_type_purchase == "grav_no_grav":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_mnt_tot_grav_no_grav = sum_mnt_tot_grav_no_grav + line.credit
                                    else:
                                        sum_mnt_tot_grav_no_grav = sum_mnt_tot_grav_no_grav + line.debit
                                # NO GRAVADA
                                if tax.tax_type_purchase == "no_grav":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_mnt_tot_no_grav = sum_mnt_tot_no_grav + line.credit
                                    else:
                                        sum_mnt_tot_no_grav = sum_mnt_tot_no_grav + line.debit
                                # EXCENTO
                                if tax.tax_type_purchase == "excento":
                                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                        sum_mnt_excento = sum_mnt_excento + line.credit
                                    else:
                                        sum_mnt_excento = sum_mnt_excento + line.debit
                    name_partner = invoice.partner_id.name or ''
                    state = '0'
                    month = "%02d" % (account_period.month,)
                    date_comprobante = invoice.invoice_date
                    mes_comprobante = str(date_comprobante.year) + "" + str("%02d" % (date_comprobante.month))
                    mes_actual = str(account_period.year) + "" + str(month)
                    mes_count = diff_month(account_period, date_comprobante)
                    if invoice.l10n_latam_document_type_id.code in ["02", "10"] and mes_actual == mes_comprobante:
                        state = '0'
                    if invoice.l10n_latam_document_type_id.code in ['01', '03'] and mes_actual == mes_comprobante:
                        state = '1'
                    if invoice.l10n_latam_document_type_id.code in ['01',
                                                                    '07'] and mes_actual != mes_comprobante and mes_count <= 12:
                        state = '6'
                    if mes_actual != mes_comprobante and mes_count > 12:
                        state = '7'
                    invoice_it_importe_total = abs(invoice.amount_total_signed)
                    taxable_base = sum_taxable_base
                    invoice_grav_no_grav = sum_mnt_tot_grav_no_grav
                    invoice_grav_no_grav_igv = sum_mnt_tot_grav_no_grav_igv
                    invoice_no_grav = sum_mnt_tot_no_grav
                    invoice_no_grav_igv = sum_mnt_tot_no_grav_igv
                    invoice_exento = sum_mnt_excento

                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                        taxable_base = - taxable_base
                        sum_mnt_tot_trb_igv_nac = -sum_mnt_tot_trb_igv_nac
                        invoice_grav_no_grav = - invoice_grav_no_grav
                        invoice_grav_no_grav_igv = - invoice_grav_no_grav_igv
                        invoice_no_grav = - invoice_no_grav
                        invoice_no_grav_igv = - invoice_no_grav_igv
                        invoice_exento = - invoice_exento
                        sum_mnt_tot_trb_isc_nac = -sum_mnt_tot_trb_isc_nac
                        invoice_it_importe_total = - invoice_it_importe_total
                    if invoice.state == 'cancel':
                        state = '2'
                        name_partner = 'Anulado'
                        taxable_base = 0.00
                        sum_mnt_tot_trb_igv_nac = float(0.00)
                        invoice_grav_no_grav = float(0.00)
                        invoice_grav_no_grav_igv = float(0.00)
                        invoice_no_grav = float(0.00)
                        invoice_no_grav_igv = float(0.00)
                        invoice_exento = float(0.00)
                        sum_mnt_tot_trb_isc_nac = float(0.00)
                        invoice_it_importe_total = float(0.00)

                    # pago de la detraccion
                    reconciled_vals = invoice._get_payment_detraction_JSON_values()
                    detraccion_fecha_pago = ""
                    detraccion_numero = ""
                    if 'payment_id' in reconciled_vals:
                        detraccion_fecha_pago = reconciled_vals["detraction_date"]
                        detraccion_numero = reconciled_vals["detraction_number"]

                    moves_json.append({
                        'field_1': "%s%s00" % (account_period.year, "%02d" % (account_period.month)),  # campo 1
                        'field_2': invoice.id,  # campo 2
                        'field_3': "M" + str(invoice.id) or "00",  # campo 3
                        'field_4': date_emission,  # campo 4
                        'field_5': expiration_date,  # campo 5
                        'field_6': invoice.type_document_code or '00',  # campo 6
                        'field_7': invoice.serie_code or '0',  # campo 7
                        'field_8': date_dua or '',  # campo 8
                        'field_9': invoice.correlative or '0',  # campo 9
                        'field_10': '',  # campo 10
                        'field_11': document_type or '0',  # campo 11
                        'field_12': invoice.partner_id.vat or '00000000',  # campo 12
                        'field_13': name_partner or '',  # campo 13
                        'field_14': "%.2f" % round(taxable_base, 2),  # campo 14
                        'field_15': "%.2f" % round(sum_mnt_tot_trb_igv_nac, 2),  # campo 15
                        'field_16': "%.2f" % round(invoice_grav_no_grav, 2),  # campo 16
                        'field_17': "%.2f" % round(invoice_grav_no_grav_igv, 2),  # campo 17
                        'field_18': "%.2f" % round(invoice_no_grav, 2),  # campo 18
                        'field_19': "%.2f" % round(invoice_no_grav_igv, 2),  # campo 19
                        'field_20': "%.2f" % round(invoice_exento, 2),  # campo 20
                        'field_21': "%.2f" % round(sum_mnt_tot_trb_isc_nac, 2),  # campo 21
                        'field_22': "%.2f" % round(otros_impuestos_22, 2),  # campo 22
                        'field_23': "%.2f" % round(otros_impuestos_23, 2),  # campo 23
                        'field_24': "%.2f" % round(invoice_it_importe_total, 2),  # campo 24
                        'field_25': invoice.currency_id.name or 'PEN',  # campo 25
                        'field_26': "%.3f" % invoice.exchange_rate,  # campo 26
                        'field_27': date_refund or '',  # campo 27
                        'field_28': type_refund or '',  # campo 28
                        'field_29': serie_refund.rjust(4, '0') or '0000',  # campo 29
                        'field_30': '',  # campo 30
                        'field_31': correlative_refund.rjust(8, '0') or '00000000',  # campo 31
                        'field_32': detraccion_fecha_pago or '',  # campo 32
                        'field_33': detraccion_numero or '',  # campo 33
                        'field_34': '',  # campo 34
                        'field_35': '',  # campo 35
                        'field_36': '',  # campo 36
                        'field_37': '',  # campo 37
                        'field_38': '',  # campo 38
                        'field_39': '',  # campo 39
                        'field_40': '',  # campo 40
                        'field_41': '',  # campo 41
                        'field_42': state,  # campo 42
                        'field_43': '',  # campo 43
                    })
        if b_type == 'non_domiciled':
            types_doc = ["in_invoice", "in_refund"]
            array_values_initial = self.env["account.move"].sudo().search(
                [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
                 ('company_id', '=', res_company['id']), ('state', 'in', ['posted', 'cancel']),
                 ('move_type', 'in', types_doc), ('partner_id.country_id.code', '!=', 'PE'), ('show_book', '=', True)])
            for invoice in array_values_initial:
                if (
                        invoice.l10n_latam_document_type_id.code == "00" or invoice.l10n_latam_document_type_id.code == "91" or invoice.l10n_latam_document_type_id.code == "97" or invoice.l10n_latam_document_type_id.code == "98" or invoice.l10n_latam_document_type_id.code != "02") and (
                        invoice.correlative) and (invoice.serie_code) and (
                        invoice.l10n_latam_document_type_id.show_book):
                    if invoice.invoice_date:
                        date = invoice.invoice_date
                        date_emission = date.strftime("%d/%m/%Y")

                    # Monto Total del IGV GRAVADA
                    sum_mnt_tot_trb_igv_nac = 0.00
                    for line in invoice.line_ids:
                        # Igv
                        if line.tax_line_id.id is not False:
                            # MONTO TOTAL DEL IGV
                            if line.tax_line_id.l10n_pe_edi_tax_code == "1000" and line.tax_line_id.tax_type_purchase == "grav":
                                if invoice.l10n_latam_document_type_id.tax_decrease is True:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.credit
                                else:
                                    sum_mnt_tot_trb_igv_nac = sum_mnt_tot_trb_igv_nac + line.debit

                    invoice_it_importe_total = abs(invoice.amount_total_signed)
                    name_partner = invoice.partner_id.name or ''
                    if invoice.l10n_latam_document_type_id.tax_decrease is True:
                        invoice_it_importe_total = - invoice_it_importe_total
                        sum_mnt_tot_trb_igv_nac = - sum_mnt_tot_trb_igv_nac
                    if invoice.state == 'cancel':
                        invoice_it_importe_total = float(0.00)
                        sum_mnt_tot_trb_igv_nac = float(0.00)
                        name_partner = "Anulado"
                    state = '0'
                    month = "%02d" % (account_period.month,)
                    date_comprobante = invoice.invoice_date
                    mes_comprobante = str(date_comprobante.year) + "" + str("%02d" % (date_comprobante.month))
                    mes_actual = str(account_period.year) + "" + str(month)
                    if mes_actual != mes_comprobante:
                        state = '9'
                    else:
                        state = '0'
                    moves_json.append({
                        'field_1': "%s%s00" % (account_period.year, "%02d" % (account_period.month)),  # campo 1
                        'field_2': invoice.id,  # campo 2
                        'field_3': "M" + str(invoice.id) or "00",  # campo 3
                        'field_4': date_emission,  # campo 4
                        'field_5': invoice.l10n_latam_document_type_id.code or '00',  # campo 5
                        'field_6': invoice.serie_code or '0',  # campo 6
                        'field_7': invoice.correlative or '0',  # campo 7
                        'field_8': '',  # campo 8
                        'field_9': '',  # campo 9
                        'field_10': "%.2f" % round(invoice_it_importe_total, 2),  # campo 10
                        'field_11': '',  # campo 11
                        'field_12': '',  # campo 12
                        'field_13': '',  # campo 13
                        'field_14': '',  # campo 14
                        'field_15': "%.2f" % round(sum_mnt_tot_trb_igv_nac, 2),  # campo 15
                        'field_16': invoice.currency_id.name or 'PEN',  # campo 16
                        'field_17': "%.3f" % round(invoice.exchange_rate, 3),  # campo 17
                        'field_18': invoice.partner_id.country_id.code_sunat or 'PE',  # campo 18
                        'field_19': name_partner or '',  # campo 19
                        'field_20': invoice.partner_id.street or '',  # campo 20
                        'field_21': invoice.partner_id.vat or '',  # campo 21
                        'field_22': '',  # campo 22
                        'field_23': '',  # campo 23
                        'field_24': '',  # campo 24
                        'field_25': '',  # campo 25
                        'field_26': '',  # campo 26
                        'field_27': '',  # campo 27
                        'field_28': '',  # campo 28
                        'field_29': '',  # campo 29
                        'field_30': '',  # campo 30
                        'field_31': invoice.partner_id.sunat_type_agreement.code or '00',  # campo 31
                        'field_32': '',  # campo 32
                        'field_33': '00',  # campo 33
                        'field_34': '',  # campo 34
                        'field_35': '',  # campo 35
                        'field_36': state,  # campo 36
                        'field_37': '',  # campo 37
                    })
        return moves_json

    @api.model
    def get_name_xlsx(self, options):
        xlsx_name = ""
        account_period = datetime.datetime.strptime(
            options["date_to"], "%Y-%m-%d")
        b_type = options["book_type"]
        if b_type == 'sale':
            name = "Record sale"
            xlsx_name = "%s%s%s%s%s" % (name, " - ", account_period.strftime("%B"), " ", account_period.year)
        if b_type == 'purchase':
            name = "Purchase record"
            xlsx_name = "%s%s%s%s%s" % (name, " - ", account_period.strftime("%B"), " ", account_period.year)
        if b_type == 'non_domiciled':
            name = "Registration of purchase subject not domiciled"
            xlsx_name = "%s%s%s%s%s" % (name, " - ", account_period.strftime("%B"), " ", account_period.year)
        return xlsx_name

    @api.model
    def get_name_txt(self, options):
        count_sale = options['count_report']  # options['count_sale'] or 0
        count_purchase = options['count_report']  # options['count_purchase'] or 0
        count_purchase_no = options['count_report']  # options['count_purchase_no'] or 0
        res_company = self.env["res.company"].sudo().browse(
            options["company_id"])
        account_period = datetime.datetime.strptime(
            options["date_to"], "%Y-%m-%d")
        month = "%02d" % (account_period.month)
        b_type = options["book_type"]
        txt_name = ''
        if b_type == 'sale':
            txt_name = "%s%s%s%s%s%s%s%s%s%s%s" % (
                "LE",
                res_company.partner_id.vat,
                account_period.year,
                month,
                '00',
                '140100',
                '00',
                '1',
                str(count_sale),
                '1',
                '1'
            )
        if b_type == 'purchase':
            txt_name = '%s%s%s%s%s%s%s%s%s%s%s' % (
                "LE",
                res_company.partner_id.vat,
                account_period.year,
                month,
                '00',
                '080100',
                '00',
                '1',
                str(count_purchase),
                '1',
                '1'
            )
        if b_type == 'non_domiciled':
            txt_name = '%s%s%s%s%s%s%s%s%s%s%s' % (
                "LE",
                res_company.partner_id.vat,
                account_period.year,
                month,
                '00',
                '080200',
                '00',
                '1',
                str(count_purchase_no),
                '1',
                '1'
            )
        return txt_name

    def get_report_filename(self, options):
        if 'txt' in options:
            report_name = self.get_name_txt(options)
        elif 'excel' in options:
            report_name = self.get_name_xlsx(options)
        return report_name

    def export_excel(self):
        if self.date_from > self.date_to:
            raise UserError(_("The Start date cannot be less than the end date "))
        else:
            data = {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'company_id': self.company_id.id,
                'book_type': self.book_type,
                'excel': 'excel'
            }
            return {
                'type': 'ir.actions.client',
                'report_type': 'xlsx_txt',
                'data': {'model': 'report.account.books',
                         'options': json.dumps(data, default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Excel Report',
                         }
            }

    def export_txt(self):
        if self.date_from > self.date_to:
            raise UserError(_("The Start date cannot be less than the end date "))
        else:
            data = {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'company_id': self.company_id.id,
                'book_type': self.book_type,
                'txt': 'txt'
            }

            return {
                'type': 'ir.actions.client',
                'report_type': 'xlsx_txt',
                'data': {'model': 'report.account.books',
                         'options': json.dumps(data, default=date_utils.json_default),
                         'output_format': 'txt',
                         'report_name': 'txt report',
                         }
            }
