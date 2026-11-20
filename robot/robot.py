# Робот группы заявок: сидит в Telegram под твоим аккаунтом, каждое сообщение группы
# отправляет на сервер «Лимитов» (/grp). Сервер решает — робот ставит «+» ответом на заявку.
# Настройки — в файле .env рядом (см. README.md). Сам ничего не решает: пороги и лимиты в приложении.
import asyncio, os, json, time, logging, urllib.request
from telethon import TelegramClient, events
from telethon.sessions import StringSession

def env(k, d=''):
    v = os.environ.get(k, d)
    if not v and os.path.exists('.env'):
        for line in open('.env', encoding='utf-8'):
            if line.strip().startswith(k + '='): v = line.split('=', 1)[1].strip()
    return v

API_ID, API_HASH, SESSION = int(env('API_ID', '0')), env('API_HASH'), env('SESSION')
CHAT = env('CHAT', 'Заявки UAH/PLN')          # название группы или её id
URL, KEY = env('WORKER_URL').rstrip('/'), env('APP_KEY')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger('robot')

def call(path, body=None):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(URL + path, data=data, method='POST', headers={'x-app-key': KEY, 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read().decode())

def name_of(u):
    if not u: return ''
    return (' '.join(x for x in [getattr(u, 'first_name', None), getattr(u, 'last_name', None)] if x) or getattr(u, 'title', '') or getattr(u, 'username', '') or '').strip()

async def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()
    chat = None
    async for d in client.iter_dialogs():
        if str(d.id) == CHAT or d.name == CHAT: chat = d.entity; break
    if not chat: raise SystemExit('Не нашёл группу «%s». Проверь CHAT в .env' % CHAT)
    me = await client.get_me()
    log.info('Робот на связи: %s, группа «%s»', name_of(me), getattr(chat, 'title', CHAT))

    async def handle(ev):
        m = ev.message
        if m.out or not (m.message or '').strip(): return
        body = {'id': m.id, 'text': m.message, 'from': name_of(await m.get_sender())}
        if m.reply_to_msg_id:
            try:
                r = await m.get_reply_message()
                if r: body['reply'] = {'id': r.id, 'text': r.message or '', 'from': name_of(await r.get_sender())}
            except Exception as e: log.warning('reply: %s', e)
        try:
            res = await asyncio.get_running_loop().run_in_executor(None, call, '/grp', body)
        except Exception as e:
            log.warning('сервер: %s', e); return
        if res.get('plus'):
            await client.send_message(chat, '+', reply_to=int(res.get('reply') or m.id))
            log.info('+ на %s: %s', res.get('reply') or m.id, body['text'][:60])

    client.add_event_handler(handle, events.NewMessage(chats=chat))
    client.add_event_handler(handle, events.MessageEdited(chats=chat))

    async def poll():   # ручной «+» из бота + «я на связи»
        done = []
        while True:
            try:
                res = await asyncio.get_running_loop().run_in_executor(None, call, '/grppoll', {'done': done})
                done = []
                for k in res.get('plus', []):
                    await client.send_message(chat, '+', reply_to=int(k)); done.append(k); log.info('+ вручную на %s', k)
            except Exception as e: log.warning('poll: %s', e)
            await asyncio.sleep(3)
    asyncio.create_task(poll())
    await client.run_until_disconnected()

if __name__ == '__main__':
    while True:
        try: asyncio.run(main())
        except SystemExit: raise
        except Exception as e: log.error('упал: %s — перезапуск через 10 с', e); time.sleep(10)
