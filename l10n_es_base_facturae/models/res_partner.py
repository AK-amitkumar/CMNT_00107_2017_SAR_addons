# -*- coding: utf-8 -*-

from odoo import models, fields
from e_invoice import REPORT_TEMPLATE, SIGN_STRATEGY, FILE_NAME_STRATEGY, PUSH_STRATEGY


class ResPartner(models.Model):
    _inherit = "res.partner"

    e_invoice_schema_id = fields.Many2one('e.invoice.schema', string="Invoice validation schema")
    e_invoice_sign_schema_id = fields.Many2one('e.invoice.schema', string="Invoice sign validation schema")
    e_invoice_template = fields.Selection(REPORT_TEMPLATE, string="Report creation template ")
    sign_strategy = fields.Selection(SIGN_STRATEGY, string="Sign strategy")
    file_name_strategy = fields.Selection(FILE_NAME_STRATEGY, string="File name strategy")
    push_strategy = fields.Selection(PUSH_STRATEGY, string="Push strategy")
