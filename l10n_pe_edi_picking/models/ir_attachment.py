# -*- coding: utf-8 -*-

import base64
import io
import logging
import zipfile
import requests
from requests.exceptions import RequestException
from lxml import etree, objectify
from io import BytesIO
from odoo import _, models, tools
from odoo.tools import xml_utils
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'ir.attachment'

    def _l10n_pe_edi_picking_load_xsd_attachments(self):
        # This method only brings the xsd files if it doesn't exist as attachment
        url = 'http://cpe.sunat.gob.pe/sites/default/files/inline-files/XSD%202.1.zip'
        _logger.info('Downloading file from sunat: %s' % (url))
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except RequestException as error:
            _logger.warning('Connection error %s with the given URL: %s' % (error, url))
            return

        try:
            archive = zipfile.ZipFile(io.BytesIO(response.content))
        except:
            _logger.warning('UNZIP for XSD failed from URL: %s' % (url))
            return
        for file_path in archive.namelist():
            _, file_name = file_path.rsplit('/', 1)
            if not file_name:
                continue
            attachment = self.env.ref('l10n_pe_edi_picking.%s' % file_name, False)
            if attachment:
                continue

            content = archive.read(file_path)
            try:
                content = content.replace(b'schemaLocation="../common/', b'schemaLocation="')
                xsd_object = objectify.fromstring(content)
            except etree.XMLSyntaxError as e:
                _logger.warning('You are trying to load an invalid xsd file.\n%s', e)
                return
            validated_content = etree.tostring(xsd_object, pretty_print=True)
            _validator_attach = self.search([('name', '=', file_name)], limit=1)
            if not _validator_attach.id:
                attachment = self.create({
                    'name': file_name,
                    'description': "l10n_pe_edi_picking.%s" % file_path,
                    'datas': base64.encodebytes(validated_content),
                    'company_id': False,
                })
                self.env['ir.model.data'].create({
                    'name': "l10n_pe_edi_picking.%s" % file_path,
                    'module': 'l10n_pe_edi_picking',
                    'res_id': attachment.id,
                    'model': 'ir.attachment',
                    'noupdate': False,
                })
            else:
                _validator_attach.write({"datas": base64.encodebytes(validated_content)})

    def _l10n_pe_edi_picking_check_with_xsd(self, xml_to_validate):
        xsd_fname = 'l10n_pe_edi_picking.UBL-DespatchAdvice-2.1.xsd'
        try:
            xml_utils._check_with_xsd(xml_to_validate, xsd_fname, self.env)
            return ''
        except FileNotFoundError:
            _logger.info('The XSD validation files from Sunat has not been found, please run the cron manually. ')
            return ''
        except UserError as exc:
            return str(exc)
