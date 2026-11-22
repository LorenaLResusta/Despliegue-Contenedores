---
title: "UD04 · Prácticas"
weight: 2
bookToc: true
---

# UD04 · Prácticas

{{< ra "RA5:a,b,c,d,e,f,g,h" "RA3:f" >}}

| Práctica | Tipo | Nivel | Horas | CE principales |
|---|---|---|--:|---|
| [4.1 Redes de Docker y DNS interno](#práctica-41--redes-de-docker-y-dns-interno) | Guiada | ●○○ | 2 | RA5: a, e |
| [4.2 Macvlan y overlay con Docker Swarm](#práctica-42--macvlan-y-overlay-con-docker-swarm) | Guiada | ●●● | 2 | RA5: a |
| [4.3 Volúmenes, bind mounts y copias de seguridad](#práctica-43--volúmenes-bind-mounts-y-copias-de-seguridad) | Guiada | ●○○ | 2 | RA5: f, h |
| [4.4 Services y LoadBalancer con MetalLB](#práctica-44--services-y-loadbalancer-con-metallb) | Guiada | ●●○ | 2 | RA5: b, c, e |
| [4.5 Gateway API con Traefik y HTTPS](#práctica-45--gateway-api-con-traefik-y-https) | Guiada | ●●○ | 2,5 | RA5: d |
| [4.6 Almacenamiento dinámico con StorageClasses y NFS](#práctica-46--almacenamiento-dinámico-con-storageclasses-y-nfs) | Guiada | ●●○ | 2 | RA5: f, g, h |
| [4.7 MiTienda expuesta y persistente](#práctica-47--mitienda-expuesta-y-persistente) | Proyecto | ●●● | 1,5 | RA5: c, d, g, h |
| **Total** | | | **14 h** | |

> [!NOTE]
> Las prácticas 4.1 a 4.3 son de Docker en `ct-lab`. La 4.5 se hace en **kind** (usa los puertos 80 y 443 que reservaste en la práctica 3.1). Las 4.4, 4.6 y 4.7 se hacen en el clúster **kubeadm** de la práctica 3.7, porque necesitan IP reales de la red del laboratorio y almacenamiento compartido entre nodos.

---

## Práctica 4.1 · Redes de Docker y DNS interno

{{< practica num="4.1" tipo="Guiada" duracion="2 h" nivel="1" ra="RA5: a, e" entorno="ct-lab · Docker Engine · iproute2 · nftables" entrega="no" >}}

#### Objetivo

Comparar la red *bridge* por defecto con las definidas por el usuario, usar el DNS interno, separar capas y entender cómo Docker publica puertos.

#### Desarrollo

{{% steps %}}

1. **Lo que ya existe:**

    ```bash
    docker network ls
    ip -br addr show docker0
    docker network inspect bridge --format '{{json .IPAM.Config}}'
    ```

2. **Bridge por defecto: sin DNS.**

    ```bash
    docker run -d --name a1 nginx:1.29-alpine
    docker run --rm alpine:3.22 ping -c 2 a1 || echo "No resuelve a1"
    IP=$(docker inspect a1 --format '{{.NetworkSettings.IPAddress}}')
    docker run --rm alpine:3.22 ping -c 2 "$IP"     # por IP sí
    ```

3. **Red definida por el usuario: con DNS.**

    ```bash
    docker network create --subnet 172.30.10.0/24 frontal
    docker run -d --name web --network frontal nginx:1.29-alpine
    docker run --rm --network frontal alpine:3.22 sh -c 'cat /etc/resolv.conf; ping -c 2 web'
    ```

    Fíjate en `nameserver 127.0.0.11`: es el DNS embebido de Docker.

4. **Alias y balanceo DNS sencillo:**

    ```bash
    docker run -d --name eco1 --network frontal --network-alias eco hashicorp/http-echo -text="soy eco1"
    docker run -d --name eco2 --network frontal --network-alias eco hashicorp/http-echo -text="soy eco2"
    docker run --rm --network frontal alpine:3.22 sh -c 'nslookup eco; for i in 1 2 3 4; do wget -qO- eco:5678; done'
    ```

5. **Separación en capas.** Una red interna sin salida a Internet y un contenedor «puente» en las dos:

    ```bash
    docker network create --internal datos
    docker run -d --name bd --network datos -e POSTGRES_PASSWORD=x postgres:17-alpine
    docker network connect datos web            # web en frontal y en datos
    docker exec web ping -c 1 bd                # web llega a bd
    docker run --rm --network frontal alpine:3.22 ping -c 1 -W 1 bd || echo "frontal no ve bd"
    docker exec bd wget -qO- -T 3 http://example.com || echo "datos sin Internet"
    ```

6. **Por dentro: veth, puente y NAT.**

    ```bash
    ip -br link | grep -E 'br-|veth'
    bridge link
    sudo nft list ruleset | grep -A3 -i 'dnat\|masquerade' | head -30
    ```

7. **Publicación de puertos y su IP.**

    ```bash
    docker run -d --name local -p 127.0.0.1:8081:80 nginx:1.29-alpine
    docker run -d --name todos -p 8082:80 nginx:1.29-alpine
    ss -tlnp | grep -E '8081|8082'
    ```

    Desde tu equipo anfitrión prueba `http://192.168.56.10:8081` (no responde) y `:8082` (responde).

8. **Red `host` y `none`:**

    ```bash
    docker run --rm --network host alpine:3.22 ip -br addr   # las interfaces del anfitrión
    docker run --rm --network none alpine:3.22 ip -br addr   # solo lo
    ```

9. **Limpieza:** `docker rm -f $(docker ps -aq); docker network prune -f`.

{{% /steps %}}

#### Comprobación

- [ ] `a1` no se resuelve en la *bridge* por defecto; `web` sí en `frontal`.
- [ ] `nslookup eco` devuelve dos IP y las respuestas alternan.
- [ ] `frontal` no llega a `bd`; `bd` no sale a Internet; `web` llega a `bd`.
- [ ] El puerto 8081 solo escucha en `127.0.0.1`.

#### Errores habituales

- **`Pool overlaps with other one on this address space`**: la subred elegida choca con otra red. Usa otra o revisa `default-address-pools`.
- **`ping: permission denied`** en algunas imágenes: el usuario del contenedor no tiene la capacidad `NET_RAW`. Usa `wget` o `nc`.

#### Ampliación

Añade en la cadena `DOCKER-USER` una regla `nftables` que solo permita acceder al puerto 8082 desde `192.168.56.1` (tu anfitrión).

---

## Práctica 4.2 · Macvlan y overlay con Docker Swarm

{{< practica num="4.2" tipo="Guiada" duracion="2 h" nivel="3" ra="RA5: a" entorno="ct-lab + ct-lab2 (clon enlazado) · Docker Engine · Swarm" entrega="no" >}}

#### Objetivo

Conectar un contenedor directamente a la red del laboratorio con macvlan, y conectar contenedores de dos anfitriones con una red overlay de Docker Swarm.

#### Requisitos

Un **clon enlazado** de `ct-lab` llamado `ct-lab2` con IP `192.168.56.14` (cambia también el nombre de host y regenera el identificador: `sudo rm /etc/machine-id && sudo systemd-machine-id-setup`). En VirtualBox, pon el adaptador 2 de `ct-lab` en **modo promiscuo: permitir todo** (necesario para macvlan).

#### Desarrollo

{{% steps %}}

1. **Macvlan en `ct-lab`.** El contenedor tendrá una IP de la red `192.168.56.0/24`:

    ```bash
    docker network create -d macvlan --subnet 192.168.56.0/24 --gateway 192.168.56.1 \
      --ip-range 192.168.56.240/29 -o parent=enp0s8 lan
    docker run -d --name enlan --network lan --ip 192.168.56.241 nginx:1.29-alpine
    ```

    Desde tu **equipo anfitrión** abre `http://192.168.56.241`: responde como si fuera otra máquina. Desde `ct-lab`, en cambio, **no** llega (limitación de macvlan: el anfitrión no ve a sus propios contenedores macvlan sin una interfaz macvlan adicional).

2. **Swarm de dos nodos.** En `ct-lab`:

    ```bash
    docker swarm init --advertise-addr 192.168.56.10
    ```

    Copia la orden `docker swarm join ...` y ejecútala en `ct-lab2`. De vuelta en `ct-lab`:

    ```bash
    docker node ls
    ```

3. **Red overlay y servicio replicado:**

    ```bash
    docker network create -d overlay --attachable global
    docker service create --name eco --replicas 4 --network global -p 8090:5678 \
      hashicorp/http-echo -text="hola desde Swarm"
    docker service ps eco          # réplicas en los dos nodos
    ```

4. **Comunicación entre nodos por la overlay:**

    ```bash
    docker run --rm --network global alpine:3.22 sh -c 'nslookup eco; nslookup tasks.eco'
    ```

    `eco` resuelve a una **IP virtual** (balanceada) y `tasks.eco` a las IP de cada réplica, estén en el nodo que estén.

5. **Malla de enrutado:** `curl 192.168.56.14:8090` responde aunque preguntes al nodo que no tenga réplicas. Compruébalo con `docker service scale eco=1`.

6. **Prueba de fallo:** apaga `ct-lab2` y mira cómo Swarm recrea sus réplicas en `ct-lab` (`docker service ps eco`).

7. **Limpieza:** `docker service rm eco`, `docker swarm leave` en `ct-lab2`, `docker swarm leave --force` en `ct-lab`, `docker network rm lan`.

{{% /steps %}}

#### Comprobación

- [ ] El contenedor macvlan responde desde el anfitrión en `192.168.56.241`.
- [ ] `docker service ps eco` muestra réplicas en ambos nodos.
- [ ] `tasks.eco` devuelve cuatro IP de la red overlay.
- [ ] Al apagar `ct-lab2`, las réplicas se recrean en `ct-lab`.

#### Errores habituales

- **Macvlan sin respuesta**: falta el modo promiscuo en VirtualBox o `parent` no es la interfaz correcta.
- **El nodo no se une al Swarm**: puertos TCP 2377, TCP/UDP 7946 y UDP 4789 bloqueados entre las VM.

#### Ampliación

Despliega MiTienda en el Swarm con `docker stack deploy -c compose.yaml producto` (las imágenes deben estar en el registro privado). ¿Qué partes del `compose.yaml` ignora Swarm y cuáles usa (`deploy:`)?

---

## Práctica 4.3 · Volúmenes, bind mounts y copias de seguridad

{{< practica num="4.3" tipo="Guiada" duracion="2 h" nivel="1" ra="RA5: f, h" entorno="ct-lab · Docker Engine · PostgreSQL 17" entrega="no" >}}

#### Objetivo

Elegir el tipo de almacenamiento adecuado en Docker, comprobar la persistencia y hacer y restaurar copias de seguridad.

#### Desarrollo

{{% steps %}}

1. **Sin volumen, los datos se pierden:**

    ```bash
    docker run -d --name efimera -e POSTGRES_PASSWORD=x postgres:17-alpine
    sleep 5 ; docker exec efimera psql -U postgres -c "CREATE TABLE t(x int); INSERT INTO t VALUES (1);"
    docker rm -f efimera
    docker run -d --name efimera -e POSTGRES_PASSWORD=x postgres:17-alpine
    sleep 5 ; docker exec efimera psql -U postgres -c "SELECT * FROM t;"   # no existe
    docker rm -f efimera
    docker volume ls          # ¡un volumen anónimo por cada ejecución! (lo declara la imagen)
    docker volume prune -f
    ```

2. **Volumen con nombre:**

    ```bash
    docker volume create pgdatos
    docker run -d --name pg -e POSTGRES_PASSWORD=x -v pgdatos:/var/lib/postgresql/data postgres:17-alpine
    sleep 5 ; docker exec pg psql -U postgres -c "CREATE TABLE t(x int); INSERT INTO t VALUES (42);"
    docker rm -f pg
    docker run -d --name pg -e POSTGRES_PASSWORD=x -v pgdatos:/var/lib/postgresql/data postgres:17-alpine
    sleep 5 ; docker exec pg psql -U postgres -c "SELECT * FROM t;"        # 42
    docker volume inspect pgdatos
    sudo ls /var/lib/docker/volumes/pgdatos/_data | head
    ```

3. ***Bind mount* de configuración (solo lectura) y contenido:**

    ```bash
    mkdir -p ~/ud04/web && echo "<h1>Desde el anfitrión</h1>" > ~/ud04/web/index.html
    docker run -d --name web -p 8083:80 -v ~/ud04/web:/usr/share/nginx/html:ro nginx:1.29-alpine
    curl localhost:8083
    echo "<h1>Cambiado en caliente</h1>" > ~/ud04/web/index.html ; curl localhost:8083
    docker exec web sh -c 'echo x > /usr/share/nginx/html/x' || echo "Solo lectura: correcto"
    ```

4. **Volumen con nombre frente a *bind mount* sobre una ruta con contenido:**

    ```bash
    docker run --rm -v vol-nginx:/etc/nginx alpine:3.22 ls /etc/nginx     # vacío: alpine no tiene nginx
    docker run --rm -v vol-conf:/etc/nginx nginx:1.29-alpine ls /etc/nginx # se copia el contenido de la imagen
    mkdir -p /tmp/vacio
    docker run --rm -v /tmp/vacio:/etc/nginx nginx:1.29-alpine ls /etc/nginx || true   # el bind mount lo oculta
    ```

5. **`tmpfs`:**

    ```bash
    docker run --rm --tmpfs /secreto:size=10m,mode=700 alpine:3.22 sh -c 'df -h /secreto; mount | grep secreto'
    ```

6. **Copia de seguridad coherente de la base de datos** (lógica) y del volumen (física, con el servicio parado):

    ```bash
    mkdir -p ~/ud04/copias && cd ~/ud04/copias
    docker exec pg pg_dumpall -U postgres > pg-$(date +%F).sql
    docker stop pg
    docker run --rm -v pgdatos:/origen:ro -v "$PWD":/copia alpine:3.22 \
      tar czf /copia/pgdatos-$(date +%F).tar.gz -C /origen .
    docker start pg
    ls -lh
    ```

7. **Restauración en un volumen nuevo** (simulacro de desastre):

    ```bash
    docker volume create pgdatos-restaurado
    docker run --rm -v pgdatos-restaurado:/destino -v "$PWD":/copia alpine:3.22 \
      tar xzf /copia/pgdatos-$(date +%F).tar.gz -C /destino
    docker run -d --name pg2 -e POSTGRES_PASSWORD=x -v pgdatos-restaurado:/var/lib/postgresql/data postgres:17-alpine
    sleep 5 ; docker exec pg2 psql -U postgres -c "SELECT * FROM t;"      # 42
    ```

8. **Limpieza:** `docker rm -f pg pg2 web` y `docker volume rm pgdatos pgdatos-restaurado vol-conf vol-nginx`.

{{% /steps %}}

#### Comprobación

- [ ] Sin volumen el dato desaparece; con volumen con nombre se conserva.
- [ ] El *bind mount* refleja los cambios del anfitrión al instante y es de solo lectura.
- [ ] La restauración en un volumen nuevo devuelve el valor 42.

#### Errores habituales

- **Permisos en *bind mounts***: el UID del proceso del contenedor no coincide con el propietario del directorio del anfitrión. Ajusta con `chown` o `--user`.
- Restaurar el `tar` en un volumen con datos previos: mezcla ficheros. Usa siempre un volumen vacío.

#### Ampliación

Crea un volumen sobre NFS con el *driver* `local` (opciones `type=nfs`) usando el servidor que montarás en la práctica 4.6 y comprueba que dos contenedores en `ct-lab` y `ct-lab2` ven los mismos ficheros.

---

## Práctica 4.4 · Services y LoadBalancer con MetalLB

{{< practica num="4.4" tipo="Guiada" duracion="2 h" nivel="2" ra="RA5: b, c, e" entorno="Clúster kubeadm (3.7) · Calico · MetalLB" entrega="no" >}}

#### Objetivo

Exponer una aplicación con cada tipo de Service, entender el DNS del clúster y obtener IP externas reales con MetalLB.

#### Desarrollo

{{% steps %}}

1. **Contexto y aplicación de prueba** (desde `ct-lab` o `k8s-cp`):

    ```bash
    kubectl config use-context kubeadm
    kubectl create namespace redes
    kubectl config set-context --current --namespace=redes
    kubectl create deployment eco --image=registry.k8s.io/e2e-test-images/agnhost:2.39 --replicas=3 \
      -- /agnhost netexec --http-port=8080
    ```

2. **ClusterIP y DNS:**

    ```bash
    kubectl expose deployment eco --port=80 --target-port=8080
    kubectl get svc eco
    kubectl get endpointslices -l kubernetes.io/service-name=eco
    kubectl run c --rm -it --image=busybox:1.37 --restart=Never -- sh -c '
      cat /etc/resolv.conf
      nslookup eco
      nslookup eco.redes.svc.cluster.local
      for i in 1 2 3 4; do wget -qO- eco/hostname; echo; done'
    ```

3. **Cómo lo implementa kube-proxy.** En un nodo:

    ```bash
    sudo nft list ruleset | grep -A2 "$(kubectl get svc eco -o jsonpath='{.spec.clusterIP}')" | head
    ```

    (Si tu kube-proxy usa iptables: `sudo iptables -t nat -S KUBE-SERVICES | grep eco`.)

4. **Readiness y endpoints.** Escala a 0 y a 3 mientras observas `kubectl get endpointslices -w`.

5. **NodePort:**

    ```bash
    kubectl expose deployment eco --name eco-np --type=NodePort --port=80 --target-port=8080
    kubectl get svc eco-np        # anota el puerto 3xxxx
    ```

    Desde tu anfitrión: `curl http://192.168.56.12:<puerto>/hostname` y lo mismo con `.13` y `.11`. Responde en **todos** los nodos.

6. **MetalLB.** Instálalo y dale un rango de IP de la red del laboratorio:

    ```bash
    kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml
    kubectl -n metallb-system wait --for=condition=Ready pod --all --timeout=120s
    cat <<'EOF' | kubectl apply -f -
    apiVersion: metallb.io/v1beta1
    kind: IPAddressPool
    metadata: {name: laboratorio, namespace: metallb-system}
    spec:
      addresses: ["192.168.56.200-192.168.56.220"]
    ---
    apiVersion: metallb.io/v1beta1
    kind: L2Advertisement
    metadata: {name: laboratorio, namespace: metallb-system}
    spec:
      ipAddressPools: [laboratorio]
    EOF
    ```

7. **LoadBalancer:**

    ```bash
    kubectl expose deployment eco --name eco-lb --type=LoadBalancer --port=80 --target-port=8080
    kubectl get svc eco-lb -w          # EXTERNAL-IP 192.168.56.200
    ```

    Desde tu anfitrión: `curl http://192.168.56.200/hostname` varias veces.

8. **Prueba de fallo.** Apaga el nodo que anuncia la IP (`kubectl describe svc eco-lb` → eventos `nodeAssigned`) y comprueba que otro nodo toma la IP en unos segundos.

{{% /steps %}}

#### Comprobación

- [ ] `nslookup eco` resuelve a la ClusterIP y el FQDN completo también.
- [ ] El NodePort responde en los tres nodos.
- [ ] `eco-lb` obtiene una IP del rango y responde desde el anfitrión, incluso tras apagar el nodo que la anunciaba.

#### Errores habituales

- **`EXTERNAL-IP <pending>`** tras instalar MetalLB: falta el `IPAddressPool` o el `L2Advertisement`.
- **La IP no responde desde el anfitrión**: el rango no está en la misma red que el adaptador solo-anfitrión o choca con el DHCP de VirtualBox (desactívalo en `vboxnet0`).

#### Ampliación

Crea un Service *headless* para `eco` y compara qué devuelve `nslookup` con el Service normal.

---

## Práctica 4.5 · Gateway API con Traefik y HTTPS

{{< practica num="4.5" tipo="Guiada" duracion="2,5 h" nivel="2" ra="RA5: d" entorno="kind (curso) · Helm · Traefik · Gateway API · OpenSSL" entrega="ud04/p4.5/ con los manifiestos y las pruebas con curl" >}}

#### Objetivo

Instalar un controlador de entrada, publicar dos aplicaciones por nombre con Gateway API, añadir HTTPS, hacer un reparto *canary* y comparar con la API Ingress.

#### Desarrollo

{{% steps %}}

1. **Contexto kind y CRD de Gateway API** (canal estándar; comprueba la última versión en la web del proyecto):

    ```bash
    kubectl config use-context kind-curso
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml
    kubectl get crd | grep gateway
    ```

2. **Traefik con Helm.** Lo publicamos con NodePort en los puertos que kind redirige a 80 y 443 del anfitrión (práctica 3.1):

    ```bash
    helm repo add traefik https://traefik.github.io/charts && helm repo update
    cat > traefik-valores.yaml <<'EOF'
    service:
      type: NodePort
    ports:
      web:
        nodePort: 30080
      websecure:
        nodePort: 30443
    providers:
      kubernetesGateway:
        enabled: true
      kubernetesIngress:
        enabled: true
    gateway:
      enabled: false
    EOF
    helm install traefik traefik/traefik -n traefik --create-namespace -f traefik-valores.yaml
    kubectl -n traefik get pods,svc
    kubectl get gatewayclass
    ```

3. **Dos aplicaciones de prueba:**

    ```bash
    kubectl create namespace apps
    for a in azul verde; do
      kubectl -n apps create deployment $a --image=hashicorp/http-echo -- /http-echo -text="Aplicación $a"
      kubectl -n apps expose deployment $a --port=80 --target-port=5678
    done
    ```

4. **El Gateway** (lo gestiona «el equipo de plataforma»):

    ```yaml
    apiVersion: gateway.networking.k8s.io/v1
    kind: Gateway
    metadata: {name: publico, namespace: traefik}
    spec:
      gatewayClassName: traefik
      listeners:
        - name: http
          protocol: HTTP
          port: 8000
          allowedRoutes:
            namespaces: {from: All}
    ```

    ```bash
    kubectl apply -f gateway.yaml
    kubectl -n traefik get gateway publico      # PROGRAMMED True
    ```

5. **Rutas por nombre** (las gestiona «el equipo de cada aplicación»):

    ```yaml
    apiVersion: gateway.networking.k8s.io/v1
    kind: HTTPRoute
    metadata: {name: azul, namespace: apps}
    spec:
      parentRefs: [{name: publico, namespace: traefik}]
      hostnames: [azul.local]
      rules:
        - backendRefs: [{name: azul, port: 80}]
    ---
    apiVersion: gateway.networking.k8s.io/v1
    kind: HTTPRoute
    metadata: {name: verde, namespace: apps}
    spec:
      parentRefs: [{name: publico, namespace: traefik}]
      hostnames: [verde.local]
      rules:
        - backendRefs: [{name: verde, port: 80}]
    ```

    ```bash
    kubectl apply -f rutas.yaml
    curl -H "Host: azul.local" http://localhost
    curl -H "Host: verde.local" http://localhost
    curl -s -o /dev/null -w '%{http_code}\n' -H "Host: otro.local" http://localhost   # 404
    ```

    Añade `azul.local` y `verde.local` al `/etc/hosts` de tu anfitrión (IP de `ct-lab`) y pruébalo en el navegador.

6. **Canary con pesos:** modifica la ruta de `azul` para que el 80 % vaya a `azul` y el 20 % a `verde`:

    ```yaml
          rules:
            - backendRefs:
                - {name: azul, port: 80, weight: 80}
                - {name: verde, port: 80, weight: 20}
    ```

    ```bash
    for i in $(seq 20); do curl -s -H "Host: azul.local" http://localhost; done | sort | uniq -c
    ```

7. **HTTPS.** Certificado autofirmado para `*.local`, Secret TLS y un segundo *listener*:

    ```bash
    openssl req -x509 -newkey rsa:2048 -nodes -days 365 -keyout tls.key -out tls.crt \
      -subj "/CN=*.local" -addext "subjectAltName=DNS:azul.local,DNS:verde.local,DNS:mitienda.local"
    kubectl -n traefik create secret tls comodin-local --cert=tls.crt --key=tls.key
    ```

    Añade al Gateway:

    ```yaml
        - name: https
          protocol: HTTPS
          port: 8443
          tls:
            mode: Terminate
            certificateRefs: [{name: comodin-local}]
          allowedRoutes:
            namespaces: {from: All}
    ```

    ```bash
    kubectl apply -f gateway.yaml
    curl --cacert tls.crt --resolve verde.local:443:127.0.0.1 https://verde.local
    ```

8. **Redirección de HTTP a HTTPS** para `verde`: una regla con filtro `RequestRedirect` asociada solo al *listener* `http` (`sectionName: http`) y la ruta normal asociada al `https`. Compruébalo con `curl -I -H "Host: verde.local" http://localhost` (código 301).

9. **Lo mismo con Ingress** (para que lo reconozcas en clústeres existentes):

    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata: {name: azul-ingress, namespace: apps}
    spec:
      ingressClassName: traefik
      rules:
        - host: azul-ing.local
          http:
            paths:
              - path: /
                pathType: Prefix
                backend: {service: {name: azul, port: {number: 80}}}
    ```

    ```bash
    kubectl apply -f ingress.yaml
    curl -H "Host: azul-ing.local" http://localhost
    ```

{{% /steps %}}

#### Comprobación

- [ ] `azul.local` y `verde.local` llegan a su aplicación; otro nombre da 404.
- [ ] El reparto 80/20 se aproxima en 20 peticiones.
- [ ] `https://verde.local` responde con el certificado y `http://verde.local` redirige con 301.
- [ ] El Ingress también funciona con el mismo controlador.
- [ ] `kubectl describe httproute -n apps` muestra `Accepted: True` y `ResolvedRefs: True`.

#### Errores habituales

- **`curl` devuelve 404 para todo**: el puerto del *listener* no coincide con el *entrypoint* de Traefik (8000 para HTTP, 8443 para HTTPS) o la ruta no está aceptada (`allowedRoutes`).
- **`GatewayClass traefik` no existe**: falta `providers.kubernetesGateway.enabled=true` o se instalaron las CRD después de Traefik (reinicia el Pod de Traefik).
- **Error de certificado**: el nombre no está en `subjectAltName` o falta `--cacert`.

#### Ampliación

Instala **cert-manager** y crea una `ClusterIssuer` autofirmada (o una CA propia) que emita automáticamente los certificados de los *listeners* HTTPS.

---

## Práctica 4.6 · Almacenamiento dinámico con StorageClasses y NFS

{{< practica num="4.6" tipo="Guiada" duracion="2 h" nivel="2" ra="RA5: f, g, h" entorno="Clúster kubeadm · local-path-provisioner · servidor NFS en ct-lab · csi-driver-nfs" entrega="no" >}}

#### Objetivo

Proveer almacenamiento al clúster kubeadm (que no trae ninguno), primero estático, luego dinámico local y por último compartido (RWX) con NFS.

#### Desarrollo

{{% steps %}}

1. **Sin StorageClass, un PVC se queda esperando:**

    ```bash
    kubectl config use-context kubeadm
    kubectl create namespace almacen ; kubectl config set-context --current --namespace=almacen
    kubectl get storageclass          # vacío
    cat <<'EOF' | kubectl apply -f -
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata: {name: espera}
    spec:
      accessModes: [ReadWriteOnce]
      resources: {requests: {storage: 1Gi}}
    EOF
    kubectl get pvc espera ; kubectl describe pvc espera | tail -3
    ```

2. **Aprovisionamiento estático** con un PV `hostPath` en `k8s-w1` (solo laboratorio):

    ```yaml
    apiVersion: v1
    kind: PersistentVolume
    metadata: {name: pv-manual}
    spec:
      capacity: {storage: 1Gi}
      accessModes: [ReadWriteOnce]
      persistentVolumeReclaimPolicy: Retain
      hostPath: {path: /srv/pv-manual, type: DirectoryOrCreate}
      nodeAffinity:
        required:
          nodeSelectorTerms:
            - matchExpressions:
                - {key: kubernetes.io/hostname, operator: In, values: [k8s-w1]}
    ```

    Aplica y observa cómo `espera` pasa a `Bound`. Borra el PVC: el PV queda `Released` (por `Retain`).

3. **Aprovisionamiento dinámico local** con *local-path-provisioner*, marcado como clase por defecto:

    ```bash
    kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.30/deploy/local-path-storage.yaml
    kubectl patch storageclass local-path -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
    kubectl get sc
    ```

    Crea un PVC sin clase y un Pod que lo use; comprueba con `kubectl get pv` que el PV se creó solo y en qué nodo están los datos (`kubectl describe pv`).

4. **Servidor NFS en `ct-lab`:**

    ```bash
    sudo apt install -y nfs-kernel-server
    sudo mkdir -p /srv/nfs/k8s && sudo chown nobody:nogroup /srv/nfs/k8s
    echo "/srv/nfs/k8s 192.168.56.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee /etc/exports.d/k8s.exports
    sudo exportfs -ra && sudo exportfs -v
    ```

    En **los tres nodos** del clúster: `sudo apt install -y nfs-common`.

5. **Controlador CSI de NFS y su StorageClass:**

    ```bash
    helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
    helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs -n kube-system
    cat <<'EOF' | kubectl apply -f -
    apiVersion: storage.k8s.io/v1
    kind: StorageClass
    metadata: {name: nfs}
    provisioner: nfs.csi.k8s.io
    parameters:
      server: 192.168.56.10
      share: /srv/nfs/k8s
      mountPermissions: "0777"     # que procesos sin privilegios (UID 70, 999…) puedan escribir
    reclaimPolicy: Retain
    volumeBindingMode: Immediate
    allowVolumeExpansion: true
    mountOptions: ["nfsvers=4.1"]
    EOF
    ```

6. **Volumen compartido RWX** entre réplicas de distintos nodos:

    ```yaml
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata: {name: compartido}
    spec:
      accessModes: [ReadWriteMany]
      storageClassName: nfs
      resources: {requests: {storage: 500Mi}}
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata: {name: escritores}
    spec:
      replicas: 3
      selector: {matchLabels: {app: escritores}}
      template:
        metadata: {labels: {app: escritores}}
        spec:
          containers:
            - name: e
              image: busybox:1.37
              command: ["sh", "-c", "while true; do echo \"$(date +%T) $(hostname)\" >> /datos/registro.txt; sleep 5; done"]
              volumeMounts: [{name: d, mountPath: /datos}]
          volumes:
            - name: d
              persistentVolumeClaim: {claimName: compartido}
    ```

    ```bash
    kubectl apply -f rwx.yaml
    kubectl get pods -o wide                 # en w1 y w2
    sleep 15 ; kubectl exec deploy/escritores -- tail -6 /datos/registro.txt
    ls /srv/nfs/k8s/ && tail -3 /srv/nfs/k8s/*/registro.txt     # en ct-lab
    ```

7. **Persistencia ante borrado y reprogramación:** borra el Deployment entero, vuelve a crearlo y comprueba que el registro continúa donde estaba. Borra después el PVC: con `Retain`, la carpeta sigue en el servidor NFS.

8. **Ampliar un volumen:** `kubectl patch pvc compartido -p '{"spec":{"resources":{"requests":{"storage":"1Gi"}}}}'` y `kubectl get pvc`.

{{% /steps %}}

#### Comprobación

- [ ] El PVC sin clase queda `Pending` hasta que existe un PV o una clase por defecto.
- [ ] El PV estático pasa a `Released` al borrar el PVC.
- [ ] Tres réplicas en nodos distintos escriben en el mismo fichero NFS.
- [ ] Los datos sobreviven al borrado del Deployment y del PVC (`Retain`).

#### Errores habituales

- **`mount.nfs: access denied by server`**: la red de `/etc/exports` no incluye la IP del nodo, o no has hecho `exportfs -ra`.
- **`bad option; for several filesystems (e.g. nfs...) you might need a /sbin/mount.<type> helper`**: falta `nfs-common` en el nodo.
- **Dos StorageClasses por defecto**: los PVC sin clase fallan o eligen una al azar. Solo una debe tener la anotación.

#### Ampliación

Crea una `VolumeSnapshotClass` para el CSI de NFS, haz una instantánea del PVC y restaura un PVC nuevo a partir de ella.

---

## Práctica 4.7 · MiTienda expuesta y persistente

{{< practica num="4.7" tipo="Proyecto" duracion="1,5 h" nivel="3" ra="RA5: c, d, g, h" entorno="Clúster kubeadm · registro privado · MetalLB · Traefik · NFS" entrega="mitienda/k8s/ actualizado + docs/04-red-almacenamiento.md · Hito H4" >}}

#### Objetivo

Llevar MiTienda al clúster kubeadm usando las imágenes del registro privado, publicarla en `http://mitienda.local` y `https://mitienda.local` con Gateway API y demostrar que sus datos sobreviven a la pérdida de un nodo.

{{< descarga "recursos/mitienda/k8s/50-gateway.yaml" >}}

#### Enunciado

1. **Imágenes del registro privado.** En los tres nodos, haz que containerd confíe en `registro.local:5000`:

    ```bash
    sudo mkdir -p /etc/containerd/certs.d/registro.local:5000
    sudo scp alumno@ct-lab:/srv/registro/certs/registro.crt /etc/containerd/certs.d/registro.local:5000/ca.crt
    cat <<'EOF' | sudo tee /etc/containerd/certs.d/registro.local:5000/hosts.toml
    server = "https://registro.local:5000"
    [host."https://registro.local:5000"]
      ca = "/etc/containerd/certs.d/registro.local:5000/ca.crt"
    EOF
    sudo sed -i 's#config_path = ""#config_path = "/etc/containerd/certs.d"#' /etc/containerd/config.toml
    sudo systemctl restart containerd
    ```

    Crea el Secret de credenciales en el espacio `mitienda` y asígnalo a la cuenta de servicio `default` (`kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"registro-cred"}]}'`). Cambia las imágenes de `30-api.yaml` y `40-web.yaml` por las del registro.

2. **Almacenamiento.** La base de datos debe usar la clase `nfs` (añade `storageClassName: nfs` al `volumeClaimTemplates`) y la caché un PVC `local-path` en lugar de `emptyDir`. Justifica en el documento por qué cada una.

3. **Exposición.** Instala Traefik en el clúster kubeadm con `service.type=LoadBalancer` (MetalLB le dará una IP del rango) y aplica `50-gateway.yaml` añadiendo el *listener* HTTPS con un certificado para `mitienda.local`. Apunta `mitienda.local` a esa IP en el `/etc/hosts` de tu anfitrión.

4. **Pruebas que debes documentar:**
    - `curl -k https://mitienda.local/api/salud` y la web en el navegador.
    - Compra tres unidades. **Apaga el nodo donde está `db-0`** desde VirtualBox. Espera a que Kubernetes lo reprograme (o fuérzalo con `kubectl delete pod db-0 --force --grace-period=0` tras ver el nodo `NotReady`) y comprueba que los productos comprados siguen descontados del stock.
    - Borra todo el espacio de nombres excepto los PV, vuelve a desplegar y comprueba que los datos se recuperan (pista: con `Retain` tendrás que reutilizar el PV `Released` o recuperar la carpeta NFS).

#### Comprobación

- [ ] Los Pods tiran las imágenes de `registro.local:5000` (`kubectl describe pod` → `Pulled`).
- [ ] `https://mitienda.local` responde a través de la IP de MetalLB.
- [ ] Tras apagar el nodo de la base de datos, los datos siguen ahí.
- [ ] El documento explica el recorrido de una petición: navegador → IP de MetalLB → Service de Traefik → Gateway → HTTPRoute → Service `web` → Pod `web` → Service `api` → Pod `api` → Service `db` → `db-0` → volumen NFS.
