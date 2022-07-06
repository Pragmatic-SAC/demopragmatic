# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _


def column_excel_unit():
    return [
        {'name': _("Date"), 'class': 'date'},
        {'name': _("CUO")},
        {'name': _("Movement")},
        {'name': _("Establishment")},
        {'name': _("Product")},
        {'name': _("Reference")},
        {'name': _("Series")},
        {'name': _("Operation type")},
        {'name': _("Inputs"), 'class': 'number'},
        {'name': _("Outputs"), 'class': 'number'},
        {'name': _("Final Balance"), 'class': 'number'},
    ]


def column_excel_val():
    return [
        {'name': _("Date"), 'class': 'date'},
        {'name': _("CUO")},
        {'name': _("Movement")},
        {'name': _("Establishment")},
        {'name': _("Product")},
        {'name': _("Reference")},
        {'name': _("Operation type")},
        {'name': _("Input Cant."), 'class': 'number'},
        {'name': _("Input Cost Unit."), 'class': 'number'},
        {'name': _("Input Cost Total"), 'class': 'number'},
        {'name': _("Output Cant."), 'class': 'number'},
        {'name': _("Output Cost Unit."), 'class': 'number'},
        {'name': _("Output Cost Total"), 'class': 'number'},
        {'name': _("Final Cant."), 'class': 'number'},
        {'name': _("Final Cost Unit."), 'class': 'number'},
        {'name': _("Final Cost Total"), 'class': 'number'}
    ]


def add_line_physical(data):
    json = {
        "name": str(data['date_from']),
        "columns": [
            {"name": data['saldo_inicial'][0]['id'] if data['saldo_inicial'] else data['res']['id']},
            {"name": data['res']['reference']},
            {"name": data['establishment']},
            {"name": data['product'].display_name},
            {"name": ""},
            {"name": ""},
            {"name": "%s%s%s" % (data['type_operation_init'].code, '-', data['type_operation_init'].name)},
            {"name": data['saldo'], 'class': 'number'},
            {"name": 0.0, 'class': 'number'},
            {"name": data['saldo'], 'class': 'number'}
        ],
        "id": data['line_id'],
        "unfoldable": True,
        "level": data['level']
    }
    return json


def add_line_physical_op(data):
    json_op = {
        "name": str(data['res']['date']),
        "columns": [
            {"name": data['res']['id']},
            {"name": data['res']['reference']},
            {"name": data['establishment']},
            {"name": data['product'].display_name},
            {"name": data['reference_code']},
            {"name": data['serie_code']},
            {"name": data['type_operation_move']},
            {"name": data['cant_entrada'], 'class': 'number'},
            {"name": data['cant_salida'], 'class': 'number'},
            {"name": data['saldo'], 'class': 'number'}
        ],
        "id": "product" + str(data['res']['product_id']),
        "unfoldable": False,
        "level": data['level']
    }
    return json_op


def add_line_valued(data):
    json = {
        "name": str(data['date_from']),
        "columns": [
            {"name": data['res']['id']},
            {"name": data['stock_move']['reference']},
            {"name": data['establishment']},
            {"name": data['product'].display_name},
            {"name": data["reference_code"]},
            {"name": data["type_operation_init"].name},
            {"name": data['cant_total'], 'class': 'number'},
            {"name": data['cost_total'], 'class': 'number'},
            {"name": data['saldo_'], 'class': 'number'},
            {"name": 0.00, 'class': 'number'},
            {"name": 0.00, 'class': 'number'},
            {"name": 0.00, 'class': 'number'},
            {"name": data['cant_total'], 'class': 'number'},
            {"name": data['cost_total'], 'class': 'number'},
            {"name": data['saldo_'], 'class': 'number'}
        ],
        "id": "product" + str(data['res']['product_id']),
        "unfoldable": True,
        "level": data['level']
    }
    return json


