# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import re

_logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _message_post_after_hook(self, message, msg_vals):
        super(DiscussChannel, self)._message_post_after_hook(message, msg_vals)
        if self.name == 'Gemini Agente de inventario':
            body = message.body or ''
            text = re.sub('<[^>]*>', '', body).strip()
            if text:
                self._generate_response(text)

    def _generate_response(self, prompt):
        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini_inventory.api_key')
        if not api_key or not genai:
            return
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            products = self.env['product.product'].search([('type', '=', 'product')], limit=10)
            stock_info = "Stock:\n" + "\n".join([f"- {p.name}: {p.qty_available}" for p in products])
            response = model.generate_content(f"{stock_info}\n\nPregunta: {prompt}")
            if response and response.text:
                self.message_post(body=response.text)
        except Exception as e:
            _logger.error("Error: %s", str(e))
