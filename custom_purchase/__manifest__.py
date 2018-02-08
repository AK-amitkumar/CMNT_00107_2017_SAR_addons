# -*- coding: utf-8 -*-
# © 2018 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Custom Purchase",
    'version': '10.0.1.0.0',
    'category': 'Textile Vertical',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    "depends": [
        'purchase',
        'textile_base',
        'task_tracking_wip'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/purchase_view.xml',
    ],
    "installable": True
}
