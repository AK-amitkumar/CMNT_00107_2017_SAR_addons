# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def search_existing_mo(self):
        self.ensure_one()
        product = self.product_id
        domain = [
            ('procurement_group_id', '=', self.group_id.id),
            ('product_id.product_tmpl_id', '=', product.product_tmpl_id.id),
            ('state', '=', 'confirmed')
        ]
        mo = self.env['mrp.production'].search(domain, limit=1)
        if mo:
            mo_color = mo.product_id.attribute_value_ids.filtered('is_color')
            prod_color = product.attribute_value_ids.filtered('is_color')
            if mo_color == prod_color:
                return mo
        return False

    @api.multi
    def _add_finished_moves(self, exist_mo):
        move = self.env['stock.move'].create({
            'name': exist_mo.name,
            'date': exist_mo.date_planned_start,
            'date_expected': exist_mo.date_planned_start,
            'product_id': self.product_id.id,
            'product_uom': exist_mo.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'location_id': self.product_id.property_stock_production.id,
            'location_dest_id': exist_mo.location_dest_id.id,
            'move_dest_id': self.move_dest_id.id or False,
            'procurement_id': self.id,
            'company_id': exist_mo.company_id.id,
            'production_id': exist_mo.id,
            'origin': exist_mo.name,
            'group_id': exist_mo.procurement_group_id.id,
            'propagate': exist_mo.propagate,
        })
        move.with_context(no_confirm=True).action_confirm()
        return move

    @api.multi
    def _update_raw_material_moves(self, exist_mo):
        factor_num = exist_mo.product_uom_id.\
            _compute_quantity(self.product_qty,
                              exist_mo.bom_id.product_uom_id)
        factor = factor_num / exist_mo.bom_id.product_qty
        boms, exploded_lines = exist_mo.bom_id.explode(self.product_id, factor,
                                                       picking_type=exist_mo.
                                                       bom_id.picking_type_id)
        # Update or create new lines
        for bom_line, line_data in exploded_lines:
            quantity = line_data['qty']
            prod = bom_line.product_id
            raw_move = exist_mo.move_raw_ids.\
                filtered(lambda x: x.product_id.id == prod.id)
            # Update quantity
            if raw_move:
                raw_move.product_uom_qty = raw_move.product_uom_qty + quantity
            # Create new move
            else:
                if exist_mo.routing_id:
                    routing = exist_mo.routing_id
                else:
                    routing = exist_mo.bom_id.routing_id

                if routing and routing.location_id:
                    source_location = routing.location_id
                else:
                    source_location = exist_mo.location_src_id
                original_quantity = self.product_qty - \
                    exist_mo.qty_produced
                vals = {
                    'sequence': bom_line.sequence,
                    'name': exist_mo.name,
                    'date': exist_mo.date_planned_start,
                    'date_expected': exist_mo.date_planned_start,
                    'bom_line_id': bom_line.id,
                    'product_id': bom_line.product_id.id,
                    'product_uom_qty': quantity,
                    'product_uom': bom_line.product_uom_id.id,
                    'location_id': source_location.id,
                    'location_dest_id':
                    exist_mo.product_id.property_stock_production.id,
                    'raw_material_production_id': exist_mo.id,
                    'company_id': exist_mo.company_id.id,
                    'operation_id': bom_line.operation_id.id,
                    'price_unit': bom_line.product_id.standard_price,
                    'procure_method': 'make_to_stock',
                    'origin': exist_mo.name,
                    'warehouse_id': source_location.get_warehouse().id,
                    'group_id': exist_mo.procurement_group_id.id,
                    'propagate': exist_mo.propagate,
                    'unit_factor': quantity / original_quantity,
                }
        return self.env['stock.move'].create(vals)
        return

    @api.multi
    def extend_mo(self, exist_mo):
        """
        Add new product quantity, recalculate raw material,
        and add finished product
        """
        # Add the finished move
        self._add_finished_moves(exist_mo)
        # Update quantity on raw material id
        self._update_raw_material_moves(exist_mo)
        # Write Sum product_quantity ¿Debo hacerlo con compute quantity?
        exist_mo.product_qty = exist_mo.product_qty + self.product_qty
        self.ensure_one()
        return

    @api.multi
    def make_mo(self):
        """ We need to group in the same productions diferent
            sizes of the same color """
        res = {}
        for procurement in self:
            exist_mo = procurement.search_existing_mo()
            if exist_mo:
                procurement.extend_mo(exist_mo)
                res[procurement.id] = exist_mo.id
            else:
                res[procurement.id] = \
                    super(ProcurementOrder, procurement.
                          with_context(no_confirm=True)).make_mo()
        return res

    @api.multi
    def make_po(self):
        """
        Full overwrited to set default distribution line
        """
        cache = {}
        res = []
        for procurement in self:
            suppliers = procurement.product_id.seller_ids\
                .filtered(lambda r: (not r.company_id or r.company_id == procurement.company_id) and (not r.product_id or r.product_id == procurement.product_id))
            if not suppliers:
                procurement.message_post(body=_('No vendor associated to product %s. Please set one to fix this procurement.') % (procurement.product_id.name))
                continue
            supplier = procurement._make_po_select_supplier(suppliers)
            partner = supplier.name

            domain = procurement._make_po_get_domain(partner)

            if domain in cache:
                po = cache[domain]
            else:
                po = self.env['purchase.order'].search([dom for dom in domain])
                po = po[0] if po else False
                cache[domain] = po
            if not po:
                vals = procurement._prepare_purchase_order(partner)
                po = self.env['purchase.order'].create(vals)
                name = (procurement.group_id and (procurement.group_id.name + ":") or "") + (procurement.name != "/" and procurement.name or procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.name or "")
                message = _("This purchase order has been created from: <a href=# data-oe-model=procurement.order data-oe-id=%d>%s</a>") % (procurement.id, name)
                po.message_post(body=message)
                cache[domain] = po
            elif not po.origin or procurement.origin not in po.origin.split(', '):
                # Keep track of all procurements
                if po.origin:
                    if procurement.origin:
                        po.write({'origin': po.origin + ', ' + procurement.origin})
                    else:
                        po.write({'origin': po.origin})
                else:
                    po.write({'origin': procurement.origin})
                name = (self.group_id and (self.group_id.name + ":") or "") + (self.name != "/" and self.name or self.move_dest_id.raw_material_production_id and self.move_dest_id.raw_material_production_id.name or "")
                message = _("This purchase order has been modified from: <a href=# data-oe-model=procurement.order data-oe-id=%d>%s</a>") % (procurement.id, name)
                po.message_post(body=message)
            if po:
                res += [procurement.id]

            # Create Line
            po_line = False
            related_sale_id = False
            if procurement.move_dest_id and procurement.move_dest_id.task_id\
                     and  procurement.move_dest_id.task_id.sale_id:
                related_sale_id = procurement.move_dest_id.task_id.sale_id.id
            for line in po.order_line:
                if line.product_id == procurement.product_id and line.product_uom == procurement.product_id.uom_po_id:
                    procurement_uom_po_qty = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_po_id)
                    seller = procurement.product_id._select_seller(
                        partner_id=partner,
                        quantity=line.product_qty + procurement_uom_po_qty,
                        date=po.date_order and po.date_order[:10],
                        uom_id=procurement.product_id.uom_po_id)

                    price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, self.company_id) if seller else 0.0
                    if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
                        price_unit = seller.currency_id.compute(price_unit, po.currency_id)

                    po_line = line.write({
                        'product_qty': line.product_qty + procurement_uom_po_qty,
                        'price_unit': price_unit,
                        'procurement_ids': [(4, procurement.id)]
                    })
                    # CREATE DEFAULT DISTRIBUTION LINE
                    self.env['wip.distribution.line'].create(
                        {'pl_id': po_line.id,
                         'qty': procurement_uom_po_qty,
                         'sale_id': related_sale_id
                    })
                    break
            if not po_line:
                vals = procurement._prepare_purchase_order_line(po, supplier)
                new_line = self.env['purchase.order.line'].create(vals)
                # CREATE DEFAULT DISTRIBUTION LINE
                self.env['wip.distribution.line'].create(
                    {'pl_id': new_line.id,
                     'qty': new_line.product_qty,
                     'sale_id': related_sale_id
                    })
        return res
