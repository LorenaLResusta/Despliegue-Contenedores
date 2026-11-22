---
title: "UD05 · Prácticas"
weight: 2
bookToc: true
---

# UD05 · Prácticas

{{< ra "RA6:a,b,c,d,e,f,g,h,i" >}}

| Práctica | Tipo | Nivel | Horas | CE principales |
|---|---|---|--:|---|
| [5.1 Endurecer contenedores Docker](#práctica-51--endurecer-contenedores-docker) | Guiada | ●●○ | 2 | RA6: a, b |
| [5.2 Análisis de vulnerabilidades y SBOM con Trivy](#práctica-52--análisis-de-vulnerabilidades-y-sbom-con-trivy) | Guiada | ●●○ | 2 | RA6: a, c |
| [5.3 RBAC: usuarios y cuentas de servicio](#práctica-53--rbac-usuarios-y-cuentas-de-servicio) | Guiada | ●●● | 2 | RA6: e |
| [5.4 Pod Security Standards, cuotas y límites](#práctica-54--pod-security-standards-cuotas-y-límites) | Guiada | ●●○ | 1,5 | RA6: b, f |
| [5.5 Políticas de red con Calico](#práctica-55--políticas-de-red-con-calico) | Guiada | ●●○ | 1,5 | RA6: d |
| [5.6 Métricas, paneles y alertas con Prometheus y Grafana](#práctica-56--métricas-paneles-y-alertas-con-prometheus-y-grafana) | Guiada | ●●○ | 2 | RA6: g |
| [5.7 Registros centralizados con Fluent Bit y Loki](#práctica-57--registros-centralizados-con-fluent-bit-y-loki) | Guiada | ●●● | 2 | RA6: g |
| [5.8 Práctica final: MiTienda en alta disponibilidad](#práctica-58--práctica-final-mitienda-en-alta-disponibilidad) | Proyecto | ●●● | 5 | RA6: a-i · RA4: g, h |
| **Total** | | | **18 h** | |

> [!NOTE]
> 5.1 y 5.2 se hacen con Docker en `ct-lab`. De la 5.3 a la 5.8 se trabaja en el **clúster kubeadm** (Calico aplica las NetworkPolicies). La monitorización necesita memoria: si tus nodos tienen 3 GB, apaga lo que no uses (por ejemplo, desinstala los ejemplos de la UD04).

---

## Práctica 5.1 · Endurecer contenedores Docker

{{< practica num="5.1" tipo="Guiada" duracion="2 h" nivel="2" ra="RA6: a, b" entorno="ct-lab · Docker Engine · Docker Bench for Security" entrega="no" >}}

#### Objetivo

Comprobar lo que puede hacer un atacante dentro de un contenedor mal configurado y aplicar, una a una, las medidas de endurecimiento.

#### Desarrollo

{{% steps %}}

1. **El peligro del socket de Docker.** Un contenedor con el socket montado controla el anfitrión:

    ```bash
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker:cli \
      docker run --rm -v /:/anfitrion alpine:3.22 cat /anfitrion/etc/shadow | head -3
    ```

    Has leído el `/etc/shadow` del anfitrión desde un contenedor. **Nunca** montes el socket en contenedores que no controlas.

2. **El peligro de `--privileged`:**

    ```bash
    docker run --rm --privileged alpine:3.22 sh -c 'fdisk -l 2>/dev/null | head -5; mkdir /m; mount /dev/sda1 /m && ls /m'
    ```

    (Ajusta `/dev/sda1` a tu disco.) Un contenedor privilegiado monta el disco del anfitrión.

3. **¿Quién eres dentro?** La mayoría de imágenes se ejecutan como `root`:

    ```bash
    docker run --rm nginx:1.29-alpine id
    docker run --rm nginxinc/nginx-unprivileged:1.29-alpine id
    docker run --rm --user 1000:1000 alpine:3.22 id
    ```

4. **Capacidades.** Mira las que tiene un contenedor normal y quítalas:

    ```bash
    docker run --rm alpine:3.22 sh -c 'apk add -q libcap; capsh --print | grep Current'
    docker run --rm --cap-drop ALL alpine:3.22 sh -c 'chown nobody /tmp && echo "chown OK"' || echo "sin CAP_CHOWN"
    docker run --rm --cap-drop ALL --cap-add NET_BIND_SERVICE nginx:1.29-alpine nginx -t
    ```

5. **Un servidor web endurecido.** Combina todas las medidas:

    ```bash
    docker run -d --name web-seguro -p 8080:8080 \
      --read-only --tmpfs /tmp:size=16m \
      --cap-drop ALL --security-opt no-new-privileges \
      --memory 64m --cpus 0.5 --pids-limit 50 \
      nginxinc/nginx-unprivileged:1.29-alpine
    curl -sI localhost:8080 | head -1
    docker exec web-seguro sh -c 'touch /etc/prueba' || echo "Solo lectura: correcto"
    docker inspect web-seguro --format '{{.HostConfig.ReadonlyRootfs}} {{.HostConfig.CapDrop}} {{.HostConfig.SecurityOpt}}'
    ```

6. **Lo mismo en Compose.** Añade a cada servicio de MiTienda de la práctica 2.8:

    ```yaml
        read_only: true
        tmpfs: [/tmp]
        cap_drop: [ALL]
        security_opt: ["no-new-privileges:true"]
    ```

    Comprueba qué servicios siguen funcionando y cuáles necesitan algún ajuste (pista: PostgreSQL necesita escribir en `/var/run/postgresql`; nginx sin privilegios, en `/tmp`).

7. **Auditoría con Docker Bench for Security** (CIS Docker Benchmark):

    ```bash
    git clone https://github.com/docker/docker-bench-security.git /tmp/dbs
    cd /tmp/dbs && sudo sh docker-bench-security.sh -c container_runtime | tail -40
    ```

    Busca los avisos `[WARN]` sobre tus contenedores y relaciónalos con las medidas anteriores.

{{% /steps %}}

#### Comprobación

- [ ] Explicas por qué los pasos 1 y 2 equivalen a ser `root` en el anfitrión.
- [ ] `web-seguro` funciona con sistema de archivos de solo lectura, sin capacidades y sin `root`.
- [ ] MiTienda con Compose arranca con `read_only` y `cap_drop: [ALL]` en todos los servicios (con los ajustes necesarios).

#### Errores habituales

- **`nginx: [emerg] mkdir() "/var/cache/nginx/..." failed (30: Read-only file system)`**: la imagen oficial `nginx` escribe en `/var/cache/nginx`; usa la variante *unprivileged* o un `tmpfs` en esa ruta.
- **`bind() to 0.0.0.0:80 failed (13: Permission denied)`**: sin `root` no se puede usar un puerto menor que 1024. Escucha en el 8080.

#### Ampliación

Activa `"userns-remap": "default"` en `/etc/docker/daemon.json` y comprueba con `ps` que el `root` de un contenedor es un UID alto en el anfitrión.

---

## Práctica 5.2 · Análisis de vulnerabilidades y SBOM con Trivy

{{< practica num="5.2" tipo="Guiada" duracion="2 h" nivel="2" ra="RA6: a, c" entorno="ct-lab · Trivy · Docker" entrega="ud05/p5.2-informe.md: comparación antes/después y vulnerabilidades aceptadas justificadas" >}}

#### Objetivo

Escanear imágenes y configuraciones, interpretar los resultados, reducir las vulnerabilidades y generar el SBOM de las imágenes del proyecto.

#### Desarrollo

{{% steps %}}

1. **Instala Trivy desde su repositorio oficial** y comprueba la versión:

    ```bash
    sudo apt install -y wget gnupg
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | \
      sudo tee /usr/share/keyrings/trivy.gpg >/dev/null
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | \
      sudo tee /etc/apt/sources.list.d/trivy.list
    sudo apt update && sudo apt install -y trivy
    trivy --version
    ```

    > [!WARNING]
    > Antes de instalar una herramienta de seguridad, consulta sus avisos de seguridad recientes y comprueba que la versión que vas a usar no está afectada. Es parte de cuidar la cadena de suministro.

2. **Una imagen antigua frente a una actual:**

    ```bash
    trivy image --severity HIGH,CRITICAL python:3.9
    trivy image --severity HIGH,CRITICAL python:3.13-slim
    trivy image --severity HIGH,CRITICAL --ignore-unfixed mitienda-api:1.0.0
    ```

    Anota el número de vulnerabilidades por gravedad de cada una.

3. **Solo lo que tiene corrección y en formato tabla resumida:**

    ```bash
    trivy image --ignore-unfixed --format table --severity CRITICAL,HIGH,MEDIUM mitienda-web:1.0.0
    ```

4. **Configuraciones incorrectas** (Dockerfile y manifiestos de Kubernetes):

    ```bash
    cd ~/curso/mitienda
    trivy config api/Dockerfile
    trivy config k8s/
    ```

    Escanea también el `compose.yaml` del reto 2.9 y compara los hallazgos con los errores que encontraste.

5. **Secretos olvidados.** Crea una imagen con una clave dentro y busca:

    ```bash
    mkdir -p /tmp/fuga && cd /tmp/fuga
    printf 'AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n' > .env
    printf 'FROM alpine:3.22\nCOPY .env /app/.env\n' > Dockerfile
    docker build -q -t fuga:1 .
    trivy image --scanners secret fuga:1
    ```

6. **SBOM en CycloneDX:**

    ```bash
    trivy image --format cyclonedx --output sbom-api.cdx.json mitienda-api:1.0.0
    jq '.components | length' sbom-api.cdx.json
    jq -r '.components[] | select(.name=="flask") | "\(.name) \(.version)"' sbom-api.cdx.json
    trivy sbom sbom-api.cdx.json --severity HIGH,CRITICAL     # escanear el SBOM, sin la imagen
    ```

7. **Corrige y vuelve a medir.** Para la imagen con más hallazgos de tu proyecto, aplica al menos dos medidas (base más reciente o más pequeña, actualizar dependencias de `requirements.txt`, quitar paquetes) y repite el escaneo. Las que no puedas corregir, documéntalas en `.trivyignore` con un comentario de por qué y hasta cuándo se aceptan.

8. **Escanear el clúster** (opcional, con el contexto `kubeadm`):

    ```bash
    trivy k8s --report summary --include-namespaces mitienda
    ```

{{% /steps %}}

#### Comprobación

- [ ] Tabla con las vulnerabilidades HIGH/CRITICAL de `python:3.9`, `python:3.13-slim` y tus dos imágenes.
- [ ] El secreto de la imagen `fuga:1` detectado.
- [ ] SBOM generado y consultado.
- [ ] Antes/después de tu corrección y `.trivyignore` justificado.

#### Errores habituales

- **El primer escaneo tarda**: Trivy descarga su base de datos de vulnerabilidades. Las siguientes ejecuciones usan la caché.
- Aceptar vulnerabilidades sin revisar si el paquete se usa en ejecución: una CVE crítica en un compilador que solo está en la etapa de construcción no está en la imagen final.

#### Ampliación

Firma `mitienda-api:1.0.0` en el registro privado con **cosign** (`cosign generate-key-pair`, `cosign sign --key cosign.key registro.local:5000/mitienda/api:1.0.0`) y verifica la firma.

---

## Práctica 5.3 · RBAC: usuarios y cuentas de servicio

{{< practica num="5.3" tipo="Guiada" duracion="2 h" nivel="3" ra="RA6: e" entorno="Clúster kubeadm · OpenSSL · API CertificateSigningRequest" entrega="ud05/p5.3/ con los manifiestos RBAC y la salida de kubectl auth can-i" >}}

#### Objetivo

Crear una usuaria con certificado y permisos limitados a un espacio de nombres, y una cuenta de servicio con permisos mínimos para una aplicación.

#### Contexto

Ana, desarrolladora de MiTienda, necesita desplegar y ver registros en su espacio de nombres, pero no debe leer Secrets ni tocar otros espacios. Un proceso de monitorización interno necesita listar Pods y nada más.

#### Desarrollo

{{% steps %}}

1. **Clave y petición de certificado** (en `ct-lab`). El CN es el usuario y la O, el grupo:

    ```bash
    mkdir -p ~/ud05/rbac && cd ~/ud05/rbac
    openssl genrsa -out ana.key 2048
    openssl req -new -key ana.key -out ana.csr -subj "/CN=ana/O=desarrollo"
    ```

2. **Que la CA del clúster lo firme** con la API `CertificateSigningRequest`:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: certificates.k8s.io/v1
    kind: CertificateSigningRequest
    metadata: {name: ana}
    spec:
      request: $(base64 -w0 ana.csr)
      signerName: kubernetes.io/kube-apiserver-client
      expirationSeconds: 2592000
      usages: [client auth]
    EOF
    kubectl get csr ana
    kubectl certificate approve ana
    kubectl get csr ana -o jsonpath='{.status.certificate}' | base64 -d > ana.crt
    openssl x509 -in ana.crt -noout -subject -enddate
    ```

3. **Kubeconfig de Ana** (un fichero aparte, el que se le entregaría):

    ```bash
    SERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
    kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d > ca.crt
    export KUBECONFIG=~/ud05/rbac/ana.kubeconfig
    kubectl config set-cluster curso --server="$SERVER" --certificate-authority=ca.crt --embed-certs
    kubectl config set-credentials ana --client-certificate=ana.crt --client-key=ana.key --embed-certs
    kubectl config set-context ana@curso --cluster=curso --user=ana --namespace=mitienda
    kubectl config use-context ana@curso
    kubectl get pods            # Forbidden: autenticada, pero sin permisos
    unset KUBECONFIG
    ```

4. **Role y RoleBinding** para el grupo `desarrollo` en `mitienda`:

    ```yaml
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata: {name: desarrollador, namespace: mitienda}
    rules:
      - apiGroups: [""]
        resources: [pods, pods/log, services, configmaps]
        verbs: [get, list, watch]
      - apiGroups: ["apps"]
        resources: [deployments, replicasets]
        verbs: [get, list, watch, update, patch]
      - apiGroups: ["apps"]
        resources: [deployments/scale]
        verbs: [update, patch]
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata: {name: desarrollo, namespace: mitienda}
    subjects:
      - {kind: Group, name: desarrollo, apiGroup: rbac.authorization.k8s.io}
    roleRef: {kind: Role, name: desarrollador, apiGroup: rbac.authorization.k8s.io}
    ```

5. **Comprueba los permisos** con suplantación (como administradora) y con el kubeconfig de Ana:

    ```bash
    for v in "get pods" "list deployments" "patch deployments" "get secrets" "delete pods" "create pods/exec"; do
      printf '%-20s %s\n' "$v" "$(kubectl auth can-i $v -n mitienda --as ana --as-group desarrollo)"
    done
    kubectl auth can-i get pods -n kube-system --as ana --as-group desarrollo
    KUBECONFIG=~/ud05/rbac/ana.kubeconfig kubectl scale deployment api --replicas=4
    KUBECONFIG=~/ud05/rbac/ana.kubeconfig kubectl get secret db-cred      # Forbidden
    ```

6. **ServiceAccount con permisos mínimos para un proceso:**

    ```yaml
    apiVersion: v1
    kind: ServiceAccount
    metadata: {name: monitor, namespace: mitienda}
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata: {name: lector-pods, namespace: mitienda}
    rules:
      - apiGroups: [""]
        resources: [pods]
        verbs: [list]
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata: {name: monitor, namespace: mitienda}
    subjects: [{kind: ServiceAccount, name: monitor, namespace: mitienda}]
    roleRef: {kind: Role, name: lector-pods, apiGroup: rbac.authorization.k8s.io}
    ```

7. **Un Pod que usa la API con su token:**

    ```bash
    kubectl -n mitienda run sonda --image=curlimages/curl:8.11.1 --restart=Never \
      --overrides='{"spec":{"serviceAccountName":"monitor","securityContext":{"runAsNonRoot":true,"runAsUser":100,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"sonda","image":"curlimages/curl:8.11.1","command":["sleep","3600"],"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}}}]}}'
    kubectl -n mitienda exec sonda -- sh -c '
      T=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
      C=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      curl -s --cacert $C -H "Authorization: Bearer $T" https://kubernetes.default.svc/api/v1/namespaces/mitienda/pods | grep -c "\"name\""
      curl -s --cacert $C -H "Authorization: Bearer $T" https://kubernetes.default.svc/api/v1/namespaces/mitienda/secrets | grep -o "\"reason\": \"[A-Za-z]*\""'
    ```

8. **Revisión de la cuenta por defecto.** Comprueba que la ServiceAccount `default` de `mitienda` no tiene permisos y añade `automountServiceAccountToken: false` a los Deployments de MiTienda (no usan la API).

{{% /steps %}}

#### Comprobación

- [ ] Ana se autentica con su certificado y solo puede lo que dice su Role en `mitienda`.
- [ ] `get secrets` y cualquier acción en `kube-system` devuelven `no`.
- [ ] La sonda lista Pods y recibe `Forbidden` al pedir Secrets.

#### Errores habituales

- **`error: You must be logged in to the server (Unauthorized)`**: el certificado no lo firmó la CA del clúster o caducó.
- **Grupo ignorado**: el grupo sale de la O del certificado; si se te olvidó en `-subj`, Ana no pertenece a `desarrollo`.
- Usar un `ClusterRoleBinding` donde bastaba un `RoleBinding`: concede permisos en todos los espacios.

#### Ampliación

Revoca el acceso de Ana sin poder revocar su certificado (Kubernetes no tiene lista de revocación): ¿qué harías? Pista: borra el RoleBinding y explica por qué en producción se prefieren tokens OIDC de corta duración.

---

## Práctica 5.4 · Pod Security Standards, cuotas y límites

{{< practica num="5.4" tipo="Guiada" duracion="1,5 h" nivel="2" ra="RA6: b, f" entorno="Clúster kubeadm" entrega="no" >}}

#### Objetivo

Aplicar los estándares de seguridad de Pods por espacio de nombres y limitar el consumo de recursos con cuotas y valores por defecto.

#### Desarrollo

{{% steps %}}

1. **Espacio de pruebas en modo aviso:**

    ```bash
    kubectl create namespace seguro
    kubectl label namespace seguro pod-security.kubernetes.io/warn=restricted
    kubectl -n seguro run inseguro --image=nginx:1.29-alpine
    ```

    Se crea, pero `kubectl` muestra un aviso con todo lo que incumple.

2. **Modo obligatorio:**

    ```bash
    kubectl label namespace seguro pod-security.kubernetes.io/enforce=restricted --overwrite
    kubectl -n seguro run inseguro2 --image=nginx:1.29-alpine        # rechazado
    kubectl -n seguro run privilegiado --image=alpine:3.22 --privileged -- sleep 1d   # rechazado
    ```

3. **Un Pod que cumple `restricted`:**

    ```yaml
    apiVersion: v1
    kind: Pod
    metadata: {name: correcto, namespace: seguro}
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 101
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: web
          image: nginxinc/nginx-unprivileged:1.29-alpine
          securityContext:
            allowPrivilegeEscalation: false
            capabilities: {drop: ["ALL"]}
            readOnlyRootFilesystem: true
          volumeMounts: [{name: tmp, mountPath: /tmp}]
      volumes: [{name: tmp, emptyDir: {}}]
    ```

4. **Antes de exigirlo en un espacio con cargas, simula:**

    ```bash
    kubectl label --dry-run=server --overwrite namespace mitienda pod-security.kubernetes.io/enforce=restricted
    kubectl label --dry-run=server --overwrite namespace kube-system pod-security.kubernetes.io/enforce=restricted
    ```

5. **LimitRange** (valores por defecto y máximos por contenedor):

    ```yaml
    apiVersion: v1
    kind: LimitRange
    metadata: {name: por-defecto, namespace: seguro}
    spec:
      limits:
        - type: Container
          defaultRequest: {cpu: 50m, memory: 32Mi}
          default: {cpu: 200m, memory: 128Mi}
          max: {cpu: "1", memory: 512Mi}
    ```

    Crea un Pod sin `resources` y comprueba con `kubectl get pod -o yaml` que los ha recibido. Prueba otro con `limits.memory: 1Gi`: rechazado.

6. **ResourceQuota** del espacio de nombres:

    ```yaml
    apiVersion: v1
    kind: ResourceQuota
    metadata: {name: cuota, namespace: seguro}
    spec:
      hard:
        pods: "5"
        requests.cpu: "500m"
        requests.memory: 512Mi
        limits.memory: 1Gi
        persistentvolumeclaims: "2"
        services.loadbalancers: "0"
    ```

    ```bash
    kubectl -n seguro create deployment muchos --image=nginxinc/nginx-unprivileged:1.29-alpine --replicas=10
    kubectl -n seguro describe quota cuota
    kubectl -n seguro get events | grep -i quota | tail -3
    ```

    El Deployment no rellena las 10 réplicas (fallan por PSS o por cuota): lee los eventos del ReplicaSet y explica por qué.

{{% /steps %}}

#### Comprobación

- [ ] Los Pods inseguros se rechazan en modo `enforce` y el Pod `correcto` se admite.
- [ ] El Pod sin `resources` recibe los valores del LimitRange.
- [ ] La cuota impide superar 5 Pods y crear Services `LoadBalancer`.

#### Ampliación

Instala **Kyverno** y crea una política que rechace imágenes que no procedan de `registro.local:5000` o que usen la etiqueta `latest`.

---

## Práctica 5.5 · Políticas de red con Calico

{{< practica num="5.5" tipo="Guiada" duracion="1,5 h" nivel="2" ra="RA6: d" entorno="Clúster kubeadm · Calico" entrega="ud05/p5.5/ con la matriz de conectividad antes y después" >}}

#### Objetivo

Aplicar un modelo de **denegación por defecto** a MiTienda y permitir solo los flujos necesarios, comprobándolo con una matriz de conectividad.

{{< descarga "recursos/mitienda/k8s/70-networkpolicies.yaml" >}}

#### Desarrollo

{{% steps %}}

1. **Pod de pruebas** en el espacio de MiTienda y otro en un espacio ajeno:

    ```bash
    kubectl create namespace intruso
    for ns in mitienda intruso; do
      kubectl -n $ns run prueba --image=busybox:1.37 --labels=app=prueba --restart=Never \
        --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":1000,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"prueba","image":"busybox:1.37","command":["sleep","1d"],"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}}}]}}'
    done
    ```

2. **Matriz antes de las políticas.** Guarda este script como `matriz.sh` y ejecútalo:

    ```bash
    #!/bin/sh
    # Uso: ./matriz.sh  → prueba conexiones TCP con nc desde cada origen
    prueba() { # $1 ns  $2 pod  $3 destino  $4 puerto
      if kubectl -n "$1" exec "$2" -- nc -z -w 2 "$3" "$4" 2>/dev/null; then r=SI; else r=no; fi
      printf '%-30s -> %-35s %s\n' "$1/$2" "$3:$4" "$r"
    }
    WEB=$(kubectl -n mitienda get pod -l app=web -o name | head -1 | cut -d/ -f2)
    API=$(kubectl -n mitienda get pod -l app=api -o name | head -1 | cut -d/ -f2)
    prueba mitienda "$WEB" api 8000
    prueba mitienda "$WEB" db 5432
    prueba mitienda "$API" db 5432
    prueba mitienda "$API" cache 6379
    prueba mitienda prueba db 5432
    prueba intruso prueba api.mitienda 8000
    prueba intruso prueba db.mitienda 5432
    ```

    > [!NOTE]
    > Si la imagen de algún Pod no tiene `nc`, usa `kubectl debug` con un contenedor efímero de `busybox` o haz la prueba desde el Pod `prueba` cambiando sus etiquetas para que «se haga pasar» por `web` o `api`.

3. **Aplica las políticas** y vuelve a pasar la matriz:

    ```bash
    kubectl apply -f ~/curso/mitienda/k8s/70-networkpolicies.yaml
    kubectl -n mitienda get networkpolicy
    ./matriz.sh
    ```

4. **¿Sigue funcionando la aplicación?** `curl -k https://mitienda.local/api/salud`. Si no, revisa la política de entrada de `web` (el espacio de Traefik debe coincidir con `kubernetes.io/metadata.name: traefik`).

5. **Comprueba el DNS** desde `prueba` (debe resolver) y la salida a Internet (debe fallar):

    ```bash
    kubectl -n mitienda exec prueba -- nslookup api
    kubectl -n mitienda exec prueba -- wget -qO- -T 3 http://example.com || echo "Sin salida a Internet"
    ```

6. **Política propia.** Escribe una política que permita a los Pods con etiqueta `app=prueba` del espacio `intruso` acceder **solo** al puerto 8000 de la API (simula un servicio de otro equipo autorizado). Compruébalo con la matriz.

{{% /steps %}}

#### Comprobación

Matriz esperada tras las políticas:

| Origen → destino | Antes | Después |
|---|:-:|:-:|
| web → api:8000 | SI | SI |
| web → db:5432 | SI | no |
| api → db:5432 / cache:6379 | SI | SI |
| prueba (mitienda) → db | SI | no |
| intruso → api / db | SI | no (api: SI con tu política del paso 6) |

#### Errores habituales

- **Todo sigue permitido**: tu CNI no aplica políticas (kind con versiones antiguas, Flannel). Comprueba que estás en el contexto `kubeadm`.
- **La web deja de responder** tras aplicar las políticas: falta permitir la entrada desde el controlador de entrada o la salida DNS.

#### Ampliación

Con la API de Calico (`projectcalico.org/v3`), crea una `GlobalNetworkPolicy` que deniegue en todo el clúster el acceso al puerto 6443 del plano de control desde los Pods, salvo desde `kube-system`.

---

## Práctica 5.6 · Métricas, paneles y alertas con Prometheus y Grafana

{{< practica num="5.6" tipo="Guiada" duracion="2 h" nivel="2" ra="RA6: g" entorno="Clúster kubeadm · Helm · kube-prometheus-stack · Gateway API" entrega="ud05/p5.6/ con el panel exportado (JSON), la regla de alerta y capturas" >}}

#### Objetivo

Instalar la pila de monitorización, consultar métricas con PromQL, crear un panel para MiTienda y una alerta que salte cuando la API deje de estar disponible.

#### Desarrollo

{{% steps %}}

1. **Instala kube-prometheus-stack** con valores ajustados al laboratorio:

    ```bash
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    cat > kps-valores.yaml <<'EOF'
    grafana:
      adminPassword: "Grafana_Curso_2026"
      resources: {requests: {cpu: 50m, memory: 128Mi}}
    prometheus:
      prometheusSpec:
        retention: 3d
        resources: {requests: {cpu: 100m, memory: 512Mi}}
        ruleSelectorNilUsesHelmValues: false
        serviceMonitorSelectorNilUsesHelmValues: false
    alertmanager:
      alertmanagerSpec:
        resources: {requests: {cpu: 20m, memory: 64Mi}}
    EOF
    helm install kps prometheus-community/kube-prometheus-stack -n monitorizacion --create-namespace -f kps-valores.yaml
    kubectl -n monitorizacion get pods -w
    ```

2. **Publica Grafana** con una HTTPRoute en el Gateway de la UD04 (`grafana.local`, Service `kps-grafana`, puerto 80) y añade `grafana.local` a tu `/etc/hosts`. Entra con `admin` y la contraseña de los valores.

3. **Explora los paneles incluidos**: *Kubernetes / Compute Resources / Namespace (Pods)* para `mitienda`, *Node Exporter / Nodes*. ¿Qué nodo tiene más memoria ocupada?

4. **PromQL.** Desde *Explore* (origen Prometheus), ejecuta las consultas de la teoría y estas:

    ```text
    sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="mitienda", container!=""}[5m]))
    kube_deployment_status_replicas_available{namespace="mitienda"}
    sum by (namespace) (kube_pod_container_status_restarts_total)
    ```

5. **Panel de MiTienda.** Crea un panel nuevo con cuatro visualizaciones: réplicas disponibles por Deployment, CPU por Pod, memoria por Pod y reinicios en la última hora. Expórtalo en JSON.

6. **Regla de alerta** (`alerta-api.yaml`):

    ```yaml
    apiVersion: monitoring.coreos.com/v1
    kind: PrometheusRule
    metadata:
      name: mitienda
      namespace: monitorizacion
    spec:
      groups:
        - name: mitienda
          rules:
            - alert: APISinReplicas
              expr: kube_deployment_status_replicas_available{namespace="mitienda", deployment="api"} < 1
              for: 1m
              labels: {severity: critical}
              annotations:
                summary: "MiTienda: la API no tiene réplicas disponibles"
            - alert: PodsReiniciando
              expr: increase(kube_pod_container_status_restarts_total{namespace="mitienda"}[15m]) > 3
              labels: {severity: warning}
              annotations:
                summary: "{{ $labels.pod }} se ha reiniciado más de 3 veces en 15 min"
    ```

    ```bash
    kubectl apply -f alerta-api.yaml
    ```

7. **Provoca la alerta:** `kubectl -n mitienda scale deployment api --replicas=0`. Observa en Prometheus (*Alerts*: `Pending` → `Firing`) y en Alertmanager (`kubectl -n monitorizacion port-forward svc/kps-alertmanager 9093`). Restaura las réplicas y comprueba que se resuelve.

{{% /steps %}}

#### Comprobación

- [ ] Todos los Pods de `monitorizacion` en `Running` y Grafana accesible por `grafana.local`.
- [ ] Panel de MiTienda con las cuatro visualizaciones.
- [ ] La alerta `APISinReplicas` pasa a `Firing` con la API a 0 y se resuelve al restaurarla.

#### Errores habituales

- **Pods de Prometheus en `Pending`**: falta memoria en los nodos o la StorageClass por defecto. Revisa `describe pod`.
- **La regla no aparece en Prometheus**: el Prometheus del *chart* solo carga reglas con la etiqueta `release: kps`, salvo que pongas `ruleSelectorNilUsesHelmValues: false` como en los valores de arriba.

#### Ampliación

Configura Alertmanager para enviar las alertas a un bot de Telegram o a un canal de Slack/Discord (*webhook*) con `alertmanager.config` en los valores de Helm.

---

## Práctica 5.7 · Registros centralizados con Fluent Bit y Loki

{{< practica num="5.7" tipo="Guiada" duracion="2 h" nivel="3" ra="RA6: g" entorno="Clúster kubeadm · Helm · Loki · Fluent Bit · Grafana" entrega="no" >}}

#### Objetivo

Recoger los registros de todos los contenedores del clúster con un DaemonSet, almacenarlos en Loki y consultarlos desde Grafana, incluso después de que los Pods hayan desaparecido.

#### Desarrollo

{{% steps %}}

1. **Loki en modo de un solo binario** (almacenamiento en el sistema de archivos, suficiente para el laboratorio):

    ```bash
    helm repo add grafana https://grafana.github.io/helm-charts && helm repo update
    cat > loki-valores.yaml <<'EOF'
    deploymentMode: SingleBinary
    loki:
      auth_enabled: false
      commonConfig: {replication_factor: 1}
      storage: {type: filesystem}
      schemaConfig:
        configs:
          - from: "2024-04-01"
            store: tsdb
            object_store: filesystem
            schema: v13
            index: {prefix: loki_index_, period: 24h}
    singleBinary:
      replicas: 1
      persistence: {size: 5Gi}
    read: {replicas: 0}
    write: {replicas: 0}
    backend: {replicas: 0}
    chunksCache: {enabled: false}
    resultsCache: {enabled: false}
    EOF
    helm install loki grafana/loki -n monitorizacion -f loki-valores.yaml
    kubectl -n monitorizacion get pods -l app.kubernetes.io/name=loki
    ```

2. **Fluent Bit como DaemonSet** que envía a Loki:

    ```bash
    helm repo add fluent https://fluent.github.io/helm-charts
    cat > fluentbit-valores.yaml <<'EOF'
    config:
      outputs: |
        [OUTPUT]
            Name                   loki
            Match                  kube.*
            Host                   loki-gateway.monitorizacion.svc.cluster.local
            Port                   80
            Labels                 job=fluent-bit
            Auto_Kubernetes_Labels on
    EOF
    helm install fluent-bit fluent/fluent-bit -n monitorizacion -f fluentbit-valores.yaml
    kubectl -n monitorizacion get ds fluent-bit       # un Pod por nodo
    ```

3. **Loki como origen de datos en Grafana:** *Connections → Data sources → Add → Loki*, URL `http://loki-gateway.monitorizacion.svc.cluster.local`.

4. **Consultas LogQL** en *Explore*:

    ```text
    {namespace="mitienda"}
    {namespace="mitienda", container="api"} |= "POST /api/comprar"
    {namespace="mitienda", container="api"} |= " 409 "
    sum by (container) (count_over_time({namespace="mitienda"}[5m]))
    ```

    (Los nombres exactos de las etiquetas dependen de `Auto_Kubernetes_Labels`; usa el navegador de etiquetas de Grafana.)

5. **Registros que sobreviven al Pod.** Intenta comprar un producto agotado, sin stock (respuesta 409), borra el Pod de la API que respondió y busca la línea en Loki: sigue ahí aunque `kubectl logs` ya no pueda mostrarla.

6. **Comparación con EFK.** Redacta en tu cuaderno qué cambiaría si en lugar de Loki se usara Elasticsearch + Kibana (recursos, tipo de búsquedas, componentes) y en qué caso lo elegirías.

{{% /steps %}}

#### Comprobación

- [ ] Un Pod de Fluent Bit por nodo en `Running`.
- [ ] Las consultas LogQL devuelven las peticiones de la API.
- [ ] Encuentras en Loki la línea del 409 de un Pod ya borrado.

#### Errores habituales

- **Fluent Bit sin errores pero Loki vacío**: el nombre del Service de Loki no coincide (`kubectl -n monitorizacion get svc | grep loki`).
- **Loki en `CrashLoopBackOff` con errores de esquema**: revisa `schemaConfig` y que la versión del *chart* coincide con la sintaxis de los valores (`helm show values grafana/loki`).

#### Ampliación

Crea en Grafana una **alerta basada en registros**: más de 5 respuestas 409 en 5 minutos.

---

## Práctica 5.8 · Práctica final: MiTienda en alta disponibilidad

{{< practica num="5.8" tipo="Proyecto" duracion="5 h (+ trabajo fuera del aula)" nivel="3" ra="RA6: a-i · RA4: g, h" entorno="Clúster kubeadm completo (UD03-UD05)" entrega="Repositorio mitienda/ completo + informe final + simulacro en directo (defensa) · Hito H5 · 40 % de la nota" >}}

#### Objetivo

Entregar MiTienda **lista para producción**: segura, observable, en alta disponibilidad y con los procedimientos de operación documentados, y demostrarlo en un **simulacro de fallos en directo**.

#### Contexto

El ayuntamiento va a poner MiTienda en marcha para la temporada de verano. Antes de firmar, su responsable técnico quiere ver la plataforma funcionando y **romperla delante de ti**.

#### Requisitos que debe cumplir

| # | Requisito | RA/CE | Evidencia |
|---|---|---|---|
| 1 | Imágenes propias en el registro privado, versionadas (semver), sin `latest`, sin vulnerabilidades CRITICAL corregibles; SBOM generado | RA6: a, c | Informe de Trivy y SBOM |
| 2 | Todos los contenedores sin `root`, `drop: ALL`, sin escalada, seccomp; espacio de nombres con PSS `restricted` en `enforce` | RA6: b, f | `kubectl label` + manifiestos |
| 3 | *Requests*/*limits* en todo, LimitRange y ResourceQuota en `mitienda` | RA6: f | `describe quota` |
| 4 | API con ≥ 3 réplicas repartidas en nodos (`topologySpreadConstraints`), PDB, HPA, sondas, `RollingUpdate` sin indisponibilidad | RA4: g, h · RA6: h | Manifiestos + prueba de carga |
| 5 | `web` y Traefik con ≥ 2 réplicas; acceso por `https://mitienda.local` con Gateway API y MetalLB | RA6: h | `curl` + navegador |
| 6 | Base de datos con volumen persistente (NFS, `Retain`) y **copia lógica diaria** con un CronJob (`pg_dump` a otro PVC) | RA6: h, i | CronJob + restauración probada |
| 7 | NetworkPolicies con denegación por defecto y solo los flujos necesarios | RA6: d | Matriz de conectividad |
| 8 | RBAC: usuaria `ana` (desarrollo) y ServiceAccounts sin token montado donde no hace falta | RA6: e | `kubectl auth can-i` |
| 9 | Panel de Grafana de MiTienda, alertas `APISinReplicas` y `PodsReiniciando`, registros en Loki | RA6: g | Capturas + JSON del panel |
| 10 | Copia de etcd y procedimiento escrito de restauración | RA6: i | Fichero de *snapshot* + documento |
| 11 | Todo declarativo en Git (Kustomize o Helm); un único `README` permite desplegar desde cero | RA4: i · RA6: i | Repositorio |

> [!NOTE]
> **Sobre la base de datos.** Con una sola réplica de PostgreSQL, la base de datos es un punto único de fallo: si cae su nodo, hay unos minutos de indisponibilidad hasta que se reprograma. Es **aceptable** en esta práctica si lo documentas, mides el tiempo de recuperación (RTO) y la pérdida de datos posible (RPO, según tu copia). Para subir nota (reto), sustitúyela por un clúster de **CloudNativePG** de 3 instancias con conmutación automática y repite el simulacro.

#### Simulacro de fallos (defensa)

Durante la defensa tendrás un cliente haciendo peticiones continuas a `https://mitienda.local/api/info` y `/api/productos` y contando errores. La profesora elegirá varios de estos fallos:

1. Borrar todos los Pods de la API a la vez.
2. Desplegar una versión de la API que no arranca y pedirte que vuelvas atrás.
3. `kubectl drain` de un nodo de trabajo durante la carga.
4. **Apagar** un nodo de trabajo de golpe (sin `drain`).
5. Borrar el Pod de la base de datos.
6. Generar carga para que el HPA escale.
7. Intentar acceder a la base de datos desde un Pod de otro espacio de nombres.
8. Pedirte que restaures la base de datos a partir de la copia de la noche anterior.

Para cada fallo debes: **predecir** qué pasará, **observarlo** (Grafana, `kubectl get -w`, Loki), **explicar** el mecanismo que actúa (o por qué no actúa) y, si hace falta, **recuperar** el servicio.

#### Informe final (`mitienda/docs/informe-final.md`)

1. **Arquitectura**: diagrama completo (nodos, espacios de nombres, servicios, red, almacenamiento) y recorrido de una petición.
2. **Decisiones de diseño** justificadas (por qué cada objeto, cada política, cada valor de recursos).
3. **Seguridad**: resumen de las medidas por capa (las 4C) y riesgos residuales aceptados.
4. **Operación**: cómo desplegar, actualizar, escalar, ver métricas y registros.
5. **Recuperación**: restaurar la base de datos, restaurar etcd, sustituir un nodo.
6. **Resultados del simulacro** propio previo: tabla con fallo, errores observados, tiempo de recuperación y conclusión.
7. **Mejoras** que harías con más tiempo o presupuesto (GitOps, base de datos replicada, almacenamiento distribuido, plano de control en HA, clúster gestionado…).

#### Rúbrica de la práctica final

| Criterio | Peso |
|---|--:|
| Requisitos 1-11 cumplidos y verificables | 40 % |
| Simulacro: predicción, explicación y recuperación | 25 % |
| Informe final (claridad, justificación, procedimientos reproducibles) | 20 % |
| Calidad del repositorio (declarativo, sin secretos, README) | 10 % |
| Reto: base de datos replicada con conmutación automática | +10 % |
| Defensa oral (preguntas sobre cualquier parte del curso aplicada al proyecto) | 5 % |
