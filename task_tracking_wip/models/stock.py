# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_related_project(self):
        """
        Search related sale of procurement group to get the project
        """
        for pick in self:
            project_id = False
            if pick.group_id:
                domain = [('procurement_group_id', '=', pick.group_id.id)]
                sale_obj = self.env['sale.order'].search(domain, limit=1)
                if sale_obj:
                    project_id = sale_obj.project_wip_id.id
            if not project_id and pick.move_lines \
                    and pick.move_lines[0].move_dest_id:
                project_id = pick.move_lines[0].move_dest_id.\
                    picking_id.project_wip_id.id
            # Incoming picking
            if not project_id and pick.move_lines:
                    for move in pick.move_lines:
                        if move.task_ids:
                            project_id = move.task_ids[0].project_id.id
                        break
            pick.project_wip_id = project_id

    task_ids = fields.One2many('project.task', 'picking_id', 'Tasks',
                               readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Initial Project',
                                     compute='_get_related_project')

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(StockPicking, self).action_cancel()
        self.mapped('task_ids').unlink()
        return res

    @api.multi
    def _create_backorder(self, backorder_moves=[]):
        track_model = self.env['tracking.wip']
        res = super(StockPicking, self)._create_backorder(backorder_moves)
        for backorder in res:
            for move in backorder.move_lines:
                if not move.split_from:
                    continue

                # Delete distribution
                move.split_from.wip_line_ids.unlink()
                for t in move.split_from.task_ids:
                    new_task = t.copy({'move_id': move.id})
                    # Write successors to new task
                    sucessors = t.mapped('sucessor_ids.task_id')
                    track_model.link_predecessor_task(sucessors, new_task)
                    # Write pedecessors to new task
                    for predecessor in t.mapped('sucessor_ids.parent_task_id'):
                        track_model.link_predecessor_task(new_task,
                                                          predecessor)
                track_record = track_model.get_track_for_model(backorder._name,
                                                               backorder)
                # Recompute child tasks
                if track_record:
                    track_record.manage_parent_child_tasks(backorder)
        return res

    @api.multi
    def write(self, vals):
        """
        Propagate to task da date expected to date end.
        # TODO maybe date done too?
        """
        res = super(StockPicking, self).write(vals)
        if 'min_date' in vals:
            for pick in self:
                if not pick.task_ids:
                    continue
                ref_task = pick.task_ids[0]  # because all tasks same date
                new_date_end = pick.min_date
                # Skip innecesary write
                # if new_date_end == ref_task.date_end:
                #     continue

                if new_date_end < ref_task.date_start:
                    new_date_end = ref_task.date_start

                # Update task_ids date end
                pick.task_ids.write({'date_end': new_date_end})
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_related_project(self):
        """
        Search related sale of procurement group to get the project
        """
        for move in self:
            project_id = False
            if move.group_id:
                domain = [('procurement_group_id', '=', move.group_id.id)]
                sale_obj = self.env['sale.order'].search(domain, limit=1)
                if sale_obj:
                    project_id = sale_obj.project_wip_id.id
            if not project_id and move.move_dest_id:
                project_id = move.move_dest_id.project_wip_id.id

            # Incoming move or move with distribution lines
            if not project_id and move.wip_line_ids:
                project_id = move.wip_line_ids[0].task_id.project_id.id and \
                    move.wip_line_ids[0].task_id.project_id.id
            move.project_wip_id = project_id

    # task_id = fields.Many2one('project.task', 'Task', readonly=True)
    task_ids = fields.One2many('project.task', 'move_id', 'Tasks',
                               readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Initial Project',
                                     compute='_get_related_project')
    wip_line_ids = fields.One2many('wip.distribution.line', 'move_id',
                                   'Distribution Lines')

    @api.multi
    def assign_picking(self):
        track_model = self.env['tracking.wip']
        res = super(StockMove, self).assign_picking()
        for move in self:
            pick = move.picking_id
            if pick and not pick.task_ids:
                track_record = track_model.get_track_for_model(pick._name,
                                                               pick)
                if track_record:
                    track_record.create_task_tracking(pick)

            # Create parent-child relationship
            if move.task_ids and pick.task_ids:
                # We need both writes
                pick.move_lines.mapped('task_ids').\
                    write({'parent_id': pick.task_ids[0].id})
                move.task_ids.write({'parent_id': pick.task_ids[0].id})
            return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(StockMove, self).action_cancel()
        self.mapped('picking_id.task_ids').unlink()
        self.mapped('task_ids').unlink()
        return res

    @api.multi
    def action_confirm(self):
        """
        """
        res = False
        if not self._context.get('no_confirm', False):
            res = super(StockMove, self).action_confirm()
        return res

    @api.model
    def create(self, vals):
        track_model = self.env['tracking.wip']
        res = super(StockMove, self).create(vals)
        track_record = track_model.get_track_for_model(res._name, res)
        if track_record:
            if res.wip_line_ids:
                # CREATE TASKS FOR INCOMING MOVES WITH DISTRIBUTION LINES
                track_record.create_move_tasks_tracking(res)
            else:
                track_record.create_task_tracking(res)
        return res

    @api.multi
    def break_links(self):
        """
        Break all move_dest_id links, making state in confirmed
        """
        domain = [('move_dest_id', 'in', self.ids)]
        # Break moves links
        prev_moves = self.search(domain)
        prev_moves.write({'move_dest_id': False})
        # Break procurements links
        prev_procs = self.env['procurement.order'].search(domain)
        prev_procs.write({'move_dest_id': False})
        # Change waitigs moves to confirmed
        self.filtered(lambda m: m.state == 'waiting').write({
            'state': 'confirmed',
            'procure_method': 'make_to_stock'
        })
        return

    @api.multi
    def action_done(self):
        """
        Create as many quants as distribution lines, and reserve moves for it.
        """
        res = super(StockMove, self).action_done()
        todo_quants = self.env['stock.quant']
        for move in self:
            todo_quants += move.quant_ids
            for line in move.wip_line_ids:
                rel_move = line.task_id.model_reference
                rem_qty = line.qty
                while rem_qty > 0:
                    for q in todo_quants:
                        if q.qty > rem_qty:
                            new_quant = q._quant_split(line.qty)
                            if new_quant:
                                todo_quants += new_quant

                        # q.write({'pre_reservation_id': rel_move.id})
                        q.write({'reservation_id': rel_move.id})
                        # rel_move.action_assign()
                        # TODO reserve
                        todo_quants -= q
                        rem_qty -= q.qty

                updated_quants = []
                for quant in rel_move.reserved_quant_ids:
                    updated_quants.append((quant, quant.qty))
                self.env['stock.quant'].quants_reserve(updated_quants,
                                                       rel_move)
        return res

    @api.multi
    def recompute_task_links(self):
        self.ensure_one()
        track_model = self.env['tracking.wip']
        track_model.recompute_tasks_from_reserve(self)

    @api.multi
    def write(self, vals):
        """
        Propagate to task date expected to date end.
        # TODO maybe date done too?
        """
        res = super(StockMove, self).write(vals)
        if 'date_expected' in vals:
            for move in self:
                if not move.task_ids:
                    continue
                ref_task = move.task_ids[0]
                new_date_end = move.date_expected
                # Skip innecesary write
                # if new_date_end == ref_task.date_end:
                #     continue

                if new_date_end < ref_task.date_start:
                    new_date_end = ref_task.date_start

                # Update task_ids date end
                move.task_ids.write({'date_end': new_date_end})
                # Update_parent_tasks
                move.task_ids.mapped('parent_id').write({'date_end':
                                                         new_date_end})
        return res


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def quants_reserve(self, quants, move, link=False):
        """
        Update wip from reserved quants
        """
        track_model = self.env['tracking.wip']
        super(StockQuant, self).quants_reserve(quants, move, link=link)
        if move.state == 'assigned' or move.partially_available:
            track_model.recompute_tasks_from_reserve(move)

    # pre_reservation_id = fields.Many2one('stock.move',
    #                                      'Pre Reserved for Move',
    #                                      index=True, readonly=True,
    #                                      help="The move the quant is \
    #                                      pre-reserved for")

    # @api.model
    # def quants_get_preferred_domain(self, qty, move, ops=False,
    #                                 lot_id=False, domain=None,
    #                                 preferred_domain_list=[]):
    #     pdl = preferred_domain_list

    #     domain.append = [('pre_reservation_id', '=', False)]
    #     return super(StockQuant, self).\
    #         quants_get_preferred_domain(qty, move, ops=ops, lot_id=lot_id,
    #                                     domain=domain,
    #                                     preferred_domain_list=pdl)

    # @api.model
    # def quants_reserve(self, quants, move, link=False):
    #     """
    #     PROBAMOS SIN GARANTIZAR QUE SE COGAN EXACTAMENTE ESTOS QUANTS
    #     PARA ASI NO GESTIONAR EL CAMPOR PRERESERVATION_ID
    #     If move appears in a distribution line, ignore quants param
    #     and get the ones related with the distribution line (Those quants
    #     reserved for the move param in the distribution line's move)
    #     """

    #     # Search if move in a distribution line
    #     domain = [('move_id', '!=', False), ('move_dest_id', '=', move.id)]
    #     wip_line = self.env['wip.distribution.line'].search(domain, limit=1)
    #     orig_move = wip_line.move_id if wip_line else False

    #     updated_quants = quants
    #     if orig_move:
    #         updated_quants = []
    #         for quant in orig_move.quant_ids:
    #             if quant.pre_reservation_id.id == move.id:
    #                 updated_quants.append((quant, quant.qty))
    #     super(StockQuant, self).quants_reserve(updated_quants, move,
    #                                            link=link)
