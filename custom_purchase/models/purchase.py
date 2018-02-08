# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from odoo import tools


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    origin_po_id = fields.Many2one('purchase.order', 'Purchase Origin')
    attn = fields.Char('Attention Of')

    grouped_line_ids = fields.One2many('group.po.line', 'order_id',
                                       'Grouped Lines')
    line_note = fields.Text('Line Note')
    lines_sale_id = fields.Many2one('sale.order', 'Sale purchase lines')
    lines_model_id = fields.Many2one('textile.model', 'Model Purchase lines')
    origin_sale_id = fields.Many2one('sale.order', 'Origin sale',
                                     compute='_get_from_sale_id')
    origin_model_id = fields.Many2one('textile.model', 'Origin model',
                                      compute='_get_from_sale_id',
                                      readonly=True)
    origin_model_name = fields.Char('Origin model name',
                                    compute='_get_from_sale_id',
                                    readonly=True)
    origin_sale_name = fields.Char('Origin model name',
                                   compute='_get_from_sale_id',
                                   readonly=True)

    @api.multi
    def _get_from_sale_id(self):
        for po in self:
            origin_sale_id = False
            origin_model_id = False
            origin_sale_name = ""
            origin_model_name = ""
            set_sale_ids = set()
            for pol in po.order_line:
                for wip_line in pol.wip_line_ids:
                    if not wip_line.sale_id:
                        continue
                    set_sale_ids.add(wip_line.sale_id.id)
                if pol.related_sale_id and not pol.wip_line_ids:
                    set_sale_ids.add(pol.related_sale_id.id)
            sale_ids = list(set_sale_ids)
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


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    related_sale_id = fields.Many2one('sale.order', 'Related Sale')
    related_model_id = fields.Many2one('textile.model', 'Related Model')
    color_id = fields.Many2one('product.attribute.value',
                               compute='_get_color', store=True)
    line_note = fields.Text('Line Note')

    @api.onchange('related_sale_id')
    def onchange_sale_id(self):
        if self.related_sale_id and self.related_sale_id.model_id:
            self.related_model_id = self.related_sale_id.model_id.id

    @api.depends('product_id')
    def _get_color(self):
        for pol in self:
            colors = pol.product_id.attribute_value_ids.filtered('is_color')
            pol.color_id = colors[0] if colors else False

    @api.model
    def default_get(self, field_list):
        res = super(PurchaseOrderLine, self).default_get(field_list)
        related_sale_id = self._context.get('lines_sale_id', False)
        related_model_id = self._context.get('lines_model_id', False)
        res.update({
            'related_sale_id': related_sale_id,
            'related_model_id': related_model_id
        })
        return res


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
    sale_id = fields.Many2one('sale.order', 'Related Sale', readonly=True)
    model_id = fields.Many2one('textile.model', 'Related Model', readonly=True)
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
                    att_qty = pol.product_qty
                    if gpl.sale_id and pol.wip_line_ids:
                        att_qty = 0
                        wip_lines = pol.wip_line_ids.\
                            filtered(lambda l: l.sale_id.id == gpl.sale_id.id)
                        for wl in wip_lines:
                            att_qty += wl.qty
                    detail_dic[size_att.name] = att_qty

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
                    ref_prov = seller.product_code or ""
            if ref_prov:
                ref_prov = ref_prov
            gpl.ref_prov = ref_prov

    @api.multi
    def _get_sales_str(self):
        for gpl in self:
            sales_str = ''
            if gpl.sale_id:
                sales_str += gpl.sale_id.name
            if gpl.sale_id.model_id:
                sales_str += '/' + gpl.sale_id.model_id.name
            gpl.sales_str = sales_str

    @api.model_cr
    def init(self):
        """
        @param cr: the current row, from the database cursor
        """
        tools.drop_view_if_exists(self._cr, 'group_po_line')
        self._cr.execute("""
CREATE OR REPLACE VIEW group_po_line AS (
select * from
(
SELECT
min(pol.id) as id,
pp.product_tmpl_id AS template_id,
pol.order_id AS order_id,
pol.color_id AS color_id,
pol.related_sale_id as sale_id,
pol.related_model_id as model_id,
pol.product_uom as uom_id,
coalesce(avg(pol.width), 0) as width,
coalesce(avg(pol.grammage), 0) as grammage,
coalesce(avg(pt.gauge), 0) as gauge,
coalesce(avg(pt.thread), 0) as thread,
coalesce(sum(pol.product_qty), 0) AS qty,
coalesce(pol.price_unit, 0) AS price
FROM purchase_order_line pol
LEFT JOIN product_product pp ON pp.id = pol.product_id
LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
WHERE not exists (select 1 from wip_distribution_line where pl_id = pol.id)
GROUP BY pol.order_id, pp.product_tmpl_id, pol.color_id, pol.related_sale_id,
         pol.related_model_id,pol.product_uom, pol.price_unit

UNION

SELECT
min(wdl.id) * -1 as id,
pp.product_tmpl_id AS template_id,
pol.order_id AS order_id,
pol.color_id AS color_id,
wdl.sale_id as sale_id,
tm.id as model_id,
pol.product_uom as uom_id,
coalesce(avg(pol.width), 0) as width,
coalesce(avg(pol.grammage), 0) as grammage,
coalesce(avg(pt.gauge), 0) as gauge,
coalesce(avg(pt.thread), 0) as thread,
coalesce(sum(wdl.qty), 0) AS qty,
coalesce(pol.price_unit, 0) AS price
FROM wip_distribution_line wdl
LEFT JOIN sale_order so on so.id = wdl.sale_id
LEFT JOIN textile_model tm on tm.id = so.model_id
LEFT JOIN purchase_order_line pol on pol.id = wdl.pl_id
LEFT JOIN product_product pp ON pp.id = pol.product_id
LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
WHERE exists (select 1 from wip_distribution_line where pl_id = pol.id)
GROUP BY pol.order_id, wdl.sale_id, tm.id, pp.product_tmpl_id, pol.color_id,
         pol.product_uom, pol.price_unit
) SQ

)""")
