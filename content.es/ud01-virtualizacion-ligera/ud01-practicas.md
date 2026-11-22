---
title: "UD01 · Prácticas"
weight: 2
bookToc: true
---

# UD01 · Prácticas

{{< ra "RA1:a,b,c,d,e,f,g" "RA2:f" >}}

En estas prácticas **desmontas un contenedor** pieza a pieza: lo comparas con una VM, creas namespaces y cgroups a mano, montas capas con OverlayFS y terminas construyendo tu propio contenedor sin ningún motor.

| Práctica | Tipo | Nivel | Horas | CE principales |
|---|---|---|--:|---|
| [1.1 Máquina virtual frente a contenedor](#práctica-11--máquina-virtual-frente-a-contenedor) | Guiada | ●○○ | 1,5 | RA1: a, f |
| [1.2 Namespaces a mano](#práctica-12--namespaces-a-mano) | Guiada | ●●○ | 2 | RA1: b |
| [1.3 Limitar recursos con cgroups v2](#práctica-13--limitar-recursos-con-cgroups-v2) | Guiada | ●●○ | 2 | RA1: c |
| [1.4 Capas y copia en escritura con OverlayFS](#práctica-14--capas-y-copia-en-escritura-con-overlayfs) | Guiada | ●●○ | 1,5 | RA1: d |
| [1.5 Un contenedor artesanal](#práctica-15--un-contenedor-artesanal) | Reto | ●●● | 2 | RA1: b, c, d, g |
| [1.6 Informe: ¿VM o contenedor?](#práctica-16--informe-vm-o-contenedor) | Autónoma | ●○○ | 0,5 | RA1: e, f |
| [Tarea del proyecto · Análisis de MiTienda](#tarea-del-proyecto--análisis-de-mitienda) | Proyecto | ●●○ | 0,5 | RA1: f |
| **Total** | | | **10 h** | |

## Preparación

Trabaja en la máquina `ct-lab` ([entorno](/guia/entorno/)). En esta unidad todavía no instalamos Docker: para tener contenedores con los que comparar usamos **Podman**, que está en los repositorios de Debian y no necesita demonio.

```bash
sudo apt install -y podman util-linux procps psmisc stress-ng debootstrap
podman --version
mkdir -p ~/ud01/evidencias && cd ~/ud01
```

> [!TIP]
> Haz la instantánea **«ud01-inicio»** antes de empezar. Algunas órdenes de esta unidad (cgroups, montajes) se ejecutan como `root`: si algo queda raro, vuelves atrás.

---

## Práctica 1.1 · Máquina virtual frente a contenedor

{{< practica num="1.1" tipo="Guiada" duracion="1,5 h" nivel="1" ra="RA1: a, f" entorno="VirtualBox 7 · Debian 13 · Podman" entrega="no" >}}

#### Objetivo

Medir con datos reales la diferencia de tiempo de arranque, memoria y disco entre una máquina virtual y un contenedor.

#### Contexto

Tu jefa duda entre comprar más servidores para virtualizar o pasar a contenedores. Te pide números, no opiniones.

#### Desarrollo

{{% steps %}}

1. **Arranque de una VM.** En tu equipo anfitrión, cronometra el arranque de `k8s-w2` (o de cualquier VM Debian) desde que la enciendes hasta que puedes entrar por SSH. Anota los segundos y la memoria asignada.

2. **Arranque de un contenedor.** En `ct-lab`, descarga primero la imagen (la descarga no cuenta) y mide el arranque:

    ```bash
    podman pull docker.io/library/debian:trixie-slim
    time podman run --rm debian:trixie-slim echo "hola desde el contenedor"
    ```

3. **El núcleo es el mismo.** Compara la versión del núcleo dentro y fuera:

    ```bash
    uname -r
    podman run --rm debian:trixie-slim uname -r
    podman run --rm docker.io/library/alpine:3.22 uname -r
    ```

    Las tres líneas coinciden: Debian y Alpine «son» distintas distribuciones solo en el espacio de usuario.

4. **Memoria.** Arranca un servidor web y mide cuánto consume:

    ```bash
    podman run -d --name web docker.io/library/nginx:alpine
    podman stats --no-stream web
    free -m
    ```

5. **Disco.** Compara el tamaño de las imágenes con el disco de la VM:

    ```bash
    podman images
    du -sh ~/.local/share/containers/storage
    ```

6. **El proceso se ve desde fuera.** Busca nginx en la lista de procesos del anfitrión y compara con lo que se ve dentro:

    ```bash
    ps -ef | grep "nginx: master" | grep -v grep
    podman exec web ps
    podman rm -f web
    ```

{{% /steps %}}

#### Comprobación

- [ ] Tabla con tiempo de arranque, memoria y disco para la VM y para el contenedor.
- [ ] El núcleo coincide dentro y fuera del contenedor.
- [ ] El proceso nginx aparece en el anfitrión con un PID alto y dentro del contenedor con PID 1.

#### Errores habituales

- **`Error: short-name resolution`**: Podman no sabe en qué registro buscar un nombre corto. Escribe el nombre completo (`docker.io/library/nginx:alpine`) o añade `unqualified-search-registries = ["docker.io"]` en `/etc/containers/registries.conf`.
- Medir el arranque **con la descarga** de la imagen incluida: ejecuta antes `podman pull`.

#### Ampliación

Arranca 20 contenedores nginx con un bucle `for` y mide la memoria total. ¿Cuántas VM de 512 MB cabrían en esa misma memoria?

---

## Práctica 1.2 · Namespaces a mano

{{< practica num="1.2" tipo="Guiada" duracion="2 h" nivel="2" ra="RA1: b" entorno="Debian 13 · util-linux (unshare, nsenter, lsns) · iproute2" entrega="no" >}}

#### Objetivo

Crear namespaces de PID, UTS, montaje y red con las herramientas del sistema y entrar en ellos como hace `docker exec`.

#### Desarrollo

{{% steps %}}

1. **Tus namespaces actuales.** Anota los identificadores:

    ```bash
    ls -l /proc/$$/ns
    lsns | head -20
    ```

2. **Namespace UTS (nombre de host).**

    ```bash
    sudo unshare --uts bash
    hostname caja-aislada
    hostname           # caja-aislada
    exit
    hostname           # el nombre original no ha cambiado
    ```

3. **Namespace PID con `/proc` propio.**

    ```bash
    sudo unshare --pid --fork --mount-proc bash
    echo $$            # 1
    ps -ef             # solo bash y ps
    sleep 1000 &
    ```

    Abre **otra terminal** (deja la primera abierta) y busca ese `sleep` desde el anfitrión:

    ```bash
    ps -ef | grep "sleep 1000" | grep -v grep
    sudo lsns -t pid
    ```

    Desde fuera tiene un PID normal; desde dentro tiene un PID pequeño.

4. **Entrar en el namespace como `docker exec`.** En la segunda terminal, con el PID del `bash` aislado (el padre del `sleep`):

    ```bash
    PID=$(pgrep -f "unshare --pid" | head -1)
    PID_BASH=$(pgrep -P "$PID" bash)
    sudo nsenter --target "$PID_BASH" --pid --mount ps -ef
    ```

    Ves exactamente los mismos procesos que dentro. Sal de la primera terminal con `exit`.

5. **Namespace de red.** Crea uno con nombre y conéctalo al anfitrión con un par de interfaces virtuales (`veth`):

    ```bash
    sudo ip netns add cajared
    sudo ip netns exec cajared ip link          # solo «lo», y apagada
    sudo ip link add veth-host type veth peer name veth-caja
    sudo ip link set veth-caja netns cajared
    sudo ip addr add 10.99.0.1/24 dev veth-host
    sudo ip link set veth-host up
    sudo ip netns exec cajared ip addr add 10.99.0.2/24 dev veth-caja
    sudo ip netns exec cajared ip link set veth-caja up
    sudo ip netns exec cajared ip link set lo up
    ping -c 2 10.99.0.2
    sudo ip netns exec cajared ping -c 2 10.99.0.1
    ```

    Así es, en esencia, como Docker conecta cada contenedor al puente `docker0` (UD04).

6. **Namespace de usuario sin `sudo`.** Como usuario normal:

    ```bash
    unshare --user --map-root-user bash
    id                 # uid=0(root) dentro
    touch /etc/prueba  # Permiso denegado: fuera sigues siendo tú
    exit
    ```

7. **Limpieza.**

    ```bash
    sudo ip netns del cajared
    sudo ip link del veth-host 2>/dev/null || true
    ```

{{% /steps %}}

#### Comprobación

- [ ] Captura de `ps -ef` dentro del namespace PID mostrando `bash` con PID 1.
- [ ] Ping correcto en los dos sentidos entre el anfitrión y `cajared`.
- [ ] `id` muestra `uid=0` dentro del namespace de usuario y, aun así, no puedes escribir en `/etc`.

#### Errores habituales

- **`ps` muestra todos los procesos**: falta `--mount-proc` o `--fork`.
- **`unshare: unshare failed: Operation not permitted`** con `--user`: comprueba que `sysctl kernel.unprivileged_userns_clone` vale `1` (en Debian 13 está activado por defecto).
- **El ping no responde**: alguna interfaz está en estado `DOWN`. Revisa `ip -br link` en los dos lados.

#### Ampliación

Da salida a Internet al namespace `cajared`: ruta por defecto hacia `10.99.0.1`, `net.ipv4.ip_forward=1` y una regla de NAT con `nft`. Es lo que hace Docker con cada red *bridge*.

---

## Práctica 1.3 · Limitar recursos con cgroups v2

{{< practica num="1.3" tipo="Guiada" duracion="2 h" nivel="2" ra="RA1: c" entorno="Debian 13 · cgroups v2 · stress-ng · Podman" entrega="no" >}}

#### Objetivo

Crear un cgroup, limitar la memoria, la CPU y el número de procesos, y comprobar cómo Podman escribe esos mismos ficheros.

#### Desarrollo

{{% steps %}}

1. **Comprueba que usas cgroups v2.**

    ```bash
    stat -fc %T /sys/fs/cgroup        # cgroup2fs
    cat /sys/fs/cgroup/cgroup.controllers
    ```

2. **Crea un cgroup y activa los controladores.** Como `root`:

    ```bash
    sudo -i
    echo "+memory +cpu +pids" > /sys/fs/cgroup/cgroup.subtree_control
    mkdir /sys/fs/cgroup/curso
    ls /sys/fs/cgroup/curso
    ```

3. **Límite de memoria.** 100 MB y sin *swap*:

    ```bash
    echo 100M > /sys/fs/cgroup/curso/memory.max
    echo 0    > /sys/fs/cgroup/curso/memory.swap.max
    echo $$   > /sys/fs/cgroup/curso/cgroup.procs      # la shell entra en el cgroup
    stress-ng --vm 1 --vm-bytes 80M --timeout 10s      # funciona
    stress-ng --vm 1 --vm-bytes 300M --timeout 10s     # lo mata el OOM killer
    cat /sys/fs/cgroup/curso/memory.events             # oom_kill > 0
    ```

4. **Límite de CPU.** 20 % de un núcleo:

    ```bash
    echo "20000 100000" > /sys/fs/cgroup/curso/cpu.max
    stress-ng --cpu 1 --timeout 30s &
    top -b -n 1 | grep stress-ng       # ronda el 20 %
    ```

5. **Límite de procesos.** Protege contra una *fork bomb*:

    ```bash
    echo 20 > /sys/fs/cgroup/curso/pids.max
    for i in $(seq 1 30); do sleep 100 & done   # a partir del 20.º: «Resource temporarily unavailable»
    cat /sys/fs/cgroup/curso/pids.current
    kill $(jobs -p) ; exit
    ```

6. **La forma cómoda: systemd.** Como usuario normal:

    ```bash
    sudo systemd-run --scope -p MemoryMax=64M -p CPUQuota=30% -p TasksMax=10 bash
    cat /proc/self/cgroup
    systemctl status $(cat /proc/self/cgroup | cut -d/ -f3) --no-pager
    exit
    ```

7. **Lo mismo con un motor de contenedores.**

    ```bash
    podman run -d --name limitado --memory 128m --cpus 0.5 --pids-limit 50 \
      docker.io/library/nginx:alpine
    CG=$(podman inspect limitado --format '{{.State.CgroupPath}}')
    cat /sys/fs/cgroup${CG}/memory.max /sys/fs/cgroup${CG}/cpu.max /sys/fs/cgroup${CG}/pids.max
    podman rm -f limitado
    ```

    Verás `134217728`, `50000 100000` y `50`: Podman no hace magia, escribe en cgroups.

8. **Limpieza.** `sudo rmdir /sys/fs/cgroup/curso` (debe estar vacío de procesos).

{{% /steps %}}

#### Comprobación

- [ ] `memory.events` muestra al menos un `oom_kill`.
- [ ] `top` muestra el proceso de `stress-ng` limitado al 20 % aproximadamente.
- [ ] Los tres ficheros del cgroup de Podman contienen los valores esperados.

#### Errores habituales

- **`echo: write error: Device or resource busy`** al activar controladores: el cgroup raíz no admite procesos y controladores a la vez en algunos niveles. Crea el cgroup dentro de uno que no tenga procesos o usa `systemd-run`.
- **`rmdir: Device or resource busy`**: aún hay procesos en `cgroup.procs`. Sal de la shell o muévelos al cgroup padre.
- Si `State.CgroupPath` sale vacío, ejecuta Podman con `sudo` (en modo *rootless* algunos controladores se delegan a `user@.service`).

#### Ampliación

Limita la escritura a disco a 1 MB/s con `io.max` y compruébalo con `dd if=/dev/zero of=prueba bs=1M count=20 oflag=direct`.

---

## Práctica 1.4 · Capas y copia en escritura con OverlayFS

{{< practica num="1.4" tipo="Guiada" duracion="1,5 h" nivel="2" ra="RA1: d" entorno="Debian 13 · OverlayFS · Podman" entrega="no" >}}

#### Objetivo

Montar a mano un sistema de archivos en capas y observar la copia en escritura y los *whiteouts*; después, localizar las capas reales de una imagen.

#### Desarrollo

{{% steps %}}

1. **Prepara dos capas inferiores, una superior y un directorio de trabajo.**

    ```bash
    mkdir -p ~/ud01/overlay/{base,app,upper,work,merged}
    cd ~/ud01/overlay
    echo "versión 1 (base)" > base/config.txt
    echo "fichero de la base" > base/sistema.txt
    echo "código de la app"  > app/app.py
    ```

2. **Monta la unión.** `lowerdir` lista las capas de arriba abajo, separadas por `:`.

    ```bash
    sudo mount -t overlay overlay \
      -o lowerdir=app:base,upperdir=upper,workdir=work merged
    ls merged          # app.py config.txt sistema.txt
    ```

3. **Copia en escritura.** Modifica un fichero de la capa base a través de `merged`:

    ```bash
    echo "versión 2 (modificada)" | sudo tee merged/config.txt
    cat base/config.txt        # sigue en versión 1
    cat upper/config.txt       # versión 2: se copió y modificó aquí
    ```

4. **Borrado con *whiteout*.**

    ```bash
    sudo rm merged/sistema.txt
    ls -l upper                # c--------- sistema.txt  (dispositivo 0,0 = whiteout)
    ls base                    # el original sigue ahí
    ```

5. **Fichero nuevo.** `echo nuevo | sudo tee merged/datos.txt` y comprueba que solo aparece en `upper`.

6. **Desmonta y piensa.** `sudo umount merged`. Si borraras ahora `upper`, ¿qué se perdería? Eso es lo que pasa con `docker rm`.

7. **Las capas de una imagen real.** Con Podman como `root`:

    ```bash
    sudo podman pull docker.io/library/python:3.13-slim
    sudo podman image inspect python:3.13-slim --format '{{json .RootFS.Layers}}'
    sudo podman image tree python:3.13-slim
    sudo podman run -d --name capas docker.io/library/python:3.13-slim sleep 600
    sudo podman inspect capas --format '{{json .GraphDriver.Data}}' | tr ',' '\n'
    sudo podman exec capas sh -c 'echo hola > /tmp/nuevo.txt'
    sudo podman diff capas
    sudo podman rm -f capas
    ```

    `podman diff` muestra solo lo que ha cambiado en la capa escribible (`A` añadido, `C` cambiado, `D` borrado).

{{% /steps %}}

#### Comprobación

- [ ] `base/config.txt` no cambia aunque modifiques `merged/config.txt`.
- [ ] Aparece el *whiteout* de `sistema.txt` en `upper`.
- [ ] `podman diff` muestra `A /tmp/nuevo.txt`.

#### Errores habituales

- **`wrong fs type`**: `workdir` y `upperdir` deben estar en el mismo sistema de archivos y `workdir` vacío.
- Montar sin `sudo`: OverlayFS necesita privilegios (salvo dentro de un namespace de usuario).

#### Ampliación

Crea una cuarta capa encima de `app` que modifique `app.py` y comprueba qué versión se ve. ¿En qué orden busca OverlayFS?

---

## Práctica 1.5 · Un contenedor artesanal

{{< practica num="1.5" tipo="Reto" duracion="2 h" nivel="3" ra="RA1: b, c, d, g" entorno="Debian 13 · unshare · cgroups v2 · OverlayFS · chroot" entrega="contenedor.sh + evidencias de su ejecución (en el repositorio, carpeta ud01)" >}}

#### Objetivo

Integrar namespaces, cgroups y OverlayFS en un script que lance un «contenedor» sin ningún motor.

#### Enunciado

Escribe `contenedor.sh` que, ejecutado como `root`, haga lo siguiente:

1. Use como **capa base** el sistema de archivos de una imagen Alpine. Puedes obtenerlo con Podman (no se permite usarlo para ejecutar):

    ```bash
    mkdir -p /srv/capas/alpine
    podman export $(podman create docker.io/library/alpine:3.22) | tar -x -C /srv/capas/alpine
    ```

2. Monte con OverlayFS una **capa escribible propia** por cada ejecución (en `/srv/contenedores/<nombre>/`).
3. Cree un **cgroup** con 64 MB de memoria, 25 % de CPU y 30 procesos como máximo y meta en él el proceso.
4. Lance `/bin/sh` en namespaces nuevos de **PID, UTS, mount, IPC y red**, con `chroot` a la vista unida y `/proc` montado.
5. Ponga como nombre de host el nombre recibido como parámetro: `./contenedor.sh caja1`.
6. Al salir, desmonte, borre el cgroup y la capa escribible.

> [!TIP]
> Pistas: `unshare --pid --fork --uts --ipc --net --mount --mount-proc=<merged>/proc chroot <merged> /bin/sh`. Para meter el proceso en el cgroup, escribe `$$` en `cgroup.procs` **antes** de llamar a `unshare`: los hijos heredan el cgroup.

#### Comprobación

Ejecuta dentro del contenedor y guarda la salida:

```text
/ # hostname          → caja1
/ # ps                → sh con PID 1
/ # ip link           → solo lo
/ # cat /etc/os-release → Alpine Linux
/ # cat /sys/fs/cgroup/memory.max (si está montado) o compruébalo desde fuera
```

- [ ] Dos contenedores lanzados a la vez no ven los ficheros que crea el otro.
- [ ] Un `stress-ng`/bucle de memoria dentro termina por OOM.
- [ ] Al salir no quedan montajes (`mount | grep overlay`) ni cgroups.

#### Defensa

Explica qué le falta a tu script para ser Docker: imágenes, registro, red con salida, volúmenes, capacidades, seccomp…

---

## Práctica 1.6 · Informe: ¿VM o contenedor?

{{< practica num="1.6" tipo="Autónoma" duracion="0,5 h + trabajo fuera del aula" nivel="1" ra="RA1: e, f" entorno="—" entrega="ud01/p1.6-informe.md (máx. 2 páginas)" >}}

#### Enunciado

Para cada caso, decide **máquina virtual**, **contenedor** o **contenedor dentro de VM**, y justifica en 3-4 líneas con conceptos de la unidad (núcleo compartido, aislamiento, densidad, estado, OCI…):

1. Una academia quiere que cada alumno tenga su propio WordPress de pruebas durante un mes.
2. Un hospital tiene un programa de gestión de 2009 que solo funciona en Windows Server 2012.
3. Una *startup* despliega su API 15 veces al día y el tráfico se multiplica por 10 los domingos.
4. Un proveedor de alojamiento quiere vender «servidores» a clientes desconocidos que tendrán `root`.
5. El departamento de I+D necesita probar un módulo de núcleo nuevo para una tarjeta de red.
6. El ayuntamiento quiere modernizar **MiTienda** ([proyecto](/guia/proyecto-mitienda/)).

Añade una tabla final con los **componentes OCI** (motor, *runtime* de alto nivel, *runtime* de bajo nivel, formato de imagen, registro) que usarías en el caso 3.

#### Rúbrica

Decisión correcta y argumentada (60 %) · uso preciso del vocabulario (30 %) · presentación (10 %).

---

## Tarea del proyecto · Análisis de MiTienda

{{< practica num="P1" tipo="Proyecto" duracion="0,5 h" nivel="2" ra="RA1: f" entorno="—" entrega="mitienda/docs/01-analisis.md" >}}

#### Enunciado

Lee la descripción del [proyecto MiTienda](/guia/proyecto-mitienda/) y redacta el documento de análisis:

1. **Inventario de componentes**: para cada servicio, imagen base, puerto, si tiene estado y qué datos guarda.
2. **Dependencias**: qué servicio necesita a cuál y qué pasa si cae cada uno.
3. **Recursos estimados**: memoria y CPU de cada servicio (usa `podman stats` con las imágenes base como referencia).
4. **Riesgos de la instalación actual** (un solo servidor instalado a mano) y cómo los contenedores ayudan o no ayudan a resolverlos.
5. Un **diagrama** (Mermaid o draw.io) de la arquitectura objetivo.

#### Comprobación

- [ ] Se identifica que `db` es el único servicio cuyo estado es imprescindible.
- [ ] Se explica que contenerizar **no** resuelve por sí solo la pérdida del disco: hace falta almacenamiento persistente y copias (UD04).
