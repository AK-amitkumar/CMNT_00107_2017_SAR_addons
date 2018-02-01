# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Logistics WIP view",
    'version': '10.0.1.0.0',
    'category': 'Textile Vertical',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    "depends": [
        'textile_base',
        'sale_stock',
        'project_task_dependency',
        'web_gantt',
        'procurement_jit',
        'mrp_mto_with_stock',
        'stock_mts_mto_rule',
        'task_tracking_wip',
    ],
    "data": ['views/textile_model_view.xml'],
    "installable": True
}