def add_line_valued_op(data):
    json_op = {
        "name": str(data['res']['date']),
        "columns": [
            {"name": data['res']['id']},
            {"name": data['stock_move']['reference']},
            {"name": data['establishment']},
            {"name": data['product'].display_name},
            {"name": data['reference_code']},
            {"name": data['type_operation_move']},
            {"name": data['cant_entrada'], 'class': 'number'},
            {"name": data['cost_entrada'], 'class': 'number'},
            {"name": data['entrada'], 'class': 'number'},
            {"name": abs(data['cant_salida']), 'class': 'number'},
            {"name": abs(data['cost_salida']), 'class': 'number'},
            {"name": abs(data['salida']), 'class': 'number'},
            {"name": data['cant_total'] if data['cant_total'] > 0 else 0.00,
             'class': 'number'},
            {"name": data['cost_total'] if data['cant_total'] > 0 else 0.00,
             'class': 'number'},
            {"name": abs(data['saldo_']) if data['cant_total'] > 0 else 0.00,
             'class': 'number'},
        ],
        "id": "product" + str(data['res']['product_id']),
        "unfoldable": False,
        "level": data['level']
    }
    return json_op


def add_line_average_cost(data):
    json_ = {
        "name": str(data['res']['date']),
        "columns": [
            {"name": data['product'].display_name},
            {"name": data['description']},
            {"name": data['type_operation_move']},
            {"name": abs(data['quantity']), 'class': 'number'},
            {"name": abs(data['cost']), 'class': 'number'},
            {"name": abs(data['average_cost']), 'class': 'number'},
        ],
        "id": "product" + str(data['res']['product_id']),
        "unfoldable": False,
        "level": data['level']
    }
    return json_


def get_name_units(obj):
    return "%s%s%s%s%s%s%s%s%s%s%s" % (
        "LE",
        obj["company_ruc"],
        obj["account_period"].year,
        "%02d" % (obj["account_period"].month),
        "00",
        "120100",
        "00",
        "1",
        "1",  # Con informacion,
        "1",  # Moneda Validar,
        1
    )


def data_txt_units(obj):
    return "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\r\n" % (
        obj["period"],
        obj["cuo"],
        obj["account_correlative"],
        obj["code_establishment"],
        obj["code_catalog"],
        obj["type_existence"],
        obj["code_existence"],
        obj["code_existence_catalog"],
        obj["date_emision"],
        obj["type_document_move"],
        obj["series_document_move"],
        obj["number_document_move"],
        obj["type_operation"],
        obj["description_existence"],
        obj["code_uom"],
        obj["entry_input_phisical"],
        obj["entry_ouput_phisical"],
        obj["state_operation"]
    )


def get_name_valued(obj):
    return "%s%s%s%s%s%s%s%s%s%s%s" % (
        "LE",
        obj["company_ruc"],
        obj["account_period"].year,
        "%02d" % (obj["account_period"].month),
        "00",
        "130100",
        "00",
        "1",
        "1",  # Con informacion,
        "1",  # Moneda Validar,
        1
    )


def data_txt_valued(obj):
    return "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|\r\n" % (
        obj["period"],
        obj["cuo"],
        obj["account_correlative"],
        obj["code_establishment"],
        obj["code_catalog"],
        obj["type_existence"],
        obj["code_existence"],
        obj["code_existence_catalog"],
        obj["date_emision"],
        obj["type_document_move"],
        obj["series_document_move"],
        obj["number_document_move"],
        obj["type_operation"],
        obj["description_existence"],
        obj["code_uom"],
        obj["cost_method"],
        obj["cant_input"],
        obj["cost_unit_input"],
        obj["cost_total_input"],
        obj["cant_ouput"],
        obj["cost_unit_ouput"],
        obj["cost_total_ouput"],
        obj["cant_saldo_final"],
        obj["cost_unit_saldo_final"],
        obj["cost_saldo_final"],
        obj["state_operation"]
    )


