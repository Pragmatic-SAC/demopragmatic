# -*- coding: utf-8 -*-
{
    # App information
    "name": "Contabilidad - Peru",
    "category": "Localization",
    "summary": "Campos adicionales para la contabilidad Peruana.",
    "version": "14.0.0",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": ["l10n_pe_contacts", "l10n_pe_product", "l10n_pe_edi", "l10n_pe_journal_sequence"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/decimal_precision_invoice.xml",
        "data/type_income_sunat_table_31.xml",
        "data/edi_common_line.xml",
        "data/edi_void_documents.xml",
        "data/type_income_sunat_catalog_51.xml",
        "views/l10n_latam_document_type.xml",
        "views/pragmatic_type_income.xml",
        "views/account_payment_register.xml",
        "views/account_payment.xml",
        "views/account_tax_view.xml",
        "views/pragmatic_type_operation.xml",
        "views/menu_menu.xml",
        "views/res_currency_rate_tree.xml",
        "views/pragmatic_serie_sequence.xml",
        "views/view_l10n_latam_identification_type_view.xml",
        "views/account_move.xml",
        "views/res_partner_bank.xml",
        "views/res_config_settings_view.xml",
        "report/account_move_fe.xml",
        "report/account_move_fe_ticket.xml",
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
