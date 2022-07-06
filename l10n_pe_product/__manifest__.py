# -*- coding: utf-8 -*-
{
    # App information
    "name": "Localizaciones productos - Peru",
    "category": "Localization",
    "summary": "Modulo para las localizaciones producto, contiene algunos catalogos.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": [
        "l10n_pe_conf", "product_unspsc"
    ],
    "data": [
        "data/type_of_existence_sunat_table_5.xml",
        "data/unit_of_measurement_sunat_table_6.xml",
        "security/ir.model.access.csv",
        "views/product_template.xml",
        "views/uom_uom.xml",
        "views/pragmatic_table_5.xml",
        "views/pragmatic_table_6.xml",
        "views/menu_menu.xml",
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
