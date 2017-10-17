# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # @api.multi
    # @api.depends('predecessor_ids.parent_task_id.date_end',
    #              'model_reference')
    # def _compute_dates(self):
    #     # import ipdb; ipdb.set_trace()
    #     for task in self:
    #         date_start = False
    #         date_end = False
    #         if task.model_reference:
    #             # SALE line tasks
    #             if task.model_reference._name == 'sale.order.line':
    #                 date_start = task.model_reference.create_date
    #                 date_end = task.model_reference.order_id.commitment_date

    #             # MOVE tasks
    #             elif task.model_reference._name == 'stock.move':
    #                 date_start = task.model_reference.date_expected
    #                 date_end = task.model_reference.date_expected
    #                 if task.predecessor_ids:
    #                     if task.predecessor_ids[0].parent_task_id.date_end:
    #                         date_start = task.predecessor_ids[0].\
    #                             parent_task_id.date_end
    #         # import ipdb; ipdb.set_trace()
    #         task.date_start = date_start
    #         task.date_end = date_end if date_end > date_start else date_start

    # @api.multi
    # def _set_end_dates(self):
    #     import ipdb; ipdb.set_trace()
    #     for task in self:
    #         if task.model_reference:
    #             if task.model_reference._name == 'stock.move':
    #                 task.model_reference.date_expected = task.date_end

    # date_start = fields.Datetime(compute='_compute_dates', store=True)
    # date_end = fields.Datetime(compute='_compute_dates',
    #                            inverse='_set_end_dates',
    #                            store=True)
    sucessor_ids = fields.One2many('project.task.predecessor',
                                   'parent_task_id', 'Sucessors')
    progress_model = fields.Float(compute='_get_model_progress', store=False,
                                  string='Origin Progress',
                                  group_operator="avg")

    @api.multi
    def _get_model_progress(self):
        for task in self:
            progress = 0.0

            if task.model_reference:
                m = task.model_reference
                if m == 'sale_order_line' and m.product_uom_qty:
                    progress = m.qty_delivered / m.product_uom_qty
                elif m == 'stock.move' and m.production_id and m.quantity:
                    progress = m.quantity_done / m.quantity
                elif m == 'stock.move' and m.state == 'done':
                    progress = 100
                elif m == 'mrp.workorder' and m.qty_production:
                    progress = m.qty_produced / m.qty_production

            task.progress_model = progress * 100.0

    @api.multi
    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if 'date_end' in vals:
            for task in self:
                # Propagate date end to date_start succesor
                if task.sucessor_ids and \
                        task.sucessor_ids[0]._name == 'stock.move':
                    task.mapped('sucessor_ids.task_id').\
                        write({'date_start': task.date_end})
                # Change date_expected in move
                if task.model_reference and \
                        task.model_reference._name == 'stock.move' and \
                        task.model_reference.date_expected != task.date_end:
                    task.model_reference.write({
                        'date_expected': task.date_end})

        if 'predecessor_ids' in vals:
            for task in self:
                if task.predecessor_ids and task.model_reference and \
                        task.model_reference._name != 'sale.order.line':
                    task.date_start = \
                        task.predecessor_ids[0].parent_task_id.date_end if \
                        task.predecessor_ids[0].parent_task_id.date_end < \
                        task.date_end else task.date_end
        return res


class ProjectTaskPresecessor(models.Model):
    _inherit = 'project.task.predecessor'

    task_id = fields.Many2one(ondelete='cascade')
    parent_task_id = fields.Many2one(ondelete='cascade')
