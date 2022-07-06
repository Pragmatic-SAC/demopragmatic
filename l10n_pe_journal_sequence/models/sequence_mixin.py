from odoo import api, fields, models, _


class SequenceMixin(models.AbstractModel):
    _inherit = 'sequence.mixin'

    def _constrains_date_sequence(self):
        return
