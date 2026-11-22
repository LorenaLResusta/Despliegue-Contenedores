# syntax=docker/dockerfile:1
# Imagen del frontal web de MiTienda: nginx sin privilegios + página estática
FROM nginxinc/nginx-unprivileged:1.29-alpine
LABEL org.opencontainers.image.title="mitienda-web"
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/nginx-salud || exit 1
