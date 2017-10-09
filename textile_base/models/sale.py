# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    made_in = fields.Many2one(
        'res.country', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    label_types = fields.Many2many(
        'label.type', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    label_prices = fields.One2many(
        'sale.label.price', 'sale_id', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
