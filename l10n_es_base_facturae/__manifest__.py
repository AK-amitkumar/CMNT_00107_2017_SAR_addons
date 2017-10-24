# -*- coding: utf-8 -*-

{
    "name": "Creación de Factura-e",
    "version": "10.0.1.0.0",
    "author": "Victor Rojo",
    'description': """Módulo base para la creación de facturas electrónicas""",
    "category": "Accounting & Finance",
    "depends": [
        "account",
        "base_iso3166",
        "account_payment_partner",
        "l10n_es_facturae"
    ],
    "data": [
        "data/e_invoice_data.xml",
        "views/account_invoice_view.xml",
        "views/e_invoice_view.xml",
        "views/res_partner_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
