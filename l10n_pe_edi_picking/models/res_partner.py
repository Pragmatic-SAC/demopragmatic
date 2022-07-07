# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    transport_units = fields.One2many(comodel_name='transport.unit', string='Transport Unit', copy=False,
                                      inverse_name='partner_id')
    drivers = fields.One2many(comodel_name='res.driver', string='Drivers', copy=False, inverse_name='partner_id')
    compute_is_transport = fields.Boolean(string='Is Transport', compute='_compute_is_transport')

    @api.depends('category_id')
    def _compute_is_transport(self):
        picking_edi_transport = self.env.ref('l10n_pe_edi_picking.picking_edi_transport')
        for partner in self:
            partner.compute_is_transport = True if picking_edi_transport.id in partner.category_id.ids else False

    def _get_picking_address(self):
        return "{street} - {district} {city} {state} {country}".format(street=self.street or '',
                                                                       country=self.country_id.name or '',
                                                                       state=self.state_id.name or '',
                                                                       city=self.city_id.name or '',
                                                                       district=self.l10n_pe_district.name or '')

    def _get_name(self):
        name = super(ResPartner, self)._get_name()
        if self._context.get('show_address_picking', False):
            name = self._get_picking_address()
        return name

    def get_full_picking_address(self):
        return "{street} {district} {city} {state} {country}".format(
            street=self.street or '',
            district=self.l10n_pe_district.name + ' - ' if self.l10n_pe_district.id else '',
            city=self.city_id.name + ' - ' if self.city_id.id else '',
            state=self.state_id.name + ', ' if self.state_id.id else '',
            country=self.country_id.name or '')
