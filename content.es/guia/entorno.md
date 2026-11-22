---
title: "Entorno de trabajo"
weight: 4
bookToc: true
---

# Entorno de trabajo

Todo el curso se hace sobre **máquinas virtuales** propias. Así puedes romper cosas sin miedo: antes de cada práctica delicada haces una **instantánea** y, si algo sale mal, vuelves atrás en segundos.

## 1. Máquinas virtuales

| Máquina | Uso | vCPU | RAM | Disco | IP (red solo-anfitrión) |
|---|---|:-:|:-:|:-:|---|
| `ct-lab` | Máquina principal: Docker, Podman, kind, Helm, registro privado y herramientas | 4 | 8 GB | 60 GB | 192.168.56.10 |
| `k8s-cp` | Plano de control del clúster kubeadm (desde la práctica 3.7) | 2 | 3 GB | 30 GB | 192.168.56.11 |
| `k8s-w1` | Nodo de trabajo 1 | 2 | 3 GB | 30 GB | 192.168.56.12 |
| `k8s-w2` | Nodo de trabajo 2 | 2 | 3 GB | 30 GB | 192.168.56.13 |

> [!TIP]
> **Equipo con poca memoria.** Si tu ordenador tiene 8 GB de RAM, trabaja solo con `ct-lab` (con 5-6 GB) y usa **kind** para todo Kubernetes. Las prácticas de kubeadm (3.7) se pueden hacer por parejas o con `k8s-w2` apagado.

Todas las máquinas usan **Debian 13 (trixie)** instalado sin entorno gráfico, con el servidor SSH y las utilidades estándar del sistema.

## 2. Red del laboratorio

Cada máquina tiene **dos adaptadores** de red en VirtualBox:

| Adaptador | Tipo | Para qué sirve |
|---|---|---|
| 1 | NAT | Salida a Internet (paquetes, imágenes) |
| 2 | Solo-anfitrión (`vboxnet0`, 192.168.56.0/24) | Acceder desde tu equipo por SSH y navegador, y comunicar los nodos del clúster entre sí |

Configura la IP fija del segundo adaptador en `/etc/network/interfaces.d/lab` (en `ct-lab`; cambia la IP en cada máquina):

```text
auto enp0s8
iface enp0s8 inet static
    address 192.168.56.10/24
```

```bash
sudo systemctl restart networking
ip -br address
```

Añade los nombres al fichero `/etc/hosts` de **todas** las máquinas y también al de tu equipo anfitrión:

```text
192.168.56.10  ct-lab registro.local mitienda.local grafana.local
192.168.56.11  k8s-cp
192.168.56.12  k8s-w1
192.168.56.13  k8s-w2
```

## 3. Preparación básica de cada máquina

```bash
# Como root, nada más instalar
apt update && apt full-upgrade -y
apt install -y sudo curl wget ca-certificates gnupg git vim jq tree htop bash-completion
usermod -aG sudo alumno          # sustituye «alumno» por tu usuario
```

Cierra la sesión, vuelve a entrar y comprueba `sudo whoami`. Después haz la **instantánea «base»** de la máquina apagada.

## 4. Software del curso

| Software | Dónde | Se instala en |
|---|---|---|
| Docker Engine + plugins `buildx` y `compose` | `ct-lab` | [Práctica 2.1](/ud02-motores-contenedores/ud02-practicas/#práctica-21--instalar-docker-engine-en-debian-13) |
| Podman | `ct-lab` | [Práctica 2.3](/ud02-motores-contenedores/ud02-practicas/#práctica-23--podman-sin-privilegios-y-comparación-de-motores) |
| kind y `kubectl` | `ct-lab` | [Práctica 3.1](/ud03-kubernetes/ud03-practicas/#práctica-31--primer-clúster-con-kind) |
| containerd, kubeadm, kubelet, kubectl (v1.36) | `k8s-cp`, `k8s-w1`, `k8s-w2` | [Práctica 3.7](/ud03-kubernetes/ud03-practicas/#práctica-37--clúster-de-tres-nodos-con-kubeadm) |
| Helm | `ct-lab` y `k8s-cp` | [Práctica 3.9](/ud03-kubernetes/ud03-practicas/#práctica-39--empaquetar-con-helm-y-kustomize) |
| Trivy | `ct-lab` | [Práctica 5.2](/ud05-seguridad-monitorizacion/ud05-practicas/#práctica-52--análisis-de-vulnerabilidades-y-sbom-con-trivy) |

> [!IMPORTANT]
> **Instala siempre desde los repositorios oficiales del proyecto** (Docker, Kubernetes, Helm…). El paquete `docker.io` de Debian funciona, pero va por detrás en versiones y no incluye los plugins `buildx` y `compose` actuales. Los apuntes indican en cada caso de dónde sale cada paquete.

## 5. Recursos del proyecto

El código de la aplicación **MiTienda** está en esta misma web. Para tenerlo en `ct-lab`:

```bash
mkdir -p ~/curso && cd ~/curso
for f in api/app.py api/requirements.txt api/Dockerfile web/index.html web/nginx.conf \
         web/Dockerfile db/init.sql compose.yaml; do
  mkdir -p "mitienda/$(dirname "$f")"
  wget -q -O "mitienda/$f" "https://lorenalresusta.github.io/Contenedores/recursos/mitienda/$f"
done
tree mitienda
```

Los manifiestos de Kubernetes del proyecto están en `recursos/mitienda/k8s/` y se descargan en la [UD03](/ud03-kubernetes/ud03-practicas/).

## 6. Normas del laboratorio

- **Instantánea antes de cada práctica marcada con** ⚠️. Ponle un nombre que diga qué contiene (`antes-3.7-kubeadm`).
- **Nunca expongas** el socket de Docker (`/var/run/docker.sock`) por red ni lo montes en contenedores que no sean de tu confianza: equivale a dar acceso de `root` a la máquina.
- **Las contraseñas de las prácticas no se reutilizan** fuera del laboratorio y los ficheros de secretos (`secrets/*.txt`, `*.key`) **no se suben** a Git.
- Al terminar la sesión, `docker system df` te dice cuánto ocupan imágenes y volúmenes. Limpia lo que no uses con `docker system prune` (lee lo que va a borrar antes de confirmar).
