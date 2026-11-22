---
title: "Despliegue de contenedores"
weight: 1
bookToc: true
---

# Despliegue de plataformas de ejecución de contenedores

Apuntes y prácticas del curso **Despliegue de plataformas de ejecución de contenedores: instalación y gestión**, curso **2026/27**. El objetivo es que sepas **planificar, instalar, configurar y administrar** entornos basados en contenedores (Docker, Podman, containerd) y en orquestadores (Kubernetes), y que los dejes listos para producción: con red, almacenamiento persistente, seguridad, monitorización y alta disponibilidad.


> [!NOTE]
> Este módulo forma parte del curso de especialización junto con [Mantenimiento del sistema de contenedores desplegado (5169)](https://lorenalresusta.github.io/Mantenimiento-Contenedores/). La [relación entre los dos módulos](/guia/relacion-modulos/) enlaza cada concepto con el otro, y el [portal de FP](https://lorenalresusta.github.io/FP/) reúne todas las asignaturas por ciclo.

| Característica | Valor |
|---|---|
| **Duración** | **120 horas** (≈ 37 h de teoría y 83 h de prácticas) |
| **Resultados de aprendizaje** | 6 (RA1 a RA6). Consulta la [guía](/guia/ra-ce/) |
| **Entorno de laboratorio** | VirtualBox 7 · Debian 13 · Docker Engine · Podman · kind · kubeadm + Kubernetes 1.36 |
| **Proyecto común** | [MiTienda: de un `docker run` a un clúster en alta disponibilidad](/guia/proyecto-mitienda/) |

> [!NOTE]
> Todo el curso sigue el mismo hilo: **entender el mecanismo → instalarlo → usarlo → romperlo a propósito → comprobar que se recupera**. Por eso casi todas las prácticas terminan con una **prueba de fallo** (parar un contenedor, borrar un Pod, apagar un nodo) y su comprobación.

## El hilo del curso

```mermaid
flowchart LR
    A[Cómo funciona<br/>un contenedor<br/>UD01] --> B[Motores, imágenes<br/>y Compose<br/>UD02]
    B --> C[Orquproducto con<br/>Kubernetes<br/>UD03]
    C --> D[Redes y<br/>almacenamiento<br/>UD04]
    D --> E[Seguridad,<br/>monitorización y HA<br/>UD05]
```

## Unidades didácticas

Cada unidad tiene una página de **teoría** (conceptos, diagramas, ejemplos y autoevaluación) y una de **prácticas** clasificadas en **guiadas**, **autónomas**, **retos** y **tarea del proyecto**, con su ficha de duración, dificultad, RA/CE, software y entrega.

<div class="sad-cards">
  <div class="sad-card"><span class="sad-card-ra">RA1 · 15 h</span><h3>UD01 · Introducción y virtualización ligera</h3><p>Hipervisores frente a contenedores, namespaces, cgroups, sistemas de archivos en capas y estándares OCI.</p><div class="sad-card-links"><a href="ud01-virtualizacion-ligera/ud01-teoria/">Teoría</a> · <a href="ud01-virtualizacion-ligera/ud01-practicas/">Prácticas</a></div></div>
  <div class="sad-card"><span class="sad-card-ra">RA2 · RA3 · 25 h</span><h3>UD02 · Motores de contenedores</h3><p>Docker Engine, Podman y containerd; ciclo de vida, Dockerfile, multi-stage, registros y Docker Compose.</p><div class="sad-card-links"><a href="ud02-motores-contenedores/ud02-teoria/">Teoría</a> · <a href="ud02-motores-contenedores/ud02-practicas/">Prácticas</a></div></div>
  <div class="sad-card"><span class="sad-card-ra">RA4 · 35 h</span><h3>UD03 · Orquproducto con Kubernetes</h3><p>Arquitectura del clúster, kind y kubeadm, Pods, Deployments, StatefulSets, actualizaciones, escalado y Helm.</p><div class="sad-card-links"><a href="ud03-kubernetes/ud03-teoria/">Teoría</a> · <a href="ud03-kubernetes/ud03-practicas/">Prácticas</a></div></div>
  <div class="sad-card"><span class="sad-card-ra">RA5 · 20 h</span><h3>UD04 · Redes y almacenamiento</h3><p>Redes de Docker, CNI, Services, Ingress y Gateway API, volúmenes, PV, PVC y StorageClasses.</p><div class="sad-card-links"><a href="ud04-redes-almacenamiento/ud04-teoria/">Teoría</a> · <a href="ud04-redes-almacenamiento/ud04-practicas/">Prácticas</a></div></div>
  <div class="sad-card"><span class="sad-card-ra">RA6 · 25 h</span><h3>UD05 · Seguridad, monitorización y buenas prácticas</h3><p>Contenedores sin privilegios, escaneo de imágenes, RBAC, políticas de red, Prometheus, Grafana, logs y práctica final en HA.</p><div class="sad-card-links"><a href="ud05-seguridad-monitorizacion/ud05-teoria/">Teoría</a> · <a href="ud05-seguridad-monitorizacion/ud05-practicas/">Prácticas</a></div></div>
</div>

## Relación entre unidades y resultados de aprendizaje

| Unidad | RA1 | RA2 | RA3 | RA4 | RA5 | RA6 | Horas |
|---|:-:|:-:|:-:|:-:|:-:|:-:|--:|
| UD01 Introducción y virtualización ligera | ● | ○ | | | | ○ | 15 |
| UD02 Motores de contenedores | | ● | ● | | ○ | | 25 |
| UD03 Orquproducto con Kubernetes | | | | ● | ○ | | 35 |
| UD04 Redes y almacenamiento | | | ○ | ○ | ● | | 20 |
| UD05 Seguridad, monitorización y buenas prácticas | | | | ○ | | ● | 25 |
| **Total** | | | | | | | **120** |

● contribución principal · ○ contribución secundaria. El detalle por criterio está en [Resultados de aprendizaje y criterios de evaluación](/guia/ra-ce/).

## Empieza aquí: aprender desde cero

¿No habías tocado nunca un contenedor? Empieza por estos recursos y vuelve a ellos siempre que una unidad se te atasque. Cada unidad tiene además, al final de su teoría, sus propios vídeos y prácticas guiadas.

{{< recurso tipo="Vídeo" titulo="Curso de Docker completo, en español" autor="Pelado Nerd · YouTube" url="https://www.youtube.com/results?search_query=pelado+nerd+curso+docker+completo" desc="El punto de partida más recomendado: de la primera imagen a Docker Compose, explicado con calma." >}}
{{< recurso tipo="Interactivo" titulo="Play with Docker: contenedores en el navegador" autor="Docker · labs.play-with-docker.com" url="https://labs.play-with-docker.com/" desc="Un laboratorio gratuito para practicar sin instalar nada en tu equipo." >}}
{{< recurso tipo="Interactivo" titulo="Killercoda: clústeres de Kubernetes de prueba" autor="killercoda.com" url="https://killercoda.com/" desc="Clústeres reales y temporales para practicar kubectl paso a paso." >}}
{{< recurso tipo="Docs" titulo="Guía oficial «Get started» de Docker" autor="Docker Docs" url="https://docs.docker.com/get-started/" desc="Documentación clara y al grano para los primeros pasos." >}}

## Cómo leer estos apuntes

> [!TIP]
> **Consejo.** Una forma más cómoda o más profesional de hacer algo.

> [!WARNING]
> **Atención.** Un error habitual o algo que puede dar problemas.

> [!IMPORTANT]
> **Clave.** Un concepto imprescindible para el resultado de aprendizaje.

> [!CAUTION]
> **Peligro.** Una operación que puede destruir datos o dejarte sin acceso. Haz antes una instantánea de la máquina virtual.

Las órdenes de los bloques de código se escriben **sin indicador de prompt** para que puedas copiarlas tal cual. Cuando una orden necesita privilegios aparece con `sudo`. Si se muestra la salida esperada, va en un bloque aparte marcado como `text`.
