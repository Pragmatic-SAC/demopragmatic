# -*- coding: utf-8 -*-
import base64
import zipfile
import io
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, InvalidURL, ReadTimeout
from zeep.wsse.username import UsernameToken
from zeep import Client, Settings
from zeep.exceptions import Fault, ValidationError
from zeep.transports import Transport
from lxml import etree
from lxml.objectify import fromstring
from lxml.etree import tostring

_logger = logging.getLogger(__name__)


class ReferralGuideWizard(models.TransientModel):
    _name = 'picking.referral.guide.wizard'
    _description = 'Wizard to low Referral Guide'

    name = fields.Text(string='Note to Cancel', required=True)
    referral_slow = fields.Many2one(comodel_name='picking.referral.guide', required=True, string='Referral to Slow')

    def action_slow(self):
        new_referral = self.referral_slow.copy()
        if new_referral.id:
            new_referral.write({"referral_guide_low": self.referral_slow.id})
            self.referral_slow._action_cancel(self.name)
            return self.show_referral_guide(new_referral.id)

    def show_referral_guide(self, new_referral):
        ctx = dict(self.env.context or {})
        return {
            'res_model': 'picking.referral.guide',
            'type': 'ir.actions.act_window',
            'name': _("Referral Guide"),
            'res_id': new_referral,
            'view_mode': 'form',
        }
