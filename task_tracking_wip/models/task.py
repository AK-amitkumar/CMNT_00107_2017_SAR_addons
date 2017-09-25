# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

MODELS = [('sales.order.line', 'Sales order Line'),
          ('stock.move', 'Stock move')]


class ProjectTask(models.Model):
    """ Inherits partner and adds Tasks information in the partner form """
    _inherit = 'project.task'

    wip_model = fields.Reference(selection=MODELS, string="WIP reference")
