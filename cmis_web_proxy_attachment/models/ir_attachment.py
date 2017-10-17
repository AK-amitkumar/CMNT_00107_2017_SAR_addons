# -*- coding: utf-8 -*-

import logging
from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    due_date = fields.Date(string='Due Date')
    location = fields.Char(string='Location')
    assignment_to = fields.Char(string='Assignment To')
    document_id = fields.Char(string='Document ID')
    type = fields.Selection(selection_add=[('cmis', 'CMIS Document')])
