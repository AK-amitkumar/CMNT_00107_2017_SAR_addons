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
        'custom_purchase',  # For related sale id
        'project_model_to_task',
        'sale_order_dates',
        'project_native',
        'stock_split_picking',
        'subcontracted_service',
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/manage_distribution_wzd_view.xml',
        'views/tracking_wip_view.xml',
        'views/sale_order_view.xml',
        'views/task_view.xml',
        'views/stock_view.xml',
        'views/mrp_workorder_view.xml',
        'views/mrp_production_view.xml',
        'views/purchase_view.xml',
        'data/tracking_wip_data.xml',
    ],
    "installable": True
}
