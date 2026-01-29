# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import re

_logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    _logger.warning("Google Generative AI library not found. Install it with pip install google-generativeai")
    genai = None

class DiscussChannel(models.Model):
    _inherit = 'mail.channel'

    def _message_post_after_hook(self, message, msg_vals):
        super(DiscussChannel, self)._message_post_after_hook(message, msg_vals)
        
        # El bot escucha si el canal se llama exactamente así
        if self.name == 'Gemini Agente de inventario':
            text = self._extract_text(message.body)
            
            # Comentamos la restricción de autor para que te responda a ti (Admin)
            if text: # and not message.author_id.share:
                self._generate_response(text)

    def _extract_text(self, html):
        if not html:
            return ""
        return re.sub('<[^>]*>', '', html).strip()

    def _generate_response(self, prompt):
        if not genai:
            self.message_post(body="Error: Librería Gemini no instalada.")
            return

        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini_inventory.api_key')
        if not api_key:
            self.message_post(body="Error: API Key no configurada en Parámetros del Sistema.")
            return

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            # Buscamos productos para darle contexto a la IA
            products = self.env['product.product'].search([('type', '=', 'product')], limit=10)
            stock_info = ""
            for p in products:
                stock_info += f"- {p.name}: {p.qty_available} unidades\n"

            full_prompt = f"Eres un asistente de inventario en Odoo. Stock actual:\n{stock_info}\n\nUsuario dice: {prompt}"
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                self.message_post(body=response.text)
        except Exception as e:
            _logger.error("Error en Gemini: %s", str(e))
            self.message_post(body=f"Error técnico: {str(e)}")
