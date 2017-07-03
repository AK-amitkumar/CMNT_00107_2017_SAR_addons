# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order.line'

    thread = fields.Float('Thread', related='product_id.thread')
    gauge = fields.Float('Gauge', related='product_id.gauge')
    width = fields.Float('Width')
    grammage = fields.Float('Grammage')
