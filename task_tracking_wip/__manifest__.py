# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Task Tracking WIP",
    'version': '10.0.1.0.0',
    'category': 'Textile Vertical',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    "depends": [
        'base',
        'sale',
        'stock',
        'mrp',
        'purchase',
        'project_model_to_task',
        'textile_base',
        'sale_order_dates',
        'project_task_dependency'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/tracking_wip_view.xml',
        'views/sale_order_view.xml',
        'views/task_view.xml',
    ],
    "installable": True
}
