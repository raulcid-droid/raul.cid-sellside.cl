# -*- coding: utf-8 -*-
import logging
from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from bs4 import BeautifulSoup
except ImportError:
    genai = None
    BeautifulSoup = None


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    @api.model
    def _message_post_after_hook(self, message, msg_vals):
        result = super()._message_post_after_hook(message, msg_vals)
        
        if self.name == 'Gemini Agente de inventario' and message.body:
            text = self._extract_text(message.body)
            # if text and not message.author_id.share:
                try:
                    response = self._generate_response(text)
                    self.message_post(body=response, message_type='comment')
                except Exception as e:
                    _logger.error(f"Error: {e}")
        return result

    def _extract_text(self, html):
        if not html or not BeautifulSoup:
            return html or ""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(strip=True)

    def _generate_response(self, message):
        if not genai:
            raise UserError("Instale google-generativeai")
        
        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini_inventory.api_key')
        if not api_key:
            raise UserError("Configure API Key")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        context = self._get_inventory(message)
        prompt = f"Asistente de inventario.\n\nINVENTARIO:\n{context}\n\nPREGUNTA: {message}"
        
        return model.generate_content(prompt).text

    def _get_inventory(self, message):
        words = message.lower().split()
        domain = []
        for i, w in enumerate(words):
            if i > 0:
                domain.append('|')
            domain.append(('name', 'ilike', w))
        
        products = self.env['product.product'].search(domain, limit=5)
        if products:
            return "\n".join([f"{p.name}: {p.qty_available} unidades" for p in products])
        return "Sin productos"
