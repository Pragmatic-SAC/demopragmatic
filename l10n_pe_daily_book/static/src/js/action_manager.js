// odoo.define('l10n_pe_purchase_sale_ledgers.ActionManager', function (require) {
//
//     "use strict";
//
//     /**
//
//      * The purpose of this file is to add the actions of type
//
//      * 'ir_actions_xlsx_download' to the ActionManager.
//
//      */
//
//     var ActionManager = require('web.ActionManager');
//     var framework = require('web.framework');
//     var session = require('web.session');
//
//
//     ActionManager.include({
//
//         _executeAccountReportDownloadAction: function (action) {
//
//             var self = this;
//             framework.blockUI();
//
//             return new Promise(function (resolve, reject) {
//                 session.get_file({
//                     url: '/xlsx_txt_reports',
//                     data: action.data,
//                     success: resolve,
//                     error: (error) => {
//                         self.call('crash_manager', 'rpc_error', error);
//                         reject();
//                     },
//                     complete: framework.unblockUI,
//                 });
//             });
//
//         },
//
//         _handleAction: function (action, options) {
//             console.log('action',action)
//             console.log('options',options)
//             if (action.type === 'ir_actions_xlsx_txt_download') {
//                 return this._executeAccountReportDownloadAction(action, options);
//             }
//             return this._super.apply(this, arguments);
//         },
//
//     });
//
// });

odoo.define('l10n_pe_daily_book.ActionManagerExcelTxt', function (require) {
    "use strict";

    /**
     * The purpose of this file is to add the support of Odoo actions of type
     * 'ir_actions_account_report_download' to the ActionManager.
     */

    var ActionManager = require('web.ActionManager');
    var framework = require('web.framework');
    var session = require('web.session');

    ActionManager.include({
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Executes actions of type 'ir_actions_account_report_download'.
         *
         * @private
         * @param {Object} action the description of the action to execute
         * @returns {Promise} resolved when the report has been downloaded ;
         *   rejected if an error occurred during the report generation
         */
        _executeAccountDailyReportDownloadAction: function (action) {
            var self = this;
            framework.blockUI();
            return new Promise(function (resolve, reject) {
                session.get_file({
                    url: '/xlsx_txt_daily_book',
                    data: action.data,
                    success: resolve,
                    error: (error) => {
                        self.call('crash_manager', 'rpc_error', error);
                        reject();
                    },
                    complete: framework.unblockUI,
                });
            });
        },
        /**
         * Overrides to handle the 'ir_actions_account_report_download' actions.
         *
         * @override
         * @private
         */
        _handleAction: function (action, options) {
            if (action.type === 'ir_actions_xlsx_txt_download') {
                return this._executeAccountDailyReportDownloadAction(action, options);
            }
            return this._super.apply(this, arguments);
        },
    });

});
