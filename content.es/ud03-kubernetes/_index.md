---
title: "UD03. Kubernetes"
weight: 30
---

# UD03 · Orquproducto de contenedores con Kubernetes

Con Compose gestionas contenedores **en una máquina**. ¿Y si esa máquina se apaga? ¿Y si necesitas 30 réplicas repartidas en 5 servidores, actualizarlas sin cortar el servicio y que se recoloquen solas cuando cae un nodo? Eso es un **orquestador**. En esta unidad aprendes la arquitectura de Kubernetes, montas clústeres de pruebas con kind y uno de verdad con kubeadm, y despliegas aplicaciones de forma **declarativa** con sus actualizaciones, *rollbacks* y escalado automático.

{{< ra "RA4:a,b,c,d,e,f,g,h,i" "RA2:a" "RA5:b,c" >}}

| Página | Contenido |
|---|---|
| [Teoría](/ud03-kubernetes/ud03-teoria/) | Por qué orquestar, arquitectura (plano de control y nodos), instalación (kind, Minikube, kubeadm, gestionados), modelo declarativo y YAML, Pods, ReplicaSets, Deployments, StatefulSets, DaemonSets, Jobs, ConfigMaps y Secrets, sondas, recursos, actualizaciones, escalado, Helm y Kustomize (11 h) |
| [Prácticas](/ud03-kubernetes/ud03-practicas/) | Diez prácticas: kind, Pods, Deployments, *rolling update*, configuración, cargas con estado y por lotes, kubeadm, HPA, Helm/Kustomize y MiTienda en Kubernetes (24 h) |

**Duración:** 35 horas (11 h de teoría y 24 h de prácticas). **Hito H3:** MiTienda en Kubernetes.
