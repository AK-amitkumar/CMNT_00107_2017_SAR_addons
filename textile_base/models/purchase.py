# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from odoo import tools


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_id')
    def _get_color(self):
        for pol in self:
            colors = pol.product_id.attribute_value_ids.filtered('is_color')
            pol.color_id = colors[0] if colors else False

    color_id = fields.Many2one('product.attribute.value',
                               compute='_get_color', store=True)
    line_note = fields.Text('Line Note')


class GroupPoLine(models.Model):
    _name = "group.po.line"
    _auto = False
    _description = "Groping Purchase Order Lines"

    att_detail = fields.Text('Attribute Detail', compute='_get_detail')

    @api.multi
    def _get_detail(self):
        for gpl in self:
            self.att_detail = "XXS    XS    S     M       L       XL      \
                XXL\n10       2       3      4      80      90      100"

    @api.model_cr
    def init(self):
        """
        @param cr: the current row, from the database cursor
        """
        tools.drop_view_if_exists(self._cr, 'group_po_line')
        self._cr.execute("""
CREATE OR REPLACE VIEW group_po_line AS (
SELECT
min(pol.id) as id,
pp.product_tmpl_id AS template_id,
pol.order_id AS order_id,
pol.color_id AS color_id,
sum(pol.width) as width,
sum(pol.grammage) as grammage,
sum(pt.gauge) as gauge,
sum(pt.thread) as thread,
sum(pol.product_qty) AS qty,
sum(pol.price_unit) AS price
FROM purchase_order_line pol
LEFT JOIN product_product pp ON pp.id = pol.product_id
LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
GROUP BY pol.order_id, pp.product_tmpl_id, pol.color_id
)""")
