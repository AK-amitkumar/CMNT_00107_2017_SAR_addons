# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.depends("e_invoice_id")
    def _compute_has_e_invoice(self):
        for e_inv in self:
            e_inv.has_e_invoice = (e_inv.e_invoice_id.id != False)

    e_invoice_id = fields.One2many('e.invoice', 'invoice_id', ondelete='cascade', string="E-Invoice")
    has_e_invoice = fields.Boolean(_("Has E-Invoice"), compute=_compute_has_e_invoice)

    @api.multi
    def action_e_invoice_create(self):
        e_inv_obj = self.env['e.invoice']
        for invoice in self:
            if invoice.e_invoice_id.id is False:
                vals = {
                    "invoice_id": invoice.id,
                    "report_template": invoice.partner_id.e_invoice_template,
                    "sign_strategy": invoice.partner_id.sign_strategy,
                    "file_name_strategy": invoice.partner_id.file_name_strategy,
                    "push_strategy": invoice.partner_id.push_strategy,
                    "schema_id": invoice.partner_id.e_invoice_schema_id.id,
                    "sign_schema_id": invoice.partner_id.e_invoice_sign_schema_id.id
                }
                e_invoice = e_inv_obj.create(vals)
                e_invoice.process()

    def open_e_invoice_view(self):
        [action] = self.env.ref('l10n_es_base_facturae.e_invoice_act_window').read()
        action['domain'] = [('invoice_id', 'in', self.ids)]
        return action
