{
    'name': 'Rekognition Attendance',
    'version': '1.0',
    'summary': 'Asistencia con reconocimiento facial usando AWS Rekognition',
    'author': 'Tu Nombre',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'views/rekognition_attendance_views.xml',
    ],
    'installable': True,
    'application': True,
} 