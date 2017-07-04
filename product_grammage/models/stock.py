# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    width = fields.Float('Width')
    grammage = fields.Float('Grammage')


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    @api.depends('qty')
    def compute_quant_weight(self):
        for quant in self:
            if quant.lot_id:
                quant.weight = quant.qty * quant.lot_id.grammage

    weight = fields.Float('Weight', compute='compute_quant_weight')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _create_lots_for_picking(self):
        super(StockPicking, self)._create_lots_for_picking()
        for pack_op_lot in self.mapped('pack_operation_ids').\
                mapped('pack_lot_ids'):
            if pack_op_lot.operation_id.linked_move_operation_ids:
                move = pack_op_lot.operation_id.linked_move_operation_ids[0].\
                    move_id
                purchase_line = move.purchase_line_id
                lot = pack_op_lot.lot_id
                if purchase_line and lot:
                    if not lot.width:
                        lot.width = purchase_line.width
                    if not lot.grammage:
                        lot.grammage = purchase_line.grammage
