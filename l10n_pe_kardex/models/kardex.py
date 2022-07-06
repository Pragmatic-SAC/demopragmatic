# -*- coding: utf-8 -*-
import base64
import json
import logging
# from datetime import datetime
import datetime
import calendar
import io

from pip._vendor.requests import request

from . import tools as k_tool
from .sql import SqlKardex
# from . import sql.SqlKardex
from odoo import models, _, api, fields
from odoo.exceptions import UserError
from odoo.tools import config, date_utils, get_lang
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    initial_balance = fields.Float(string="Saldo Inicial Valorizado")
    initial_balance_uni = fields.Float(string="Saldo Inicial Unidades")
    initial_cant = fields.Float(string="Cantidad  Inicial Valorizado")
    initial_cant_uni = fields.Float(string="Cantidad Inicial Unidades")
    initial_cost = fields.Float(string="Costo Inicial Valorizado")
    initial_cost_uni = fields.Float(string="Costo Inicial Unidades")


TYPEKARDEX = [('units', _('Units')), ('valued', _('Valued'))]


class KardexInventory(models.TransientModel):
    _name = 'kardex.inventory.mov'
    _description = "Kardex Inventory"

    @api.model
    def _get_from_date(self):
        date = datetime.date.today()
        start_date = datetime.datetime(date.year, date.month, 1)
        return start_date.date()

    @api.model
    def _get_name_report(self):
        date = datetime.date.today()
        name_ = "%s%s%s" % (_("Month"), " ", date.strftime('%B'))
        return name_

    @api.model
    def _get_date_to(self):
        date = datetime.date.today()
        end_date = datetime.datetime(date.year, date.month, calendar.mdays[date.month])
        return end_date.date()

    @api.model
    def get_states(self):
        return self.env['kardex.states'].search([('code', '=', 'NINGUNO')]).ids

    name = fields.Char(string="Name", required=True, default=_get_name_report)
    date_from = fields.Date(string='Date from', default=_get_from_date, required=True, )
    date_to = fields.Date(string='Date to', default=_get_date_to, required=True, )
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id,
                                 string='Company')
    establishment = fields.Many2one(comodel_name="pragmatic.establishment", string="Establishment", required=True, )
    type_kardex = fields.Selection(TYPEKARDEX, default='units', required=True)
    state_ids = fields.Many2many('kardex.states', default=get_states)

    @api.onchange('date_from', 'date_to')
    def _change_date(self):
        date = self.date_from
        name_ = "%s%s%s" % (_("Month"), " ", str(date.strftime('%B')))
        self.name = name_

    def _get_columns_name(self, options):
        if options['type_kardex'] == 'units':
            return k_tool.column_excel_unit()
        else:
            return k_tool.column_excel_val()

    def get_header(self, options):
        columns = self._get_columns_name(options)
        return [columns]

    def _get_lines(self, options):
        lines = []
        journal = self.env['account.journal'].sudo().search(
            [('code', '=', 'STJ'), ('company_id', '=', options['company_id'])], limit=1)
        stock_location = self.env['stock.location']
        stock_picking = self.env['stock.picking']
        stock_inventory = self.env['stock.inventory']
        product_product = self.env['product.product']
        type_transaction = self.env['pragmatic.type.operation.table.12']
        date_from = datetime.datetime.strptime(options["date_from"], "%Y-%m-%d")
        date_initial = date_from + datetime.timedelta(days=-1)
        obj_init = {"date_from": options["date_from"], "date_to": options["date_to"], "journal": journal.id,
                    "company": options["company_id"],
                    "date_initial": date_initial}
        if options["type_kardex"] == 'units':
            mov_uni = SqlKardex.get_unidades(self, obj_init)
            saldo_ = 0.0
            product_eq = 0
            for res in mov_uni:
                cant_entrada = 0.00
                cant_salida = 0.00
                loc_des = stock_location.sudo().browse(res['location_dest_id'])
                loc_ori = stock_location.sudo().browse(res['location_id'])
                product_env = product_product.sudo().browse(res['product_id'])
                # Saldo inicial
                type_operation_init = type_transaction.search([('code', '=', '16')],
                                                              limit=1)
                obj_physical = {"date_initial": date_initial, "product_id": res['product_id'],
                                "journal_id": journal.id, "company_id": options['company_id']}
                if options['establishment']['id'] in [loc_des.establishment.id, loc_ori.establishment.id]:
                    if saldo_ == 0 and product_eq == 0:
                        saldo_inicial = SqlKardex.get_balance_start_physical(self, obj_physical)
                        if saldo_inicial:
                            saldo_ = saldo_inicial[0]['initial_balance_uni'] or 0.00
                            product_eq = res['product_id']
                        else:
                            saldo_ = 0.00
                            product_eq = res['product_id']

                        if saldo_ != 0.00:
                            data_ = {"date_from": options['date_from'], "product": product_env,
                                     "establishment": options['establishment']['name'],
                                     "level": 2,
                                     "line_id": res['id'], "saldo_inicial": saldo_inicial,
                                     "type_operation_init": type_operation_init,
                                     "res": res, "saldo": saldo_}
                            lines.append(k_tool.add_line_physical(data_))
                    else:
                        if product_eq == res['product_id']:
                            pass
                        else:
                            saldo_inicial = SqlKardex.get_balance_start_physical(self, obj_physical)
                            if saldo_inicial:
                                saldo_ = saldo_inicial[0]['initial_balance_uni'] or 0.00
                                product_eq = res['product_id']
                            else:
                                saldo_ = 0.00
                                product_eq = res['product_id']

                            if saldo_ != 0.00:
                                data_ = {"date_from": options['date_from'], "product": product_env,
                                         "establishment": options['establishment']['name'],
                                         "level": 2,
                                         "line_id": res['id'], "saldo_inicial": saldo_inicial,
                                         "type_operation_init": type_operation_init,
                                         "res": res, "saldo": saldo_}
                                lines.append(k_tool.add_line_physical(data_))

                    # LINEAS DEL KARDEX
                    reference_code = ''
                    serie_code = ''

                    if res['picking_id'] != None:
                        picking_sale = SqlKardex.get_picking_doc(self, res['picking_id'])
                        reference_code = picking_sale['type_doc'] + '-' + picking_sale['number_doc']
                        serie_code = picking_sale['serie_doc']

                    type_operation_move = ''
                    if res['inventory_id'] != None:
                        inventory = stock_inventory.sudo().browse(res['inventory_id'])
                        type_operation_move = inventory.type_transaction.code + '-' + inventory.type_transaction.name
                    elif res['picking_id'] != None:
                        picking = stock_picking.sudo().browse(res['picking_id'])
                        type_operation_move = str(picking.type_transaction.code) + '-' + str(
                            picking.type_transaction.name)
                    elif loc_ori.usage == 'production' and loc_des.usage == 'internal':
                        type_operation_move = SqlKardex.get_type_transaction(self, '19')
                    elif loc_ori.usage == 'internal' and loc_des.usage == 'production':
                        type_operation_move = SqlKardex.get_type_transaction(self, '10')
                    elif res['picking_id'] == None:
                        if loc_ori.usage == 'internal' and loc_des.usage == 'customer':
                            type_operation_move = SqlKardex.get_type_transaction(self, '01')

                    if loc_des.usage == 'inventory' and loc_des.scrap_location is True:
                        scrap = self.env['stock.scrap'].sudo().search([('name', '=', res['origin'])])
                        type_operation_move = scrap.type_transaction.code + '-' + scrap.type_transaction.name

                    if loc_des.usage == 'internal':
                        cant_entrada = round(res['product_uom_qty'], 2)
                        saldo_ = saldo_ + cant_entrada
                        data = {"initial_balance_uni": saldo_, "account_move": res['id'],
                                "initial_cant_uni": cant_entrada}
                        SqlKardex.update_acc_mov_physical(self, data)
                    else:
                        cant_salida = round(res['product_uom_qty'], 2)  # Dato Positivo
                        saldo_ = saldo_ - abs(cant_salida)
                        data = {"initial_balance_uni": saldo_, "account_move": res['id'],
                                "initial_cant_uni": abs(cant_salida)}
                        SqlKardex.update_acc_mov_physical(self, data)

                    data_ = {"reference_code": reference_code, "product": product_env,
                             "establishment": options['establishment']['name'],
                             "level": 3,
                             "serie_code": serie_code, "type_operation_move": type_operation_move,
                             "cant_entrada": cant_entrada, "cant_salida": cant_salida,
                             "res": res, "saldo": saldo_}
                    lines.append(k_tool.add_line_physical_op(data_))

            # SALDO INICIAL DE PRODUCTO QUE TIENEN STOCK
            mov_init = SqlKardex.get_stock_init_prod(self, obj_init)

            for sald in mov_init:
                loc_des = stock_location.sudo().browse(sald['location_dest_id'])
                loc_ori = stock_location.sudo().browse(sald['location_id'])
                product_env = product_product.sudo().browse(sald['product_id'])
                type_operation_init = type_transaction.search([('code', '=', '16')],
                                                              limit=1)
                saldo_ = sald['initial_cant_uni'] or 0.00
                if options['establishment']['id'] in [loc_des.establishment.id, loc_ori.establishment.id]:
                    if saldo_ != 0.00:
                        data_ = {"date_from": options['date_from'], "product": product_env,
                                 "establishment": options['establishment']['name'],
                                 "level": 2,
                                 "line_id": sald['id'],
                                 "saldo_inicial": "",
                                 "type_operation_init": type_operation_init,
                                 "res": sald, "saldo": saldo_}
                        lines.append(k_tool.add_line_physical(data_))
        else:
            mov = SqlKardex.get_valorizado(self, obj_init)
            saldo_ = 0.0
            cant_total = 0.0
            cost_total = 0.00
            product_eq = 0
            for res in mov:
                date_move = res['date']
                cant_entrada = 0.00
                cant_salida = 0.00
                cost_entrada = 0.00
                cost_salida = 0.00
                entrada = 0.00
                salida = 0.00
                product_env = product_product.sudo().browse(res['product_id'])
                if res['stock_move_id'] is not None:
                    stock_move = SqlKardex.get_stock_move(self, {"stock_move": res['stock_move_id']})
                    loc_des = stock_location.sudo().browse(stock_move['location_dest_id'])
                    loc_ori = stock_location.sudo().browse(stock_move['location_id'])
                    if options['establishment']['id'] in [loc_des.establishment.id, loc_ori.establishment.id]:
                        reference_code = ''
                        if stock_move['picking_id'] != None:
                            picking_sale = SqlKardex.get_picking_doc(self, stock_move['picking_id'])
                            if not picking_sale['type_doc']:
                                raise ValidationError(_(
                                    "There is a Buy / Sell movement without a reference document: Type document: %s " %
                                    picking_sale['name']))
                            if not picking_sale['serie_doc']:
                                raise ValidationError(_(
                                    "There is a Buy / Sell movement without a reference document: Serie document: %s " %
                                    picking_sale['name']))
                            if not picking_sale['number_doc']:
                                raise ValidationError(_(
                                    "There is a Buy / Sell movement without a reference document: Number document: %s " %
                                    picking_sale['name']))
                            reference_code = picking_sale['type_doc'] + '-' + picking_sale['serie_doc'] + '-' + \
                                             picking_sale['number_doc']
                        type_operation_move = ''
                        if stock_move['inventory_id'] != None:
                            inventory = stock_inventory.sudo().browse(stock_move['inventory_id'])
                            type_operation_move = inventory.type_transaction.code + '-' + inventory.type_transaction.name
                        elif stock_move['picking_id'] != None:
                            picking = stock_picking.sudo().browse(stock_move['picking_id'])
                            type_operation_move = str(picking.type_transaction.code) + '-' + str(
                                picking.type_transaction.name)
                        elif loc_ori.usage == 'production' and loc_des.usage == 'internal':
                            type_operation_move = SqlKardex.get_type_transaction(self, '19')
                        elif loc_ori.usage == 'internal' and loc_des.usage == 'production':
                            type_operation_move = SqlKardex.get_type_transaction(self, '10')
                        elif stock_move['picking_id'] == None:
                            if loc_ori.usage == 'internal' and loc_des.usage == 'customer':
                                type_operation_move = SqlKardex.get_type_transaction(self, '01')

                        if loc_des.usage == 'inventory' and loc_des.scrap_location is True:
                            scrap = self.env['stock.scrap'].sudo().search([('name', '=', stock_move['origin'])])
                            type_operation_move = scrap.type_transaction.code + '-' + scrap.type_transaction.name

                        type_operation_init = type_transaction.search(
                            [('code', '=', '16')], limit=1)
                        if saldo_ == 0 and product_eq == 0:
                            obj = {"date_initial": date_initial, "product_id": res['product_id'],
                                   "journal_id": journal.id,
                                   "company_id": options['company_id']}
                            saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)

                            if saldo_inicial:
                                saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                                cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                                cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                                product_eq = res['product_id']
                            else:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                                product_eq = res['product_id']

                            if saldo_ != 0.00:
                                data_ = {"date_from": options['date_from'], "product": product_env,
                                         "establishment": options['establishment']['name'],
                                         "level": 2,
                                         "stock_move": stock_move, "reference_code": reference_code,
                                         "type_operation_init": type_operation_init,
                                         "res": res, "cant_total": cant_total, "cost_total": cost_total,
                                         "saldo_": saldo_}
                                lines.append(k_tool.add_line_valued(data_))
                        else:
                            if product_eq == res['product_id']:
                                pass
                            else:
                                obj = {"date_initial": date_initial, "product_id": res['product_id'],
                                       "journal_id": journal.id,
                                       "company_id": options['company_id']}
                                saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)
                                if saldo_inicial:
                                    saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                                    cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                                    cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                                    product_eq = res['product_id']
                                else:
                                    saldo_ = 0.00
                                    cant_total = 0.00
                                    cost_total = 0.00
                                    product_eq = res['product_id']

                                if saldo_ != 0.00:
                                    data_ = {"date_from": options['date_from'], "product": product_env,
                                             "establishment": options['establishment']['name'],
                                             "level": 2,
                                             "stock_move": stock_move, "reference_code": reference_code,
                                             "type_operation_init": type_operation_init,
                                             "res": res, "cant_total": cant_total, "cost_total": cost_total,
                                             "saldo_": saldo_}
                                    lines.append(k_tool.add_line_valued(data_))

                        if loc_des.usage == 'internal':
                            price_unit = res['amount_total'] / stock_move['product_uom_qty']
                            value_stock = stock_move['product_uom_qty'] * price_unit
                            entrada = round(value_stock, 2)
                            saldo_ = saldo_ + entrada
                            cant_entrada = round(stock_move['product_uom_qty'], 2)
                            cost_entrada = round(price_unit, 2)
                            cant_total = cant_total + cant_entrada
                            cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else 0.00
                            if round(cant_total, 2) <= 0:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                            data = {"initial_balance": saldo_, "account_move": res['id'],
                                    "initial_cant": cant_total, "initial_cost": cost_total}
                            SqlKardex.update_acc_mov_valued(self, data)
                        else:
                            price_unit = res['amount_total'] / stock_move['product_uom_qty']
                            value_stock = stock_move['product_uom_qty'] * price_unit
                            salida = round(value_stock, 2)  # Dato Negativo
                            saldo_ = saldo_ - abs(salida)
                            cant_salida = round(stock_move['product_uom_qty'], 2)  # Dato Positivo
                            cost_salida = round(price_unit, 2)  # Dato Negativo
                            cant_total = cant_total - abs(cant_salida)
                            cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else 0.00
                            if round(cant_total, 2) <= 0:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                            data = {"initial_balance": saldo_, "account_move": res['id'],
                                    "initial_cant": cant_total, "initial_cost": cost_total}
                            SqlKardex.update_acc_mov_valued(self, data)

                        data_ = {"product": product_env, "establishment": options['establishment']['name'],
                                 "level": 3,
                                 "stock_move": stock_move, "reference_code": reference_code,
                                 "type_operation_move": type_operation_move,
                                 "res": res, "cant_entrada": cant_entrada, "cost_entrada": cost_entrada,
                                 "entrada": entrada, "cant_salida": cant_salida, "cost_salida": cost_salida,
                                 "salida": salida, "cant_total": cant_total, "cost_total": cost_total,
                                 "saldo_": saldo_}
                        lines.append(k_tool.add_line_valued_op(data_))
                else:
                    type_operation_init = type_transaction.search([('code', '=', '16')], limit=1)
                    type_operation_move = type_transaction.search([('cost_adjustment', '=', True)], limit=1)
                    if saldo_ == 0 and product_eq == 0:
                        obj = {"date_initial": date_initial, "product_id": res['product_id'],
                               "journal_id": journal.id,
                               "company_id": options['company_id']}
                        saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)

                        if saldo_inicial:
                            saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                            cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                            cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                            product_eq = res['product_id']
                        else:
                            saldo_ = 0.00
                            cant_total = 0.00
                            cost_total = 0.00
                            product_eq = res['product_id']

                        data__ = {
                            "date_from": options['date_from'], "product": product_env,
                            "establishment": options['establishment']['name'],
                            "level": 2,
                            "stock_move": {'reference': ''}, "reference_code": '',
                            "type_operation_init": type_operation_init,
                            "res": res, "cant_total": cant_total, "cost_total": cost_total,
                            "saldo_": saldo_
                        }
                        lines.append(k_tool.add_line_valued(data__))
                    else:
                        if product_eq == res['product_id']:
                            pass
                        else:
                            obj = {"date_initial": date_initial, "product_id": res['product_id'],
                                   "journal_id": journal.id,
                                   "company_id": options['company_id']}
                            saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)
                            if saldo_inicial:
                                saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                                cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                                cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                                product_eq = res['product_id']
                            else:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                                product_eq = res['product_id']

                            data__ = {
                                "date_from": options['date_from'], "product": product_env,
                                "establishment": options['establishment']['name'],
                                "level": 2,
                                "stock_move": {'reference': ''}, "reference_code": '',
                                "type_operation_init": type_operation_init,
                                "res": res, "cant_total": cant_total, "cost_total": cost_total,
                                "saldo_": saldo_
                            }
                            lines.append(k_tool.add_line_valued(data__))

                    balance = SqlKardex.get_update_cost(self,
                                                        {"move_id": res["move_id"],
                                                         "product_id": res["product_id"]})
                    if balance['value'] > 0:
                        entrada = round(res['amount_total'], 2)
                        saldo_ = saldo_ + entrada
                        cant_entrada = 0.00
                        cost_entrada = 0.00
                        cant_total = cant_total + cant_entrada
                        cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else format(0.00,
                                                                                                 '.2f')
                        if cant_total <= 0:
                            saldo_ = 0.00
                            cant_total = 0.00
                            cost_total = 0.00
                        data = {"initial_balance": saldo_, "account_move": res['id'],
                                "initial_cant": cant_total, "initial_cost": cost_total}
                        SqlKardex.update_acc_mov_valued(self, data)
                    else:
                        salida = round(res['amount_total'], 2)
                        saldo_ = saldo_ - salida
                        cant_salida = 0.00
                        cost_salida = 0.00
                        cant_total = cant_total - cant_salida
                        cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else format(0.00,
                                                                                                 '.2f')
                        if round(cant_total, 2) <= 0:
                            saldo_ = 0.00
                            cant_total = 0.00
                            cost_total = 0.00
                        data = {"initial_balance": saldo_, "account_move": res['id'],
                                "initial_cant": cant_total, "initial_cost": cost_total}
                        SqlKardex.update_acc_mov_valued(self, data)

                    data__ = {"product": product_env, "establishment": options['establishment']['name'],
                              "level": 3,
                              "stock_move": {'reference': ''}, "reference_code": '',
                              "type_operation_move": type_operation_move.name,
                              "res": res, "cant_entrada": cant_entrada, "cost_entrada": cost_entrada,
                              "entrada": entrada, "cant_salida": cant_salida, "cost_salida": cost_salida,
                              "salida": salida, "cant_total": cant_total, "cost_total": cost_total,
                              "saldo_": saldo_}
                    lines.append(k_tool.add_line_valued_op(data__))

            obj_init = {"date_from": options['date_from'], "date_to": options['date_to'], "journal": journal.id,
                        "company": options['company_id'],
                        "date_initial": date_initial}
            # SALDO INICIAL DE PRODUCTO QUE TIENEN STOCK
            mov_init = SqlKardex.get_stock_init_prod_valued(self, obj_init)
            for sald in mov_init:
                product_env = product_product.sudo().browse(sald['product_id'])
                type_operation_init = type_transaction.search([('code', '=', '16')],
                                                              limit=1)
                saldo_ = sald['initial_balance'] or 0.00
                cant_total = sald['initial_cant'] or 0.00
                cost_total = sald['initial_cost'] or 0.00

                data__ = {"date_from": sald['date'], "product": product_env,
                          "establishment": options['establishment']['name'],
                          "level": 2,
                          "stock_move": {'reference': ''}, "reference_code": '',
                          "type_operation_init": type_operation_init,
                          "res": sald, "cant_total": cant_total, "cost_total": cost_total,
                          "saldo_": saldo_}
                lines.append(k_tool.add_line_valued(data__))

        return lines

    def get_xlsx(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name(data)[:31])

        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'align': 'center', })
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_1_number = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666',
             'num_format': '#,##0.00'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_number = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666',
             'num_format': '#,##0.00'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_number = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': '#,##0.00'})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        detail_general = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'font_color': '#666666', 'align': 'center'})
        line_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'align': 'start', })
        name_bold = workbook.add_format({'font_name': 'Arial', 'bold': True})

        # Set the first column width to 50
        # sheet.set_column(0, 0, 5)
        sheet.merge_range('E2:H2' if data['type_kardex'] == 'units' else 'H2:K2',
                          _('PHYSICAL KARDEX') if data['type_kardex'] == 'units' else _('VALORIZED KARDEX'),
                          title_style)
        sheet.merge_range('E3:H3' if data['type_kardex'] == 'units' else 'H3:K3', _('General detail'), detail_general)

        company = self.env.user.company_id
        image_data = io.BytesIO(base64.b64decode(company.logo))  # to convert it to base64 file
        sheet.insert_image('A3', 'logo', {'image_data': image_data, 'x_scale': 0.5, 'y_scale': 0.5})
        sheet.merge_range('D4:E4', _('Ruc:'), name_bold)
        sheet.merge_range('F4:G4', company.vat)
        sheet.merge_range('D5:E5', _('Address:'), name_bold)
        sheet.merge_range('F5:K5', company.street)
        sheet.merge_range('D6:E6', _('Mail:'), name_bold)
        sheet.merge_range('F6:G6', company.email)
        sheet.merge_range('H4:I4', _('Business name:'), name_bold)
        sheet.merge_range('J4:K4', company.name)
        sheet.merge_range('H6:I6', _('Phone:'), name_bold)
        sheet.merge_range('J6:K6', company.phone)
        sheet.merge_range('A8:K8' if data['type_kardex'] == 'units' else 'A8:P8',
                          _('INVENTORY RECORD IN PHYSICAL UNITS') if data[
                                                                         'type_kardex'] == 'units' else _(
                              'RECORD OF PERMANENT INVENTORY VALUED'),
                          line_style)
        sheet.merge_range('A9:C9', _('PERIOD:'), name_bold)
        sheet.merge_range('D9:F9',
                          _("from:") + " " + data['date_from'] + " " + _("to:") + " " + data['date_to'])
        sheet.merge_range('A10:C10', _('RUC:'), name_bold)
        sheet.merge_range('D10:F10', company.vat)
        sheet.merge_range('A11:C11', _('BUSINESS NAME:'), name_bold)
        sheet.merge_range('D11:F11', company.name)
        sheet.merge_range('A12:C12', _('ESTABLISHMENT:'), name_bold)
        sheet.merge_range('D12:F12', str(data['establishment']['name']).upper())
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)
        sheet.set_column('O:O', 15)
        sheet.set_column('P:P', 15)

        y_offset = 13

        for row in self.get_header(data):
            x = 0
            for column in row:
                colspan = column.get('colspan', 1)
                header_label = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                if colspan == 1:
                    sheet.write(y_offset, x, header_label, title_style)
                else:
                    sheet.merge_range(y_offset, x, y_offset, x + colspan - 1, header_label, title_style)
                x += colspan
            y_offset += 1

        lines = self._get_lines(data)

        # write all data rows
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
                style_number = level_1_number
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_2_col1_total_style or level_2_col1_style
                style_number = level_2_number
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_3_col1_total_style or level_3_col1_style
                style_number = level_3_number
            else:
                style = default_style
                col1_style = default_col1_style
                style_number = level_3_number

            # write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            elif cell_type == 'number':
                sheet.write_number(y + y_offset, 0, cell_value, level_1_number)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            # write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                elif cell_type == 'number':
                    sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style_number)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _get_cell_type_value(self, cell):
        if cell.get('class') == 'number':
            return ('number', cell.get('name', ''))
        elif 'date' not in cell.get('class', '') or not cell.get('name'):
            # cell is not a date
            return ('text', cell.get('name', ''))
        elif isinstance(cell['name'], (float, datetime.date, datetime.datetime)):
            # the date is xlsx compatible
            return ('date', cell['name'])

        try:
            # the date is parsable to a xlsx compatible date
            lg = self.env['res.lang']._lang_get(self.env.user.lang) or get_lang(self.env)
            return ('date', datetime.strptime(cell['name'], lg.date_format))
        except:
            # the date is not parsable thus is returned as text
            return ('text', cell['name'])

    def get_txt(self, options):
        content = ""
        moves_json = self.get_moves_json(options)
        if options['type_kardex'] == 'units':
            for move in moves_json:
                content += k_tool.data_txt_units(move)
        else:
            for move in moves_json:
                content += k_tool.data_txt_valued(move)
        return content

    @api.model
    def get_moves_json(self, options):

        journal = self.env['account.journal'].sudo().search(
            [('code', '=', 'STJ'), ('company_id', '=', options['company_id'])], limit=1)
        stock_location = self.env['stock.location']
        stock_picking = self.env['stock.picking']
        stock_inventory = self.env['stock.inventory']
        product_product = self.env['product.product']
        establishment = self.env['pragmatic.establishment']
        type_transaction = self.env['pragmatic.type.operation.table.12']
        date_from = datetime.datetime.strptime(options["date_from"], "%Y-%m-%d")
        date_initial = date_from + datetime.timedelta(days=-1)
        account_period = datetime.datetime.strptime(options["date_to"], "%Y-%m-%d")
        obj_init = {"date_from": options["date_from"], "date_to": options["date_to"], "journal": journal.id,
                    "company": options["company_id"],
                    "date_initial": date_initial}
        res_company = self.env["res.company"].sudo().browse(options["company_id"])
        moves_json = []
        if options["type_kardex"] == 'units':
            mov_uni = SqlKardex.get_unidades(self, obj_init)
            saldo_ = 0.0
            product_eq = 0
            for res in mov_uni:
                date_move = res['date']
                cant_entrada = 0.00
                cant_salida = 0.00
                product_env = product_product.sudo().browse(res['product_id'])
                date_emi2 = datetime.datetime.strptime(str(date_move), "%Y-%m-%d")

                # CODE PRODUCT unspsc
                onu_code = ''
                if product_env.product_tmpl_id.unspsc_code_id.code:
                    onu_code = product_env.product_tmpl_id.unspsc_code_id.code + "00000000"

                loc_des = stock_location.sudo().browse(res['location_dest_id'])
                loc_ori = stock_location.sudo().browse(res['location_id'])
                code_stable = ''
                type_doc = '00'
                serie_doc = '0'
                number_doc = '0'

                if res['picking_id'] != None:
                    picking_sale = SqlKardex.get_picking_doc(self, res['picking_id'])
                    type_doc = picking_sale['type_doc']
                    serie_doc = picking_sale['serie_doc']
                    number_doc = picking_sale['number_doc']

                type_operation_move = ''
                if res['inventory_id'] != None:
                    inventory = stock_inventory.sudo().browse(res['inventory_id'])
                    type_operation_move = inventory.type_transaction.code
                elif res['picking_id'] != None:
                    picking = stock_picking.sudo().browse(res['picking_id'])
                    type_operation_move = picking.type_transaction.code
                elif loc_ori.usage == 'production' and loc_des.usage == 'internal':
                    # para el caso de excel y vista consultar el modelo sunat_tipo_transaccion where code
                    type_operation_move = '19'
                elif loc_ori.usage == 'internal' and loc_des.usage == 'production':
                    type_operation_move = '10'
                elif res['picking_id'] == None:
                    if loc_ori.usage == 'internal' and loc_des.usage == 'customer':
                        type_operation_move = '01'

                if loc_des.usage == 'inventory' and loc_des.scrap_location is True:
                    scrap = self.env['stock.scrap'].sudo().search([('name', '=', res['origin'])])
                    type_operation_move = scrap.type_transaction.code

                if options['establishment']['id'] in [loc_des.establishment.id, loc_ori.establishment.id]:
                    # Saldo inicial
                    type_operation_init = type_transaction.search(
                        [('code', '=', '16')], limit=1)
                    obj_physical = {"date_initial": date_initial, "product_id": res['product_id'],
                                    "journal_id": journal.id, "company_id": options["company_id"]}
                    if saldo_ == 0 and product_eq == 0:
                        saldo_inicial = SqlKardex.get_balance_start_physical(self, obj_physical)
                        location = establishment.sudo().browse(options['establishment']['id'])

                        if saldo_inicial:
                            saldo_ = saldo_inicial[0]['initial_cant_uni'] or 0.00
                            product_eq = res['product_id']
                        else:
                            saldo_ = 0.00
                            product_eq = res['product_id']

                        if saldo_ != 0.00:
                            data = {"account_period": account_period,
                                    "cuo": saldo_inicial[0]['id'] if saldo_inicial else res['id'],
                                    "account_correlative": saldo_inicial[0]['id'] if saldo_inicial else res['id'],
                                    "code_establishment": location.sunat_code,
                                    "code_catalog": res_company.catalog_exist or '',
                                    "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                    "code_existence": res_company.catalog_exist_des or '',
                                    "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                    "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                    "type_document_move": type_doc,
                                    "series_document_move": serie_doc,
                                    "number_document_move": number_doc,
                                    "type_operation": type_operation_init.code,
                                    "description_existence": product_env.display_name,
                                    "code_uom": product_env.product_tmpl_id.uom_id.sunat_unit_measure.code or '',
                                    "entry_input_phisical": format(saldo_, '.2f') or format(0.00, '.2f'),
                                    "entry_ouput_phisical": format(0.00, '.2f'),
                                    "state_operation": '1'}
                            json_data = k_tool.get_data_init_units(data)
                            moves_json.append(json_data)

                    else:
                        if product_eq == res['product_id']:
                            pass
                        else:
                            saldo_inicial = SqlKardex.get_balance_start_physical(self, obj_physical)
                            location = establishment.sudo().browse(options['establishment']['id'])

                            if saldo_inicial:
                                saldo_ = saldo_inicial[0]['initial_cant_uni'] or 0.00
                                product_eq = res['product_id']
                            else:
                                saldo_ = 0.00
                                product_eq = res['product_id']

                            if saldo_ != 0.00:
                                data = {"account_period": account_period,
                                        "cuo": saldo_inicial[0]['id'] if saldo_inicial else res['id'],
                                        "account_correlative": saldo_inicial[0]['id'] if saldo_inicial else res[
                                            'id'],
                                        "code_establishment": location.sunat_code,
                                        "code_catalog": res_company.catalog_exist or '',
                                        "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                        "code_existence": res_company.catalog_exist_des or '',
                                        "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                        "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                        "type_document_move": type_doc,
                                        "series_document_move": serie_doc,
                                        "number_document_move": number_doc,
                                        "type_operation": type_operation_init.code,
                                        "description_existence": product_env.display_name,
                                        "code_uom": product_env.product_tmpl_id.uom_id.sunat_unit_measure.code or '',
                                        "entry_input_phisical": format(saldo_, '.2f') or format(0.00, '.2f'),
                                        "entry_ouput_phisical": format(0.00, '.2f'),
                                        "state_operation": '1'}
                                json_data = k_tool.get_data_init_units(data)
                                moves_json.append(json_data)

                if loc_des.usage == 'internal':
                    if options['establishment']['id'] == loc_des.establishment.id:
                        cant_entrada = round(res['product_uom_qty'], 2)
                        saldo_ = saldo_ + cant_entrada
                        data = {"initial_balance_uni": saldo_, "account_move": res['id'],
                                "initial_cant_uni": cant_entrada}
                        SqlKardex.update_acc_mov_physical(self, data)

                        data = {"account_period": account_period, "cuo": res['id'],
                                "account_correlative": res['id'],
                                "code_establishment": loc_des.establishment.sunat_code,
                                "code_catalog": res_company.catalog_exist or '',
                                "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                "code_existence": res_company.catalog_exist_des or '',
                                "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                "type_document_move": type_doc,
                                "series_document_move": serie_doc,
                                "number_document_move": number_doc,
                                "type_operation": type_operation_move,
                                "description_existence": product_env.display_name,
                                "code_uom": product_env.product_tmpl_id.uom_id.sunat_unit_measure.code or '',
                                "entry_input_phisical": format(cant_entrada, '.2f') or format(0.00, '.2f'),
                                "entry_ouput_phisical": format(0.00, '.2f'),
                                "state_operation": '1'}
                        json_data = k_tool.get_data_init_units(data)
                        moves_json.append(json_data)
                else:
                    if options['establishment']['id'] == loc_ori.establishment.id:
                        cant_salida = round(res['product_uom_qty'], 2)  # Dato Positivo
                        saldo_ = saldo_ - abs(cant_salida)
                        data = {"initial_balance_uni": saldo_, "account_move": res['id'],
                                "initial_cant_uni": abs(cant_salida)}
                        SqlKardex.update_acc_mov_physical(self, data)
                        data = {"account_period": account_period, "cuo": res['id'],
                                "account_correlative": res['id'],
                                "code_establishment": loc_ori.establishment.sunat_code,
                                "code_catalog": res_company.catalog_exist or '',
                                "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                "code_existence": res_company.catalog_exist_des or '',
                                "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                "type_document_move": type_doc,
                                "series_document_move": serie_doc,
                                "number_document_move": number_doc,
                                "type_operation": type_operation_move,
                                "description_existence": product_env.display_name,
                                "code_uom": product_env.product_tmpl_id.uom_id.sunat_unit_measure.code or '',
                                "entry_input_phisical": format(0.00, '.2f'),
                                "entry_ouput_phisical": format(-abs(cant_salida), '.2f') if abs(
                                    cant_salida) > 0.00 else format(abs(cant_salida), '.2f'),
                                # or format(0.00,'.2f'),
                                "state_operation": '1'}
                        json_data = k_tool.get_data_init_units(data)
                        moves_json.append(json_data)

            # SALDO INICIAL DE PRODUCTO QUE TIENEN STOCK
            mov_init = SqlKardex.get_stock_init_prod(self, obj_init)
            init_prod = 0
            for sald in mov_init:
                location = establishment.sudo().browse(options['establishment']['id'])
                # CODE PRODUCT unspsc
                product_env = product_product.sudo().browse(sald['product_id'])
                onu_code = ''
                if product_env.product_tmpl_id.unspsc_code_id.code:
                    onu_code = product_env.product_tmpl_id.unspsc_code_id.code + "00000000"
                type_doc = '00'
                serie_doc = '0'
                number_doc = '0'
                date_move = sald['date']
                date_emi2 = datetime.datetime.strptime(str(date_move), "%Y-%m-%d")
                type_operation_init = type_transaction.search([('code', '=', '16')],
                                                              limit=1)
                saldo_ = sald['initial_cant_uni'] or 0.00
                if saldo_ != 0.00:
                    data = {"account_period": account_period, "cuo": sald['id'],
                            "account_correlative": sald['id'],
                            "code_establishment": location.sunat_code,
                            "code_catalog": res_company.catalog_exist or '',
                            "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                            "code_existence": res_company.catalog_exist_des or '',
                            "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                            "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                            "type_document_move": type_doc,
                            "series_document_move": serie_doc,
                            "number_document_move": number_doc,
                            "type_operation": type_operation_init.code,
                            "description_existence": product_env.display_name,
                            "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                            "entry_input_phisical": format(saldo_, '.2f') or format(0.00, '.2f'),
                            "entry_ouput_phisical": format(0.00, '.2f'),
                            "state_operation": '1'}
                    json_data = k_tool.get_data_init_units(data)
                    moves_json.append(json_data)
        else:
            mov = SqlKardex.get_valorizado(self, obj_init)
            cont = 0
            cont2 = 0
            saldo_ = 0.0
            cant_total = 0.0
            cost_total = 0.00
            product_eq = 0

            for res in mov:
                date_move = res['date']
                cant_entrada = 0.00
                cant_salida = 0.00
                cost_entrada = 0.00
                cost_salida = 0.00
                entrada = 0.00
                salida = 0.00
                product_env = product_product.sudo().browse(res['product_id'])
                date_emi2 = datetime.datetime.strptime(str(date_move), "%Y-%m-%d")

                # CODE PRODUCT it_unspsc
                onu_code = ''
                if product_env.product_tmpl_id.unspsc_code_id.code:
                    onu_code = product_env.product_tmpl_id.unspsc_code_id.code + "00000000"
                cost_method = ''
                if product_env.product_tmpl_id.categ_id.property_cost_method:
                    if product_env.product_tmpl_id.categ_id.property_cost_method == 'standard':
                        cost_method = 3
                    elif product_env.product_tmpl_id.categ_id.property_cost_method == 'fifo':
                        cost_method = 2
                    elif product_env.product_tmpl_id.categ_id.property_cost_method == 'average':
                        cost_method = 1
                if res['stock_move_id'] is not None:
                    stock_move = SqlKardex.get_stock_move(self, {"stock_move": res['stock_move_id']})
                    loc_des = stock_location.sudo().browse(stock_move['location_dest_id'])
                    loc_ori = stock_location.sudo().browse(stock_move['location_id'])
                    code_stable = ''
                    type_doc = '00'
                    serie_doc = '0'
                    number_doc = '0'

                    if stock_move['picking_id'] != None:
                        picking_sale = SqlKardex.get_picking_doc(self, stock_move['picking_id'])
                        type_doc = picking_sale['type_doc']
                        serie_doc = picking_sale['serie_doc']
                        number_doc = picking_sale['number_doc']

                    type_operation_move = ''
                    if stock_move['inventory_id'] != None:
                        inventory = stock_inventory.sudo().browse(stock_move['inventory_id'])
                        type_operation_move = inventory.type_transaction.code
                    elif stock_move['picking_id'] != None:
                        picking = stock_picking.sudo().browse(stock_move['picking_id'])
                        type_operation_move = picking.type_transaction.code
                    elif loc_ori.usage == 'production' and loc_des.usage == 'internal':
                        # para el caso de excel y vista consultar el modelo it_sunat_tipo_transaccion where code
                        type_operation_move = '19'
                    elif loc_ori.usage == 'internal' and loc_des.usage == 'production':
                        # para el caso de excel y vista consultar el modelo it_sunat_tipo_transaccion where code
                        type_operation_move = '10'
                    elif stock_move['picking_id'] == None:
                        if loc_ori.usage == 'internal' and loc_des.usage == 'customer':
                            type_operation_move = '01'

                    if loc_des.usage == 'inventory' and loc_des.scrap_location is True:
                        scrap = self.env['stock.scrap'].sudo().search([('name', '=', stock_move['origin'])])
                        type_operation_move = scrap.type_transaction.code

                    if options['establishment']['id'] in [loc_des.establishment.id, loc_ori.establishment.id]:
                        # Saldo inicial
                        type_operation_init = type_transaction.search([('code', '=', '16')], limit=1)
                        if saldo_ == 0 and product_eq == 0:
                            obj = {"date_initial": date_initial, "product_id": res['product_id'],
                                   "journal_id": journal.id, "company_id": options["company_id"]}
                            saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)

                            if saldo_inicial:
                                saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                                cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                                cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                                product_eq = res['product_id']
                            else:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                                product_eq = res['product_id']

                            if saldo_ != 0.00:
                                data = {"account_period": account_period,
                                        "cuo": saldo_inicial[0]['id'] if saldo_inicial else res['id'],
                                        "account_correlative": saldo_inicial[0]['id'] if saldo_inicial else res[
                                            'id'],
                                        "code_establishment": loc_des.establishment.sunat_code,
                                        "code_catalog": res_company.catalog_exist or '',
                                        "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                        "code_existence": res_company.catalog_exist_des or '',
                                        "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                        "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                        "type_document_move": type_doc,
                                        "series_document_move": serie_doc,
                                        "number_document_move": number_doc,
                                        "type_operation": type_operation_init.code,
                                        "description_existence": product_env.display_name,
                                        "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                                        "cost_method": cost_method,
                                        "cant_input": format(cant_total, '.2f'),
                                        "cost_unit_input": format(cost_total, '.2f'),
                                        "cost_total_input": format(saldo_, '.2f'),
                                        "cant_ouput": format(0.00, '.2f'),
                                        "cost_unit_ouput": format(0.00, '.2f'),
                                        "cost_total_ouput": format(0.00, '.2f'),
                                        "cant_saldo_final": format(cant_total, '.2f'),
                                        "cost_unit_saldo_final": format(cost_total, '.2f'),
                                        "cost_saldo_final": format(saldo_, '.2f'),
                                        # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                                        "state_operation": '1'}
                                json_data = k_tool.get_data_init_valued(data)
                                moves_json.append(json_data)
                        else:
                            if product_eq == res['product_id']:
                                pass
                            else:
                                obj = {"date_initial": date_initial, "product_id": res['product_id'],
                                       "journal_id": journal.id, "company_id": options["company_id"]}
                                saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)
                                if saldo_inicial:
                                    saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                                    cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                                    cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                                    product_eq = res['product_id']
                                else:
                                    saldo_ = 0.00
                                    cant_total = 0.00
                                    cost_total = 0.00
                                    product_eq = res['product_id']

                                if saldo_ != 0.00:
                                    data = {"account_period": account_period,
                                            "cuo": saldo_inicial[0]['id'] if saldo_inicial else res['id'],
                                            "account_correlative": saldo_inicial[0]['id'] if saldo_inicial else res[
                                                'id'],
                                            "code_establishment": loc_des.establishment.sunat_code,
                                            "code_catalog": res_company.catalog_exist or '',
                                            "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                            "code_existence": res_company.catalog_exist_des or '',
                                            "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                            "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                            "type_document_move": type_doc,
                                            "series_document_move": serie_doc,
                                            "number_document_move": number_doc,
                                            "type_operation": type_operation_init.code,
                                            "description_existence": product_env.display_name,
                                            "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                                            "cost_method": cost_method,
                                            "cant_input": format(cant_total, '.2f'),
                                            "cost_unit_input": format(cost_total, '.2f'),
                                            "cost_total_input": format(saldo_, '.2f'),
                                            "cant_ouput": format(0.00, '.2f'),
                                            "cost_unit_ouput": format(0.00, '.2f'),
                                            "cost_total_ouput": format(0.00, '.2f'),
                                            "cant_saldo_final": format(cant_total, '.2f'),
                                            "cost_unit_saldo_final": format(cost_total, '.2f'),
                                            "cost_saldo_final": format(saldo_, '.2f'),
                                            # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                                            "state_operation": '1'}
                                    json_data = k_tool.get_data_init_valued(data)
                                    moves_json.append(json_data)

                    if loc_des.usage == 'internal':
                        if options['establishment']['id'] == loc_des.establishment.id:
                            code_stable = loc_des.establishment.sunat_code
                            price_unit = res['amount_total'] / stock_move['product_uom_qty']
                            value_stock = stock_move['product_uom_qty'] * price_unit
                            entrada = round(value_stock, 2)
                            saldo_ = saldo_ + entrada
                            cant_entrada = round(stock_move['product_uom_qty'], 2)
                            cost_entrada = round(price_unit, 2)
                            cant_total = cant_total + cant_entrada
                            cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else 0.00
                            if round(cant_total, 2) <= 0:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                            data = {"initial_balance": saldo_, "account_move": res['id'],
                                    "initial_cant": cant_total, "initial_cost": cost_total}
                            SqlKardex.update_acc_mov_valued(self, data)
                            data = {"account_period": account_period, "cuo": res['id'],
                                    "account_correlative": res['id'],
                                    "code_establishment": code_stable,
                                    "code_catalog": res_company.catalog_exist or '',
                                    "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                    "code_existence": res_company.catalog_exist_des or '',
                                    "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                    "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                    "type_document_move": type_doc,
                                    "series_document_move": serie_doc,
                                    "number_document_move": number_doc,
                                    "type_operation": type_operation_move,
                                    "description_existence": product_env.display_name,
                                    "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                                    "cost_method": cost_method,
                                    "cant_input": format(cant_entrada, '.2f'),
                                    "cost_unit_input": format(cost_entrada, '.2f'),
                                    "cost_total_input": format(entrada, '.2f'),
                                    "cant_ouput": format(0.00, '.2f'),
                                    "cost_unit_ouput": format(0.00, '.2f'),
                                    "cost_total_ouput": format(0.00, '.2f'),
                                    "cant_saldo_final": format(cant_total, '.2f'),
                                    "cost_unit_saldo_final": format(cost_total, '.2f'),
                                    "cost_saldo_final": format(saldo_, '.2f'),
                                    # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                                    "state_operation": '1'}
                            json_data = k_tool.get_data_init_valued(data)

                            moves_json.append(json_data)
                            cont2 = cont2 + 1
                    else:
                        if options['establishment']['id'] == loc_ori.establishment.id:
                            code_stable = loc_ori.establishment.sunat_code
                            price_unit = res['amount_total'] / stock_move['product_uom_qty']
                            value_stock = stock_move['product_uom_qty'] * price_unit
                            salida = round(value_stock, 2)  # Dato Negativo
                            saldo_ = saldo_ - abs(salida)
                            cant_salida = round(stock_move['product_uom_qty'], 2)  # Dato Positivo
                            cost_salida = round(price_unit, 2)  # Dato Negativo
                            cant_total = cant_total - abs(cant_salida)
                            cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else 0.00
                            if round(cant_total, 2) <= 0:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                            data = {"initial_balance": saldo_, "account_move": res['id'],
                                    "initial_cant": cant_total, "initial_cost": cost_total}
                            SqlKardex.update_acc_mov_valued(self, data)
                            data = {"account_period": account_period, "cuo": res['id'],
                                    "account_correlative": res['id'],
                                    "code_establishment": code_stable,
                                    "code_catalog": res_company.catalog_exist or '',
                                    "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                    "code_existence": res_company.catalog_exist_des or '',
                                    "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                    "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                    "type_document_move": type_doc,
                                    "series_document_move": serie_doc,
                                    "number_document_move": number_doc,
                                    "type_operation": type_operation_move,
                                    "description_existence": product_env.display_name,
                                    "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                                    "cost_method": cost_method,
                                    "cant_input": format(0.00, '.2f'), "cost_unit_input": format(0.00, '.2f'),
                                    "cost_total_input": format(0.00, '.2f'),
                                    "cant_ouput": format(abs(cant_salida), '.2f'),
                                    "cost_unit_ouput": format(abs(cost_salida), '.2f'),
                                    "cost_total_ouput": format(abs(salida), '.2f'),
                                    "cant_saldo_final": format(cant_total, '.2f') if cant_total > 0 else format(0.00,
                                                                                                                '.2f'),
                                    "cost_unit_saldo_final": format(cost_total, '.2f') if cant_total > 0 else format(
                                        0.00, '.2f'),
                                    "cost_saldo_final": format(abs(saldo_), '.2f') if cant_total > 0 else format(0.00,
                                                                                                                 '.2f'),
                                    # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                                    "state_operation": '1'}
                            json_data = k_tool.get_data_init_valued(data)

                            moves_json.append(json_data)
                            cont2 = cont2 + 1
                else:
                    location = establishment.sudo().browse(options['establishment']['id'])
                    type_operation_init = type_transaction.search(
                        [('code', '=', '16')], limit=1)
                    type_operation_move = type_transaction.search(
                        [('it_cost_adjustment', '=', True)], limit=1)
                    type_doc = '00'
                    serie_doc = '0'
                    number_doc = '0'
                    if saldo_ == 0 and product_eq == 0:
                        obj = {"date_initial": date_initial, "product_id": res['product_id'],
                               "journal_id": journal.id, "company_id": options["company_id"]}
                        saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)

                        if saldo_inicial:
                            saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                            cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                            cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                            product_eq = res['product_id']
                        else:
                            saldo_ = 0.00
                            cant_total = 0.00
                            cost_total = 0.00
                            product_eq = res['product_id']

                        if saldo_ != 0.00:
                            data = {"account_period": account_period, "cuo": res['id'],
                                    "account_correlative": res['id'],
                                    "code_establishment": location.sunat_code,
                                    "code_catalog": res_company.catalog_exist or '',
                                    "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                    "code_existence": res_company.catalog_exist_des or '',
                                    "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                    "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                    "type_document_move": type_doc,
                                    "series_document_move": serie_doc,
                                    "number_document_move": number_doc,
                                    "type_operation": type_operation_init.code,
                                    "description_existence": product_env.display_name,
                                    "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                                    "cost_method": cost_method,
                                    "cant_input": format(cant_total, '.2f'),
                                    "cost_unit_input": format(cost_total, '.2f'),
                                    "cost_total_input": format(saldo_, '.2f'),
                                    "cant_ouput": format(0.00, '.2f'),
                                    "cost_unit_ouput": format(0.00, '.2f'),
                                    "cost_total_ouput": format(0.00, '.2f'),
                                    "cant_saldo_final": format(cant_total, '.2f'),
                                    "cost_unit_saldo_final": format(cost_total, '.2f'),
                                    "cost_saldo_final": format(saldo_, '.2f'),
                                    # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                                    "state_operation": '1'}
                            json_data = k_tool.get_data_init_valued(data)
                            moves_json.append(json_data)
                    else:
                        if product_eq == res['product_id']:
                            pass
                        else:
                            obj = {"date_initial": date_initial, "product_id": res['product_id'],
                                   "journal_id": journal.id, "company_id": options["company_id"]}
                            saldo_inicial = SqlKardex.get_balance_start_valued(self, obj)
                            if saldo_inicial:
                                saldo_ = saldo_inicial[0]['initial_balance'] or 0.00
                                cant_total = saldo_inicial[0]['initial_cant'] or 0.00
                                cost_total = saldo_inicial[0]['initial_cost'] or 0.00
                                product_eq = res['product_id']
                            else:
                                saldo_ = 0.00
                                cant_total = 0.00
                                cost_total = 0.00
                                product_eq = res['product_id']

                            if saldo_ != 0.00:
                                data = {"account_period": account_period, "cuo": res['id'],
                                        "account_correlative": res['id'],
                                        "code_establishment": location.sunat_code,
                                        "code_catalog": res_company.catalog_exist or '',
                                        "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                                        "code_existence": res_company.catalog_exist_des or '',
                                        "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                                        "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                                        "type_document_move": type_doc,
                                        "series_document_move": serie_doc,
                                        "number_document_move": number_doc,
                                        "type_operation": type_operation_init.code,
                                        "description_existence": product_env.display_name,
                                        "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                                        "cost_method": cost_method,
                                        "cant_input": format(cant_total, '.2f'),
                                        "cost_unit_input": format(cost_total, '.2f'),
                                        "cost_total_input": format(saldo_, '.2f'),
                                        "cant_ouput": format(0.00, '.2f'),
                                        "cost_unit_ouput": format(0.00, '.2f'),
                                        "cost_total_ouput": format(0.00, '.2f'),
                                        "cant_saldo_final": format(cant_total, '.2f'),
                                        "cost_unit_saldo_final": format(cost_total, '.2f'),
                                        "cost_saldo_final": format(saldo_, '.2f'),
                                        # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                                        "state_operation": '1'}
                                json_data = k_tool.get_data_init_valued(data)
                                moves_json.append(json_data)

                    balance = SqlKardex.get_update_cost(self, {"move_id": res["move_id"],
                                                               "product_id": res["product_id"]})
                    if balance['value'] > 0:
                        entrada = round(res['amount_total'], 2)
                        saldo_ = saldo_ + entrada
                        cant_entrada = 0.00
                        cost_entrada = 0.00
                        cant_total = cant_total + cant_entrada
                        cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else format(0.00,
                                                                                                 '.2f')
                        if round(cant_total, 2) <= 0:
                            saldo_ = 0.00
                            cant_total = 0.00
                            cost_total = 0.00
                        data = {"initial_balance": saldo_, "account_move": res['id'],
                                "initial_cant": cant_total, "initial_cost": cost_total}
                        SqlKardex.update_acc_mov_valued(self, data)
                    else:
                        salida = round(res['amount_total'], 2)
                        saldo_ = saldo_ - salida
                        cant_salida = 0.00
                        cost_salida = 0.00
                        cant_total = cant_total - cant_salida
                        cost_total = saldo_ / cant_total if round(cant_total, 2) > 0 else format(0.00,
                                                                                                 '.2f')
                        if round(cant_total, 2) <= 0:
                            saldo_ = 0.00
                            cant_total = 0.00
                            cost_total = 0.00
                        data = {"initial_balance": saldo_, "account_move": res['id'],
                                "initial_cant": cant_total, "initial_cost": cost_total}
                        SqlKardex.update_acc_mov_valued(self, data)
                    cont = cont + 1
                    data = {"account_period": account_period, "cuo": res['id'],
                            "account_correlative": res['id'],
                            "code_establishment": location.sunat_code,
                            "code_catalog": res_company.catalog_exist or '',
                            "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                            "code_existence": res_company.catalog_exist_des or '',
                            "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                            "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                            "type_document_move": type_doc,
                            "series_document_move": serie_doc,
                            "number_document_move": number_doc,
                            "type_operation": type_operation_move.code,
                            "description_existence": product_env.display_name,
                            "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                            "cost_method": cost_method,
                            "cant_input": format(cant_entrada, '.2f'),
                            "cost_unit_input": format(cost_entrada, '.2f'),
                            "cost_total_input": format(entrada, '.2f'),
                            "cant_ouput": format(cant_salida, '.2f'),
                            "cost_unit_ouput": format(cost_salida, '.2f'),
                            "cost_total_ouput": format(salida, '.2f'),
                            "cant_saldo_final": format(cant_total, '.2f'),
                            "cost_unit_saldo_final": format(cost_total, '.2f'),
                            "cost_saldo_final": format(saldo_, '.2f'),
                            # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                            "state_operation": '1'}
                    json_data = k_tool.get_data_init_valued(data)
                    moves_json.append(json_data)

            obj_init = {"date_from": options['date_from'], "date_to": options['date_to'], "journal": journal.id,
                        "company": options['company_id'],
                        "date_initial": date_initial}
            # SALDO INICIAL DE PRODUCTO QUE TIENEN STOCK
            mov_init = SqlKardex.get_stock_init_prod_valued(self, obj_init)
            init_prod = 0

            for sald in mov_init:
                location = establishment.sudo().browse(options['establishment']['id'])
                # CODE PRODUCT it_unspsc
                onu_code = ''
                if product_env.product_tmpl_id.unspsc_code_id.code:
                    onu_code = product_env.product_tmpl_id.unspsc_code_id.code + "00000000"
                cost_method = ''
                if product_env.product_tmpl_id.categ_id.property_cost_method:
                    if product_env.product_tmpl_id.categ_id.property_cost_method == 'standard':
                        cost_method = 3
                    elif product_env.product_tmpl_id.categ_id.property_cost_method == 'fifo':
                        cost_method = 2
                    elif product_env.product_tmpl_id.categ_id.property_cost_method == 'average':
                        cost_method = 1
                loc_des = stock_location.sudo().browse(stock_move['location_dest_id'])
                type_doc = '00'
                serie_doc = '0'
                number_doc = '0'
                product_env = product_product.sudo().browse(sald['product_id'])
                date_move = sald['date']
                date_emi2 = datetime.datetime.strptime(str(date_move), "%Y-%m-%d")
                type_operation_init = type_transaction.search([('code', '=', '16')],
                                                              limit=1)
                saldo_ = sald['initial_balance'] or 0.00
                cant_total = sald['initial_cant'] or 0.00
                cost_total = sald['initial_cost'] or 0.00
                if saldo_ != 0.00:
                    data = {"account_period": account_period, "cuo": sald['id'],
                            "account_correlative": sald['id'],
                            "code_establishment": location.sunat_code,
                            "code_catalog": res_company.catalog_exist or '',
                            "type_existence": product_env.product_tmpl_id.type_existence.code or '',
                            "code_existence": res_company.catalog_exist_des or '',
                            "code_existence_catalog": onu_code, "date_emision": "%s/%s/%s" % (
                            "%02d" % date_emi2.day, "%02d" % (date_emi2.month), date_emi2.year),
                            "type_document_move": type_doc,
                            "series_document_move": serie_doc,
                            "number_document_move": number_doc, "type_operation": type_operation_init.code,
                            "description_existence": product_env.display_name,
                            "code_uom": product_env.product_tmpl_id.uom_id.l10n_pe_edi_measure_unit_code or '',
                            "cost_method": cost_method,
                            "cant_input": format(cant_total, '.2f'), "cost_unit_input": format(cost_total, '.2f'),
                            "cost_total_input": format(saldo_, '.2f'),
                            "cant_ouput": format(0.00, '.2f'),
                            "cost_unit_ouput": format(0.00, '.2f'),
                            "cost_total_ouput": format(0.00, '.2f'),
                            "cant_saldo_final": format(cant_total, '.2f'),
                            "cost_unit_saldo_final": format(cost_total, '.2f'),
                            "cost_saldo_final": format(saldo_, '.2f'),
                            # format(math.ceil(saldo_ * 100) / 100, '.2f'),
                            "state_operation": '1'}
                    json_data = k_tool.get_data_init_valued(data)
                    moves_json.append(json_data)
                    init_prod = init_prod + 1
        return moves_json

    @api.model
    def _get_report_name(self, options):
        if options['type_kardex'] == 'units':
            name_sheet = _('PHYSICAL KARDEX')
        else:
            name_sheet = _('VALORIZED KARDEX')
        return name_sheet

    @api.model
    def get_name_xlsx(self, options):
        account_period = datetime.datetime.strptime(options['date_to'], "%Y-%m-%d")
        if options['type_kardex'] == 'units':
            xlsx_name = "%s%s%s%s%s" % (
                _("PHYSICAL KARDEX "), ' ', str(_(account_period.strftime('%B'))).upper(), ' ', account_period.year)
        else:
            xlsx_name = "%s%s%s%s%s" % (
                _("VALORIZED KARDEX "), ' ', str(_(account_period.strftime('%B'))).upper(), ' ', account_period.year)

        return xlsx_name

    @api.model
    def get_name_txt(self, options):
        account_period = datetime.datetime.strptime(options["date_to"], "%Y-%m-%d")
        company = self.env["res.company"].browse(options["company_id"])
        data = {"company_ruc": company.vat, "account_period": account_period}
        if options["type_kardex"] == 'units':
            txt_name = k_tool.get_name_units(data)
        else:
            txt_name = k_tool.get_name_valued(data)

        return txt_name

    def get_report_filename(self, options):
        if 'txt' in options:
            report_name = self.get_name_txt(options)
        elif 'excel' in options:
            report_name = self.get_name_xlsx(options)
        return report_name

    def export_excel(self):
        if self.date_from > self.date_to:
            raise UserError(_("The Start date cannot be less than the end date "))
        else:
            states = []
            del_state = self.env['kardex.states'].sudo().search([('code', '=', 'NINGUNO')], limit=1)
            self.write({'state_ids': [(2, del_state.id)]})
            excel_id = self.env['kardex.states'].sudo().search([('code', '=', 'EXCEL')], limit=1)
            type_print_id = self.env['kardex.states'].sudo().search([('code', '=', self.type_kardex)], limit=1)
            states.append(type_print_id.id)
            for x in self.state_ids:
                states.append(x.id)
            states.append(excel_id.id)
            self.write({'state_ids': [(6, 0, states)]})
            data = {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'company_id': self.company_id.id,
                'establishment': {'id': self.establishment.id, 'name': self.establishment.name},
                'type_kardex': self.type_kardex,
                'excel': 'excel'
            }
            return {
                'type': 'ir.actions.client',
                'report_type': 'xlsx_txt',
                'data': {
                    'model': 'kardex.inventory.mov',
                    'options': json.dumps(data, default=date_utils.json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Excel Report',
                }
            }

    def export_txt(self):
        if self.date_from > self.date_to:
            raise UserError(_("The Start date cannot be less than the end date "))
        else:
            states = []
            del_state = self.env['kardex.states'].sudo().search([('code', '=', 'NINGUNO')], limit=1)
            self.write({'state_ids': [(2, del_state.id)]})
            txt_id = self.env['kardex.states'].sudo().search([('code', '=', 'TXT')], limit=1)
            type_print_id = self.env['kardex.states'].sudo().search([('code', '=', self.type_kardex)], limit=1)
            for x in self.state_ids:
                states.append(x.id)
            states.append(txt_id.id)
            states.append(type_print_id.id)
            self.write({'state_ids': [(6, 0, states)]})
            data = {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'company_id': self.company_id.id,
                'establishment': {'id': self.establishment.id, 'name': self.establishment.name},
                'type_kardex': self.type_kardex,
                'txt': 'txt'
            }

            return {
                'type': 'ir.actions.client',
                'report_type': 'xlsx_txt',
                'data': {
                    'model': 'kardex.inventory.mov',
                    'options': json.dumps(data, default=date_utils.json_default),
                    'output_format': 'txt',
                    'report_name': 'txt report',
                }
            }


class StateKardex(models.Model):
    _name = 'kardex.states'
    _description = "Kardex states"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    color = fields.Integer(string="Color")
