# -*- coding: utf-8 -*-
{
    # App information
    "name": "Localizaciones Inventario - Peru",
    "category": "Localization",
    "summary": "Contiene las localizaciones para inventario, catalogos SUNAT.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": [
        "l10n_pe_conf", "stock", "l10n_pe_product", "l10n_pe_account"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/type_of_operation_sunat_table_12.xml",
        "views/stock_picking.xml",
        "views/stock_picking_type.xml",
        "views/stock_scrap.xml",
        "views/stock_inventory.xml",
        "views/pragmatic_table_12.xml",
        "views/stock_warehouse.xml",
        "views/menu_menu.xml",
        "views/stock_location.xml",
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
