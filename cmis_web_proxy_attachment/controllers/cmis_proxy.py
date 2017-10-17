# -*- coding: utf-8 -*-
import json
from odoo.addons.cmis_web_proxy.controllers.cmis import CmisProxy

def _forward_post(self, url_path, proxy_info, model_inst, params):
    result = _base_forward_post(self, url_path, proxy_info, model_inst, params)
    if params['cmisaction'] == 'createDocument' and result.status_code == 200:
        response = json.loads(result.data)
        model_inst.env['ir.attachment'].create({
            'document_id': response['succinctProperties']['cmis:versionSeriesId'],
            'res_model': model_inst._name,
            'res_id': model_inst.id,
            'name': response['succinctProperties']['cmis:name'],
            'type': 'cmis'
        })
    return result

_base_forward_post = CmisProxy._forward_post
CmisProxy._forward_post = _forward_post
