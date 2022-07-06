default = {
              'record': account.move(28, ),
              'spot': {}, 'is_refund': False, 'PaymentMeansID': 'Contado',
              'invoice_date_due_vals': account.move.line(109, ), 'invoice_date_due_vals_list': [
        {'amount': 1234.0, 'currency_name': 'PEN', 'date_maturity': datetime.date(2022, 3, 21)}],
              'invoice_lines_vals': [{'index': 1, 'line': account.move.line(107, ), 'tax_details': {'base_tags': [],
                                                                                                    'taxes': [{'id': 2,
                                                                                                               'name': '18% (Included in price)',
                                                                                                               'amount': 188.24,
                                                                                                               'base': 1045.76,
                                                                                                               'sequence': 1,
                                                                                                               'account_id': 631,
                                                                                                               'analytic': False,
                                                                                                               'price_include': True,
                                                                                                               'tax_exigibility': 'on_invoice',
                                                                                                               'tax_repartition_line_id': 4,
                                                                                                               'group': None,
                                                                                                               'tag_ids': [],
                                                                                                               'tax_ids': [],
                                                                                                               'tax_amount': 18.0,
                                                                                                               'tax_amount_type': 'percent',
                                                                                                               'price_unit_type_code': '01',
                                                                                                               'l10n_pe_edi_tax_code': '1000',
                                                                                                               'l10n_pe_edi_group_code': 'IGV',
                                                                                                               'l10n_pe_edi_international_code': 'VAT'}],
                                                                                                    'total_excluded': 1045.76,
                                                                                                    'total_included': 1234.0,
                                                                                                    'total_void': 1045.76,
                                                                                                    'unit_total_included': 1.0,
                                                                                                    'unit_total_excluded': 0.85,
                                                                                                    'price_unit_type_code': '01'}}],
              'certificate_date': datetime.date(2022, 3, 21), 'format_float': < function
AccountEdiFormat._l10n_pe_edi_get_edi_values. < locals >.format_float
at
0x7f3eb975d510 >, 'total_after_spot': 1234.0, 'tax_details': {'total_excluded': 1045.76, 'total_included': 1234.0,
                                                              'total_taxes': 188.24, 'grouped_taxes': [
        {'base': 1045.76, 'amount': 188.24, 'l10n_pe_edi_group_code': 'IGV', 'l10n_pe_edi_international_code': 'VAT',
         'l10n_pe_edi_tax_code': '1000'}]}}
