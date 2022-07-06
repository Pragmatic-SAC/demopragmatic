# -*- coding: utf-8 -*-
{
    # App information
    "name": "Localizaciones Contactos - Peru",
    "category": "Localization",
    "summary": "Modulo contiene algunos catalogos SUNAT.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": [
        "l10n_pe_conf",
        "contacts",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/type_agreement_sunat_table_25.xml",
        "data/type_person_partner_sunat_anexo_2.xml",
        "views/pragmatic_table_25.xml",
        "views/pragmatic_annexed_2.xml",
        "views/res_partner_view.xml",
        "views/province_view.xml",
        "views/district_view.xml",
        "views/view_l10n_latam_identification_type_view.xml",
        "views/menu.xml",
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
