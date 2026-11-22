# Despliegue de contenedores · Apuntes

Apuntes y prácticas del curso **Despliegue de plataformas de ejecución de contenedores: instalación y gestión** (120 h), curso 2026/27. Sitio estático con [Hugo](https://gohugo.io/) y el tema [hugo-book](https://github.com/alex-shpak/hugo-book), con la misma estructura que los repositorios de BBDD y Seguridad.

## Estructura

```text
content.es/
├── _index.md                         portada: unidades, RA y horas
├── guia/                             RA/CE, temporalización, entorno, proyecto, prácticas y evaluación
├── ud01-virtualizacion-ligera/       _index · ud01-teoria · ud01-practicas
├── ud02-motores-contenedores/        _index · ud02-teoria · ud02-practicas
├── ud03-kubernetes/                  _index · ud03-teoria · ud03-practicas
├── ud04-redes-almacenamiento/        _index · ud04-teoria · ud04-practicas
└── ud05-seguridad-monitorizacion/    _index · ud05-teoria · ud05-practicas (incluye la práctica final)
data/curriculo.yaml                   RA y CE (propuesta; sustituir si hay texto oficial)
layouts/_shortcodes/                  practica, ra, quiz, descarga, figura, sw
static/recursos/mitienda/          código del proyecto: API, web, SQL, compose.yaml y manifiestos k8s/
```

## Prácticas

Cada práctica empieza con la ficha `{{< practica ... >}}` (número, tipo, duración, dificultad, RA/CE, software y entrega) y sigue el esquema Objetivo · Contexto · Desarrollo (`{{% steps %}}`) · Comprobación · Errores habituales · Ampliación.

| Tipo | Uso |
|---|---|
| Guiada | Procedimiento paso a paso; no se entrega |
| Autónoma | Sin procedimiento; se entrega |
| Reto | Problema abierto; opcional o para subir nota |
| Proyecto | Tarea de MiTienda de cada unidad; la 5.8 es la práctica final |

## Uso local

```bash
git submodule update --init --recursive   # si el tema se gestiona como submódulo
hugo server -D
```

La GitHub Action de `.github/workflows/hugo.yaml` publica el sitio en GitHub Pages. Revisa `baseURL` y `BookRepo` en `hugo.toml` cuando crees el repositorio.
