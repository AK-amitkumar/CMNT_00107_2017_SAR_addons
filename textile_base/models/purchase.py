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

    id = fields.Integer('Id', readonly=True)
    template_id = fields.Many2one('product.template', 'Template',
                                  readonly=True)
    att_detail = fields.Text('Attribute Detail', readonly=True,
                             compute='_get_detail')
    order_id = fields.Many2one('purchase.order', 'Order', readonly=True)
    color_id = fields.Many2one('product.attribute.value', readonly=True)
    width = fields.Float('Width', readonly=True)
    grammage = fields.Float('Grammage', readonly=True)
    gauge = fields.Float('Gauge', readonly=True)
    thread = fields.Float('thread', readonly=True)
    qty = fields.Float('Qty', readonly=True)
    uom_id = fields.Many2one('product.uom', 'Unit', readonly=True)
    price = fields.Float('Price', readonly=True)
    note = fields.Text('Note', readonly=True,
                       compute='_get_group_note')
    ref_prov = fields.Char('Ref Prov', readonly=True,
                           compute='_get_ref_prov')
    sales_str = fields.Char('Origin Sales and Models',
                            compute='_get_sales_str')

    @api.multi
    def _get_lines_ungruped(self):
        self.ensure_one()
        res = self.env['purchase.order.line']
        for line in self.order_id.order_line:
            if line.color_id.id == self.color_id.id and \
                    line.product_id.product_tmpl_id.id == self.template_id.id:
                res += line
        return res

    @api.model
    def _get_att_detail_str(self, gpl, detail_dic):
        separator = '   '
        res = ""
        line1_str = ""
        line2_str = ""
        for v_name in detail_dic:
            value_str = str(int(detail_dic[v_name]))
            len1 = len(v_name)
            len2 = len(value_str)
            max_len = max(len1, len2) + len(separator)
            sepa1 = ''
            for i in range(0, max_len - len1):
                sepa1 += ' '
            sepa2 = ''
            for i in range(0, max_len - len2):
                sepa2 += ' '
            line1_str += v_name + sepa1
            line2_str += value_str + sepa2

        if line1_str and line2_str:
            res = line1_str + '\n' + line2_str
        return res

    @api.multi
    def _get_detail(self):
        for gpl in self:
            detail_dic = {}
            for pol in gpl._get_lines_ungruped():
                size_att = pol.product_id.attribute_value_ids.\
                    filtered(lambda v: v.is_color is False)
                if size_att:
                    detail_dic[size_att.name] = pol.product_qty

            gpl.att_detail = self._get_att_detail_str(gpl, detail_dic)

    @api.multi
    def _get_group_note(self):
        for gpl in self:
            note = ""
            for pol in gpl._get_lines_ungruped():
                if pol.line_note:
                    note += pol.line_note
                    note += '\n'
            gpl.note = note

    @api.multi
    def _get_ref_prov(self):
        for gpl in self:
            ref_prov = ""
            for seller in gpl.template_id.seller_ids:
                if seller.name.id == gpl.order_id.partner_id.id:
                    ref_prov = seller.product_code
            if ref_prov:
                ref_prov = ref_prov
            gpl.ref_prov = ref_prov

    @api.multi
    def _get_sales_str(self):
        for gpl in self:
            sales_str = ""
            sale_ids = []
            for pol in gpl._get_lines_ungruped():
                for wip_line in pol.wip_line_ids:
                    if not wip_line.sale_id:
                        continue
                    if wip_line.sale_id.id not in sale_ids:
                        sale_ids.append(wip_line.sale_id.id)
                if not sale_ids and pol.related_sale_id:
                    sale_ids.append(wip_line.sale_id.ids)

            domain = [('id', 'in', sale_ids)]
            sale_objs = self.env['sale.order'].search(domain, order='id')
            for sale in sale_objs:
                if not sales_str:
                    sales_str += sale.name
                else:
                    sales_str += ', ' + sale.name

                if sale.model_id:
                    sales_str += '/' + sale.model_id.name
            gpl.sales_str = sales_str

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
pol.product_uom as uom_id,
coalesce(sum(pol.width), 0) as width,
coalesce(sum(pol.grammage), 0) as grammage,
coalesce(sum(pt.gauge), 0) as gauge,
coalesce(sum(pt.thread), 0) as thread,
coalesce(sum(pol.product_qty), 0) AS qty,
coalesce(sum(pol.price_unit), 0) AS price
FROM purchase_order_line pol
LEFT JOIN product_product pp ON pp.id = pol.product_id
LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
GROUP BY pol.order_id, pp.product_tmpl_id, pol.color_id, pol.product_uom
)""")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    origin_po_id = fields.Many2one('purchase.order', 'Purchase Origin')
    attn = fields.Char('Attention Of')

    @api.depends('product_id')
    def _get_color(self):
        for pol in self:
            colors = pol.product_id.attribute_value_ids.filtered('is_color')
            pol.color_id = colors[0] if colors else False

    grouped_line_ids = fields.One2many('group.po.line', 'order_id',
                                       'Grouped Lines')
    line_note = fields.Text('Line Note')
    origin_sale_id = fields.Many2one('sale.order', 'Origin sale',
                                     compute='_get_from_sale_id')
    origin_model_id = fields.Many2one('textile.model', 'Origin model',
                                      compute='_get_from_sale_id')
    origin_model_name = fields.Char('Origin model name',
                                    compute='_get_from_sale_id')
    origin_sale_name = fields.Char('Origin model name',
                                   compute='_get_from_sale_id')

    @api.multi
    def _get_from_sale_id(self):
        for po in self:
            origin_sale_id = False
            origin_model_id = False
            origin_sale_name = ""
            origin_model_name = ""
            sale_ids = []
            for pol in po.order_line:
                for wip_line in pol.wip_line_ids:
                    if not wip_line.sale_id:
                        continue
                    if wip_line.sale_id.id not in sale_ids:
                        sale_ids.append(wip_line.sale_id.id)
                if not sale_ids and pol.related_sale_id:
                    sale_ids.append(pol.sale_id.id)
            if len(sale_ids) == 1:
                origin_sale = self.env['sale.order'].browse(sale_ids[0])
                origin_model = origin_sale.model_id
                if origin_sale:
                    origin_sale_id = origin_sale.id
                    origin_sale_name = origin_sale.name
                if origin_model:
                    origin_model_id = origin_model.id
                    origin_model_name = origin_model.name
            po.origin_sale_id = origin_sale_id
            po.origin_model_id = origin_model_id
            po.origin_sale_name = origin_sale_name
            po.origin_model_name = origin_model_name
