# -*- coding: utf-8 -*-
{
    # App information
    "name": "Pragmatic Kardex - Peru",
    "category": "Reporte de Kardex",
    "summary": "Kardex Pragmatic.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Pragmatic S.A.C <soporte@pragmatic.com.pe>",
    ],
    "depends": [
        "l10n_pe_stock"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/states_kardex.xml",
        "views/action_manager.xml",
        "views/kardex.xml",
        "views/res_config.xml",
        "views/resource_sunat_pe.xml"
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
