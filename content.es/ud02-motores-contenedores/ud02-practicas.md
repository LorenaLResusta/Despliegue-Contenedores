---
title: "UD02 · Prácticas"
weight: 2
bookToc: true
---

# UD02 · Prácticas

{{< ra "RA2:a,b,c,d,e,f,g" "RA3:a,b,c,d,e,f,g,h" >}}

| Práctica | Tipo | Nivel | Horas | CE principales |
|---|---|---|--:|---|
| [2.1 Instalar Docker Engine en Debian 13](#práctica-21--instalar-docker-engine-en-debian-13) | Guiada | ●○○ | 1,5 | RA2: a, b, g |
| [2.2 Ciclo de vida, límites y depuración](#práctica-22--ciclo-de-vida-límites-y-depuración) | Guiada | ●○○ | 2 | RA2: c, d, e |
| [2.3 Podman sin privilegios y comparación de motores](#práctica-23--podman-sin-privilegios-y-comparación-de-motores) | Guiada | ●●○ | 1,5 | RA2: a, b, f |
| [2.4 Mi primer Dockerfile](#práctica-24--mi-primer-dockerfile) | Guiada | ●○○ | 2 | RA3: a, c |
| [2.5 Imágenes pequeñas con multi-stage](#práctica-25--imágenes-pequeñas-con-multi-stage) | Guiada | ●●○ | 2 | RA3: a, b |
| [2.6 Registro privado con TLS y autenticación](#práctica-26--registro-privado-con-tls-y-autenticación) | Guiada | ●●○ | 2 | RA3: c, d, e |
| [2.7 Primera aplicación con Docker Compose](#práctica-27--primera-aplicación-con-docker-compose) | Guiada | ●○○ | 1,5 | RA3: f, g |
| [2.8 MiTienda con Docker Compose](#práctica-28--mitienda-con-docker-compose) | Proyecto | ●●● | 3 | RA3: a-h |
| [2.9 Depurar un Compose roto](#práctica-29--depurar-un-compose-roto) | Reto | ●●● | 1,5 | RA2: e · RA3: f, h |
| **Total** | | | **17 h** | |

> [!IMPORTANT]
> **Antes de empezar.** Haz la instantánea **«ud02-inicio»** de `ct-lab`. Si en la UD01 añadiste Podman, no hay conflicto: Docker y Podman pueden convivir.

---

## Práctica 2.1 · Instalar Docker Engine en Debian 13

{{< practica num="2.1" tipo="Guiada" duracion="1,5 h" nivel="1" ra="RA2: a, b, g" entorno="Debian 13 · Docker Engine (repositorio oficial)" entrega="ud02/p2.1-instalacion.md con las salidas de la comprobación" >}}

#### Objetivo

Instalar Docker Engine desde el repositorio oficial, configurarlo para un uso profesional y documentar la instalación.

#### Desarrollo

{{% steps %}}

1. **Elimina paquetes que puedan entrar en conflicto** (si no hay ninguno, no pasa nada):

    ```bash
    for p in docker.io docker-doc docker-compose podman-docker containerd runc; do
      sudo apt remove -y $p 2>/dev/null
    done
    ```

2. **Añade el repositorio de Docker** y su clave:

    ```bash
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
    Types: deb
    URIs: https://download.docker.com/linux/debian
    Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
    Components: stable
    Signed-By: /etc/apt/keyrings/docker.asc
    EOF
    sudo apt update
    apt-cache policy docker-ce | head -5      # el candidato viene de download.docker.com
    ```

3. **Instala los paquetes:**

    ```bash
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```

4. **Comprueba el servicio y la primera ejecución:**

    ```bash
    systemctl status docker --no-pager
    sudo docker run --rm hello-world
    ```

5. **Permite usar Docker sin `sudo`** (entendiendo el riesgo, ver teoría):

    ```bash
    sudo usermod -aG docker "$USER"
    newgrp docker
    docker ps
    ```

6. **Configura el demonio.** Crea `/etc/docker/daemon.json`:

    ```json
    {
      "log-driver": "json-file",
      "log-opts": { "max-size": "10m", "max-file": "3" },
      "default-address-pools": [ { "base": "172.30.0.0/16", "size": 24 } ],
      "live-restore": true
    }
    ```

    ```bash
    sudo systemctl restart docker
    docker info --format 'Logging: {{.LoggingDriver}} · Live restore: {{.LiveRestoreEnabled}} · Cgroups: {{.CgroupVersion}}'
    ```

7. **Prueba `live-restore`.** Arranca un contenedor, reinicia el demonio y comprueba que el contenedor **no** se ha reiniciado:

    ```bash
    docker run -d --name vivo nginx:1.29-alpine
    docker inspect vivo --format '{{.State.StartedAt}}'
    sudo systemctl restart docker
    docker inspect vivo --format '{{.State.StartedAt}}'   # la misma hora
    docker rm -f vivo
    ```

8. **Explora la arquitectura de la UD01:**

    ```bash
    docker run -d --name arbol nginx:1.29-alpine
    ps -ef --forest | grep -B1 -A3 containerd-shim | head -20
    docker rm -f arbol
    ```

{{% /steps %}}

#### Comprobación

Guarda en `ud02/p2.1-instalacion.md`:

- [ ] `docker version` (cliente y servidor) y `docker compose version`.
- [ ] `docker info` mostrando `Cgroup Version: 2`, el driver de registros y `Live Restore Enabled: true`.
- [ ] La prueba de `live-restore` con las dos horas de arranque iguales.
- [ ] El árbol `containerd-shim → nginx` y una frase que lo relacione con la cadena dockerd → containerd → runc.

#### Errores habituales

- **`Conflicting values set for option Signed-By`**: queda un fichero antiguo del repositorio en `/etc/apt/sources.list.d/`. Bórralo.
- **`unable to configure the Docker daemon with file /etc/docker/daemon.json`**: JSON mal formado. Valídalo con `jq . /etc/docker/daemon.json`.
- **`permission denied while trying to connect to the Docker daemon socket`**: no has abierto una sesión nueva tras `usermod`.

#### Ampliación

Mueve los datos de Docker a otro disco virtual (`"data-root": "/srv/docker"`) sin perder las imágenes: para el servicio, copia con `rsync -aP`, cambia la configuración y arranca.

---

## Práctica 2.2 · Ciclo de vida, límites y depuración

{{< practica num="2.2" tipo="Guiada" duracion="2 h" nivel="1" ra="RA2: c, d, e" entorno="Docker Engine" entrega="no" >}}

#### Objetivo

Recorrer todos los estados de un contenedor, aplicar políticas de reinicio y límites, y diagnosticar contenedores que fallan.

#### Desarrollo

{{% steps %}}

1. **Ciclo de vida completo.** Observa el estado tras cada orden con `docker ps -a --format 'table {{.Names}}\t{{.Status}}'`:

    ```bash
    docker create --name ciclo -p 8081:80 nginx:1.29-alpine
    docker start ciclo
    curl -s localhost:8081 | head -4
    docker pause ciclo ; curl -m 2 localhost:8081 || echo "sin respuesta: pausado"
    docker unpause ciclo
    docker stop ciclo
    docker start ciclo
    docker rm -f ciclo
    ```

2. **Interactuar con un contenedor en marcha.**

    ```bash
    docker run -d --name web -p 8080:80 nginx:1.29-alpine
    docker exec -it web sh -c 'echo "<h1>Hola desde $(hostname)</h1>" > /usr/share/nginx/html/index.html'
    curl localhost:8080
    docker logs --tail 5 web
    docker top web
    docker stats --no-stream web
    docker cp web:/etc/nginx/conf.d/default.conf ./default.conf
    docker diff web
    ```

3. **Variables de entorno e `inspect`.**

    ```bash
    docker run -d --name bd -e MARIADB_ROOT_PASSWORD=Curso_2026 mariadb:11.8
    docker inspect bd --format '{{json .Config.Env}}' | jq
    ```

    ¿Ves la contraseña en claro? Es el motivo de usar secretos (práctica 2.8).

4. **Políticas de reinicio.** Un contenedor que falla a propósito:

    ```bash
    docker run -d --name falla --restart on-failure:3 alpine:3.22 sh -c 'echo arranco; sleep 2; exit 1'
    sleep 20
    docker inspect falla --format 'Reinicios: {{.RestartCount}} · Estado: {{.State.Status}}'
    docker logs falla
    docker run -d --name siempre --restart unless-stopped alpine:3.22 sleep 3600
    sudo systemctl restart docker
    docker ps --filter name=siempre        # vuelve a estar en marcha
    ```

5. **Límites de recursos.**

    ```bash
    docker run -d --name limitado --memory 64m --memory-swap 64m --cpus 0.5 --pids-limit 50 \
      polinux/stress stress --vm 1 --vm-bytes 200M
    sleep 5
    docker ps -a --filter name=limitado
    docker inspect limitado --format 'OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}'
    docker update --memory 512m --memory-swap 512m siempre   # cambiar límites en caliente
    ```

6. **Depuración de tres contenedores rotos.** Ejecuta cada uno, averigua por qué falla siguiendo el orden de la teoría (`ps -a` → `logs` → `inspect` → `--entrypoint sh`) y corrígelo:

    ```bash
    docker run -d --name roto1 nginx:1.29-alpine nginx            # 1
    docker run -d --name roto2 -p 8080:80 nginx:1.29-alpine       # 2
    docker run -d --name roto3 postgres:17-alpine                 # 3
    ```

7. **Limpieza** y espacio ocupado:

    ```bash
    docker rm -f $(docker ps -aq)
    docker system df
    docker image prune
    ```

{{% /steps %}}

#### Comprobación

- [ ] Sabes explicar los estados `created`, `running`, `paused`, `exited` y qué orden lleva a cada uno.
- [ ] `falla` muestra `RestartCount 3` y queda `exited`.
- [ ] `limitado` termina con `OOMKilled=true` y código 137.
- [ ] Has corregido los tres contenedores rotos (pistas: nginx en segundo plano, puerto ocupado, variable obligatoria).

#### Errores habituales

- Olvidar `--memory-swap`: si no se fija, el contenedor puede usar *swap* y tardar en morir.
- Confundir `docker stop` (envía `SIGTERM`) con `docker kill` (envía `SIGKILL` inmediatamente).

#### Ampliación

Sigue `docker events --filter container=falla` en otra terminal mientras se reinicia. ¿Qué eventos aparecen y en qué orden?

---

## Práctica 2.3 · Podman sin privilegios y comparación de motores

{{< practica num="2.3" tipo="Guiada" duracion="1,5 h" nivel="2" ra="RA2: a, b, f" entorno="Podman · Docker Engine · containerd (ctr)" entrega="ud02/p2.3-comparativa.md" >}}

#### Objetivo

Ejecutar contenedores sin privilegios con Podman, gestionarlos con systemd y comparar Docker, Podman y containerd con la misma imagen OCI.

#### Desarrollo

{{% steps %}}

1. **Podman *rootless*.** Con tu usuario normal:

    ```bash
    grep "$USER" /etc/subuid /etc/subgid
    podman run -d --name web -p 8090:80 docker.io/library/nginx:1.29-alpine
    podman ps
    curl -s localhost:8090 | head -3
    ```

2. **¿Quién es `root`?** Compara el usuario del proceso dentro y fuera:

    ```bash
    podman exec web id                       # uid=0(root) dentro
    ps -o user,pid,cmd -C nginx | head -3    # tu usuario (o un UID del rango subuid) fuera
    podman unshare cat /proc/self/uid_map
    ```

    El `root` del contenedor es tu usuario en el anfitrión: si escapara, no tendría privilegios.

3. **Sin demonio.** Busca el padre del proceso:

    ```bash
    ps -ef --forest | grep -B2 "nginx: master" | grep -v grep
    ```

    Verás `conmon` (el monitor de Podman), no un demonio central.

4. **Pods en Podman.** Un Pod agrupa contenedores que comparten red, como en Kubernetes:

    ```bash
    podman pod create --name app -p 8091:80
    podman run -d --pod app --name front docker.io/library/nginx:1.29-alpine
    podman run -d --pod app --name lateral docker.io/library/alpine:3.22 sleep 3600
    podman exec lateral wget -qO- localhost:80 | head -3   # se ven por localhost
    podman generate kube app > app-pod.yaml
    head -30 app-pod.yaml
    ```

5. **Servicio de systemd con Quadlet.** Crea `~/.config/containers/systemd/web.container`:

    ```ini
    [Unit]
    Description=Servidor web en Podman sin privilegios

    [Container]
    Image=docker.io/library/nginx:1.29-alpine
    PublishPort=8092:80

    [Install]
    WantedBy=default.target
    ```

    ```bash
    podman rm -f web
    systemctl --user daemon-reload
    systemctl --user start web
    systemctl --user status web --no-pager
    loginctl enable-linger "$USER"     # que arranque aunque no hayas iniciado sesión
    ```

6. **La misma imagen en tres motores.** Construye con Docker y ejecuta en Podman y containerd:

    ```bash
    mkdir -p ~/ud02/oci && cd ~/ud02/oci
    printf 'FROM alpine:3.22\nCMD ["echo","Imagen OCI construida con Docker"]\n' > Dockerfile
    docker build -t oci-demo:1.0 .
    docker save oci-demo:1.0 -o oci-demo.tar
    podman load -i oci-demo.tar && podman run --rm localhost/oci-demo:1.0
    sudo ctr -n curso images import oci-demo.tar
    sudo ctr -n curso run --rm docker.io/library/oci-demo:1.0 prueba
    ```

{{% /steps %}}

#### Comprobación

En `ud02/p2.3-comparativa.md`, una tabla que compare Docker, Podman y containerd en: demonio sí/no, *rootless* por defecto, CLI, integración con systemd, Compose, uso en Kubernetes; y las evidencias de:

- [ ] `id` dentro (root) y `ps` fuera (no root) del contenedor de Podman.
- [ ] El servicio `web` de Quadlet activo.
- [ ] La imagen construida con Docker ejecutada en Podman y en containerd.

#### Errores habituales

- **`rootlessport cannot expose privileged port 80`**: un usuario normal no puede publicar puertos menores que 1024. Usa puertos altos.
- **Quadlet no genera el servicio**: revisa la sintaxis con `/usr/libexec/podman/quadlet -dryrun -user`.

#### Ampliación

Instala Docker en modo *rootless* para un segundo usuario y comprueba con `docker info` que aparece `rootless` en *Security Options*.

---

## Práctica 2.4 · Mi primer Dockerfile

{{< practica num="2.4" tipo="Guiada" duracion="2 h" nivel="1" ra="RA3: a, c" entorno="Docker Engine · BuildKit" entrega="no" >}}

#### Objetivo

Construir una imagen propia, entender la caché de capas y etiquetarla con un criterio de versiones.

#### Contexto

La oficina de turismo quiere publicar una web estática con información de la ciudad. Tienes que empaquetarla en una imagen.

#### Desarrollo

{{% steps %}}

1. **Prepara el contexto de construcción:**

    ```bash
    mkdir -p ~/ud02/turismo/html && cd ~/ud02/turismo
    cat > html/index.html <<'EOF'
    <!doctype html><html lang="es"><meta charset="utf-8">
    <title>Turismo Alicante</title><h1>Bienvenido a Alicante</h1>
    <p>Versión 1.0.0</p></html>
    EOF
    echo "secreto-que-no-debe-ir-en-la-imagen" > .env
    ```

2. **Escribe el Dockerfile:**

    ```dockerfile
    # syntax=docker/dockerfile:1
    FROM nginx:1.29-alpine
    LABEL org.opencontainers.image.title="turismo" \
          org.opencontainers.image.version="1.0.0" \
          org.opencontainers.image.authors="Nombre Apellidos"
    COPY html/ /usr/share/nginx/html/
    EXPOSE 80
    HEALTHCHECK --interval=10s --timeout=2s CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
    ```

3. **Construye y prueba:**

    ```bash
    docker build -t turismo:1.0.0 .
    docker run -d --name turismo -p 8080:80 turismo:1.0.0
    curl -s localhost:8080
    docker ps --filter name=turismo     # (healthy) tras unos segundos
    ```

4. **¿Qué se ha metido en la imagen?** El `.env` no debería estar, pero el contexto entero se envió al constructor. Crea `.dockerignore`:

    ```text
    .env
    .git
    *.md
    ```

    Reconstruye y fíjate en el tamaño del contexto que muestra BuildKit (`transferring context`).

5. **La caché.** Reconstruye sin cambios (todo `CACHED`). Cambia el HTML a «Versión 1.1.0» y reconstruye: solo se rehace `COPY`.

    ```bash
    sed -i 's/1.0.0/1.1.0/' html/index.html
    docker build -t turismo:1.1.0 .
    docker history turismo:1.1.0
    ```

6. **Etiquetas semánticas** para la misma imagen:

    ```bash
    docker tag turismo:1.1.0 turismo:1.1
    docker tag turismo:1.1.0 turismo:1
    docker images turismo        # mismas IMAGE ID
    docker image inspect turismo:1.1.0 --format '{{.Id}}'
    ```

7. **Ver la diferencia entre forma shell y exec.** Crea `Dockerfile.shell` con `CMD nginx -g "daemon off;"` en lugar del `CMD` heredado, constrúyelo y mide `time docker stop` en los dos casos.

{{% /steps %}}

#### Comprobación

- [ ] El contenedor aparece `(healthy)`.
- [ ] `docker run --rm turismo:1.1.0 ls -a /usr/share/nginx/html` no muestra `.env`.
- [ ] `turismo:1.1.0`, `turismo:1.1` y `turismo:1` tienen el mismo ID.
- [ ] El contenedor con la forma *shell* tarda ≈10 s en pararse y el original menos de 1 s.

#### Errores habituales

- **`COPY failed: file not found in build context`**: la ruta es relativa al **contexto** (el `.` final de `docker build`), no al Dockerfile.
- Olvidar el punto final de `docker build -t nombre .`.

#### Ampliación

Haz que la versión del HTML se pase con `ARG VERSION` y `--build-arg VERSION=1.2.0`, y que también se use en la etiqueta `org.opencontainers.image.version`.

---

## Práctica 2.5 · Imágenes pequeñas con multi-stage

{{< practica num="2.5" tipo="Guiada" duracion="2 h" nivel="2" ra="RA3: a, b" entorno="Docker Engine · BuildKit · Go 1.25 · Python 3.13" entrega="ud02/p2.5/ con los Dockerfile y la tabla de tamaños" >}}

#### Objetivo

Reducir el tamaño y la superficie de ataque de una imagen separando construcción y ejecución.

#### Desarrollo

{{% steps %}}

1. **Una aplicación compilada.** Crea `~/ud02/saludo/main.go`:

    ```go
    package main

    import (
        "fmt"
        "net/http"
        "os"
    )

    func main() {
        http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
            h, _ := os.Hostname()
            fmt.Fprintf(w, "Hola desde %s\n", h)
        })
        http.ListenAndServe(":8080", nil)
    }
    ```

    ```bash
    cd ~/ud02/saludo
    docker run --rm -v "$PWD":/src -w /src golang:1.25 go mod init saludo
    ```

2. **Versión ingenua** (`Dockerfile.grande`):

    ```dockerfile
    FROM golang:1.25
    WORKDIR /src
    COPY . .
    RUN go build -o /saludo .
    CMD ["/saludo"]
    ```

3. **Versión *multi-stage*** (`Dockerfile`):

    ```dockerfile
    # syntax=docker/dockerfile:1
    FROM golang:1.25 AS build
    WORKDIR /src
    COPY go.mod ./
    RUN go mod download
    COPY . .
    RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /saludo .

    FROM gcr.io/distroless/static-debian12:nonroot
    COPY --from=build /saludo /saludo
    EXPOSE 8080
    USER nonroot
    ENTRYPOINT ["/saludo"]
    ```

4. **Construye y compara:**

    ```bash
    docker build -f Dockerfile.grande -t saludo:grande .
    docker build -t saludo:1.0.0 .
    docker images saludo
    docker run -d --name saludo -p 8085:8080 saludo:1.0.0 && curl localhost:8085
    docker exec saludo sh || echo "No hay shell en la imagen: menos superficie de ataque"
    ```

5. **Ahora con Python: la API de MiTienda.** Descarga los ficheros de `api/` ([entorno](/guia/entorno/#5-recursos-del-proyecto)) y estudia su Dockerfile:

    {{< descarga "recursos/mitienda/api/Dockerfile" >}}

    Construye la versión *multi-stage* y una versión de una sola etapa a partir de `python:3.13` (no *slim*) y compara tamaños.

6. **Caché de dependencias con BuildKit.** Cambia la línea `pip install` por:

    ```dockerfile
    RUN --mount=type=cache,target=/root/.cache/pip pip install --prefix=/install -r requirements.txt
    ```

    Cambia una versión en `requirements.txt` y mide el tiempo de reconstrucción con y sin el montaje de caché.

7. **Analiza las capas** con `docker history --no-trunc saludo:1.0.0` y, si quieres, con la herramienta `dive` (`docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive saludo:grande`).

{{% /steps %}}

#### Comprobación

Tabla en `ud02/p2.5/README.md`:

| Imagen | Tamaño | ¿Tiene shell? | ¿Tiene compilador? | Usuario |
|---|--:|:-:|:-:|---|
| `saludo:grande` | | | | |
| `saludo:1.0.0` | | | | |
| `mitienda-api` (1 etapa) | | | | |
| `mitienda-api:1.0.0` (*multi-stage*) | | | | |

- [ ] La imagen final de Go ocupa menos de 15 MB y se ejecuta como `nonroot`.

#### Errores habituales

- **`exec /saludo: no such file or directory`** en *distroless/static*: el binario se compiló enlazado dinámicamente. Falta `CGO_ENABLED=0`.
- `COPY --from=build` con un nombre de etapa distinto al de `AS`.

#### Ampliación

Construye la imagen para `linux/arm64` además de `linux/amd64` con `docker buildx build --platform ...` y un *builder* `docker-container`.

---

## Práctica 2.6 · Registro privado con TLS y autenticación

{{< practica num="2.6" tipo="Guiada" duracion="2 h" nivel="2" ra="RA3: c, d, e" entorno="Docker Engine · registry:3 · OpenSSL · htpasswd" entrega="no" >}}

#### Objetivo

Publicar imágenes en Docker Hub y montar un registro privado con TLS y usuario/contraseña para la empresa.

#### Desarrollo

{{% steps %}}

1. **Docker Hub.** Crea una cuenta (si no la tienes), inicia sesión y publica `turismo`:

    ```bash
    docker login
    docker tag turismo:1.1.0 <tu-usuario>/turismo:1.1.0
    docker push <tu-usuario>/turismo:1.1.0
    docker rmi <tu-usuario>/turismo:1.1.0 && docker pull <tu-usuario>/turismo:1.1.0
    ```

    Anota el *digest* que muestra `push`: es el mismo que verás al hacer `pull`.

2. **Certificado para `registro.local`** (en el laboratorio, autofirmado):

    ```bash
    sudo mkdir -p /srv/registro/{certs,auth,datos}
    sudo openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
      -keyout /srv/registro/certs/registro.key -out /srv/registro/certs/registro.crt \
      -subj "/CN=registro.local" -addext "subjectAltName=DNS:registro.local,IP:192.168.56.10"
    ```

3. **Usuario y contraseña** (bcrypt, formato que exige el registro):

    ```bash
    sudo apt install -y apache2-utils
    sudo htpasswd -Bbn alumno 'Registro_2026' | sudo tee /srv/registro/auth/htpasswd
    ```

4. **Arranca el registro:**

    ```bash
    docker run -d --name registro --restart unless-stopped -p 5000:5000 \
      -v /srv/registro/datos:/var/lib/registry \
      -v /srv/registro/certs:/certs:ro -v /srv/registro/auth:/auth:ro \
      -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/registro.crt \
      -e REGISTRY_HTTP_TLS_KEY=/certs/registro.key \
      -e REGISTRY_AUTH=htpasswd -e REGISTRY_AUTH_HTPASSWD_REALM="Registro del curso" \
      -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
      registry:3
    ```

5. **Confía en el certificado** (Docker busca certificados por registro):

    ```bash
    sudo mkdir -p /etc/docker/certs.d/registro.local:5000
    sudo cp /srv/registro/certs/registro.crt /etc/docker/certs.d/registro.local:5000/ca.crt
    ```

6. **Publica y consulta:**

    ```bash
    docker login registro.local:5000
    docker tag saludo:1.0.0 registro.local:5000/curso/saludo:1.0.0
    docker push registro.local:5000/curso/saludo:1.0.0
    curl -s --cacert /srv/registro/certs/registro.crt -u alumno:'Registro_2026' \
      https://registro.local:5000/v2/_catalog
    curl -s --cacert /srv/registro/certs/registro.crt -u alumno:'Registro_2026' \
      https://registro.local:5000/v2/curso/saludo/tags/list
    ```

7. **Comprueba la seguridad:** sin `docker login`, el `pull` falla (`docker logout registro.local:5000` y prueba). Sin el certificado instalado, falla con `x509: certificate signed by unknown authority`.

{{% /steps %}}

#### Comprobación

- [ ] `/v2/_catalog` lista `curso/saludo`.
- [ ] Un `pull` sin credenciales devuelve `unauthorized`.
- [ ] El registro sobrevive a `docker rm -f registro` y se vuelve a crear con las mismas imágenes (están en `/srv/registro/datos`).

#### Errores habituales

- **`http: server gave HTTP response to HTTPS client`**: el registro no tiene TLS configurado (revisa las variables) o falta `https`.
- **`no basic auth credentials`**: no has hecho `docker login` contra ese registro concreto (con puerto).
- Usar `insecure-registries` en lugar de TLS: solo vale para pruebas y no lo acepta Kubernetes sin configuración extra.

#### Ampliación

Instala **Harbor** con su instalador *online* en una VM aparte (4 GB de RAM) y activa el escaneo automático de imágenes con Trivy. Compara funciones con `registry:3`.

---

## Práctica 2.7 · Primera aplicación con Docker Compose

{{< practica num="2.7" tipo="Guiada" duracion="1,5 h" nivel="1" ra="RA3: f, g" entorno="Docker Compose · WordPress · MariaDB" entrega="no" >}}

#### Objetivo

Desplegar una aplicación de dos servicios con Compose, con variables en `.env`, volumen persistente y orden de arranque correcto.

#### Desarrollo

{{% steps %}}

1. **Estructura:**

    ```bash
    mkdir -p ~/ud02/blog && cd ~/ud02/blog
    cat > .env <<'EOF'
    DB_NOMBRE=blog
    DB_USUARIO=wp
    DB_CLAVE=Wp_Curso_2026
    DB_ROOT=Root_Curso_2026
    PUERTO=8088
    EOF
    ```

2. **`compose.yaml`:**

    ```yaml
    name: blog
    services:
      db:
        image: mariadb:11.8
        environment:
          MARIADB_DATABASE: ${DB_NOMBRE}
          MARIADB_USER: ${DB_USUARIO}
          MARIADB_PASSWORD: ${DB_CLAVE}
          MARIADB_ROOT_PASSWORD: ${DB_ROOT}
        volumes:
          - datos-db:/var/lib/mysql
        healthcheck:
          test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
          interval: 5s
          retries: 10
        restart: unless-stopped

      wordpress:
        image: wordpress:6-apache
        depends_on:
          db:
            condition: service_healthy
        ports:
          - "${PUERTO:-8080}:80"
        environment:
          WORDPRESS_DB_HOST: db
          WORDPRESS_DB_NAME: ${DB_NOMBRE}
          WORDPRESS_DB_USER: ${DB_USUARIO}
          WORDPRESS_DB_PASSWORD: ${DB_CLAVE}
        volumes:
          - datos-wp:/var/www/html
        restart: unless-stopped

    volumes:
      datos-db:
      datos-wp:
    ```

3. **Valida y arranca:**

    ```bash
    docker compose config        # variables sustituidas
    docker compose up -d
    docker compose ps
    docker compose logs -f wordpress   # Ctrl+C para salir
    ```

4. Abre `http://ct-lab:8088` en el navegador del anfitrión, instala WordPress y publica una entrada.

5. **Persistencia:** `docker compose down` y `docker compose up -d`: la entrada sigue ahí. ¿Qué pasaría con `down -v`?

6. **Recursos creados por Compose:**

    ```bash
    docker network ls | grep blog
    docker volume ls | grep blog
    docker compose exec wordpress getent hosts db     # resolución DNS por nombre de servicio
    ```

{{% /steps %}}

#### Comprobación

- [ ] `docker compose ps` muestra `db` como `healthy` antes de que arranque `wordpress`.
- [ ] La entrada publicada sobrevive a `down` + `up`.
- [ ] Desde `wordpress` se resuelve `db` a la IP del contenedor de MariaDB.

#### Errores habituales

- **`Error establishing a database connection`**: WordPress arrancó antes de que MariaDB estuviera lista (falta la condición) o las variables no coinciden.
- Cambiar la contraseña en `.env` después de crear el volumen: MariaDB solo la aplica **la primera vez**. Hay que cambiarla dentro de la base de datos o empezar de cero con `down -v`.

#### Ampliación

Añade un servicio `adminer` solo en el perfil `admin` (`profiles: [admin]`) y arráncalo con `docker compose --profile admin up -d`.

---

## Práctica 2.8 · MiTienda con Docker Compose

{{< practica num="2.8" tipo="Proyecto" duracion="3 h" nivel="3" ra="RA3: a-h · RA2: d, e" entorno="Docker Engine · Compose · registry:3" entrega="mitienda/ (compose.yaml, Dockerfiles, README.md, evidencias/) · Hito H2" >}}

#### Objetivo

Contenerizar la aplicación del proyecto completa: construir las imágenes, publicarlas en el registro privado y desplegarla con Compose con secretos, redes separadas, límites y comprobación de fallos.

#### Requisitos

Prácticas 2.4 a 2.7 y el registro privado de la 2.6 en marcha. Código del proyecto descargado ([entorno](/guia/entorno/#5-recursos-del-proyecto)).

{{< descarga "recursos/mitienda/compose.yaml" >}}

#### Desarrollo

{{% steps %}}

1. **Secreto de la base de datos** (fuera de Git):

    ```bash
    cd ~/curso/mitienda
    mkdir -p secrets && openssl rand -base64 24 > secrets/db_password.txt
    chmod 700 secrets && chmod 644 secrets/db_password.txt
    printf 'secrets/\n.env\n' > .gitignore
    ```

    > [!NOTE]
    > El fichero se monta tal cual en el contenedor y los procesos de `db` (UID 70) y `api` (UID 10001) no son tu usuario: deben poder leerlo. Lo protege la carpeta `secrets/` con permisos `700`.

2. **Construye y arranca:**

    ```bash
    docker compose build
    docker compose up -d
    docker compose ps
    curl -s localhost:8080/api/salud | jq
    curl -s localhost:8080/api/productos | jq '.[0]'
    ```

    Abre `http://ct-lab:8080` en el navegador y compra un producto.

3. **Comprueba el diseño de red.** La base de datos no debe ser accesible desde `web` ni tener salida a Internet:

    ```bash
    docker compose exec web wget -qO- -T 2 http://api:8000/api/info        # funciona
    docker compose exec web sh -c 'nc -zv -w 2 db 5432' || echo "web no llega a db: correcto"
    docker compose exec cache sh -c 'wget -qO- -T 3 http://example.com' || echo "datos sin Internet: correcto"
    ```

4. **El secreto no aparece en `inspect`:**

    ```bash
    docker inspect mitienda-api-1 --format '{{json .Config.Env}}' | jq
    docker compose exec api cat /run/secrets/db_password | wc -c
    ```

5. **Escalado y balanceo:**

    ```bash
    docker compose up -d --scale api=3
    for i in $(seq 6); do curl -s localhost:8080/api/info | jq -r .contenedor; done
    ```

    > [!NOTE]
    > nginx resuelve `api` al arrancar y reparte entre las IP que obtiene. Si escalas con `web` ya en marcha, reinícialo: `docker compose restart web`.

6. **Prueba de fallo.** Mata la API y la base de datos y observa la recuperación:

    ```bash
    docker kill mitienda-api-1
    docker compose ps                         # vuelve a arrancar por la política de reinicio
    docker compose stop db
    curl -s -o /dev/null -w '%{http_code}\n' localhost:8080/api/salud   # 503
    docker compose start db ; sleep 5
    curl -s localhost:8080/api/salud | jq     # vuelve a «ok»
    ```

7. **Persistencia.** `docker compose down` + `up -d`: los productos comprados siguen descontados del stock. Explica por qué el contador de visitas también se conserva (pista: `--appendonly yes` y el volumen `datos-cache`).

8. **Publica las imágenes en el registro privado** con etiquetas semánticas y cambia el `compose.yaml` para usar `image: registro.local:5000/mitienda/api:1.0.0` (y lo mismo para `web`):

    ```bash
    for s in api web; do
      docker tag mitienda-$s:1.0.0 registro.local:5000/mitienda/$s:1.0.0
      docker push registro.local:5000/mitienda/$s:1.0.0
    done
    ```

9. **Documenta** en `README.md`: requisitos, cómo crear el secreto, cómo desplegar, cómo verificar y cómo volver atrás.

{{% /steps %}}

#### Comprobación

- [ ] `/api/salud` devuelve `{"api":"ok","cache":"ok","db":"ok"}`.
- [ ] `web` no llega a `db` y `cache` no tiene salida a Internet.
- [ ] La contraseña no aparece en `docker inspect`.
- [ ] Con 3 réplicas, `/api/info` muestra al menos dos contenedores distintos.
- [ ] Evidencias de la prueba de fallo: 503 con `db` parada y recuperación al arrancarla.
- [ ] Las dos imágenes están en el registro privado (`/v2/_catalog`).

#### Errores habituales

- **`api` reinicia en bucle con `connection refused`**: la base de datos no está lista; revisa el *healthcheck* de `db`.
- **`db` no ejecuta `init.sql`**: el volumen ya existía de un arranque anterior. Los scripts de inicio solo se ejecutan con el directorio de datos vacío.
- **`secret db_password: file not found`**: la ruta del secreto es relativa a la carpeta del `compose.yaml`.

#### Ampliación

Añade un `compose.override.yaml` para desarrollo que monte `./api/app.py` dentro del contenedor y arranque Flask con recarga automática, sin tocar el fichero principal.

---

## Práctica 2.9 · Depurar un Compose roto

{{< practica num="2.9" tipo="Reto" duracion="1,5 h" nivel="3" ra="RA2: e · RA3: f, h" entorno="Docker Compose" entrega="Fichero corregido + informe con cada error, cómo lo detectaste y cómo lo corregiste" >}}

#### Enunciado

Un compañero ha preparado este `compose.yaml` para una tienda y «no funciona». Hay **ocho errores** (de sintaxis, de diseño y de seguridad). Encuéntralos usando las herramientas de la unidad (`compose config`, `ps -a`, `logs`, `inspect`, `exec`) y corrígelos.

```yaml
version: "2"
services:
  web:
    image: nginx:latest
    ports:
      - 80:8080
    depends_on: [api]
  api:
    image: python:3.13
    command: python -m http.server 8000
    environment:
      - DB_PASSWORD=SuperSecreta123
      - DB_HOST=database
    network: interna
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: tienda
    volumes:
      - /var/lib/postgresql/data
    restart: always
    privileged: true
networks:
  interna:
```

#### Comprobación

- [ ] La aplicación arranca con `docker compose up -d` y todos los servicios quedan en marcha.
- [ ] El informe explica, para cada error, el síntoma, la orden con la que lo detectaste y la corrección.
- [ ] Ninguna contraseña queda en el fichero ni en `docker inspect`.

#### Defensa

La profesora introducirá un error nuevo en tu fichero corregido y tendrás 10 minutos para encontrarlo.
