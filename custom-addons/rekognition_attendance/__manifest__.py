{
    'name': 'Rekognition Attendance',
    'version': '1.0',
    'summary': 'Asistencia con reconocimiento facial usando AWS Rekognition',
    'author': 'Tu Nombre',
    'category': 'Human Resources',
    'depends': ['base', 'web', 'hr', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/rekognition_attendance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rekognition_attendance/static/src/js/camera.js',
            'rekognition_attendance/static/src/xml/chekador_assets.xml',
        ],
    },
    'installable': True,
    'application': True,
}
