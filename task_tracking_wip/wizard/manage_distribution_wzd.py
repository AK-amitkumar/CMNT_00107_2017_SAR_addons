# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class ManageDistributionWzd(models.TransientModel):
    _name = 'manage.distribution.wzd'
    _description = 'Picking wizard'

    move_id = fields.Many2one('stock.move', 'Move',
                              readonly=True)
    pl_id = fields.Many2one('purchase.order.line', 'Purchase Line',
                            readonly=True)
    product_id = fields.Many2one('product.product', 'Product',
                                 readonly=True)
    location_id = fields.Many2one('stock.location', 'To Location',
                                  readonly=True)
    wip_lines = fields.One2many('manage.lines', 'wzd_id', 'Manage Lines')
    line_qty = fields.Float('Line Quantity', compute='_get_qtys',
                            readonly=True)
    distributed_qty = fields.Float('Dritributed Quantity', compute='_get_qtys',
                                   readonly=True)
    remaining_qty = fields.Float('Remaining Quantity', compute='_get_qtys',
                                 readonly=True)

    @api.multi
    @api.depends('pl_id.product_qty', 'wip_lines.qty')
    def _get_qtys(self):
        pl_id = self.env['purchase.order.line'].\
            browse(self._context.get('active_id'))
        self.ensure_one()
        lines_qty = 0
        for wl in self.wip_lines:
            lines_qty += wl.qty
        line_qty = pl_id.product_qty
        self.line_qty = line_qty
        self.distributed_qty = lines_qty
        self.remaining_qty = line_qty - lines_qty

    @api.model
    def default_get(self, fields):
        res = super(ManageDistributionWzd, self).default_get(fields)
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        move_id = active_id if active_model == 'stock.move' else False
        pl_id = active_id if active_model == 'purchase.order.line' else False

        model = False
        location_id = False
        if move_id:
            model = self.env['stock.move'].browse(move_id)
            location_id = model.location_dest_id.id
        else:
            model = self.env['purchase.order.line'].browse(pl_id)
            location_id = model.order_id.\
                picking_type_id.default_location_dest_id.id

        product_id = model.product_id.id
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
            'product_id': product_id,
            'location_id': location_id,
            'wip_lines': lines
        })
        return res

    @api.multi
    def apply(self):
        if self.remaining_qty > 0.00 and self.remaining_qty != self.line_qty:
            raise ValidationError(_('There is pending quantity to \
                                    distribute yet'))
        if self.remaining_qty < 0.00:
            raise ValidationError(_('There is distributed more quantity than \
                                    purchase line quantity'))
        track_model = self.env['tracking.wip']
        model = self.move_id if self.move_id else self.pl_id
        model.wip_line_ids.unlink()
        lines = []
        for line in self.wip_lines:
            vals = {
                'qty': line.qty,
                'sale_id': line.sale_id.id,
                'task_id': line.task_id.id,
                'pl_id': model.id if self.pl_id else False,
                'move_id': model.id if self.move_id else False
            }
            lines.append((0, 0, vals))
        model.write({'wip_line_ids': lines})

        if model._name == 'stock.move':
            track_model.recompute_move_task_ids(model)
        self.ensure_one()


class ManageLines(models.TransientModel):
    _name = 'manage.lines'
    _description = 'Picking wizard'

    wzd_id = fields.Many2one('manage.distribution.wzd', 'Wizard')
    qty = fields.Float(string='Quantity',
                       digits=dp.get_precision('Product Unit of Measure'))
    sale_id = fields.Many2one('sale.order', 'For Sale')
    task_id = fields.Many2one('project.task', 'Related Task')

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        if self.sale_id:
            self.task_id = False
