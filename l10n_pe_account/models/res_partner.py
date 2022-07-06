# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_full_address(self):
        return "{street} {district} {city} {state} {country}".format(
            street=self.street or '',
            district=self.l10n_pe_district.name + ' - ' if self.l10n_pe_district.id else '',
            city=self.city_id.name + ' - ' if self.city_id.id else '',
            state=self.state_id.name + ', ' if self.state_id.id else '',
            country=self.country_id.name or '')
