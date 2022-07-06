# -*- coding: utf-8 -*-
{
    # App information
    "name": "Manejo de Secuencias - Peru",
    "category": "Localization",
    "summary": "Manejo de Secuencia por tipo de documento y diario.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": [
        "l10n_pe_edi",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_view.xml",
        "views/pragmatic_serie_sequence.xml",
        "views/account_journal.xml",
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
