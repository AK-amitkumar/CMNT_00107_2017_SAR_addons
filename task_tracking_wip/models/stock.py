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
            pick.project_wip_id = project_id

    task_id = fields.Many2one('project.task', 'Task', readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Project',
                                     compute='_get_related_project')

    # @api.multi
    # def write(self, vals):
    #     """
    #     Propagate to task da date expected to date end
    #     """
    #     res = super(StockPicking, self).write(vals)
    #     if 'min_date' in vals:
    #         for pick in self:
    #             if pick.task_id and \
    #                     pick.task_id.date_end != pick.min_date:
    #                 pick.task_id.date_end = pick.min_date
    #     return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(StockPicking, self).action_cancel()
        self.mapped('task_id').unlink()
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
            move.project_wip_id = project_id

    # task_id = fields.Many2one('project.task', 'Task', readonly=True)
    task_ids = fields.One2many('project.task', 'move_id', 'Tasks',
                               readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Project',
                                     compute='_get_related_project')
    wip_line_ids = fields.One2many('wip.distribution.line', 'move_id',
                                   'Distribution Lines')

    @api.multi
    def assign_picking(self):
        track_model = self.env['tracking.wip']
        res = super(StockMove, self).assign_picking()
        for move in self:
            pick = move.picking_id
            if pick and not pick.task_id:
                track_record = track_model.get_track_for_model(pick._name,
                                                               pick)
                if track_record:
                    track_record.create_task_tracking(pick)

            # Create parent-child relationship
            if move.task_ids and pick.task_id:
                # We need both writes
                pick.move_lines.mapped('task_ids').\
                    write({'parent_id': pick.task_id.id})
                move.task_ids.write({'parent_id': pick.task_id.id})
            return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(StockMove, self).action_cancel()
        self.mapped('picking_id.task_id').unlink()
        self.mapped('task_ids').unlink()
        return res

    @api.multi
    def action_confirm(self):
        """
        """
        # import ipdb; ipdb.set_trace()
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
            track_record.create_task_tracking(res)

        return res

    # @api.multi
    # def write(self, vals):
    #     """
    #     Propagate to task da date expected to date end
    #     # TODO review
    #     """
    #     res = super(StockMove, self).write(vals)
    #     import ipdb; ipdb.set_trace()
    #     if 'date_expected' in vals:
    #         for move in self:
    #             if move.task_id and \
    #                     move.task_id.date_end != move.date_expected:
    #                 move.task_id.date_end = move.date_expected \
    #                     if move.date_expected >= move.task_id.date_start \
    #                     else move.task_id.date_start
    #     return res

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
                while rem_qty:
                    for q in todo_quants:
                        if q.qty > rem_qty:
                            new_quant = q._quant_split(line.qty)
                            todo_quants += new_quant

                        q.write({'pre_reservation_id': rel_move.id})
                        todo_quants -= q
                        rem_qty -= q.qty
        return res


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    pre_reservation_id = fields.Many2one('stock.move', 'Pre Reserved for Move',
                                         index=True, readonly=True,
                                         help="The move the quant is \
                                         pre-reserved for")

    @api.model
    def quants_get_preferred_domain(self, qty, move, ops=False,
                                    lot_id=False, domain=None,
                                    preferred_domain_list=[]):
        pdl = preferred_domain_list
        if move._context.get('custom_assign', False):
            domain.append = [('pre_reservation_id', '=', False)]
        return super(StockQuant, self).\
            quants_get_preferred_domain(qty, move, ops=ops, lot_id=lot_id,
                                        domain=domain,
                                        preferred_domain_list=pdl)

    @api.model
    def quants_reserve(self, quants, move, link=False):
        """
        If move appears in a distribution line, ignore quants param
        and get the ones related with the distribution line (Those quants
        reserved for the move param in the distribution line's move)
        """

        # Search if move in a distribution line
        domain = [('move_id', '!=', False), ('move_dest_id', '=', move.id)]
        wip_line = self.env['wip.distribution.line'].search(domain, limit=1)
        orig_move = wip_line.move_id if wip_line else False

        updated_quants = quants
        if orig_move:
            updated_quants = []
            for quant in orig_move.quant_ids:
                if quant.pre_reservation_id.id == move.id:
                    updated_quants.append((quant, quant.qty))
        super(StockQuant, self).quants_reserve(updated_quants, move, link=link)
