# -*- coding: utf-8 -*-
import logging
from odoo import api
from odoo.models import BaseModel
from odoo.addons.cmis_field import fields

from lxml import etree

EXCLUDED_MODELS = ["ir.attachment"]

_logger = logging.getLogger(__name__)

@api.model
def _add_magic_fields(self):
    _add_magic_fields.origin(self)
    if "cmis_folder" not in self._fields:
        self._add_field("cmis_folder", fields.CmisFolder())


@api.model
def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    result = fields_view_get.origin(self, view_id, view_type, toolbar, submenu)
    if result['type'] == 'form' and (self._transient is None or self._transient is False) and result['model'] not in EXCLUDED_MODELS:
        arch = etree.fromstring(result['arch'])
        page = etree.fromstring('<page string="Documents" groups="base.group_user"><field name="cmis_folder"/></page>')
        if arch.find('./sheet/notebook') is not None:
            node = arch.find('./sheet/notebook')
        elif arch.find('./sheet') is not None:
            node = etree.fromstring('<notebook></notebook>')
            arch.find('./sheet').append(node)
        else:
            node = etree.fromstring('<notebook></notebook>')
            arch.append(node)

        node.append(page)
        result['arch'] = etree.tostring(arch, encoding='utf-8')
        result['fields'].update(self.fields_get("cmis_folder"))
    return result


def create_model_folders(self):
    if self._name not in EXCLUDED_MODELS:
        backends = self.env['cmis.backend'].search([])
        for backend in backends:
            path = '/'.join([backend.initial_directory_write,
                             self._name.replace('.', '_')])
            backend.get_folder_by_path(
                path, create_if_not_found=True)

@api.model
def _setup_complete(self):
    _setup_complete.origin(self)
    try:
        create_model_folders(self)
    except Exception as inst:
        _logger.error(inst)

# CMNT fail because not loaded wel cmis_folder, sometimes fail when new install
# sometimes when installation of other module. We need to comment fot that.
# other error is, current transition is aborted
BaseModel._patch_method("_add_magic_fields", _add_magic_fields)
BaseModel._patch_method("fields_view_get", fields_view_get)

# Este aveces hace que las cosas fallen (o hacía)
BaseModel._patch_method("_setup_complete", _setup_complete)
