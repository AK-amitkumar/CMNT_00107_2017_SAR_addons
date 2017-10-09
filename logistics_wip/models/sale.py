# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class SaleOrder(models.Model):

    _inherit = "sale.order"

    model_id = fields.Many2one("textile.model", "Model",
                               domain=[('model_type', '=', 'model'),
                                       ('state', '=', 'approved')])
    project_wip_id = fields.Many2one('project.project', 'Project',
                                     related="model_id.project_id",
                                     readonly=True)
