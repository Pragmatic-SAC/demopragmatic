# -*- coding: utf-8 -*-
{
    # App information
    "name": "Reporte de Compras y Ventas - Peru",
    "category": "Localization",
    "summary": "Modulo Reporte de compras y Ventas, funciona en Community  y Enterprise.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Pragmatic S.A.C <soporte@pragmatic.com.pe>",
    ],
    "depends": [
        "l10n_pe_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/action_manager.xml",
        "views/account_books.xml",
        "views/latam_document_type.xml",
        "views/account_move.xml",
        "views/account_tax.xml",
        "views/res_country.xml",
    ],
    # Odoo Store Specific
    "images": [

    ],

    # Author
    "author": "Pragmatic S.A.C",
    "website": "pragmatic.com.pe",
    "maintainer": "Pragmatic S.A.C.",

    # Technical
    "installable": True,
    "auto_install": False,
    "application": True,
    "currency": "PEN",
}
