# Onliner Tasks Monitor

Бот для уведомлений в Telegram о новых заявках на Onliner Services.

Категории:

- Ремонт бытовой техники
- Ремонт компьютерной техники
- Ремонт видеотехники

## Настройка

В GitHub репозитории откройте Settings → Secrets and variables → Actions и добавьте секреты:

- `TELEGRAM_TOKEN` — новый токен Telegram-бота из BotFather
- `TELEGRAM_CHAT_ID` — `1912674581`

Потом откройте Actions → Onliner Tasks Monitor → Run workflow.

Первый запуск только сохранит текущие заявки. Уведомления начнут приходить со второго запуска, когда появятся новые заявки.
