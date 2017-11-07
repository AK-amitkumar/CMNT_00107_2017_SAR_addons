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

    task_id = fields.Many2one('project.task', 'Task', readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Project',
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
        for res in self:
            track_record = track_model.get_track_for_model(res._name, res)
            if track_record:
                track_record.create_task_tracking(res)
        return res

    # @api.multi
    # def write(self, vals):
    #     """
    #     Propagate to task da date expected to date end
    #     """
    #     res = super(StockMove, self).write(vals)
    #     if 'date_expected' in vals:
    #         for move in self:
    #             if move.task_id and \
    #                     move.task_id.date_end != move.date_expected:
    #                 move.task_id.date_end = move.date_expected
    #     return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(MrpProduction, self).action_cancel()
        self.mapped('task_id').unlink()
        return res
