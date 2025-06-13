from odoo import models, fields, api
import boto3
import os
import base64
from botocore.exceptions import ClientError, NoCredentialsError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    face_id = fields.Char(string='AWS FaceId', readonly=True)

    def _get_rekognition_client(self):
        """Get AWS Rekognition client using default credential chain"""
        try:
            return boto3.client('rekognition', region_name='us-east-2')
        except Exception as e:
            raise ValueError(f"Error configurando el cliente AWS: {str(e)}")

    def action_register_face(self, image_path):
        try:
            rekognition = self._get_rekognition_client()
            with open(image_path, 'rb') as image_file:
                response = rekognition.index_faces(
                    CollectionId='empleados_cardic',
                    Image={'Bytes': image_file.read()},
                    ExternalImageId=str(self.id),
                    DetectionAttributes=[]
                )
                if response['FaceRecords']:
                    face_id = response['FaceRecords'][0]['Face']['FaceId']
                    self.face_id = face_id
                    return face_id
                else:
                    return False
        except Exception as e:
            raise ValueError(f"Error al registrar el rostro desde archivo: {str(e)}")

    def action_register_face_wizard(self):
        for rec in self:
            if not rec.image_1920:
                raise ValueError("El empleado no tiene imagen cargada.")
            
            try:
                image_bytes = base64.b64decode(rec.image_1920)
                rekognition = self._get_rekognition_client()
                
                response = rekognition.index_faces(
                    CollectionId='empleados_cardic',
                    Image={'Bytes': image_bytes},
                    ExternalImageId=str(rec.id),
                    DetectionAttributes=[]
                )
                
                if response['FaceRecords']:
                    face_id = response['FaceRecords'][0]['Face']['FaceId']
                    rec.face_id = face_id
                else:
                    raise ValueError("No se detectó rostro en la imagen.")
                    
            except NoCredentialsError:
                raise ValueError(
                    "No se encontraron credenciales de AWS. Por favor, asegúrese de que las credenciales "
                    "están configuradas en ~/.aws/credentials para el usuario odoo."
                )
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                raise ValueError(f"Error de AWS ({error_code}): {error_message}")
            except Exception as e:
                raise ValueError(f"Error al registrar el rostro: {str(e)}")

    def open_chekador_facial_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Checador Facial',
            'res_model': 'rekognition.attendance.chekador',
            'view_mode': 'form',
            'target': 'new',
        }

class RekognitionAttendanceChekador(models.TransientModel):
    _name = 'rekognition.attendance.chekador'
    _description = 'Checador de Asistencia con Reconocimiento Facial'

    image = fields.Binary(string='Foto tomada', attachment=True)
    result_message = fields.Char(string='Resultado', readonly=True)

    def action_check_attendance(self):
        self.ensure_one()
        if not self.image:
            self.result_message = "No se ha tomado ninguna foto."
            return self._notification("Error", self.result_message)

        try:
            # Decodifica la imagen base64
            image_bytes = base64.b64decode(self.image)
            rekognition = self.env['hr.employee']._get_rekognition_client()
            response = rekognition.search_faces_by_image(
                CollectionId='empleados_cardic',
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                FaceMatchThreshold=90
            )
            if response['FaceMatches']:
                face_id = response['FaceMatches'][0]['Face']['FaceId']
                employee = self.env['hr.employee'].search([('face_id', '=', face_id)], limit=1)
                if employee:
                    # Marcar asistencia
                    self.env['hr.attendance'].create({
                        'employee_id': employee.id,
                        'check_in': fields.Datetime.now(),
                    })
                    self.result_message = f"Asistencia registrada para {employee.name}."
                else:
                    self.result_message = "Rostro reconocido, pero no se encontró el empleado."
            else:
                self.result_message = "No se encontró coincidencia de rostro."
        except Exception as e:
            self.result_message = f"Error: {str(e)}"

        return self._notification("Resultado", self.result_message)

    def _notification(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
            }
        } 