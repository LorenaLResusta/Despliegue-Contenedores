---
title: "UD05. Seguridad y monitorización"
weight: 50
---

# UD05 · Seguridad, monitorización y buenas prácticas

Una plataforma que funciona no es una plataforma lista para producción. Falta que sea **segura** (contenedores sin privilegios, imágenes sin vulnerabilidades conocidas, permisos mínimos, tráfico restringido), **observable** (métricas, paneles, alertas y registros centralizados) y **resistente** (alta disponibilidad comprobada con simulacros). Esta unidad cierra el curso con la **práctica final**: MiTienda en alta disponibilidad, defendida ante un simulacro de fallos.

{{< ra "RA6:a,b,c,d,e,f,g,h,i" "RA4:g,h" >}}

| Página | Contenido |
|---|---|
| [Teoría](/ud05-seguridad-monitorizacion/ud05-teoria/) | Modelo de amenazas (las 4C), cadena de suministro, endurecimiento de contenedores, escaneo y SBOM, RBAC y cuentas de servicio, Pod Security Standards, cuotas, NetworkPolicies, secretos, observabilidad (Prometheus, Grafana, Alertmanager, EFK/ELK y Loki) y alta disponibilidad (7 h) |
| [Prácticas](/ud05-seguridad-monitorizacion/ud05-practicas/) | Siete prácticas guiadas (endurecimiento, Trivy, RBAC, PSS y cuotas, NetworkPolicies, Prometheus/Grafana, registros centralizados) y la **práctica final** (18 h) |

**Duración:** 25 horas (7 h de teoría y 18 h de prácticas). **Hito H5:** práctica final.
