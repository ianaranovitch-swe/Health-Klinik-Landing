# Статический лендинг: отдаём HTML/CSS через Caddy
FROM caddy:2-alpine

WORKDIR /app

COPY Caddyfile /etc/caddy/Caddyfile
COPY index.html style.css booking.js booking-form.js /srv/
COPY bilder /srv/bilder

# Railway задаёт PORT; по умолчанию 8080 для локального запуска
ENV PORT=8080
EXPOSE 8080

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
