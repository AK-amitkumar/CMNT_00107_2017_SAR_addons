# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ProductAttributeValueSizeRefs(models.Model):

    _name = "product.attribute.value.size.refs"

    customer = fields.Many2one("res.partner", "Customer", required=True,
                               domain=[('customer', '=', True)])
    code = fields.Char("Ref.", help="Ref. in customer", required=True)
    name = fields.Char("Name", help="Name in customer", required=True)
    attribute_value = fields.Many2one("product.attribute.value", "Attribute")


class ProductAttribute(models.Model):

    _inherit = "product.attribute"

    is_size = fields.Boolean("Is size",
                             help="Check it if attribute will contain sizes")


class ProductAttributeValue(models.Model):

    _inherit = "product.attribute.value"

    size_refs = fields.One2many("product.attribute.value.size.refs",
                                "attribute_value", "References")
    is_size = fields.Boolean("Is size", related="attribute_id.is_size",
                             readonly=True)
