# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _get_related_project(self):
        """
        Search related sale of procurement group to get the project
        """
        for mo in self:
            project_id = False
            if mo.procurement_group_id:
                domain = [
                    ('procurement_group_id', '=', mo.procurement_group_id.id)
                ]
                sale_obj = self.env['sale.order'].search(domain, limit=1)
                if sale_obj:
                    project_id = sale_obj.project_wip_id.id
            mo.project_wip_id = project_id

    task_ids = fields.One2many('project.task', 'production_id', 'Tasks',
                               readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Initial Project',
                                     compute='_get_related_project')

    # def _generate_raw_moves(self, exploded_lines):
    #     self.ensure_one()
    #     moves = self.env['stock.move']
    #     for bom_line, line_data in exploded_lines:
    #         moves += self._generate_raw_move(bom_line, line_data)
    #     return moves

    @api.multi
    def _generate_moves(self):
        """
        Instead in create beacause of action_confirm in generate_moves
        """
        track_model = self.env['tracking.wip']
        super(MrpProduction, self)._generate_moves()
        for mo in self:
            track_record = track_model.get_track_for_model(mo._name, mo)
            if track_record:
                track_record.create_task_tracking(mo)

            # Create parent-child relationship
            if mo.task_ids:
                    mo.move_finished_ids.mapped('task_ids').\
                        write({'parent_id': mo.task_ids[0].id})
        return mo

    @api.multi
    def write(self, vals):
        """
        Propagate to task da date expected to date end
        """
        res = super(MrpProduction, self).write(vals)
        if 'date_planned_finished' in vals:
            for mo in self:
                if mo.task_ids and \
                        mo.task_ids[0].date_end != mo.date_planned_finished:
                    mo.task_ids.write({'date_end': mo.date_planned_finished})
        return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(MrpProduction, self).action_cancel()
        self.mapped('task_ids').unlink()
        return res
