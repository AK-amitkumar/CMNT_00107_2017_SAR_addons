# -*- coding: utf-8 -*-

{
    "name": "Factura-e Inditex",
    "version": "10.0.1.0.0",
    "author": "Victor Rojo",
    'description': """Módulo para la facturación electrónica a Inditex""",
    "category": "Accounting & Finance",
    "depends": [
        "l10n_es_base_facturae",
    ],
    "data": [
        "data/e_invoice_data.xml",
        "data/transport_mode_data.xml",
        "views/account_invoice_view.xml",
        "views/report_facturae_inditex.xml",
        "views/res_partner_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}

# depends PR #14869 handle xml namespaces in qweb