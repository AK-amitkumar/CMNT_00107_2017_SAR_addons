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
        for lot in self:
            grammage = 2
            lot.weight = lot.qty * grammage

    weight = fields.Float('Weight', compute='compute_quant_weight')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _create_lots_for_picking(self):
        # import ipdb; ipdb.set_trace()
        super(StockPicking, self)._create_lots_for_picking()
        