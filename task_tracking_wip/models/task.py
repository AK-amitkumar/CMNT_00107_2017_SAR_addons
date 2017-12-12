# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sucessor_ids = fields.One2many('project.task.predecessor',
                                   'parent_task_id', 'Sucessors')
    progress_model = fields.Float(compute='_get_model_progress', store=False,
                                  string='Origin Progress',
                                  group_operator="avg")
    sale_id = fields.Many2one('sale.order', 'Related Sale', readonly=True)
    move_id = fields.Many2one('stock.move', 'Related Move', readonly=True)
    production_id = fields.Many2one('mrp.production', 'Related Move',
                                    readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Related Picking',
                                 readonly=True)
    product_id = fields.Many2one('product.product', 'Product',
                                 related='move_id.product_id', readonly=True)
    location_id = fields.Many2one('stock.location', 'Location',
                                  related='move_id.location_id', readonly=True)
    partner_sale_id = fields.Many2one('res.partner', 'Sale Patner',
                                      readonly=True,
                                      related='sale_id.partner_id')
    shipping_sale_id = \
        fields.Many2one('res.partner', 'Sale Shipping Dir', readonly=True,
                        related='sale_id.partner_shipping_id')

    @api.multi
    def _get_model_progress(self):
        for task in self:
            progress = 0.0

            if task.model_reference:
                m = task.model_reference
                if m._name == 'sale.order.line' and m.product_uom_qty:
                    progress = m.qty_delivered / m.product_uom_qty
                # elif m._name == 'stock.move' and m.production_id and \
                #         m.production_id.quantity:
                #     progress = m.quantity_done / m.production_id.quantity
                elif m._name == 'stock.move' and m.state == 'done':
                    progress = 1
                elif m._name == 'stock.picking' and m.state == 'done':
                    progress = 1
                elif m._name == 'mrp.workorder' and m.qty_production:
                    progress = m.qty_produced / m.qty_production

            task.progress_model = progress * 100.0

    @api.multi
    def write(self, vals):
        updated_tasks = self
        ref_task = self[0]
        # Avoid errors by constraints
        if 'date_end' in vals:
            if ref_task.date_start > vals['date_end']:
                vals['date_start'] = vals['date_end']
        if 'date_start' in vals:
            if vals['date_start'] > ref_task.date_end:
                vals['date_start'] = ref_task.date_end

        # Update parent and child tasks with same date end
        if 'date_end' in vals or 'date_start' in vals:
            updated_tasks += self.mapped('parent_id')
            updated_tasks += self.search([('parent_id', 'in', self.ids)])
        res = super(ProjectTask, updated_tasks).write(vals)

        if 'date_end' in vals:
            # for task in self:
            # PROPAGATE DATE END TO DATE START SUCESSOR
            # except sale.order.line
            new_start_date = ref_task.date_end
            if ref_task.sucessor_ids and \
                    ref_task.sucessor_ids[0].task_id.model_reference and \
                    ref_task.sucessor_ids[0].task_id.\
                    model_reference._name != 'sale.order.line':
                # if task.sucessor_ids[0].task_id.date_end < new_start_date:
                #         new_start_date = task.sucessor_ids[0].\
                #             task_id.date_end
                self.mapped('sucessor_ids.task_id').\
                    write({'date_start': new_start_date})

            # UPDATE DATE IN THE LINKED TASK MODEL
            # But Skip when conevnient (from link predecessors)
            if ref_task._context.get('no_propagate', False):
                return

            # UPDATE STOCK PINKING MIN DATE
            if ref_task.model_reference and \
                    ref_task.model_reference._name == 'stock.picking' and \
                    ref_task.model_reference.min_date != ref_task.date_end:
                if ref_task.model_reference.state == 'done':
                    raise UserError(_('Can not set date to picking \
                                       because is done'))
                self.mapped('model_reference').\
                    with_context(do_not_propagate=True).\
                    write({'min_date': ref_task.date_end})

            # UPDATE STOCK MOVE DATE EXPECTED
            if ref_task.model_reference and \
                    ref_task.model_reference._name == 'stock.move' and \
                    ref_task.model_reference.date_expected != \
                    ref_task.date_end:
                if ref_task.model_reference.state == 'done':
                    raise UserError(_('Can not set date to move \
                                       because is done'))
                self.mapped('model_reference').\
                    with_context(do_not_propagate=True).\
                    write({'date_expected': ref_task.date_end})

            # UPDATE production date FINISHED DATE EXPECTED
            if ref_task.model_reference and \
                    ref_task.model_reference._name in ['mrp.production',
                                                       'mrp.workorder'] and \
                    ref_task.model_reference.date_planned_finished != \
                    ref_task.date_end:
                if ref_task.model_reference.state == 'done':
                    raise UserError(_('Can not set date to \
                                       production / workorder because \
                                       is done'))
                self.mapped('model_reference').write({
                    'date_planned_finished': ref_task.date_end
                })
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

    def do_sorting(self, subtask_project_id=None, project_id=None):
        """
        Slow Function, called allways in write by project native
        """
        pass


class ProjectTaskPresecessor(models.Model):
    """
    Called predecessors but represents links between successors and
    predecessors.
    """
    _inherit = 'project.task.predecessor'

    task_id = fields.Many2one(ondelete='cascade')
    parent_task_id = fields.Many2one(ondelete='cascade')
