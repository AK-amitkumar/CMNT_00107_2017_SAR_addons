# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpBomLine(models.Model):

    _inherit = 'mrp.bom.line'

    @api.multi
    @api.depends()
    def _get_weight_per(self):
        for line in self:
            val = 0.0
            if line.model_id and line.model_id.bom_weight:
                line_weight = line.product_id.weight * line.product_qty
                val = (line_weight / line.model_id.bom_weight) * 100
            line.weight_per = val

    bom_id = fields.Many2one(required=False)
    model_id = fields.Many2one('textile.model')
    model_type = fields.Selection(
        (('premodel', 'Pre-model'), ('model', 'Model')),
        related='model_id.model_type', readonly=True)
    weight_per = fields.Float(compute='_get_weight_per', string='Weigth %')
