# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sucessor_ids = fields.One2many('project.task.predecessor',
                                   'parent_task_id', 'Sucessors')

class ProjectTaskPresecessor(models.Model):
    _inherit = 'project.task.predecessor'

    task_id = fields.Many2one(ondelete='cascade')
    parent_task_id = fields.Many2one(ondelete='cascade')
