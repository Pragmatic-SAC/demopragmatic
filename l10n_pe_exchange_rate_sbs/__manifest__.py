# -*- coding: utf-8 -*-
{
    'name': 'Tipo de cambio $ - SBS/SUNAT',
    'version': '14.1',
    'author': "Pragmatic S.A.C",
    'category': 'Tools',
    'summary': 'Obtiene el tipo de cambio de la fecha actual desde SBS y SUNAT.',
    'license': 'AGPL-3',
    'contributors': [
        'Pragmatic S.A.C <soporte@pragmatic.com.pe>',
    ],
    'description': "",
    'website': 'https://www.pragmatic.com.pe/',
    'depends': ["l10n_pe_account"],
    "external_dependencies": {"python": ["bs4"], "bin": []},
    'data': [
        "data/ir_config_parameter.xml",
        "views/form_view.xml",
        "data/ir_cron.xml"
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
