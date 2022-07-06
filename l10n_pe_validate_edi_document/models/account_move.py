# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from zeep.transports import Transport
from zeep import Client, Settings
from zeep.exceptions import Fault
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, InvalidURL, ReadTimeout
from odoo import models, fields, api, _, _lt
from zeep.wsse.username import UsernameToken
from lxml import etree
from odoo.exceptions import UserError

import base64
import io
import zipfile
import re
import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_sunat_wsdl(self):
        return 'https://ww1.sunat.gob.pe/ol-it-wsconscpegem/billConsultService?wsdl'

    def _l10n_pe_edi_get_sunat_credentials(self):
        company = self.company_id
        self.ensure_one()
        res = {'fault_ns': 'soap-env'}
        if company.l10n_pe_edi_test_env:
            res.update({
                'wsdl': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl',
                'token': UsernameToken('MODDATOS', 'MODDATOS'),
            })
        else:
            res.update({
                'wsdl': self._get_sunat_wsdl(),
                'token': UsernameToken(company.l10n_pe_edi_provider_username, company.l10n_pe_edi_provider_password),
            })
        return res

    def get_edi_validate_documents(self):
        credentials = self._l10n_pe_edi_get_sunat_credentials()
        result = self._l10n_pe_edi_validate_document(credentials)
        if 'error' in result:
            raise UserError(result.get('error', 'Error'))
        cdr_tree = etree.fromstring(result['cdr'])
        doc_resoponse_code = cdr_tree.find('.//{*}ResponseCode')
        doc_description = cdr_tree.find('.//{*}Description')
        attacht_id = False
        blocking_level = False
        state = 'sent'
        if doc_resoponse_code.text != '0':
            blocking_level = 'error'
            state = 'to_cancel'
        else:
            edi_filename = '%s-%s-%s' % (
                self.company_id.vat,
                self.l10n_latam_document_type_id.code,
                self.name,
            )
            documents = []
            documents.append(('CDR-%s.xml' % edi_filename, result['cdr']))
            zip_edi_str = self._l10n_pe_edi_zip_edi_document(documents)
            attacht_id = self.env['ir.attachment'].create({
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'name': '%s.zip' % edi_filename,
                'datas': base64.encodebytes(zip_edi_str),
                'mimetype': 'application/zip',
            })
            message = _("The EDI document was successfully created and signed by the government.")
            if doc_description is not None:
                message += '\n' + doc_description.text
            self.with_context(no_new_invoice=True).message_post(
                body=message,
                attachment_ids=attacht_id.ids,
            )
        existing_edi_document = self.edi_document_ids.filtered(lambda x: x.state == 'to_send')
        if existing_edi_document.ids:
            existing_edi_document = existing_edi_document[0]
            existing_edi_document.write({'blocking_level': blocking_level, 'state': state,
                                         'attachment_id': attacht_id.id, 'error': False,
                                         })

    @api.model
    def _l10n_pe_edi_zip_edi_document(self, documents):
        buffer = io.BytesIO()
        zipfile_obj = zipfile.ZipFile(buffer, 'w')
        for filename, content in documents:
            zipfile_obj.writestr(filename, content, compress_type=zipfile.ZIP_DEFLATED)
        zipfile_obj.close()
        content = buffer.getvalue()
        buffer.close()
        return content

    def get_edi_validate_state(self):
        credentials = self._l10n_pe_edi_get_sunat_credentials()
        result = self._l10n_pe_edi_validate_state(credentials)
        if 'error' in result:
            raise UserError(result.get('error', 'Error'))
        message = _("SUNAT reponse: ")
        if result is not None:
            message += '\n' + str(result['code']) + '-' + str(result['message'])
        self.with_context(no_new_invoice=True).message_post(body=message)

    def _l10n_pe_edi_validate_state(self, credentials):
        self.ensure_one()
        transport = Transport(operation_timeout=15, timeout=15)
        try:
            settings = Settings(raw_response=True)
            client = Client(
                wsdl=credentials['wsdl'],
                wsse=credentials['token'],
                settings=settings,
                transport=transport,
            )
            result = client.service.getStatus(self.company_id.vat, self.type_document_code, self.serie_code,
                                              self.correlative)
            result.raise_for_status()
        except Fault:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE07'], 'blocking_level': 'warning'}
        except (InvalidSchema, KeyError):
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE08'], 'blocking_level': 'error'}
        cdr_str = result.content
        cdr_tree = etree.fromstring(cdr_str)
        code_cdr = cdr_tree.find('.//statusCode')
        message_cdr = cdr_tree.find('.//statusMessage')
        if code_cdr.text:
            return {'success': True, 'code': code_cdr.text, 'message': message_cdr.text}
        return {'error': True, 'message': _('An error occurred while querying the status')}

    def _l10n_pe_edi_validate_document(self, credentials):
        self.ensure_one()
        transport = Transport(operation_timeout=15, timeout=15)
        try:
            settings = Settings(raw_response=True)
            client = Client(
                wsdl=credentials['wsdl'],
                wsse=credentials['token'],
                settings=settings,
                transport=transport,
            )
            result = client.service.getStatusCdr(self.company_id.vat, self.type_document_code, self.serie_code,
                                                 self.correlative)
            result.raise_for_status()
        except Fault:
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE07'], 'blocking_level': 'warning'}
        except (InvalidSchema, KeyError):
            return {'error': self._l10n_pe_edi_get_general_error_messages()['L10NPE08'], 'blocking_level': 'error'}
        cdr_str = result.content
        cdr_tree = etree.fromstring(cdr_str)
        content_cdr = cdr_tree.find('.//content')
        code_cdr = cdr_tree.find('.//statusCode')
        message_cdr = cdr_tree.find('.//statusMessage')
        if cdr_tree.find('.//statusCode') is None:
            return {'error': _('Code not found'), 'blocking_level': 'error'}
        if code_cdr.text != '0004':
            return {'error': message_cdr.text, 'blocking_level': 'error'}
        zip_content = self._l10n_pe_edi_unzip_edi_document(base64.b64decode(content_cdr.text))
        return {'success': True, 'cdr': zip_content, 'message': message_cdr}

    @api.model
    def _l10n_pe_edi_unzip_edi_document(self, zip_str):
        buffer = io.BytesIO(zip_str)
        zipfile_obj = zipfile.ZipFile(buffer)
        regex = re.compile('R-')
        filename = [string for string in zipfile_obj.namelist() if re.match(regex, string)][0]
        content = zipfile_obj.read(filename)
        buffer.close()
        return content

    @api.model
    def _l10n_pe_edi_get_general_error_messages(self):
        return {
            'L10NPE02': _lt("The zip file is corrupted, please check that the zip we are reading is the one you need."),
            'L10NPE03': _lt("The XML inside of the zip file is corrupted or has been altered, please review the XML "
                            "inside of the XML we are reading."),
            'L10NPE07': _lt("Trying to send the invoice to the OSE the webservice returned a controlled error, please "
                            "try again later, the error is on their side not here."),
            'L10NPE08': _lt("Check your firewall parameters, it is not being possible to connect with server to sign "
                            "invoices."),
            'L10NPE10': _lt("The URL provided to connect to the OSE is wrong, please check your implementation."),
            'L10NPE11': _lt("The XML generated is not valid."),
            'L10NPE16': _lt("There was an error while establishing the connection to the server, try again and "
                            "if it fails check the URL in the parameter l10n_pe_edi.endpoint."),
            'L10NPE17': _lt("There are problems with the connection to the IAP server. "
                            "Please try again in a few minutes."),
            'L10NPE18': _lt("The URL provided for the IAP server is wrong, please go to  Settings --> System "
                            "Parameters and add the right URL to parameter l10n_pe_edi.endpoint."),
        }

    @api.model
    def _l10n_pe_edi_response_code_sunat(self, cdr_tree):
        content = cdr_tree.find('.//content') if cdr_tree.find('.//content') else False
        status_code = cdr_tree.find('.//statusCode') if cdr_tree.find('.//statusCode') else False
        status_message = cdr_tree.find('.//statusMessage') if cdr_tree.find('.//statusMessage') else False
        return content, status_code, status_message
