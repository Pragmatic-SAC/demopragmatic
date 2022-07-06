import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class XLSXReportController(http.Controller):

    @http.route('/xlsx_txt_reports', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx_txt(self, model, options, output_format, token, financial_id=None, **kw):
        uid = request.session.uid
        options = json.loads(options)
        cids = request.httprequest.cookies.get('cids', str(request.env.user.company_id.id))
        allowed_company_ids = [int(cid) for cid in cids.split(',')]
        report_obj = request.env[model].with_user(uid).with_context(allowed_company_ids=allowed_company_ids)
        try:
            if output_format == 'xlsx':
                report_name = report_obj.get_report_filename(options)
                response = request.make_response(
                    None,
                    headers=[('Content-Type', 'application/vnd.ms-excel'),
                             ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                             ]
                )
                report_obj.get_xlsx(options, response)
            if output_format == 'txt':
                content = report_obj.get_txt(options)
                if len(content) > 0:
                    options['count_report'] = 1
                else:
                    options['count_report'] = 0
                report_name = report_obj.get_report_filename(options)
                response = request.make_response(
                    content,
                    headers=[
                        ('Content-Type', 'text/plain'),
                        ('Content-Disposition', content_disposition(report_name + '.txt')),
                        ('Content-Length', len(content))
                    ]
                )
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
