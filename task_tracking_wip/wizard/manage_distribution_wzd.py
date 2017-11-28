# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class ManageDistributionWzd(models.TransientModel):
    _name = 'manage.distribution.wzd'
    _description = 'Picking wizard'

    move_id = fields.Many2one('stock.move', 'Move')
    pl_id = fields.Many2one('purchase.order.line', 'Purchase Line')
    wip_lines = fields.One2many('manage.lines', 'wzd_id', 'Manage Lines')

    @api.model
    def default_get(self, fields):
        res = super(ManageDistributionWzd, self).default_get(fields)
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        move_id = active_id if active_model == 'stock.move' else False
        pl_id = active_id if active_model == 'purchase.order.line' else False

        model = False
        if move_id:
            model = self.env['stock.move'].browse(move_id)
        else:
            model = self.env['purchase.order.line'].browse(pl_id)

        lines = []
        for line in model.wip_line_ids:
            vals = {
                'wzd_id': self.id,
                'qty': line.qty,
                'sale_id': line.sale_id.id,
                'task_id': line.task_id.id
            }
            lines.append((0, 0, vals))
        res.update({
            'move_id': move_id,
            'pl_id': pl_id,
            'wip_lines': lines
        })
        return res


class ManageLines(models.TransientModel):
    _name = 'manage.lines'
    _description = 'Picking wizard'

    wzd_id = fields.Many2one('manage.distribution.wzd', 'Wizard')
    qty = fields.Float(string='Quantity',
                       digits=dp.get_precision('Product Unit of Measure'))
    sale_id = fields.Many2one('sale.order', 'For Sale')
    task_id = fields.Many2one('project.task', 'Related Task')
