# -*- coding: utf-8 -*-
import logging
import codecs
from lxml import etree

from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError


REPORT_TEMPLATE = [("l10n_es_base_facturae.report_facturae", "Factura-e")]
SIGN_STRATEGY = [("none", "None")]
FILE_NAME_STRATEGY = [("none", "None")]
PUSH_STRATEGY = [("none", "None")]

_logger = logging.getLogger(__name__)


class EInvoice(models.Model):
    _name = "e.invoice"
    _inherit = ['mail.thread']

    @staticmethod
    def _validate_xml_schemas(schemas, xml_string):
        xml = bytes(bytearray(xml_string, encoding='UTF-8'))
        for schema in schemas:
            xml_schema = etree.XMLSchema(etree.parse(tools.file_open(schema.file_path)))
            try:
                xml_schema.assertValid(etree.XML(xml))
            except Exception, e:
                _logger.warning("The XML file is invalid against the XML Schema Definition")
                _logger.warning(schema.name)
                _logger.warning(e)
                raise UserError(
                    _("The generated XML file is not valid against the XML Schema Definition : %s") % unicode(e))
        return True

    @api.depends('e_invoice_data')
    def _compute_datas(self):
        for e_inv in self:
            e_inv.e_invoice_binary = codecs.encode(e_inv.e_invoice_data.encode('utf-8'), 'base64')

    e_invoice_data = fields.Char('E-Invoice file', readonly=True)
    e_invoice_binary = fields.Binary(string='File Binary', compute='_compute_datas')
    e_invoice_file_name = fields.Char("File name")
    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference',
                                 ondelete='cascade', index=True)
    schema_id = fields.Many2one('e.invoice.schema', string="Invoice validation schema")
    sign_schema_id = fields.Many2one('e.invoice.schema', string="Invoice sign validation schema")
    report_template = fields.Selection(REPORT_TEMPLATE, string="Report creation template ")
    sign_strategy = fields.Selection(SIGN_STRATEGY, string="Sign strategy")
    file_name_strategy = fields.Selection(FILE_NAME_STRATEGY, string="File name strategy")
    push_strategy = fields.Selection(PUSH_STRATEGY, string="Push strategy")
    response_data = fields.Char('Response', readonly=True)
    state = fields.Selection([
        ('unsigned', 'Unsigned'),
        ('signed', 'Signed'),
        ('sent', 'Sent'),
        ('done', 'Locked'),
        ('error', 'Error'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='unsigned')

    @api.multi
    def name_get(self):
        result = []
        for e_inv in self:
            result.append((e_inv.id, e_inv.invoice_id.number))
        return result

    def action_e_invoice_sign(self):
        self._sign_invoice()
        self._validate_sign_schemas()

    def action_e_invoice_push(self):
        self._push_invoice()

    def action_e_invoice_download(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=e.invoice&id=' + str(self.id) +
                   '&field=e_invoice_binary&filename_field=e_invoice_file_name&download=true',
            'target': 'self',
        }

    def _set_file_name(self):
        if self.file_name_strategy == 'none':
            self.e_invoice_file_name = (self.invoice_id.number + '.xml').replace('/', '-')
        else:
            raise UserError(_('File name strategy %s not implemented.') % (self.file_name_strategy,))

    def _sign_invoice(self):
        if self.sign_strategy == 'none':
            pass
        else:
            raise UserError(_('Sign strategy %s not implemented.') % (self.sign_strategy,))

    def _push_invoice(self):
        if self.push_strategy == 'none':
            pass
        else:
            raise UserError(_('Push strategy %s not implemented.') % (self.push_strategy,))

    def _validate_invoice_schemas(self):
        return self._validate_xml_schemas(self.schema_id, self.e_invoice_data)

    def _validate_sign_schemas(self):
        return self._validate_xml_schemas(self.sign_schema_id, self.e_invoice_data)

    def process(self):
        report = self.env.ref(self.report_template)
        xml = self.env['report'].get_html(self.invoice_id.ids, report.report_name)
        xml = etree.fromstring(xml, etree.XMLParser(remove_blank_text=True, strip_cdata=False))
        self.e_invoice_data = etree.tostring(xml, pretty_print=True, encoding="UTF-8", xml_declaration=True)
        self._validate_invoice_schemas()
        self._set_file_name()
        self._sign_invoice()
        self._validate_sign_schemas()
        self._push_invoice()


class EInvoiceSchema(models.Model):
    _name = "e.invoice.schema"

    name = fields.Char(string='Schema Name', required=True)
    file_path = fields.Char(string='Schema File Path ', required=True)
