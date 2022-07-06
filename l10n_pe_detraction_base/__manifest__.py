# -*- coding: utf-8 -*-
{
    # App information
    "name": "Calculo base de detraccion - Peru",
    "category": "Localization",
    "summary": "Modulo del calculo base de detraccion.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": [
        "l10n_pe_conf", "l10n_pe_product", "l10n_pe_edi"
    ],
    "data": [
        "data/codes_detraction_sunat_catalog_54.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "views/product_product.xml",
        "views/product_template.xml",
        "views/pragmatic_catalog_54.xml",
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
    "application": False,
    "currency": "PEN",
}
