# -*- coding: utf-8 -*-

import cmis_field_4_all
from odoo.addons.cmis_field import fields


def post_init_check(cr, registry):
    models = registry.models
    for key, model in models.iteritems():
        name = "cmis_folder"
        if name not in model._fields:
            field = fields.CmisFolder()
            model._fields[name] = field
            setattr(model, name, field)
            field.setup_base(model, name)
    registry.init_models(cr, models.keys(), {})
    return True
