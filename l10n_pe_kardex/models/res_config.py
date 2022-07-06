# -*- coding: utf-8 -*-

from odoo import models, fields, api

CATALOG = [('1', 'NACIONES UNIDAS'), ('2', 'CUBSO'), ('3', 'GS1 (EAN-UCC)'), ('9', 'OTROS')]


class ResCompany(models.Model):
    _inherit = 'res.company'

    catalog_exist = fields.Selection(CATALOG, string="Type existences")
    catalog_exist_des = fields.Char(string="Descripcion")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    catalog_exist = fields.Selection(CATALOG, string="Type existences")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            catalog_exist=self.env.user.company_id.catalog_exist or '',
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        for conf in self:
            conf.company_id.write({
                'catalog_exist': self.catalog_exist,
                'catalog_exist_des': dict(self._fields['catalog_exist'].selection).get(self.catalog_exist)
            })
