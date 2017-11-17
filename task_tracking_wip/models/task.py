# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sucessor_ids = fields.One2many('project.task.predecessor',
                                   'parent_task_id', 'Sucessors')
    progress_model = fields.Float(compute='_get_model_progress', store=False,
                                  string='Origin Progress',
                                  group_operator="avg")
    sale_id = fields.Many2one('sale_order', 'Related Sale', readonly=True)

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
                # except sale.order.line
                if task.sucessor_ids and \
                        task.sucessor_ids[0].task_id.model_reference and \
                        task.sucessor_ids[0].task_id.\
                        model_reference._name != 'sale.order.line':
                    task.mapped('sucessor_ids.task_id').\
                        write({'date_start': task.date_end})

                # Change min date in picking
                if task.model_reference and \
                        task.model_reference._name == 'stock.picking' and \
                        task.model_reference.min_date != task.date_end:
                    task.model_reference.write({
                        'min_date': task.date_end})

                if task.model_reference and \
                        task.model_reference._name == 'stock.move' and \
                        task.model_reference.date_expected != task.date_end:
                    task.model_reference.write({
                        'date_expected': task.date_end
                    })

        if 'predecessor_ids' in vals:
            for task in self:
                if task.predecessor_ids and task.model_reference:
                    if task.model_reference._name != 'sale.order.line':
                        task.date_start = \
                            task.predecessor_ids[0].\
                            parent_task_id.date_end if \
                            task.predecessor_ids[0].\
                            parent_task_id.date_end < \
                            task.date_end else task.date_end
                    else:
                        task.mapped('predecessor_ids.parent_task_id').\
                            write({'date_end': task.date_end})
        return res

    @api.multi
    def unlink(self):
        """
        Avoid unlink warning when delete parent task, we remove first child
        tasks
        """
        child_tasks = self.search([('parent_id', 'in', self.ids)])
        if child_tasks:
            child_tasks.unlink()
        return super(ProjectTask, self).unlink()


class ProjectTaskPresecessor(models.Model):
    _inherit = 'project.task.predecessor'

    task_id = fields.Many2one(ondelete='cascade')
    parent_task_id = fields.Many2one(ondelete='cascade')
