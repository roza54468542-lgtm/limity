# Один раз: вход в Telegram и получение SESSION для .env. Код из Telegram вводишь сам, никому его не показывай.
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
api_id = int(input('API_ID: ')); api_hash = input('API_HASH: ').strip()
with TelegramClient(StringSession(), api_id, api_hash) as c:
    s = c.session.save()
open('.env', 'a', encoding='utf-8').write('API_ID=%d\nAPI_HASH=%s\nSESSION=%s\n' % (api_id, api_hash, s))
print('\nГотово: вход сохранён в .env (SESSION — это ключ от аккаунта, никому не показывай).')
