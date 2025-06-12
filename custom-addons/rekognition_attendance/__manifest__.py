{
    'name': 'Rekognition Attendance',
    'version': '1.0',
    'summary': 'Asistencia con reconocimiento facial usando AWS Rekognition',
    'author': 'Tu Nombre',
    'category': 'Human Resources',
    'depends': ['base', 'web', 'hr', 'hr_attendance'],
    'data': [
        'views/rekognition_attendance_views.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/chekador_assets.xml',
    ],
    'installable': True,
    'application': True,
} 