def get_data_init_units(obj):
    return {
        "period": "%s%s00" % (obj['account_period'].year, "%02d" % (obj['account_period'].month)),
        # CAMPO 1: PERIODO
        "cuo": obj['cuo'],  # CAMPO 2: ID ACCOUNT MOVE
        "account_correlative": "M%s" % obj['account_correlative'],  # CAMPO 3 : CORRELATIVO
        "code_establishment": obj['code_establishment'],  # CAMPO 4 : CODIGO DEL ESTABLECIMIENTO
        "code_catalog": obj['code_catalog'],  # CAMPO 5 : CONFIG EN GENERAL
        "type_existence": obj['type_existence'],  # CAMPO 6 : TIPO DE EXISTENCIA
        "code_existence": obj['code_existence'],  # CAMPO 7 CODIGO DE EXISTENCIA
        "code_existence_catalog": obj['code_existence_catalog'],  # CAMPO 9 CODIGO DE PRODUCTO - ONU
        "date_emision": obj['date_emision'],
        # CAMPO 10 FECHA DE EMISION
        "type_document_move": obj['type_document_move'],  # CAMPO 11 TIPO DE DOCUMENTO DE TRANSLADO
        "series_document_move": obj['series_document_move'],  # CAMPO 12 SERIE DE DOCUMENTO DE TRANSLADO
        "number_document_move": obj['number_document_move'],  # CAMPO 13 NUMERO DE DOCUMENTO DE TRANSLADO
        "type_operation": obj['type_operation'],  # CAMPO 14 TIPO DE OPERACION AFECTUADA
        "description_existence": obj['description_existence'][:80],
        # CAMPO 15 DESCRIPCION DE LA EXISTENCIA == PENDIENTE
        "code_uom": obj['code_uom'],  # CAMPO 16 CODIGO DE LA UNIDAD DE MEDIDA
        "entry_input_phisical": obj['entry_input_phisical'],
        # CAMPO 17 ENTRADA DE LAS UNIDADES FISICAS
        "entry_ouput_phisical": obj['entry_ouput_phisical'],
        # CAMPO 18 SALIDA DE LAS UNIDADES FISICAS
        "state_operation": obj['state_operation'],  # CAMPO 19 ESTADO DE LA OPERACION
    }


def get_data_init_valued(obj):
    return {
        "period": "%s%s00" % (obj['account_period'].year, "%02d" % (obj['account_period'].month)),
        # CAMPO 1: PERIODO
        "cuo": obj['cuo'],  # CAMPO 2: ID ACCOUNT MOVE
        "account_correlative": "M%s" % obj['account_correlative'],  # CAMPO 3 : CORRELATIVO
        "code_establishment": obj['code_establishment'],  # CAMPO 4 : CODIGO DEL ESTABLECIMIENTO
        "code_catalog": obj['code_catalog'],  # CAMPO 5 : CONFIG EN GENERAL
        "type_existence": obj['type_existence'],  # CAMPO 6 : TIPO DE EXISTENCIA
        "code_existence": obj['code_existence'],  # CAMPO 7 CODIGO DE EXISTENCIA
        "code_existence_catalog": obj['code_existence_catalog'],  # CAMPO 9 CODIGO DE PRODUCTO - ONU
        "date_emision": obj['date_emision'],
        # CAMPO 10 FECHA DE EMISION
        "type_document_move": obj['type_document_move'],  # CAMPO 11 TIPO DE DOCUMENTO DE TRANSLADO
        "series_document_move": obj['series_document_move'],  # CAMPO 12 SERIE DE DOCUMENTO DE TRANSLADO
        "number_document_move": obj['number_document_move'],  # CAMPO 13 NUMERO DE DOCUMENTO DE TRANSLADO
        "type_operation": obj['type_operation'],  # CAMPO 14 TIPO DE OPERACION AFECTUADA
        "description_existence": obj['description_existence'][:80],
        # CAMPO 15 DESCRIPCION DE LA EXISTENCIA == PENDIENTE
        "code_uom": obj['code_uom'],  # CAMPO 16 CODIGO DE LA UNIDAD DE MEDIDA
        "cost_method": obj['cost_method'],
        "cant_input": obj['cant_input'],
        "cost_unit_input": obj['cost_unit_input'],
        "cost_total_input": obj['cost_total_input'],
        "cant_ouput": obj['cant_ouput'],
        "cost_unit_ouput": obj['cost_unit_ouput'],
        "cost_total_ouput": obj['cost_total_ouput'],
        "cant_saldo_final": obj['cant_saldo_final'],
        "cost_unit_saldo_final": obj['cost_unit_saldo_final'],
        "cost_saldo_final": obj['cost_saldo_final'],
        "state_operation": obj['state_operation'],  # CAMPO 19 ESTADO DE LA OPERACION
    }
