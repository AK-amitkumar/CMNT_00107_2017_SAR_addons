# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Product Grammage",
    'version': '10.0.1.0.0',
    'category': 'Textile Vertical',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    "depends": [
        'base',
        'purchase',
        'stock',
        'product'
    ],
    "data": [
        'views/product_view.xml',
        'views/purchase_view.xml',
        'views/stock_view.xml'
    ],
    "installable": True
}
