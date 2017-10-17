/*---------------------------------------------------------
 + * Odoo cmis_web_proxy_attachment
 + * Author Victor Rojo Carballo 2016
 + *---------------------------------------------------------
 +*/

 odoo.define('cmis_web_proxy_attachment.form_widgets', function( require) {
"use strict";

var core = require('web.core');
var form_widgets = require('cmis_web.form_widgets');
var Model = require('web.Model');

var _t = core._t;

form_widgets.FieldCmisFolder.include({

    get_datatable_config: function(){
        var config = this._super.apply(this, arguments);
        config.columns = config.columns.slice(0, config.columns.length - 1).concat([
            {
                data: 'location',
                width:'60px',
                visible: false,
            },
            {
                data: 'due_date',
                width:'60px',
                visible: false,
            },
            {
                data: 'assignment_to',
                width:'60px',
                visible: false,
            }], config.columns.slice(config.columns.length - 1));
        return config;
    },

    render_value: function() {
        this._super.apply(this, arguments);
        var value = this.get('value');
        if (!value && !this.view.datarecord._is_creating_root_folder){
            this.view.datarecord._is_creating_root_folder = true;
            this.on_click_create_root();
            this.$el.find('button.cmis-create-root').addClass('hidden');
        }
    },


    register_content_events: function(){
        this._super.apply(this, arguments);
        var self = this;
        this.$el.find('tbody > tr').on('dblclick', function(e) {
             var row = self._get_event_row(e);
             self.on_double_click_preview2(row);
         });
    },

    on_double_click_preview: function(row){
        if(row.data().baseTypeId == "cmis:document") {
            var dialog = new CmisUpdateAttachmentInfoDialog(this, row);
            dialog.open();
        }
    },
    on_double_click_preview2: function(row){
        if(row.data().baseTypeId == "cmis:document") {
            self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "ir.attachment",
                res_id: row.data().ir_attachment_id,
                views: [[false, 'form']],
                target: 'new',
                context: {}
            }, { on_close: function(){
                                self.datatable.ajax.reload();
                            }
           });
        }
    },

    datatable_query_cmis_data: function(data, callback, settings) {
        this._super(data, this.add_attachment_data.bind(this, callback), settings);
    },

    add_attachment_data: function(callback, data){
        if(data.data && data.data.length > 0 ) {
            var model = new Model("ir.attachment");
            var doc_ids = _.map(data.data, function(el) { return el.versionSeriesId })
            model.query(['document_id', 'location', 'due_date', 'assignment_to'])
                 .filter([['document_id', 'in', doc_ids]])
                 .all().then(function (attachments) {
                    _.each(data.data, function(el){
                        var attachment = _.find(attachments, function(att){ return el.versionSeriesId == att.document_id})
                        if ( attachment ) {
                            el.location = attachment.location ? attachment.location : null;
                            el.due_date = attachment.due_date ? attachment.due_date : null;
                            el.assignment_to = attachment.assignment_to ? attachment.assignment_to : null;
                            el.ir_attachment_id = attachment.id;
                        } else {
                            el.location = el.due_date = el.assignment_to = null;
                        }
                    });
                    callback(data);
            });
        } else {
            callback(data);
        }
    }
});
});
