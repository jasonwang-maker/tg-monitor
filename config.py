import os

API_ID = int(os.environ['TG_API_ID'])
API_HASH = os.environ['TG_API_HASH']
SESSION_NAME = 'session_file'

CHANNELS = [
    'netblocks',
    'usher2',
    'zatelecom',
    'INTERNETFORIRAN',
    'vps_xhq',
]

EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_TO = os.environ.get('EMAIL_TO', os.environ['EMAIL_FROM'])
EMAIL_SMTP = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
