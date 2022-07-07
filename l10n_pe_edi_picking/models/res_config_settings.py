# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def button_process_edi_picking(self):
        self.company_id.process_edi_picking_certificate()

    picking_edi_environment = fields.Selection(string="EDI Picking Environment", related="company_id.picking_edi_environment", readonly=False)
    edi_cert_content = fields.Binary(string='PFX Certificate', related="company_id.edi_cert_content", readonly=False)
    edi_cert_password = fields.Char(string='Passphrase for the PFX certificate', related="company_id.edi_cert_password", readonly=False)
    edi_cert_startdate = fields.Datetime(string='Start Date', related="company_id.edi_cert_startdate", readonly=False)
    edi_cert_enddate = fields.Datetime(string='End Date', related="company_id.edi_cert_enddate", readonly=False)
    edi_sol_username = fields.Char(string='SOL User',related="company_id.edi_sol_username", readonly=False)
    edi_sol_password = fields.Char(string='SOL Password',related="company_id.edi_sol_password", readonly=False)
    edi_cert_serial_number = fields.Char(string='Serial Number',related="company_id.edi_cert_serial_number", readonly=False)