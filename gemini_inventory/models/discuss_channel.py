# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import re

_logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    _logger.warning("Libreria google-generativeai no encontrada")
    genai = None

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _message_post_after_hook(self, message, msg_vals):
        super(DiscussChannel, self)._message_post_after_hook(message, msg_vals)
        
        # Filtro por nombre de canal y contenido
        if self.name == 'Gemini Agente de inventario':
            body = message.body or ''
            text = re.sub('<[^>]*>', '', body).strip()
            
            if text:
                self._generate_response(text)

    def _generate_response(self, prompt):
        # API Key configurada en Parametros del Sistema
        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini_inventory.api_key')
        
        if not api_key or not genai:
            return

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            # Contexto de inventario (limitado a 10 productos para velocidad)
            products = self.env['product.product'].search([('type', '=', 'product')], limit=10)
            stock_info = "Stock actual:\n" + "\n".join([f"- {p.name}: {p.qty_available}" for p in products])

            full_prompt = f"Eres un asistente de inventario. {stock_info}\n\nPregunta: {prompt}"
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                self.message_post(body=response.text, message_type='comment', subtype_xmlid='mail.mt_comment')
        except Exception as e:
            _logger.error("Error Gemini: %s", str(e))
