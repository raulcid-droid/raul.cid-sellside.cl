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
        
        # TAREA 1: El bot escucha solo en su canal
        if self.name == 'Gemini Agente de inventario':
            body = message.body or ''
            # Aquí limpiamos el HTML para que la IA reciba texto puro
            clean_text = re.sub('<[^>]*>', '', body).strip()
            
            if clean_text:
                self._generate_response(clean_text)

    def _generate_response(self, prompt):
        # Buscamos la API Key que configuraste en Parametros del Sistema
        api_key = self.env['ir.config_parameter'].sudo().get_param('gemini_inventory.api_key')
        
        if not api_key or not genai:
            _logger.error("Falta API Key o libreria google-generativeai")
            return

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # TAREA 1.1: El bot consulta el inventario real
            products = self.env['product.product'].search([('type', '=', 'product')], limit=15)
            stock_info = "Stock actual en bodega:\n"
            for p in products:
                stock_info += f"- {p.name}: {p.qty_available} unidades\n"

            contexto = f"Eres un asistente de inventario de Odoo. {stock_info}\n\nPregunta del usuario: {prompt}"
            response = model.generate_content(contexto)
            
            if response and response.text:
                self.message_post(body=response.text)
        except Exception as e:
            _logger.error("Error en Gemini: %s", str(e))
