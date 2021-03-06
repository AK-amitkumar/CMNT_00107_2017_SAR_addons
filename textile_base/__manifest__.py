# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Textile base",
    'version': '10.0.1.0.0',
    'category': 'Textile Vertical',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    "depends": [
        'analytic',
        'sale',
        'purchase',
        'web_widget_color',
        'product_harmonized_system_extend',
        'base_multi_image',
        'mrp',
        'sale_order_variant_mgmt',
        'purchase_order_variant_mgmt',
        'task_tracking_wip'
    ],
    "data": [
        'data/textile_base_data.xml',
        'views/season_view.xml',
        'views/color_view.xml',
        'views/composition_view.xml',
        'views/size_view.xml',
        'views/textile_model.xml',
        'views/assets.xml',
        'views/product_view.xml',
        'views/sale.xml',
        # 'views/purchase.xml',
        'views/label.xml',
        'views/mrp_bom.xml',
        'security/ir.model.access.csv'
    ],
    "installable": True
}
