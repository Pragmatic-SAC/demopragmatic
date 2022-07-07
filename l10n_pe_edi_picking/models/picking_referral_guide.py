# -*- coding: utf-8 -*-
import base64
import zipfile
import io
import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout
from zeep.wsse.username import UsernameToken
from zeep import Client, Settings
from zeep.exceptions import Fault
from zeep.transports import Transport
from lxml import etree
from lxml.objectify import fromstring
from datetime import datetime

_logger = logging.getLogger(__name__)


class ReferralGuide(models.Model):
    _name = 'picking.referral.guide'
    _description = 'Referral Guide'
    _order = 'name desc'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    who_received = fields.Boolean(store=True, compute="_compute_who_received")

    @api.depends("picking_id")
    def _compute_who_received(self):
        for referral in self:
            referral.who_received = referral.picking_id.picking_type_id.who_received

    description = fields.Text(string='Description')

    def get_edi_attachments(self):
        attachments = []
        attachment_pdf = self.env['ir.attachment'].search(
            [('name', '=', '%s.pdf' % self.get_name_sunat()), ('res_model', '=', self._name), ('res_id', '=', self.id),
             ('mimetype', '=', 'application/pdf')], limit=1)
        if attachment_pdf.id:
            attachments.append(attachment_pdf.id)
        attachment_zip = self.env['ir.attachment'].search(
            [('name', '=', '%s.zip' % self.get_name_sunat()), ('res_model', '=', self._name), ('res_id', '=', self.id),
             ('mimetype', '=', 'application/zip')], limit=1)
        if attachment_zip.id:
            attachments.append(attachment_zip.id)
        return attachments

    def generate_pdf_attachement(self):
        attachment_pdf = self.env['ir.attachment'].search(
            [('name', '=', '%s.pdf' % self.get_name_sunat()), ('res_model', '=', self._name), ('res_id', '=', self.id),
             ('mimetype', '=', 'application/pdf')],
            limit=1)
        if not attachment_pdf.id:
            report_template_id = self.env.ref(
                'l10n_pe_edi_picking.action_report_l10n_picking_referral_guide')._render_qweb_pdf(self.id)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': '%s.pdf' % self.get_name_sunat(),
                'type': 'binary',
                'res_model': self._name,
                'res_id': self.id,
                'datas': data_record,
                'mimetype': 'application/pdf',
            }
            self.env['ir.attachment'].create(ir_values)

    def action_referral_sent(self):
        self.ensure_one()
        template = self.env.ref('l10n_pe_edi_picking.mail_template_referral_guide', False)
        self.generate_pdf_attachement()
        # template.attachment_ids = [(6, 0, self.get_edi_attachments())]
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model=self._name,
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            default_attachment_ids=[(6, 0, self.get_edi_attachments())],
            custom_layout='mail.mail_notification_light',
            force_email=True,
        )
        return {
            'name': _('Send Referral Guide Electronic'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    referral_guide_low = fields.Many2one(comodel_name="picking.referral.guide", string="Referral Guide Low", copy=False)
    referral_note_low = fields.Text(string="Reason for Low", copy=False)
    name = fields.Char(string='Referral Guide Sequence', default=_('Draft'), copy=False)
    company_id = fields.Many2one(related='picking_id.company_id', string='Company', readonly=True)
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Stock Picking', required=True,
                                 ondelete="cascade")
    referral_lines = fields.One2many(comodel_name='picking.referral.guide.line', string='Referral Guide Lines',
                                     inverse_name='referral_guide_id')
    state = fields.Selection(selection=[('draft', 'Draft'), ('validated', 'Validated'), ('sunat_send', 'Sunat Send'),
                                        ('cancel', 'Cancel')], default='draft', copy=False)

    def _default_type_document(self):
        return self.env["l10n_latam.document.type"].search([('code', '=', '09')], limit=1)

    type_document = fields.Many2one(comodel_name="l10n_latam.document.type", string="Type Document",
                                    default=_default_type_document)

    transport_mode = fields.Many2one(comodel_name='pragmatic.transport.mode.catalog.18', string='Transport mode')
    transport_mode_code = fields.Char(related="transport_mode.code")

    def _default_unit_of_measurement(self):
        uom_default = self.env["uom.uom"].search([('l10n_pe_edi_measure_unit_code', '=', 'KGM')], limit=1)
        return uom_default

    unit_of_measurement = fields.Many2one(comodel_name='uom.uom', string='Unit of measurement',
                                          default=_default_unit_of_measurement)
    total_weight = fields.Float(string='Total weight', store=True, compute="_compute_total_weight")
    string_qr = fields.Char(string='String QR')
    string_hash = fields.Char(string='String Hash')

    @api.depends("referral_lines.total_weight")
    def _compute_total_weight(self):
        for referral in self:
            total_weight = 0.0
            for line in referral.referral_lines:
                total_weight += line.total_weight
            referral.total_weight = total_weight

    sunat_port_code = fields.Char(string='Sunat: Port code')
    observation = fields.Text(string='Observation')
    reason_for_transfer = fields.Many2one(comodel_name='pragmatic.transportation.reason.catalog.20',
                                          string='Reason for transfer')

    @api.onchange("reason_for_transfer")
    def onchange_reason_for_transfer(self):
        if self.reason_for_transfer.id:
            if self.reason_for_transfer.code not in ['08', '09']:
                self.sunat_port_code = False
            if self.reason_for_transfer.code not in ['08']:
                self.container = False
            self.description = self.reason_for_transfer.name

    reason_for_transfer_code = fields.Char(related="reason_for_transfer.code")
    edit_origin = fields.Boolean(related='reason_for_transfer.edit_origin')
    issuing_date = fields.Datetime(string='Issuing date', default=datetime.now())
    transfer_date = fields.Datetime(string='Transfer date', default=datetime.now())
    delivery_date = fields.Datetime(string='Delivery date', default=datetime.now())
    package = fields.Float(string='Package')
    container = fields.Char(string='ID of Container')
    establishment = fields.Many2one(comodel_name='pragmatic.establishment', string='Establisment')
    origin_id = fields.Many2one(comodel_name='res.partner', string='Origin')
    addressee_id = fields.Many2one(comodel_name='res.partner', string='Addressee')

    @api.onchange('addressee_id')
    def onchange_addressee_id(self):
        if self.addressee_id:
            self.destination_addresses_id = False

    addressee_type_document_id = fields.Many2one(related='addressee_id.l10n_latam_identification_type_id',
                                                 string='Document Type', readonly=True)
    addressee_document_number = fields.Char(related='addressee_id.vat', string='Document Number', readonly=True)
    origin_addresses_id = fields.Many2one(comodel_name='res.partner', string='Origin addresses')
    destination_addresses_id = fields.Many2one(comodel_name='res.partner', string='Destination addresses')
    origin_filter = fields.Many2many(comodel_name='res.partner', relation='origin_filter',
                                     string='Origin Filter', store=True,
                                     compute="_compute_origin_filter")
    destination_filter = fields.Many2many(comodel_name='res.partner', relation='destination_filter',
                                          string='Destination Filter', store=True,
                                          compute="_compute_destination_filter")

    def get_addressee(self):
        return self.addressee_id.parent_id if self.addressee_id.parent_id.id else self.addressee_id

    def get_issuer(self):
        return self.origin_id.parent_id if self.origin_id.parent_id.id else self.origin_id

    @api.depends("origin_id")
    def _compute_origin_filter(self):
        for referral in self:
            partner_id = referral.origin_id.parent_id if referral.origin_id.parent_id.id else referral.origin_id
            _ids = partner_id.child_ids.ids if partner_id.child_ids.ids else []
            _ids.append(partner_id.id)
            referral.origin_filter = _ids

    @api.depends("addressee_id")
    def _compute_destination_filter(self):
        for referral in self:
            partner_id = referral.addressee_id.parent_id if referral.addressee_id.parent_id.id else referral.addressee_id
            _ids = partner_id.child_ids.ids if partner_id.child_ids.ids else []
            _ids.append(partner_id.id)
            referral.destination_filter = _ids

    carrier_id = fields.Many2one(comodel_name='res.partner', string='Carrier')

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        if self.carrier_id:
            self.driver_id = False
            self.transport_unit_id = False

    transport_unit_id = fields.Many2one(comodel_name='transport.unit', string='Transport unit')
    license_plate = fields.Char(related='transport_unit_id.license_plate')
    driver_id = fields.Many2one(comodel_name='res.driver', string='Driver')
    third = fields.Boolean(string='Has third')
    third_document_number = fields.Char(string='Third document number')
    third_document_type = fields.Many2one(comodel_name="l10n_latam.identification.type", string='Third document type')
    third_name = fields.Char(string='Third name')

    def action_post(self):
        for referral in self:
            referral._action_post()

    def _validate_post(self):
        if not self.referral_lines.ids:
            raise UserError(_('Register referral guide detail'))
        if not self.origin_addresses_id.street:
            raise UserError(_('Enter the source address correctly'))
        if not self.destination_addresses_id.street:
            raise UserError(_('enter the destination address correctly'))
        if not self.origin_addresses_id.zip:
            raise UserError(_('Ubigeous code not found for source address'))
        if not self.destination_addresses_id.zip:
            raise UserError(_('Ubigeous code not found for destination address'))
        if not self.unit_of_measurement.l10n_pe_edi_measure_unit_code:
            raise UserError(_('Enter a measure code'))
        if self.third:
            if not self.third_document_type.id:
                raise UserError(_('Enter type of third party document'))
            if not self.third_document_number:
                raise UserError(_("Enter the third party's document number"))
        for line in self.referral_lines:
            if not line.product_id.id:
                raise UserError(_('Select a product in the detail.'))
            if not line.product_code:
                raise UserError(_('Enter a product code in the detail. (%s)', line.product_id.name))
            if not line.unit_of_measurement.l10n_pe_edi_measure_unit_code:
                raise UserError(_('Enter a measure code in the detail. (%s)', line.product_id.name))
            if not line.quantity:
                raise UserError(_('Enter quantity in the detail. (%s)', line.product_id.name))
            if not line.weight:
                raise UserError(_('Enter weight in the detail. (%s)', line.product_id.name))
            if not line.total_weight:
                raise UserError(_('Enter total weight in the detail. (%s)', line.product_id.name))

    def _action_post(self):
        self._validate_post()
        sequence_id = self.get_sequence_id()
        if not sequence_id:
            raise UserError(_('Sequence not found'))
        vals = {'state': 'validated'}
        if not self.name or self.name in ['Draft', 'Borrador']:
            _name = sequence_id.next_by_id()
            vals['name'] = _name
        self.write(vals)

    def _action_cancel(self, note_low):
        if self.state in ["sunat_send", "sunat_accepted"]:
            self.write({'state': 'cancel', 'referral_note_low': note_low})
        self.write({'state': 'cancel', 'referral_note_low': note_low})

    def action_cancel(self):
        action = self.env["ir.actions.actions"]._for_xml_id("l10n_pe_edi_picking.l10n_pe_edi_picking")
        return action

    def get_sequence_id(self):
        if not self.picking_id.picking_type_id.is_electronic:
            return False
        if not self.picking_id.picking_type_id.gre_sequence_id.id:
            return False
        return self.picking_id.picking_type_id.gre_sequence_id

    def get_name_sunat(self):
        edi_filename = '%s-%s-%s' % (
            self.company_id.vat,
            self.type_document.code,
            self.name.replace(' ', ''),
        )
        return edi_filename

    def action_draft(self):
        for referral in self:
            if referral.state == "validated":
                referral.write({"state": "draft"})

    def action_send_sunat(self):
        for referral in self:
            referral._send_sunat()

    def _l10n_pe_edi_get_edi_values(self, picking):
        self.ensure_one()
        picking_lines_vals = []
        index = 1

        def format_cdata(to_format):
            return "{string_format}".format(string_format=to_format)

        for line in self.referral_lines:
            picking_lines_vals.append({
                'line': line,
                'index': index,
            })
            index += 1
        values = {
            'doc': picking,
            'format_cdata': format_cdata,
            'picking_lines_vals': picking_lines_vals
        }
        return values

    def _l10n_pe_edi_get_sunat_credentials(self, company):
        self.ensure_one()
        res = {'fault_ns': 'soap-env'}
        _username = company.edi_sol_username if company.picking_edi_environment == 'edi.picking' else 'MODDATOS'
        _password = company.edi_sol_password if company.picking_edi_environment == 'edi.picking' else 'MODDATOS'
        get_param = self.env['ir.config_parameter'].sudo().get_param
        _url = get_param(company.picking_edi_environment, False)
        res.update({
            'wsdl': _url,
            'token': UsernameToken(_username, _password),
        })
        return res

    def _send_sunat(self):
        edi_values = self._l10n_pe_edi_get_edi_values(self)
        edi_str = self.env.ref('l10n_pe_edi_picking.pe_ubl_2_1_edi_picking_edi')._render(edi_values)
        edi_filename = self.get_name_sunat()
        credentials = self._l10n_pe_edi_get_sunat_credentials(self.company_id)
        res = self._l10n_pe_edi_sign_picking_sunat_common(self, edi_filename, edi_str, credentials)
        if 'error' in res:
            self.message_post(body=_("An error occurred: %s", res.get('error')))
            return
        documents = []
        if res.get('xml_document'):
            documents.append(('%s.xml' % edi_filename, res['xml_document']))
        if res.get('cdr'):
            documents.append(('CDR-%s.xml' % edi_filename, res['cdr']))
        if documents:
            zip_edi_str = self._l10n_pe_edi_zip_edi_document(documents)
            res['attachment'] = self.env['ir.attachment'].create({
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'name': '%s.zip' % edi_filename,
                'datas': base64.encodebytes(zip_edi_str),
                'mimetype': 'application/zip',
            })
            message = _("The EDI document was successfully created and signed by the government. %s",
                        res["doc_description"])
            self.message_post(
                body=message,
                attachment_ids=res['attachment'].ids,
            )
        self.write({"state": "sunat_send", "string_qr": res["string_qr"], "string_hash": res["string_hash"]})
        return res

    def _l10n_pe_edi_sign_picking_sunat_common(self, picking_id, edi_filename, edi_str, credentials):
        self.ensure_one()

        if not picking_id.company_id.edi_cert_content:
            return {'error': _("No valid certificate found for %s company.", picking_id.company_id.display_name)}
        edi_tree = fromstring(edi_str)
        edi_tree = picking_id.company_id.sudo()._sign(edi_tree)
        error = self.env['ir.attachment']._l10n_pe_edi_picking_check_with_xsd(edi_tree)
        if error:
            return {'error': _('XSD validation failed: %s', error), 'blocking_level': 'error'}
        edi_str = etree.tostring(edi_tree, xml_declaration=True, encoding='ISO-8859-1')
        zip_edi_str = self._l10n_pe_picking_edi_zip_edi_document([('%s.xml' % edi_filename, edi_str)])
        transport = Transport(operation_timeout=15, timeout=15)
        try:
            settings = Settings(raw_response=True)
            client = Client(
                wsdl=credentials['wsdl'],
                wsse=credentials['token'],
                settings=settings,
                transport=transport,
            )
            result = client.service.sendBill('%s.zip' % edi_filename, zip_edi_str)
            result.raise_for_status()
        # except Exception as e:
        #     _logger.error('Failed to upload to ftp: ' + str(e))
        except Fault:
            return {'error': _("Error")}
        except ConnectionError:
            return {'error': _("Connection Error")}
        except HTTPError:
            return {'error': _("Connection Error HTTP")}
        except TypeError:
            return {'error': _("Type Error")}
        except ReadTimeout:
            return {'error': _("Read Timeout")}
        cdr_str = result.content
        cdr_decoded = self._l10n_pe_edi_picking_decode_cdr(cdr_str)
        if 'error' in cdr_decoded:
            return {'error': cdr_decoded['error']}
        cdr_tree = etree.fromstring(cdr_str)
        content_cdr = cdr_tree.find('.//{*}applicationResponse')
        zip_content = self._l10n_pe_edi_unzip_edi_document(base64.b64decode(content_cdr.text))
        cdr_tree_result = etree.fromstring(zip_content)
        doc_response_code = cdr_tree_result.find('.//{*}ResponseCode')
        doc_description = cdr_tree_result.find('.//{*}Description')
        if doc_response_code.text != '0':
            return {'error': doc_description.text}
        _name_sequence = self.name.split('-')
        signature_hash = cdr_tree_result.find('.//{*}DigestValue').text
        string_qr = [
            self.company_id.vat,
            self.type_document.code,
            _name_sequence[0],
            _name_sequence[1],
            str(0.00),
            str(0.00),
            fields.Date.to_string(self.issuing_date),
            self.addressee_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            self.addressee_id.vat or '00000000',
            signature_hash,
        ]
        return {'xml_document': edi_str, 'cdr': zip_content, 'doc_response_code': doc_response_code,
                'doc_description': doc_description.text, 'string_qr': '|'.join(string_qr) + '|\r\n',
                'string_hash': signature_hash}

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
    def _l10n_pe_picking_edi_zip_edi_document(self, documents):
        buffer = io.BytesIO()
        zipfile_obj = zipfile.ZipFile(buffer, 'w')
        for filename, content in documents:
            zipfile_obj.writestr(filename, content, compress_type=zipfile.ZIP_DEFLATED)
        zipfile_obj.close()
        content = buffer.getvalue()
        buffer.close()
        return content

    @api.model
    def _l10n_pe_edi_picking_decode_cdr(self, cdr_str):
        self.ensure_one()
        cdr_tree = etree.fromstring(cdr_str)
        message_element, code = self._l10n_pe_edi_picking_response_code_sunat(cdr_tree)
        if code:
            message = message_element.text
            return {'error': message}
        cdr_number_elements = cdr_tree.xpath('//ticket')
        if cdr_number_elements:
            return {'number': cdr_number_elements[0].text}
        return {}

    @api.model
    def _l10n_pe_edi_picking_response_code_sunat(self, cdr_tree):
        message_element = cdr_tree.find('.//{*}message')
        code_element = cdr_tree.find('.//{*}faultstring')
        code = False
        if code_element is not None:
            code = code_element.text
        return message_element, code

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

    def unlink(self):
        for referral in self:
            if referral.state not in ["draft"]:
                raise UserError(_("You cannot delete once a correlative is assigned: (%s)", referral.name))
        res = super(ReferralGuide, self).unlink()
        return res
