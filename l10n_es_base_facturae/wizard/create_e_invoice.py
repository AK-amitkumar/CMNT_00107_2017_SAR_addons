# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ../models/e_invoice import REPORT_TEMPLATE, SIGN_STRATEGY, FILE_NAME_STRATEGY, PUSH_STRATEGY


class CreateEInvoice(models.TransientModel):
    _name = "create.e.invoice"

    schema = fields.Many2many('e.invoice.schema', 'create_e_invoice_schema_rel', 'create_e_invoice_id',
                              'e_invoice_schema_id', string="Invoice validation schemas")
    sign_schema = fields.Many2many('e.invoice.schema', 'create_e_invoice_sign_schema_rel', 'create_e_invoice_id',
                                   'e_invoice_schema_id', string="Invoice sign validation schemas")
    report_template = fields.Selection(REPORT_TEMPLATE, string="Report creation template ")
    sign_strategy = fields.Selection(SIGN_STRATEGY, string="Sign strategy")
    file_name_strategy = fields.Selection(FILE_NAME_STRATEGY, string="File name strategy")
    push_strategy = fields.Selection(PUSH_STRATEGY, string="Push strategy")

    def create_e_invoice(self):
        e_inv_obj = self.env['e.invoice']
        invoices = self.env['account.invoice'].browse(self._context.get('active_ids', []))
        for invoice in invoices:
            if invoice.e_invoice_id.id is False:
                vals = {
                    "invoice_id": invoice.id,
                    "report_template": self.report_template,
                    "sign_strategy": self.sign_strategy,
                    "file_name_strategy": self.file_name_strategy,
                    "push_strategy": self.push_strategy
                }
                if len(invoice.partner_id.e_invoice_schema):
                    vals["schema"] = [(4, invoice.partner_id.e_invoice_schema.ids)]
                if len(invoice.partner_id.e_invoice_sign_schema):
                    vals["sign_schema"] = [(4, invoice.partner_id.e_invoice_sign_schema.ids)]
                e_invoice = e_inv_obj.create(vals)
                e_invoice.process()
        return {'type': 'ir.actions.act_window_close'}


