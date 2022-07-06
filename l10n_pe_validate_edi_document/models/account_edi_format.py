# -*- coding: utf-8 -*-

import base64
import zipfile
import io
from lxml import etree
import logging
import re

_logger = logging.getLogger(__name__)
from odoo import models, fields, api, _, _lt


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    @api.model
    def _l10n_pe_edi_unzip_edi_document_cancel(self, zip_str):
        buffer = io.BytesIO(zip_str)
        zipfile_obj = zipfile.ZipFile(buffer)
        regex = re.compile('R-')
        filename = [string for string in zipfile_obj.namelist() if re.match(regex, string)][0]
        content = zipfile_obj.read(filename)
        buffer.close()
        return content

    @api.model
    def validate_cancel_edi(self, invoice, attachment):
        edi_attach = self.env['ir.attachment'].search(
            [('res_model', '=', invoice._name), ('res_id', '=', invoice.id),
             ('name', '=', 'CDR-VOID-%s.xml' % attachment.name[:-4])], limit=1)
        response = {'success': True}
        if edi_attach.datas:
            content = base64.b64decode(edi_attach.datas)
            cdr_tree = etree.fromstring(content)
            content_cdr = cdr_tree.find('.//content')
            code_cdr = cdr_tree.find('.//statusCode')
            if content_cdr.text is not None:
                result_xml = self._l10n_pe_edi_unzip_edi_document_cancel(base64.b64decode(content_cdr.text))
                cdr_tree = etree.fromstring(result_xml)
                doc_resoponse_code = cdr_tree.find('.//{*}ResponseCode')
                doc_description = cdr_tree.find('.//{*}Description')
                message_error = "%s - %s" % (doc_resoponse_code.text, doc_description.text)
                invoice.with_context(no_new_invoice=True).message_post(body=message_error)
                if code_cdr.text != "0":
                    response['success'] = False
                    response['error'] = message_error
        return response

    def _l10n_pe_edi_cancel_invoice_edi_step_2(self, invoices, edi_attachments, cdr_number):
        self.ensure_one()
        response = super(AccountEdiFormat, self)._l10n_pe_edi_cancel_invoice_edi_step_2(invoices, edi_attachments,
                                                                                        cdr_number)
        edi_values = list(zip(invoices, edi_attachments))
        for invoice, attachment in edi_values:
            is_cancel = self.validate_cancel_edi(invoice, attachment)
            if not is_cancel.get('success'):
                response[invoice] = {'success': False, 'blocking_level': 'error', 'error': is_cancel.get('error')}
        return response
