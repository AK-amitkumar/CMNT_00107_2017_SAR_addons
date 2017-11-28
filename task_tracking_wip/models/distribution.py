# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class WipDistributionLine(models.Model):
    _name = 'wip.distribution.line'

    @api.depends('task_id')
    def _get_move_info(self):
        for line in self:
            if line.task_id and line.task_id.model_reference and \
                    line.task_id.model_reference._name == 'stock.move':
                line.move_dest_id = line.task_id.model_reference.id

    pl_id = fields.Many2one('purchase.order.line', 'Purchase Line')
    move_id = fields.Many2one('stock.move', 'Move')
    qty = fields.Float(string='Quantity',
                       digits=dp.get_precision('Product Unit of Measure'))
    sale_id = fields.Many2one('sale.order', 'For Sale')
    task_id = fields.Many2one('project.task', 'Related Task')
    move_dest_id = fields.Many2one('stock.move', 'Destination move',
                                   compute=_get_move_info, store=True)
