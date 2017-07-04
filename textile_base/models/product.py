# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    article_type = fields.Selection(
        (('premodel', 'Premodel'),
         ('model', 'Model'),
         ('cost', 'Cost'),
         ('accesory', 'Accesory'),
         ('service', 'Service'),
         ('tissue', 'Tissue'),
         ('others', 'Others')))
