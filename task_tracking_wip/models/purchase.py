# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    wip_line_ids = fields.One2many('wip.distribution.line', 'pl_id',
                                   'Distribution Lines')
    # related_sale_id = fields.Many2one('sale.order', 'Related Sale')
    # related_model_id = fields.Many2one('textile.model', 'Related Model')

    # @api.onchange('related_sale_id')
    # def onchange_sale_id(self):
    #     if self.related_sale_id and self.related_sale_id.model_id:
    #         self.related_model_id = self.related_sale_id.model_id.id

    @api.multi
    def _prepare_stock_moves(self, picking):
        """
        If distribution line, we break links in move_dest_id and avoid
        to create a move for each procurement. Instead it, we create an unique
        move with same distribution lines
        """
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        self.ensure_one()
        if self.wip_line_ids:
            # Avoid move_dest_id links
            self.mapped('procurement_ids.move_dest_id').break_links()

            # Get total qty in procuremnts
            dic_tmp = res[0]
            sum_qty = 0.0
            worst_date = False
            for dic in res:
                sum_qty += dic.get('product_uom_qty', '0.0')
                if not worst_date:
                    worst_date = dic.get('date_expected', False)
                elif worst_date < dic.get('date_expected', False):
                    worst_date = dic.get('date_expected', False)
            move_wip_lines = self.env['wip.distribution.line']
            for wip_line in self.wip_line_ids:
                new_wip_line = wip_line.copy()
                new_wip_line.write({'pl_id': False})
                move_wip_lines += new_wip_line

            # Mix move values in an unique dictionary
            dic_tmp.update({
                'product_uom_qty': sum_qty,
                'date_expected': worst_date,
                'move_dest_id': False,
                'procurement_id': False,
                'propagate': False,
                'wip_line_ids': [(6, 0, move_wip_lines.ids)]
            })
            res = [dic_tmp]
        return res

    @api.multi
    def _create_stock_moves(self, picking):
        """
        Function called when creating incoming moves from purchase.order.line
        After super, moves were created aud assigend to several tasks, one for
        each distribution line.
        """
        track_model = self.env['tracking.wip']
        res = super(PurchaseOrderLine, self)._create_stock_moves(picking)

        # CREATE TASK FOR INCOMING PICKING
        if picking and not picking.task_ids:
            track_record = track_model.get_track_for_model(picking._name,
                                                           picking)
            if track_record:
                track_record.create_task_tracking(picking)
                track_record.manage_parent_child_tasks(picking)
        return res


class WipDistributionLine(models.Model):
    _name = 'wip.distribution.line'

    pl_id = fields.Many2one('purchase.order.line', 'Purchase Line')
    move_id = fields.Many2one('stock.move', 'Move')
    qty = fields.Float(string='Quantity',
                       digits=dp.get_precision('Product Unit of Measure'))
    sale_id = fields.Many2one('sale.order', 'For Sale')
    task_id = fields.Many2one('project.task', 'Related Task')
