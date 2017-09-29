# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_related_project(self):
        for move in self:
            project_id = False
            project_id = 2
            move.project_wip_id = project_id

    task_id = fields.Many2one('project.task', 'Task')
    project_wip_id = fields.Many2one('project.project', 'Project',
                                     compute='_get_related_project')
