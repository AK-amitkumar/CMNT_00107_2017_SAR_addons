# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpBom(models.Model):

    _inherit = 'mrp.bom'

    def explode(self, product, quantity, picking_type=False):
        boms_done, lines_done = super(MrpBom, self).\
            explode(product, quantity, picking_type=picking_type)
        new_boms_done = []
        new_lines_done = []
        for touple in boms_done:
            bom = touple[0]
            dic = touple[1]
            if dic.get('parent_line', False) and \
                    dic['parent_line'].product_efficiency:
                dic['qty'] = dic['qty'] / dic['parent_line'].product_efficiency
            new_boms_done.append((bom, dic))

        for touple in lines_done:
            current_line = touple[0]
            dic = touple[1]
            if current_line and current_line.product_efficiency:
                dic['qty'] = dic['qty'] / current_line.product_efficiency
            new_lines_done.append((current_line, dic))
        return new_boms_done, new_lines_done


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
    # In older versions
    product_efficiency = fields.Float('Manufacturing Efficiency',
                                      help="A factor of 0.9 means a loss of \
                                      10% within the production process.")
