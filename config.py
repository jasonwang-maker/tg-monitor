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
    'projectXtls',
    'projectVless',
]

NOISY_CHANNELS = {'projectVless'}
NOISY_MIN_LENGTH = 80
NOISY_KEYWORDS = [
    'блокиров', 'белый список', 'белые списки', 'whitelist',
    'QUIC', 'quic', 'TLS', 'tls', 'REALITY', 'reality', 'VLESS', 'vless',
    'xray', 'Xray', 'xhttp', 'XHTTP', 'DPI', 'dpi',
    'VPN', 'vpn', 'впн', 'ВПН',
    'РКН', 'Роскомнадзор', 'роскомнадзор',
    'протокол', 'protocol',
    'AnyTLS', 'anytls', 'GoodbyeDPI', 'goodbyedpi',
    'zapret', 'Zapret', 'amnezia', 'Амнезия',
    'обход', 'блокировк', 'фильтр',
    'UDP', 'udp', 'TCP', 'tcp', 'CDN', 'cdn',
    'SNI', 'sni', 'proxy', 'прокси',
    'Iran', 'иран', 'China', 'Китай', 'GFW', 'gfw',
    'SSH', 'ssh', 'WireGuard', 'wireguard',
    'max.ru', 'макс', 'МаКС',
    'telegram', 'Telegram', 'телеграм',
    'shutdown', 'отключ', 'шатдаун',
    'санкци', 'закон', 'штраф', 'уголов',
]

EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_TO = os.environ.get('EMAIL_TO', os.environ['EMAIL_FROM'])
EMAIL_SMTP = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

GROQ_API_KEY = os.environ['GROQ_API_KEY'].strip()
