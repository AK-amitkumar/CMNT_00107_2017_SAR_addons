# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
import odoo.addons.decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order.line'

    wip_line_ids = fields.One2many('wip.distribution.line', 'pl_id',
                                   'Distribution Lines')


class WipDistributionLine(models.Model):
    _name = 'wip.distribution.line'

    pl_id = fields.Many2one('purchase.order.line', 'Purchase Line')
    qty = fields.Float(string='Quantity',
                       digits=dp.get_precision('Product Unit of Measure'))
    sale_id = fields.Many2one('sale.order', 'For Sale')
