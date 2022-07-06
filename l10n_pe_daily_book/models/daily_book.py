# -*- coding: utf-8 -*-
import io
import json
import logging
import datetime
import calendar
import base64
from odoo.exceptions import UserError
from odoo.tools import config, date_utils, get_lang
from odoo import models, _, api, fields

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


def column_name_daily_book():
    return [{'name': _("CUO")},
            {'name': _("Date"), 'class': 'date'},
            {'name': _("Operation Description")},
            {'name': _("Book code")},
            {'name': _("Number correlative")},
            {'name': _("Series")},
            {'name': _("Account code")},
            {'name': _("Denomination")},
            {'name': _("Debit"), 'class': 'number'},
            {'name': _("Credit"), 'class': 'number'},
            ]


class ReportDailyBook(models.Model):
    _name = 'report.daily.book'
    _description = "report of daily book"

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

    BOOK_TYPE = [('daily_book', _('Daily Book')), ('plain_account', _('Plain Account'))]

    name = fields.Char(string="Name", required=True)
    date_from = fields.Date(string='Date from', default=_get_from_date, required=True, )
    date_to = fields.Date(string='Date to', default=_get_date_to, required=True, )
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id,
                                 string='Company')
    book_type = fields.Selection(BOOK_TYPE, default='daily_book', required=True, string='Book Type')

    @api.model
    def _get_report_name(self, options):
        name_sheet = ""
        if options['book_type'] == 'daily_book':
            name_sheet = _('Daily book')
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
        if b_type == 'daily_book':
            return column_name_daily_book()

    def _get_lines(self, options):
        lines = []
        diary_count = '0'
        # OBTENER LA CABECERA
        array_values_initial = self.env["account.move"].sudo().search(
            [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
             ('company_id', '=', options['company_id'])])
        account_period = datetime.datetime.strptime(
            options["date_to"], "%Y-%m-%d")
        for account in array_values_initial:
            cod_libro = ''
            for line in account.line_ids.filtered(lambda s: s.display_type not in ['line_section', 'line_note']):
                if line.parent_state == 'posted':
                    diary_count = '1'
                    invoice = account
                    move_id = line.id
                    # VENTAS
                    if (invoice.move_type == "out_invoice" or invoice.move_type == "out_refund") and (
                            invoice.state == "posted" or invoice.state == "cancel") and (
                            invoice.correlative is not False):
                        cod_libro = "140100" + "&" + str(
                            str(account_period.year) + "" + str(
                                "%02d" % (account_period.month,)) + "00", ) + "&" + str(
                            move_id) + "&" + str(str("M") + str(move_id))
                    # COMPRAS
                    if (invoice.move_type == "in_invoice" or invoice.move_type == "in_refund") and (
                            invoice.l10n_latam_document_type_id.code != "02") and (
                            invoice.state == "posted" or invoice.state == "cancel") and (
                            account.correlative is not False) and (
                            account.serie_code is not False) and (
                            invoice.l10n_latam_document_type_id.code == "00" or invoice.l10n_latam_document_type_id.code != "91"
                            or invoice.l10n_latam_document_type_id.code != "97" or invoice.l10n_latam_document_type_id.code != "98" or invoice.l10n_latam_document_type_id.code != "02"):
                        cod_libro = "080100" + "&" + str(
                            str(account_period.year) + "" + str(
                                "%02d" % (account_period.month,)) + "00", ) + "&" + str(
                            move_id) + "&" + str(str("M") + str(move_id))

                    # COMPRAS SUJETOS A DOMICILIADOS
                    if (invoice.move_type == "in_invoice" or invoice.move_type == "in_refund") and (
                            invoice.l10n_latam_document_type_id.code != "02") and (
                            invoice.state == "posted" or invoice.state == "cancel") and (
                            account.correlative is not False) and (
                            account.serie_code is not False) and (
                            invoice.l10n_latam_document_type_id.code == "00" or invoice.l10n_latam_document_type_id.code == "91"
                            or invoice.l10n_latam_document_type_id.code == "97" or invoice.l10n_latam_document_type_id.code == "98"):
                        cod_libro = "080200" + "&" + str(
                            str(account_period.year) + "" + str(
                                "%02d" % (account_period.month,)) + "00", ) + "&" + str(
                            move_id) + "&" + str(str("M") + str(move_id))

                    serie = '0'
                    if invoice.serie_code:
                        serie = invoice.serie_code or ''
                    else:
                        serie = invoice.serie_code or ''

                    correlative = '0'
                    if invoice.correlative:
                        correlative = invoice.correlative or ''

                    lines.append({
                        "name": account.id,
                        "columns": [
                            {
                                "name": account.date or '',
                                'class': 'date'
                            },
                            {
                                "name": str(line.name) or ''
                            },
                            {
                                "name": cod_libro or ''
                            },
                            {
                                "name": line.name or ''
                            },
                            {
                                "name": serie or '0' + '-' + correlative
                            },
                            {
                                "name": line.account_id.code or ''
                            },
                            {
                                "name": str(line.account_id.name) or ''
                            },
                            {
                                "name": line.debit or ''
                            },
                            {
                                "name": line.credit or ''
                            },
                        ],
                        "id": "move" + str(line),
                        "unfoldable": False,
                        "level": 3
                    })

        options['diary_count'] = diary_count
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
        if data['book_type'] == 'daily_book':
            sheet.merge_range('E2:H2', _('Daily Book'), title_style)
            sheet.merge_range('E3:H3', _('General detail'), detail_general)
            sheet.merge_range('A8:K8', _('DAILY BOOK REPORT'), line_style)

        company = self.env.user.company_id
        image_data = io.BytesIO(base64.b64decode(company.logo))  # to convert it to base64 file
        sheet.insert_image('A3', 'logo', {'image_data': image_data, 'x_scale': 0.5, 'y_scale': 0.5})
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
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            elif cell_type == 'number':
                sheet.write_number(y + y_offset, 0, cell_value, level_1_number)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            # write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                elif cell_type == 'number':
                    sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style_number)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def get_name_xlsx(self, options):
        xlsx_name = ""
        account_period = datetime.datetime.strptime(
            options["date_to"], "%Y-%m-%d")
        b_type = options["book_type"]
        if b_type == 'daily_book':
            name = "Daily Book"
            xlsx_name = "%s%s%s%s%s" % (name, " - ", account_period.strftime("%B"), " ", account_period.year)
        return xlsx_name

    def get_txt(self, options):
        if options["book_type"] == 'plain_account':
            content = ""
            moves_json = self.get_moves_json(options)
            for move in moves_json:
                content += "%s|%s|%s|%s|%s|%s|%s|%s|\r\n" % (
                    move['time_frame'],
                    move['account_code'],
                    move['account_description'],
                    move['plain_code'],
                    move['plain_description'],
                    move['account_code_coorp'],
                    move['account_description_coorp'],
                    move['operation_status'],
                )
            return content
        else:
            content = ""
            moves_json = self.get_moves_json(options)
            for move in moves_json:
                content += "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\r\n" % (
                    move["periodo"],
                    move["cuo"],
                    move["account_correlative"],
                    move["code_account"],
                    move["code_unit"],
                    move["code_cost"],
                    move["type_currency"],
                    move["type_document_identity"],
                    move["document_number_identity"],
                    move["type_document"],
                    move["serial_number"],
                    move["correlative_document"],
                    move["accounting_date"],
                    move["expiration_date"],
                    move["date_of_issue"],
                    move["description"],
                    move["reference"],
                    move["debit"],
                    move["credit"],
                    move["book_code"],
                    move["status_operation"],
                )
            return content

    def new_line(self, linea):
        # return linea.strip()
        resultado = linea.splitlines()
        new_string = ""
        new_string2 = ""
        if len(resultado) - 1 > 0:
            s = str(resultado)
            ss = s[1:-1]
            sss = ss.replace("'", '')
            new_string = sss.rstrip('\n')
        else:
            new_string = linea.rstrip('\n')
        new_string2 = new_string.strip()
        return new_string2

    def get_moves_json(self, options):
        if options["book_type"] == 'plain_account':
            res_company = self.env["res.company"].sudo().browse(
                options["company_id"])
            moves_json = []
            array_values_initial = self.env["account.account"].sudo().search(
                [('company_id', '=', res_company['id']), ("write_date", ">=", options["date_from"]),
                 ("write_date", "<=", options["date_to"]), ('deprecated', '=', False)])
            account_period = datetime.datetime.strptime(
                options["date_to"], "%Y-%m-%d")
            account_period_from = datetime.datetime.strptime(
                options["date_from"], "%Y-%m-%d")
            mes = "%02d" % (account_period.month)
            plain_code = '01'  # res_company.it_account_plan_code
            if (mes == '01'):
                array_values_initial = self.env["account.account"].sudo().search(
                    [('company_id', '=', res_company['id']), ('deprecated', '=', False)])
                for operation in array_values_initial:
                    moves_json.append({
                        "time_frame": "%s%s%s" % (
                            account_period.year, "%02d" % (account_period.month), "%02d" % (account_period.day)),
                        # CAMPO 1: PERIODO
                        # CAMPO 2: CODIGO DE LA CUENTA
                        "account_code": operation.code[:24] or '',
                        "account_description": operation.name[:100] or '',  # CAMPO 3: DESCRIPCION DE LA CUENTA
                        "plain_code": plain_code or '',  # CAMPO 4: CODIGO DE PLAN DE CUENTAS
                        "plain_description": '',  # CAMPO 5: DESCRIPCION DE PLAN DE CUENTAS
                        "account_code_coorp": '',  # CAMPO 6: CODIGO DE LA CUENTA COORPORATIVA
                        "account_description_coorp": '',  # CAMPO 7: DESCRIPCION DE LA CUENTA COORPORATIVA
                        "operation_status": '1',  # CAMPO 8:
                    })
            else:
                if (len(array_values_initial) > 0):
                    array_values_initial = self.env["account.account"].sudo().search(
                        [('company_id', '=', res_company['id']), ('deprecated', '=', False)])
                    for operation in array_values_initial:
                        moves_json.append({
                            "time_frame": "%s%s%s" % (
                                account_period.year, "%02d" % (account_period.month), "%02d" % (account_period.day)),
                            # CAMPO 1: PERIODO
                            # CAMPO 2: CODIGO DE LA CUENTA
                            "account_code": operation.code[:24] or '',
                            "account_description": operation.name[:100] or '',  # CAMPO 3: DESCRIPCION DE LA CUENTA
                            "plain_code": plain_code or '',  # CAMPO 4: CODIGO DE PLAN DE CUENTAS
                            "plain_description": '',  # CAMPO 5: DESCRIPCION DE PLAN DE CUENTAS
                            "account_code_coorp": '',  # CAMPO 6: CODIGO DE LA CUENTA COORPORATIVA
                            "account_description_coorp": '',  # CAMPO 7: DESCRIPCION DE LA CUENTA COORPORATIVA
                            "operation_status": '1',  # CAMPO 8:
                        })

            return moves_json
        else:
            res_company = self.env["res.company"].sudo().browse(
                options["company_id"])
            moves_json = []
            array_values_initial = self.env["account.move"].sudo().search(
                [("date", ">=", options["date_from"]), ("date", "<=", options["date_to"]),
                 ('company_id', '=', res_company['id'])])
            # FIELD FOR THE REPORT
            account_period = datetime.datetime.strptime(
                options["date_to"], "%Y-%m-%d")
            contador = 0

            for account in array_values_initial:
                cont = 0
                for line in account.line_ids.filtered(lambda s: s.display_type not in ['line_section', 'line_note']):
                    date_account = ''
                    expiration_date = ''
                    broadcast_date = ''
                    cod_libro = ''
                    if line.parent_state == 'posted':
                        cont += 1
                        invoice = account
                        move_id = line.id
                        # VENTAS
                        if invoice.move_type in ['out_invoice', 'out_refund'] and invoice.state in ['posted',
                                                                                                    'cancel'] and invoice.correlative is not False and account.show_book is True:
                            cod_libro = "140100" + "&" + str(
                                str(account_period.year) + "" + str(
                                    "%02d" % (account_period.month,)) + "00", ) + "&" + str(
                                account.id) + "&" + str(str("M") + str(account.id))
                        # COMPRAS
                        if invoice.move_type in ['in_invoice', 'in_refund'] and invoice.state in ['posted',
                                                                                                  'cancel'] and account.correlative is not False and account.show_book is True and invoice.l10n_latam_document_type_id.code not in [
                            '91', '97', '98', '02']:
                            cod_libro = "080100" + "&" + str(
                                str(account_period.year) + "" + str(
                                    "%02d" % (account_period.month,)) + "00", ) + "&" + str(
                                account.id) + "&" + str(str("M") + str(account.id))

                        # COMPRAS SUJETOS A DOMICILIADOS
                        if invoice.move_type in ['in_invoice', 'in_refund'] and invoice.state in ['posted',
                                                                                                  'cancel'] and account.correlative is not False and account.serie_code is not False and account.show_book is True and invoice.l10n_latam_document_type_id.code in [
                            '00', '91', '97', '98'] and invoice.l10n_latam_document_type_id.code != "02":
                            cod_libro = "080200" + "&" + str(
                                str(account_period.year) + "" + str(
                                    "%02d" % (account_period.month,)) + "00", ) + "&" + str(
                                account.id) + "&" + str(str("M") + str(account.id))
                        if account.date:
                            date = account.date
                            date_account = date.strftime("%d/%m/%Y")
                        if account.invoice_date_due:
                            from_date = account.invoice_date_due
                            date = account.invoice_date_due
                            expiration_date = date.strftime("%d/%m/%Y")
                        if account.invoice_date:
                            date = account.invoice_date
                            broadcast_date = date.strftime("%d/%m/%Y")
                        serie = '0'
                        if invoice.serie_code:
                            serie = invoice.serie_code or ''
                        else:
                            serie = invoice.serie_code or ''

                        correlative = '0'
                        if invoice.correlative:
                            correlative = invoice.correlative or ''
                        # for i in array_values_initial:
                        #     if i.move_id.id == move.move_id.id:
                        #         cont += 1
                        #     my_list.append(cont)
                        reference_doc1 = account.ref or ''
                        reference_doc = self.new_line(reference_doc1)
                        code_cost = line.analytic_account_id.name or ''
                        ref = ""
                        if account.l10n_latam_document_type_id and account.serie_code and account.correlative:
                            ref = '%s-%s-%s' % (
                                account.l10n_latam_document_type_id.code, account.serie_code, account.correlative)
                        description1 = line.name or ref
                        description = self.new_line(description1)

                        moves_json.append({
                            # CAMPO 1: PERIODO
                            "periodo": "%s%s00" % (account_period.year, "%02d" % (account_period.month)),
                            "cuo": account.id,  # CAMPO 2: CUO
                            # CAMPO 3 : CORRELATIVO DEL ASIENTO
                            "account_correlative": "M" + str(cont),
                            # CAMPO 4 : CODIGO DE LA CUENTA CONTABLE
                            "code_account": line.account_id.code[:24] or '',
                            "code_unit": '',  # CAMPO 5: CODIGO DE LA UNIDAD
                            # CAMPO 6: CODIGO DE LA CUENTA ANALITICA
                            "code_cost": code_cost[:24] or '',
                            "type_currency": account.currency_id.name or '',  # CAMPO 7: TIPO DE MONEDA
                            "type_document_identity": line.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or '0',
                            # CAMPO 8: TIPO DE DOCUMENTO DE IDENTIDAD
                            "document_number_identity": line.partner_id.vat or '00000000',
                            # CAMPO 9: NUMERO DOCUMENTO DE IDENTIDAD
                            # CAMPO 10: TIPO DE OOMPROBANTE
                            "type_document": invoice.l10n_latam_document_type_id.code or '00',
                            "serial_number": serie or '0',  # CAMPO 11: NUMERO DE SERIE DEL COMPROBANTE
                            # CAMPO 12: NUMERO DE COMPROBANTE DE PAGO
                            "correlative_document": correlative or '0',
                            "accounting_date": date_account or '',  # CAMPO 13: FECHA COMTABLE
                            "expiration_date": expiration_date or '',  # CAMPO 14: FECHA VENCIMIENTO
                            "date_of_issue": broadcast_date or date_account,  # CAMPO 15: FECHA DE EMISION
                            "description": description[:200] or '',  # CAMPO 16: GLOSA O DESCRIPCION
                            "reference": reference_doc[:200] or '',  # CAMPO 17: GLOSA REFERENCIAL
                            # CAMPO 18: MOVIMIENTOS DEL DEBE
                            "debit": "%.2f" % round(line.debit, 2) or "0.00",
                            # CAMPO 19: MOVIMIENTOS DEL HABER
                            "credit": "%.2f" % round(line.credit, 2) or "0.00",
                            "book_code": cod_libro or '',  # CAMPO 20: CODIGO DEL LIBRO
                            "status_operation": '1',  # CAMPO 21: ESTADO DE LA OPERACION
                        })
                        contador += 1
            return moves_json

    def get_name_txt(self, options):
        res_company = self.env["res.company"].sudo().browse(
            options["company_id"])
        account_period = datetime.datetime.strptime(
            options["date_to"], "%Y-%m-%d")
        month = "%02d" % (account_period.month)
        account_period = datetime.datetime.strptime(
            options["date_to"], "%Y-%m-%d")
        account_period_from = datetime.datetime.strptime(
            options["date_from"], "%Y-%m-%d")
        mes = "%02d" % (account_period.month)
        count_sale = "1"
        if options["book_type"] == 'plain_account':
            array_values_initial = self.env["account.account"].sudo().search(
                [('company_id', '=', res_company.id), ("write_date", ">=", options["date_from"]),
                 ("write_date", "<=", options["date_to"])])
            if (mes == '01'):
                pass
            else:
                if (len(array_values_initial) > 0):
                    pass
                else:
                    count_sale = "0"

            txt_name = "%s%s%s%s%s%s%s%s%s%s%s" % (
                "LE",
                res_company.vat,
                account_period.year,
                month,
                '00',
                '050300',
                '00',
                '1',
                count_sale,
                '1',
                '1'
            )
            return txt_name
        else:
            count = "1"
            txt_name = "%s%s%s%s%s%s%s%s%s%s%s" % ("LE",  # 1 -2
                                                   res_company.vat,  # 3-13
                                                   account_period.year,
                                                   "%02d" % (
                                                       account_period.month),
                                                   '00',
                                                   '050100',
                                                   '00',
                                                   '1',
                                                   count,
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
                'type': 'ir_actions_account_report_download',
                'data': {'model': 'report.daily.book',
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
                'type': 'ir_actions_account_report_download',
                'data': {'model': 'report.daily.book',
                         'options': json.dumps(data, default=date_utils.json_default),
                         'output_format': 'txt',
                         'report_name': 'txt report',
                         }
            }
