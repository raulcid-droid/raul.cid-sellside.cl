# -*- coding: utf-8 -*-
from odoo import models
import logging
import re

_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _message_post_after_hook(self, message, msg_vals):
        super(DiscussChannel, self)._message_post_after_hook(message, msg_vals)
        if message.author_id.id == self.env.ref('base.partner_root').id:
            return
        if self.name == 'Gemini Inventory Agent':
            body = message.body or ''
            clean_text = re.sub('<[^>]*>', '', body).strip()
            if clean_text:
                self._generate_response(clean_text)

    def _generate_response(self, prompt):
        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini_inventory.api_key')
        if not api_key:
            _logger.error("Gemini: API Key no configurada")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            products = self.env['product.product'].search([('type', '=', 'product')], limit=10)
            stock_info = "Stock actual:\n" + "\n".join([f"- {p.name}: {p.qty_available}" for p in products])
            contexto = f"Eres un asistente de inventario de Odoo. Contexto:\n{stock_info}\n\nPregunta: {prompt}"
            response = model.generate_content(contexto)
            if response and response.text:
                self.message_post(body=response.text)
        except Exception as e:
            _logger.error("Gemini Error: %s", str(e))
