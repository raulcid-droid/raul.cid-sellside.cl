# from odoo import http


# class MiModuloPractica(http.Controller):
#     @http.route('/mi_modulo_practica/mi_modulo_practica', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mi_modulo_practica/mi_modulo_practica/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mi_modulo_practica.listing', {
#             'root': '/mi_modulo_practica/mi_modulo_practica',
#             'objects': http.request.env['mi_modulo_practica.mi_modulo_practica'].search([]),
#         })

#     @http.route('/mi_modulo_practica/mi_modulo_practica/objects/<model("mi_modulo_practica.mi_modulo_practica"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mi_modulo_practica.object', {
#             'object': obj
#         })

