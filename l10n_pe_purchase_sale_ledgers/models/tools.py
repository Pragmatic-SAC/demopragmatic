# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _


def column_excel_sale():
    return [{'name': _("CUO")},
            {'name': _("F. Cont"), 'class': 'date'},
            {'name': _("F. Vencim"), 'class': 'date'},
            {'name': _("Tipo Doc")},
            {'name': _("Serie Doc")},
            {'name': _("Numero Doc")},
            {'name': _("Tipo Doc Cliente")},
            {'name': _("Numero Doc Cliente")},
            {'name': _("Razon Social Cliente")},
            {'name': _("Valor Fact Exportacion")},
            {'name': _("Base Imp Grav")},
            {'name': _("Exonerado")},
            {'name': _("Inafecto")},
            {'name': _("ISC")},
            {'name': _("IGV")},
            {'name': _("Imp Bolsas plastico")},
            {'name': _("Otros Tributos")},
            {'name': _("Total"), 'class': 'number'},
            {'name': _("Tipo de cambio")},
            {'name': _("Ref Fecha Doc")},
            {'name': _("Ref Tipo Doc")},
            {'name': _("Ref Serie Doc")},
            {'name': _("Ref Numero Doc")},
            {'name': _("Estado")}, ]


def column_excel_purchase():
    return [{'name': _("CUO")},
            {'name': _("NUMBER")},
            {'name': _("F. Cont"), 'class': 'date'},
            {'name': _("F. Vencim"), 'class': 'date'},
            {'name': _("COMPROBANTE DE PAGO / TIPO")},
            {'name': _("COMPROBANTE DE PAGO / SERIE")},
            {'name': _("COMPROBANTE DE PAGO / AÑO DUA O DSI")},
            {'name': _("COMPROBANTE DE PAGO / NUMERO")},
            {'name': _("PROVEEDOR / TIPO DOCUMENTO")},
            {'name': _("PROVEEDOR / NUMERO DOCUMENTO")},
            {'name': _("PROVEEDOR / RAZON SOCIAL")},
            {'name': _(
                "ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O EXPORTACION / BASE IMPONIBLE")},
            {'name': _("ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O EXPORTACION / IGV")},
            {'name': _(
                "ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O DE EXPORTACIÓN Y A OPERACIONES NO GRAVADAS / BASE IMPONIBLE")},
            {'name': _(
                "ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O DE EXPORTACIÓN Y A OPERACIONES NO GRAVADAS / IGV")},
            {'name': _("ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES NO GRAVADAS / BASE IMPONIBLE")},
            {'name': _("ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES NO GRAVADAS / IGV")},
            {'name': _("VALOR DE LAS ADQUISICIONES NO GRAVADAS")},
            {'name': _("ISC")},
            {'name': _("IMPUESTO AL CONSUMO DE BOLSAS DE PLASTICO")},
            {'name': _("OTROS TRIBUTOS Y CARGOS")},
            {'name': _("IMPORTE TOTAL")},
            {'name': _("N° DE COMPROBANTE DE PAGO EMITIDO POR SUJETO NO DOMICILIADO")},
            {'name': _("CONSTANCIA DE DEPOSITO DE DETRACCION / NUMERO")},
            {'name': _("CONSTANCIA DE DEPOSITO DE DETRACCION / FECHA DE EMISION")},
            {'name': _("TIPO DE CAMBIO")},
            {'name': _("REFERENCIA DEL COMPROBANTE DE PAGO O DOCUMENTO ORIGINAL QUE SE MODIFICA / FECHA")},
            {'name': _("REFERENCIA DEL COMPROBANTE DE PAGO O DOCUMENTO ORIGINAL QUE SE MODIFICA / TIPO")},
            {'name': _("REFERENCIA DEL COMPROBANTE DE PAGO O DOCUMENTO ORIGINAL QUE SE MODIFICA / SERIE")},
            {'name': _("REFERENCIA DEL COMPROBANTE DE PAGO O DOCUMENTO ORIGINAL QUE SE MODIFICA / NUMERO")},
            {'name': _("ESTADO")}, ]


def column_excel_non_domiciled():
    return [{'name': _("CUO")},
            {'name': _("F. Cont"), 'class': 'date'},
            {'name': _("COMPROBANTE DE PAGO / TIPO")},
            {'name': _("COMPROBANTE DE PAGO / SERIE")},
            {'name': _("COMPROBANTE DE PAGO / NUMERO")},
            {'name': _("COMPROBANTE DE PAGO / AÑO DUA O DSI")},
            {'name': _("VALOR DE LAS ADQUISICIONES")},
            {'name': _("OTROS CONCEPTOS ADICIONALES")},
            {'name': _("IMPORTE TOTAL DE LAS ADQUISIONES")},
            {'name': _("MONTO DE RETENCION DEL IGV")},
            {'name': _("MONEDA")},
            {'name': _("TIPO DE CAMBIO")},
            {'name': _("SUJETO NO DOMICILIADO / PAIS DE RESIDENCIA")},
            {'name': _("SUJETO NO DOMICILIADO / RAZON SOCIAL")},
            {'name': _("SUJETO NO DOMICILIADO / DIRECCION")},
            {'name': _("SUJETO NO DOMICILIADO / NRO IDENTIFICACION")},
            {'name': _("CONVENIO PARA EVITAR DOBLE IMPOSICION")},
            {'name': _("TIPO DE RENTA")},
            {'name': _("ANOTACION O INDICACION DE AJUSTE")},
            {'name': _("ESTADO")}, ]
