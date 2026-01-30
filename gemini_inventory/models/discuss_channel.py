# -*- coding: utf-8 -*-

from odoo import models
import logging
import re

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _message_post_after_hook(self, message, msg_vals):
        super(DiscussChannel, self)._message_post_after_hook(message, msg_vals)

        # El bot escucha solo en su canal
        if self.name == 'Gemini Agente de inventario':
            body = message.body or ''

            # Limpiar HTML
            clean_text = re.sub('<[^>]*>', '', body).strip()

            if clean_text:
                self._generate_response(clean_text)

    def _generate_response(self, prompt):

        # Obtener API Key desde parámetros del sistema
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'gemini_inventory.api_key'
        )

        if not api_key:
            _logger.error("No hay API Key configurada")
            return

        # Import dinámico (OBLIGATORIO en Odoo.sh)
        try:
            import google.generativeai as genai
        except Exception as e:
            _logger.error("No se pudo importar google.generativeai: %s", e)
            return

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # Consultar inventario real
            products = self.env['product.product'].search(
                [('type', '=', 'product')],
                limit=15
            )

            stock_info = "Stock actual en bodega:\n"
            for p in products:
                stock_info += f"- {p.name}: {p.qty_available} unidades\n"

            contexto = f"""
Eres un asistente de inventario de Odoo.

{stock_info}

Pregunta del usuario:
{prompt}
"""

            response = model.generate_content(contexto)

            if response and getattr(response, "text", False):
                self.message_post(body=response.text)

        except Exception as e:
            _logger.error("Error Gemini runtime: %s", str(e))
