# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    sunat_type_agreement = fields.Many2one(comodel_name="pragmatic.table.25", string="Sunat Type Agreement")

    sunat_type_person = fields.Many2one(comodel_name="pragmatic.annexed.2", string="Sunat Type Person")

    @api.model_create_multi
    def create(self, vals_list):
        for index in range(len(vals_list)):
            if vals_list[index].get('l10n_pe_district', False):
                district = self.env["l10n_pe.res.city.district"].browse(
                    int(vals_list[index].get('l10n_pe_district')))
                city_id = district.city_id.id
                state_id = district.city_id.state_id.id
                vals_list[index]["city_id"] = city_id
                vals_list[index]["state_id"] = state_id
                if not vals_list[index].get('zip', False):
                    vals_list[index]["zip"] = district.code or ""
        response = super(ResPartner, self).create(vals_list)
        return response

    country_code = fields.Char(related='country_id.code', readonly=True)

    def write(self, vals):
        if not vals.get('city_id', False):
            if vals.get('l10n_pe_district', False):
                district = self.env["l10n_pe.res.city.district"].browse(
                    int(vals.get('l10n_pe_district')))
                city_id = district.city_id.id
                state_id = district.city_id.state_id.id
                vals["city_id"] = city_id
                vals["state_id"] = state_id
        response = super(ResPartner, self).write(vals)
        return response
