# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
class SqlKardex():

    def get_stock_init_prod(self, obj):
        self._cr.execute("SELECT DISTINCT ON(l.product_id) a.id,a.name,a.stock_move_id, "
                         "l.product_id,a.date,l.create_date, a.amount_total,a.initial_balance_uni, "
                         "a.initial_cant_uni,s.location_dest_id,s.location_id, "
                         "s.picking_id,s.product_uom_qty,s.inventory_id,s.origin,s.reference "
                         "FROM account_move AS a INNER JOIN account_move_line AS l "
                         "ON a.id=l.move_id INNER JOIN stock_move s ON a.stock_move_id = s.id "
                         "WHERE a.DATE <=%s AND a.initial_balance_uni >0 "
                         "AND a.journal_id=%s AND a.STATE='posted' AND a.company_id =%s "
                         "AND l.product_id NOT IN (SELECT product_id FROM (SELECT DISTINCT (l.move_id),a.id,a.name,a.stock_move_id, "
                         "l.product_id,a.date,l.create_date, a.amount_total,a.initial_balance_uni, "
                         "a.initial_cant_uni,s.location_dest_id,s.location_id, "
                         "s.picking_id,s.product_uom_qty,s.inventory_id "
                         "FROM account_move AS a INNER JOIN account_move_line AS l "
                         "ON a.id=l.move_id INNER JOIN stock_move s ON a.stock_move_id = s.id "
                         "WHERE a.DATE >= %s AND a.DATE <=%s "
                         "AND a.journal_id=%s AND a.STATE='posted' AND a.company_id =%s "
                         "AND l.product_id IS NOT NULL AND a.stock_move_id IS NOT NULL "
                         "ORDER BY l.product_id,a.id ASC,l.create_date ASC)account_move_line)"
                         "AND a.stock_move_id IS NOT NULL "
                         "ORDER BY l.product_id,a.id DESC ,l.create_date DESC ;",
                         (obj['date_initial'], obj['journal'], obj['company'], obj['date_from'], obj['date_to'],
                          obj['journal'], obj['company']))
        mov = self.env.cr.dictfetchall()
        return mov

    def get_balance_start_physical(self, obj):
        self._cr.execute("SELECT DISTINCT (l.move_id),"
                         "a.id,a.name,a.stock_move_id,l.product_id,a.date,l.create_date, a.amount_total,a.initial_balance_uni,a.initial_cant_uni "
                         "FROM account_move AS a INNER JOIN account_move_line as l ON a.id=l.move_id "
                         "WHERE a.date <= %s AND l.product_id =%s "
                         "AND a.journal_id=%s AND a.STATE='posted' "
                         "AND a.company_id =%s  "
                         "ORDER BY a.id DESC, l.create_date DESC LIMIT 1;",
                         (obj["date_initial"], obj['product_id'], obj["journal_id"], obj["company_id"]))

        saldo_inicial = self.env.cr.dictfetchall()
        return saldo_inicial

    def get_unidades(self, obj):
        self._cr.execute("SELECT DISTINCT (l.move_id),a.id,a.name,a.stock_move_id, "
                         "l.product_id,a.date,l.create_date, a.amount_total,a.initial_balance_uni, "
                         "a.initial_cant_uni,s.location_dest_id,s.location_id, "
                         "s.picking_id,s.product_uom_qty,s.inventory_id, s.origin, s.reference "
                         "FROM account_move AS a INNER JOIN account_move_line AS l "
                         "ON a.id=l.move_id INNER JOIN stock_move s ON a.stock_move_id = s.id "
                         "WHERE a.DATE >= %s AND a.DATE <=%s "
                         "AND a.journal_id=%s AND a.STATE='posted' AND a.company_id =%s "
                         "AND l.product_id IS NOT NULL AND a.stock_move_id IS NOT NULL "
                         "ORDER BY l.product_id,a.id ASC,l.create_date ASC;",
                         (obj['date_from'], obj['date_to'], obj['journal'], obj['company']))
        mov = self.env.cr.dictfetchall()
        return mov

    def get_picking_doc(self, picking_id):
        type_doc = '00'
        serie_doc = '0'
        number_doc = '0'
        name = ''
        stock_picking = self.env['stock.picking']
        referral_guide = stock_picking.sudo().browse(picking_id)
        # Vamos a tener a cambiar aqui
        if 'l10n_latam_document_type_id' in referral_guide and referral_guide.l10n_latam_document_type_id.id:
            type_doc = referral_guide.l10n_latam_document_type_id.code
            serie_doc = referral_guide.serie
            number_doc = referral_guide.correlative
            name = referral_guide.name
            return {'type_doc': type_doc, 'serie_doc': serie_doc, 'number_doc': number_doc, 'name': name}
        else:
            type_doc = ""
            serie_doc = ""
            number_doc = ""
            name = ""
            # # TODO Verificar la condicion de referral guide, opcional
            # if 'referral_guide_count' in referral_guide and referral_guide.referral_guide_count > 0:
            #     val = referral_guide.mapped('referral_guides').filtered(
            #         lambda r: r.state == 'done').sorted(key=lambda r: r.create_date, reverse=True)
            #     if len(val) > 0:
            #         type_doc = val[0].sunat_catalog01.code
            #         serie_doc = val[0].sunat_serie_documento.code
            #         number_doc = val[0].sunat_correlativo_documento
            #         name = val[0].name
            #     return {'type_doc': type_doc, 'serie_doc': serie_doc, 'number_doc': number_doc, 'name': name}
            # # TODO El campo sale_id no existe en la v 14
            # elif referral_guide.sale_id:
            #     if len(referral_guide.sale_id.invoice_ids) > 0:
            #         val = referral_guide.sale_id.mapped('invoice_ids').filtered(
            #             lambda r: r.state in ('posted')).sorted(key=lambda r: r.create_date,
            #                                                     reverse=True)
            #         if len(val) > 0:
            #             type_doc = val[0].type_document.code
            #             serie_doc = val[0].serie.code
            #             number_doc = val[0].correlative
            #             name = val[0].name
            #         return {'type_doc': type_doc, 'serie_doc': serie_doc, 'number_doc': number_doc, 'name': name}
            # # TODO El campo purchase_id no existe en la v 14
            # elif referral_guide.purchase_id:
            #     if len(referral_guide.purchase_id.invoice_ids) > 0:
            #         val = referral_guide.purchase_id.mapped('invoice_ids').filtered(
            #             lambda r: r.state in ('posted')).sorted(key=lambda r: r.create_date,
            #                                                     reverse=True)
            #         if len(val) > 0:
            #             type_doc = val[0].type_document.code
            #             serie_doc = val[0].serie_code
            #             number_doc = val[0].correlative
            #             name = val[0].name
            #     return {'type_doc': type_doc, 'serie_doc': serie_doc, 'number_doc': number_doc, 'name': name}
            # # TODO revisar dependencia de modelo, necesitaria a pos.order no siempre se instala esa app.
            # elif referral_guide.origin:
            #     pos_order = self.env['pos.order'].sudo().search([('name', '=', referral_guide.origin)], limit=1)
            #     return {'type_doc': pos_order.serie.type_document.code or '00',
            #             'serie_doc': pos_order.serie.code or '0',
            #             'number_doc': pos_order.correlative or '0', 'name': pos_order.name or ''}
        return {'type_doc': type_doc, 'serie_doc': serie_doc, 'number_doc': number_doc, 'name': name}

    def get_type_transaction(self, code):
        type_transaction = self.env['pragmatic.type.operation.table.12'].sudo().search([('code', '=', code)], limit=1)
        return type_transaction.code + '-' + type_transaction.name

    def update_acc_mov_physical(self, obj):
        self._cr.execute("UPDATE account_move SET initial_balance_uni =%s,initial_cant_uni=%s "
                         "WHERE id = %s",
                         (obj['initial_balance_uni'], obj['initial_cant_uni'], obj['account_move']))

    # REPORT KARDEX FOR VALUED
    def get_valorizado(self, obj):
        query_data = "SELECT * FROM \
                     ((SELECT DISTINCT (l.move_id), a.id,a.name,a.stock_move_id,l.product_id,a.date,l.create_date, \
                     a.amount_total,a.initial_balance,a.initial_cant,a.initial_cost \
                     FROM account_move AS a INNER JOIN account_move_line AS l ON a.id=l.move_id \
                     WHERE a.DATE >= '" + str(obj['date_from']) + "' AND a.DATE <='" + str(obj['date_to']) + "' \
                     AND a.journal_id='" + str(obj['journal']) + "' AND a.STATE='posted'  \
                     AND a.company_id ='" + str(obj['company']) + "' \
                     AND l.product_id IS NOT NULL AND a.stock_move_id IS NOT NULL \
                     ORDER BY l.product_id, a.id ASC, l.create_date ASC) \
                     UNION ALL \
                     (SELECT DISTINCT (l.move_id), a.id,a.name,a.stock_move_id,l.product_id,a.date,l.create_date, \
                     a.amount_total,a.initial_balance,a.initial_cant,a.initial_cost \
                     FROM account_move AS a INNER JOIN account_move_line AS l ON a.id=l.move_id \
                     WHERE a.DATE >='" + str(obj['date_from']) + "' AND a.DATE <='" + str(obj['date_to']) + "' \
                     AND a.journal_id='" + str(obj['journal']) + "' AND a.STATE='posted'  \
                     AND a.company_id ='" + str(obj['company']) + "' \
                     AND l.product_id IS NOT NULL AND l.name LIKE '%cambio costo de%' \
                     ORDER BY l.product_id, a.id ASC, l.create_date ASC) )account_move_line \
                     ORDER BY product_id, id ASC, create_date ASC"
        # query_param = (obj['date_from'], obj['date_to'], obj['journal'], obj['company'])
        self._cr.execute(query_data)
        # (obj['date_from'], obj['date_to']) obj['journal'], obj['company']
        mov = self.env.cr.dictfetchall()
        return mov

    def get_average_cost(self, obj):
        query_data = "SELECT * FROM \
                     ((SELECT DISTINCT (l.move_id), a.id,a.name,a.stock_move_id,l.product_id,a.date,l.create_date, \
                     a.amount_total,a.initial_balance,a.initial_cant,a.initial_cost \
                     FROM account_move AS a INNER JOIN account_move_line AS l ON a.id=l.move_id \
                     WHERE a.DATE >= '" + str(obj['date_from']) + "' AND a.DATE <='" + str(obj['date_to']) + "' \
                     AND a.journal_id='" + str(obj['journal']) + "' AND a.STATE='posted'  \
                     AND a.company_id ='" + str(obj['company']) + "' AND l.product_id='" + str(obj['product_id']) + "' \
                     AND l.product_id IS NOT NULL AND a.stock_move_id IS NOT NULL \
                     ORDER BY l.product_id, a.id ASC, l.create_date ASC) \
                     UNION ALL \
                     (SELECT DISTINCT (l.move_id), a.id,a.name,a.stock_move_id,l.product_id,a.date,l.create_date, \
                     a.amount_total,a.initial_balance,a.initial_cant,a.initial_cost \
                     FROM account_move AS a INNER JOIN account_move_line AS l ON a.id=l.move_id \
                     WHERE a.DATE >='" + str(obj['date_from']) + "' AND a.DATE <='" + str(obj['date_to']) + "' \
                     AND a.journal_id='" + str(obj['journal']) + "' AND a.STATE='posted'  \
                     AND a.company_id ='" + str(obj['company']) + "' AND l.product_id='" + str(obj['product_id']) + "' \
                     AND l.product_id IS NOT NULL AND l.name LIKE '%cambio costo de%' \
                     ORDER BY l.product_id, a.id ASC, l.create_date ASC) )account_move_line \
                     ORDER BY product_id, id ASC, create_date ASC"
        self._cr.execute(query_data)
        mov = self.env.cr.dictfetchall()
        return mov

    def get_stock_move(self, obj):
        self._cr.execute("SELECT st.id as id_stock,st.date as stock_date,st.reference, "
                         "st.product_id AS product_stock,st.location_dest_id, "
                         "st.location_id,st.picking_id, "
                         "st.origin,st.product_uom_qty,st.inventory_id, st.price_unit "
                         "FROM stock_move AS st WHERE st.id = '" + str(obj['stock_move']) + "'")
        stock_move = self.env.cr.dictfetchone()
        return stock_move

    def get_balance_start_valued(self, obj):
        self._cr.execute("SELECT DISTINCT (l.move_id),"
                         "a.id,a.name,a.stock_move_id,l.product_id,a.date,l.create_date, a.amount_total,a.initial_balance,a.initial_cant,a.initial_cost "
                         "FROM account_move AS a INNER JOIN account_move_line as l ON a.id=l.move_id "
                         "WHERE a.date <= %s AND l.product_id =%s "
                         "AND a.journal_id=%s AND a.STATE='posted' "
                         "AND a.company_id =%s  "
                         "ORDER BY a.id DESC, l.create_date DESC LIMIT 1;",
                         (obj["date_initial"], obj['product_id'], obj["journal_id"], obj["company_id"]))

        saldo_inicial = self.env.cr.dictfetchall()
        return saldo_inicial

    def update_acc_mov_valued(self, obj):
        self._cr.execute("UPDATE account_move SET initial_balance =%s,initial_cant=%s,initial_cost=%s "
                         "WHERE id = %s",
                         (obj['initial_balance'], obj['initial_cant'], obj['initial_cost'], obj['account_move']))

    def get_account_type(self):
        self._cr.execute("SELECT act.type FROM account_account_type AS act "
                         "WHERE act.type = 'other' AND act.name LIKE '%Current Assets%'")
        return self.env.cr.fetchone()

    def get_acc_mov_line(self, obj):
        self._cr.execute("SELECT ml.debit,ml.credit,ml.balance,ml.quantity FROM account_move_line AS ml "
                         "WHERE ml.move_id=%s AND ml.account_internal_type=%s", (obj['move_id'], obj['type']))
        return self.env.cr.dictfetchone()

    def get_update_cost(self, obj):
        self._cr.execute("SELECT * FROM stock_valuation_layer la \
                         WHERE la.product_id = %s AND la.account_move_id=%s;", (obj['product_id'], obj['move_id']))
        return self.env.cr.dictfetchone()

    def get_stock_init_prod_valued(self, obj):
        self._cr.execute("SELECT DISTINCT ON(l.product_id) \
                        a.id,a.name,a.stock_move_id,l.move_id,l.product_id,a.date,\
                        l.create_date, a.amount_total,a.initial_balance,\
                        a.initial_cant,a.initial_cost\
                        FROM account_move_line AS l\
                        INNER JOIN account_move AS a ON l.move_id=a.id\
                        WHERE a.date <= '" + str(obj['date_initial']) + "' \
                        AND a.journal_id='" + str(obj['journal']) + "' \
                        AND a.STATE='posted' AND a.company_id ='" + str(obj['company']) + "' \
                        AND a.initial_balance > 0 AND l.product_id \
                        NOT IN ( SELECT product_id FROM ((\
                        SELECT DISTINCT (l.move_id), a.id,a.name,a.stock_move_id,l.product_id,\
                        a.date,l.create_date, a.amount_total,a.initial_balance,\
                        a.initial_cant,a.initial_cost\
                        FROM account_move AS a\
                        INNER JOIN account_move_line AS l ON a.id=l.move_id\
                        WHERE a.date >= '" + str(obj['date_from']) + "' \
                        AND a.date <='" + str(obj['date_to']) + "' \
                        AND a.journal_id='" + str(obj['journal']) + "' \
                        AND a.STATE='posted' AND a.company_id ='" + str(obj['company']) + "' \
                        AND l.product_id IS NOT NULL AND a.stock_move_id IS NOT NULL\
                        ORDER BY l.product_id,a.id ASC,l.create_date ASC) UNION ALL \
                        (SELECT DISTINCT (l.move_id), a.id,a.name,a.stock_move_id,l.product_id,\
                        a.date,l.create_date, a.amount_total,a.initial_balance,\
                        a.initial_cant,a.initial_cost\
                        FROM account_move AS a\
                        INNER JOIN account_move_line AS l ON a.id=l.move_id\
                        WHERE a.date >='" + str(obj['date_from']) + "' \
                        AND a.date <='" + str(obj['date_to']) + "' \
                        AND a.journal_id='" + str(obj['journal']) + "' \
                        AND a.STATE='posted' AND a.company_id ='" + str(obj['company']) + "' \
                        AND l.product_id IS NOT NULL AND l.name LIKE '%cambio costo de%'\
                        ORDER BY l.product_id,a.id ASC,l.create_date ASC))account_move_line\
                        ORDER BY product_id,id ASC, create_date ASC)\
                        ORDER BY l.product_id,l.move_id DESC,l.create_date DESC;")
        saldo_inicial = self.env.cr.dictfetchall()
        return saldo_inicial
