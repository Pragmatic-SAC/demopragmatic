# -*- coding: utf-8 -*-
from odoo import api, models, fields, _,tools
from odoo.exceptions import ValidationError
import hashlib
import ssl
from base64 import b64decode, b64encode
from copy import deepcopy
from lxml import etree
from pytz import timezone
from datetime import datetime
from OpenSSL import crypto
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    picking_edi_environment = fields.Selection(selection=[('edi.picking.beta','Test'),('edi.picking','Production')],string="EDI Picking Environment")

    def get_environment_url(self):
        if not self.picking_edi_environment:
            raise ValidationError(_('Select an environment in the inventory configuration: Referral Guide Configurations.'))
        get_param = self.env['ir.config_parameter'].sudo().get_param
        _url = get_param(self.picking_edi_environment, False)
        if not _url:
            raise ValidationError(_('Environment url not configured %s',self.picking_edi_environment))
        return _url

    edi_cert_content = fields.Binary(string='PFX Certificate')
    edi_cert_password = fields.Char(string='Passphrase for the PFX certificate')
    edi_cert_startdate = fields.Datetime(string='Start Date')
    edi_cert_enddate = fields.Datetime(string='End Date')
    edi_cert_serial_number = fields.Char(string='Serial Number')

    edi_sol_username = fields.Char(string='SOL User')
    edi_sol_password = fields.Char(string='SOL Password')


    @api.model
    def _get_pe_current_datetime(self):
        peruvian_tz = timezone('America/Lima')
        return datetime.now(peruvian_tz)

    @tools.ormcache('self.edi_cert_content', 'self.edi_cert_password')
    def _decode_certificate(self):
        decrypted_content = crypto.load_pkcs12(b64decode(self.edi_cert_content), self.edi_cert_password.encode())
        certificate = decrypted_content.get_certificate()
        private_key = decrypted_content.get_privatekey()
        pem_certificate = crypto.dump_certificate(crypto.FILETYPE_PEM, certificate)
        pem_private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, private_key)

        for to_clean in ('\n', ssl.PEM_HEADER, ssl.PEM_FOOTER):
            pem_certificate = pem_certificate.replace(to_clean.encode('UTF-8'), b'')

        return pem_certificate, pem_private_key, certificate

    def process_edi_picking_certificate(self):
        self.ensure_one()
        if not self.edi_cert_content:
            raise ValidationError(_('certificate not found'))
        peruvian_tz = timezone('America/Lima')
        peruvian_dt = self._get_pe_current_datetime()
        date_format = '%Y%m%d%H%M%SZ'
        try:
            pem_certificate, pem_private_key, certificate = self._decode_certificate()
            cert_date_start = peruvian_tz.localize(datetime.strptime(certificate.get_notBefore().decode(), date_format))
            cert_date_end = peruvian_tz.localize(datetime.strptime(certificate.get_notAfter().decode(), date_format))
            serial_number = certificate.get_serial_number()
        except crypto.Error:
            raise ValidationError(_('There has been a problem with the certificate, some usual problems can be:\n'
                                    '- The password given or the certificate are not valid.\n'
                                    '- The certificate content is invalid.'))
        # Assign extracted values from the certificate
        self.write({
            'edi_cert_serial_number': ('%x' % serial_number)[1::2],
            'edi_cert_startdate': fields.Datetime.to_string(cert_date_start),
            'edi_cert_enddate': fields.Datetime.to_string(cert_date_end),
        })
        if peruvian_dt > cert_date_end:
            raise ValidationError(_('The certificate is expired since %s') % self.edi_cert_enddate)
        return True

    def _sign(self, edi_tree):
        self.ensure_one()
        pem_certificate, pem_private_key, certificate = self._decode_certificate()
        namespaces = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}

        edi_tree_copy = deepcopy(edi_tree)
        _logger.info("edi_tree_copy")
        _logger.info(edi_tree_copy)
        signature_element = edi_tree_copy.xpath('.//ds:Signature', namespaces=namespaces)[0]
        signature_element.getparent().remove(signature_element)

        edi_tree_c14n_str = etree.tostring(edi_tree_copy, method='c14n', exclusive=True, with_comments=False)
        digest_b64 = b64encode(hashlib.new('sha1', edi_tree_c14n_str).digest())
        signature_str = self.env.ref('l10n_pe_edi_picking.pe_edi_picking_ubl_2_1_signature')._render({'digest_value': digest_b64})

        # Eliminate all non useful spaces and new lines in the stream
        signature_str = signature_str.decode('UTF-8').replace('\n', '').replace('  ', '')

        signature_tree = etree.fromstring(signature_str)
        signed_info_element = signature_tree.xpath('.//ds:SignedInfo', namespaces=namespaces)[0]
        signature = etree.tostring(signed_info_element, method='c14n', exclusive=True, with_comments=False)
        private_pem_key = crypto.load_privatekey(crypto.FILETYPE_PEM, pem_private_key)
        signature_b64_hash = b64encode(crypto.sign(private_pem_key, signature, 'sha1'))

        signature_tree.xpath('.//ds:SignatureValue', namespaces=namespaces)[0].text = signature_b64_hash
        signature_tree.xpath('.//ds:X509Certificate', namespaces=namespaces)[0].text = pem_certificate
        signed_edi_tree = deepcopy(edi_tree)
        signature_element = signed_edi_tree.xpath('.//ds:Signature', namespaces=namespaces)[0]
        for child_element in signature_tree:
            signature_element.append(child_element)
        return signed_edi_tree
    