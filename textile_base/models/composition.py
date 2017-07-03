# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ProductComposition(models.Model):

    _name = "product.composition"

    name = fields.Char("Short description", required=True)
    description = fields.Text("Long Description", required=True)
    fabric_type = fields.Selection([('plain', 'Plain'), ('point', 'Point'),
                                    ('other', 'Other')], 'Fabric type',
                                   required=True, default="plain")
    hs_code_id = fields.Many2one("hs.code", "HS Code",
                                 help="Harmonized System Code. (Taric)")
