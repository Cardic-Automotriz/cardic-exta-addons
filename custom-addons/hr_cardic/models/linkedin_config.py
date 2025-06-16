from odoo import models, fields, api
import requests
import json
from odoo.exceptions import ValidationError

class LinkedInConfig(models.Model):
    _name = 'hr_cardic.linkedin_config'
    _description = 'Configuración de LinkedIn'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True, default='Configuración LinkedIn')
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token')
    organization_id = fields.Char(string='Organization ID', required=True)
    active = fields.Boolean(string='Activo', default=True)
    last_token_update = fields.Datetime(string='Última actualización del token')
    authorization_code = fields.Char(string='Authorization Code')
    redirect_uri = fields.Char(string='Redirect URI', required=True, default='https://TU_DOMINIO/oauth2/callback')

    def get_authorization_url(self):
        self.ensure_one()
        return (
            f"https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope=w_member_social"
        )

    def _get_access_token(self):
        """Obtener o refrescar el token de acceso de LinkedIn"""
        self.ensure_one()
        
        if not self.access_token or not self.last_token_update:
            if not self.authorization_code:
                raise ValidationError("Debes obtener y pegar el Authorization Code de LinkedIn.")
            url = 'https://www.linkedin.com/oauth/v2/accessToken'
            data = {
                'grant_type': 'authorization_code',
                'code': self.authorization_code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            try:
                response = requests.post(url, data=data)
                if response.status_code == 200:
                    token_data = response.json()
                    self.write({
                        'access_token': token_data.get('access_token'),
                        'last_token_update': fields.Datetime.now()
                    })
                else:
                    raise ValidationError(f"Error obteniendo token de LinkedIn: {response.text}")
            except Exception as e:
                raise ValidationError(f"Error en la conexión con LinkedIn: {str(e)}")
        
        return self.access_token

    def publish_job(self, job_data):
        """Publicar una vacante como post en LinkedIn usando UGC API"""
        self.ensure_one()
        access_token = self._get_access_token()
        url = 'https://api.linkedin.com/v2/ugcPosts'

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        # Construir el payload para UGC API
        payload = {
            "author": f"urn:li:organization:{self.organization_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": f"{job_data.get('name')}\n{job_data.get('description')}\nPostúlate aquí: {job_data.get('application_url')}"
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in (200, 201):
                # El ID del post viene en el header X-RestLi-Id
                post_id = response.headers.get('X-RestLi-Id')
                # Construir la URL del post
                post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None
                return {'id': post_id, 'url': post_url}
            else:
                raise ValidationError(f"Error publicando en LinkedIn: {response.text}")
        except Exception as e:
            raise ValidationError(f"Error en la conexión con LinkedIn: {str(e)}")

    @api.model
    def get_active_config(self):
        """Obtener la configuración activa de LinkedIn"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            raise ValidationError('No hay configuración activa de LinkedIn')
        return config

    def show_authorization_url(self):
        self.ensure_one()
        url = self.get_authorization_url()
        return {
            'type': 'ir.actions.act_window',
            'name': 'URL de autorización de LinkedIn',
            'res_model': 'ir.actions.act_url',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_url': url},
        } 
