# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ProductAttributeValueColorRefs(models.Model):

    _name = "product.attribute.value.color.refs"

    season = fields.Many2one("account.analytic.tag", "Season", required=True,
                             domain=[('type', '=', 'season')])
    customer = fields.Many2one("res.partner", "Customer", required=True,
                               domain=[('customer', '=', True)])
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')],
                             "State", required=True, default='draft',
                             readonly=True)
    code = fields.Char("Ref.", help="Ref. in customer", required=True)
    name = fields.Char("Name", help="Name in customer", required=True)
    attribute_value = fields.Many2one("product.attribute.value", "Attribute")
    approve_user = fields.Many2one("res.users", "Approver", readonly=True)
    approve_date = fields.Date("Approvation date", readonly=True)
    pantone = fields.Char("Pantone")
    lapdip = fields.Char("Lapdip")
    composition_id = fields.Many2one("product.composition", "Composition")

    @api.multi
    def action_approve(self):
        for ref in self:
            ref.approve_user = self.env.uid
            ref.state = "approved"
            ref.approve_date = fields.Date.context_today(ref)

    @api.multi
    def action_set_draft(self):
        for ref in self:
            ref.approve_user = False
            ref.state = "draft"
            ref.approve_date = False


class ProductAttributeValue(models.Model):

    _inherit = "product.attribute.value"

    @api.depends('attribute_id')
    def _compute_is_color(self):
        for value in self:
            if value.attribute_id == \
                    self.env.ref('textile_base.color_attribute'):
                value.is_color = True
            else:
                value.is_color = False

    color_hex = fields.Char("Color", help="Choose your color", size=7)
    color_refs = fields.One2many("product.attribute.value.color.refs",
                                 "attribute_value", "References")
    active_color_refs = fields.One2many("product.attribute.value.color.refs",
                                        "attribute_value", "References",
                                        domain=[("season.active", '=', True)])
    is_color = fields.Boolean("Is color", compute="_compute_is_color",
                              readonly=True, store=True)

    @api.multi
    def open_refs_history(self):
        action = self.env.ref('textile_base.color_refs_action')
        result = action.read()[0]
        result['domain'] = [('attribute_value', 'in', self.ids)]
        result['flags'] = {'action_buttons': False}
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        active_color_refs = self.env['product.attribute.value.color.refs']
        if self._context.get('customer', False):
            active_color_refs += \
                self.env['product.attribute.value.color.refs'].search(
                    [('customer', '=', self._context['customer']),
                     ('season', '=', self._context['season']),
                     ('state', '=', 'approved')])
            args.append(
                ('id', 'in', active_color_refs.mapped('attribute_value.id')))
        return super(ProductAttributeValue, self).name_search(
            name, args=args, operator=operator, limit=limit)
