---
title: "UD04. Redes y almacenamiento"
weight: 40
---

# UD04 · Redes, almacenamiento y volúmenes persistentes

Una aplicación en contenedores tiene que **hablar** (con otros servicios y con el exterior) y tiene que **recordar** (sus datos deben sobrevivir al contenedor). En esta unidad estudias los modelos de red de Docker y de Kubernetes, cómo se publica un servicio hacia fuera con Services, Ingress y **Gateway API**, y cómo se guardan los datos con volúmenes, PersistentVolumes, PersistentVolumeClaims y StorageClasses.

{{< ra "RA5:a,b,c,d,e,f,g,h" "RA3:f" "RA4:f" >}}

| Página | Contenido |
|---|---|
| [Teoría](/ud04-redes-almacenamiento/ud04-teoria/) | Redes de Docker (bridge, host, none, macvlan, overlay), DNS interno, modelo de red de Kubernetes y CNI, Services, DNS, Ingress, Gateway API, volúmenes de Docker, almacenamiento en Kubernetes (efímero, PV, PVC, StorageClass, CSI, modos de acceso) (6 h) |
| [Prácticas](/ud04-redes-almacenamiento/ud04-practicas/) | Siete prácticas: redes de Docker, macvlan y overlay, volúmenes, Services con MetalLB, Gateway API con Traefik y HTTPS, almacenamiento dinámico con NFS y MiTienda expuesta y persistente (14 h) |

**Duración:** 20 horas (6 h de teoría y 14 h de prácticas). **Hito H4:** MiTienda accesible por nombre y con datos persistentes.
