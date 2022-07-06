# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    type_transaction = fields.Many2one(comodel_name="pragmatic.type.operation.table.12",
                                       string="Sunat Type Transaction")

    type_transaction_filter = fields.Many2many(string="Type Operation Value",
                                               comodel_name="pragmatic.type.operation.table.12",
                                               compute="_compute_type_transaction_filter")

    @api.onchange("picking_type_id")
    def pragmatic_onchange_picking_type(self):
        if self.picking_type_id.id:
            if self.picking_type_id.type_transactions_allowed.ids:
                self.type_transaction = self.picking_type_id.type_transactions_allowed[0].id

    @api.depends("picking_type_id")
    def _compute_type_transaction_filter(self):
        for picking in self:
            picking.type_transaction_filter = [(6, False, picking.picking_type_id.type_transactions_allowed.ids)]

    l10n_latam_document_type_id = fields.Many2one(comodel_name="l10n_latam.document.type",
                                             string="Sunat Type Document", copy=False)

    serie = fields.Char(string="Serie")
    correlative = fields.Char(string="Correlative")

    @api.model
    def create(self, values):
        if "picking_type_id" in values and "type_transaction" not in values:
            picking_type = self.env["stock.picking.type"].browse(values["picking_type_id"])
            if picking_type.type_transactions_allowed.ids:
                values["type_transaction"] = picking_type.type_transactions_allowed[0].id
        record = super(StockPicking, self).create(values)
        return record
