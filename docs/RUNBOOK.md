# Runbook: Health Klinik Landing

Инструкции по деплою, откату и диагностике на Railway.

## 1. Деплой

### Первый раз

1. Создать репозиторий на GitHub и запушить код.
2. Railway → **New Project** → **Deploy from GitHub repo**.
3. Убедиться, что используется `Dockerfile` (см. `railway.toml`).
4. После успешного деплоя: **Settings → Networking → Generate Domain**.
5. Проверить:
   - главная: `https://<service>.up.railway.app/`
   - health: `https://<service>.up.railway.app/health` → ответ `ok`

### Обновление (обычный релиз)

```bash
git add .
git commit -m "Update landing copy or styles"
git push origin main
```

Railway подхватит push и задеплоит новую версию автоматически (если включён GitHub-деплой).

### Локальная проверка перед деплоем

```bash
docker build -t health-klinik-landing .
docker run --rm -p 8080:8080 -e PORT=8080 health-klinik-landing
```

Открыть `http://localhost:8080` и пройти по секциям / FAQ / контактам.

## 2. Откат (rollback)

### Через Railway Dashboard

1. Открыть сервис → **Deployments**.
2. Найти последний рабочий деплой.
3. **⋯ → Redeploy** (или Rollback, если доступно в UI).

### Через Git

```bash
git revert HEAD
git push origin main
```

Либо временно задеплоить предыдущий коммит:

```bash
git checkout <good-commit-sha>
git push origin HEAD:main --force-with-lease
```

`--force-with-lease` использовать только если команда явно договорилась об откате ветки.

## 3. Диагностика

| Симптом | Что проверить |
|---|---|
| 502 / Application failed | Логи билда и рантайма в Railway → **Deployments → View Logs** |
| Пустая страница / нет CSS | Что `style.css` лежит рядом с `index.html` и скопирован в `/srv` в Dockerfile |
| Healthcheck red | Открыть `/health`; в `Caddyfile` должен быть `handle /health` |
| Порт не слушается | Railway задаёт `PORT`; Caddy слушает `:{$PORT:8080}` |
| Старый контент после push | Дождаться конца деплоя; Hard refresh (Ctrl+F5) |

### Полезные команды

```bash
# Локально: проверить что контейнер отвечает
curl http://localhost:8080/health

# Локально: главная отдаёт HTML
curl -I http://localhost:8080/
```

## 4. Временный URL → свой домен

Пока домена нет — используй `*.up.railway.app`.

Когда домен готов (DNS в Cloudflare):

1. Railway → **Settings → Domains → Custom Domain**.
2. Ввести домен (например `example.se` и/или `www.example.se`).
3. Добавить в Cloudflare DNS записи, которые покажет Railway (обычно CNAME + TXT).
4. Proxy status в Cloudflare: сначала **DNS only** (серая тучка), пока SSL не станет Active.
5. После зелёного SSL можно снова включить Cloudflare Proxy при необходимости.

Точный чеклист DNS сделаем отдельно под выбранное имя домена.

## 5. Переменные окружения

Сейчас нужна только:

```
PORT=8080
```

На Railway `PORT` выставляется платформой — вручную задавать не нужно.

Когда появится бронирование/БД, добавить секреты только через Railway Variables (не коммитить в git).
