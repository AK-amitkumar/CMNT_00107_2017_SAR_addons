# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class LabelType(models.Model):

    _name = 'label.type'

    name = fields.Char()


class SaleLabelPrice(models.Model):

    _name = 'sale.label.price'

    price = fields.Float()
    location = fields.Many2one('label.location', 'Location')
    sale_id = fields.Many2one('sale.order')
    currency = fields.Many2one('res.currency', related="location.currency",
                               readonly=True)


class LabelLocation(models.Model):

    _name = 'label.location'

    name = fields.Char()
    currency = fields.Many2one('res.currency',
                               default=lambda s:
                               s.env.user.company_id.currency_id.id)
