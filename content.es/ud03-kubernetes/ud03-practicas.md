---
title: "UD03 · Prácticas"
weight: 2
bookToc: true
---

# UD03 · Prácticas

{{< ra "RA4:a,b,c,d,e,f,g,h,i" "RA2:a" >}}

| Práctica | Tipo | Nivel | Horas | CE principales |
|---|---|---|--:|---|
| [3.1 Primer clúster con kind](#práctica-31--primer-clúster-con-kind) | Guiada | ●○○ | 2 | RA4: a, b |
| [3.2 Pods y manifiestos YAML](#práctica-32--pods-y-manifiestos-yaml) | Guiada | ●○○ | 2 | RA4: e, f |
| [3.3 ReplicaSets, Deployments y autocuración](#práctica-33--replicasets-deployments-y-autocuración) | Guiada | ●○○ | 2 | RA4: e, f, h |
| [3.4 Actualización progresiva y vuelta atrás](#práctica-34--actualización-progresiva-y-vuelta-atrás) | Guiada | ●●○ | 2 | RA4: g |
| [3.5 Configuración, secretos, sondas y recursos](#práctica-35--configuración-secretos-sondas-y-recursos) | Guiada | ●●○ | 2 | RA4: e, f |
| [3.6 StatefulSets, DaemonSets, Jobs y CronJobs](#práctica-36--statefulsets-daemonsets-jobs-y-cronjobs) | Guiada | ●●○ | 2 | RA4: f |
| [3.7 Clúster de tres nodos con kubeadm](#práctica-37--clúster-de-tres-nodos-con-kubeadm) ⚠️ | Guiada | ●●● | 5 | RA4: c, d · RA2: a |
| [3.8 Escalado automático con HPA](#práctica-38--escalado-automático-con-hpa) | Guiada | ●●○ | 2 | RA4: h |
| [3.9 Empaquetar con Helm y Kustomize](#práctica-39--empaquetar-con-helm-y-kustomize) | Guiada | ●●○ | 2 | RA4: i |
| [3.10 MiTienda en Kubernetes](#práctica-310--mitienda-en-kubernetes) | Proyecto | ●●● | 3 | RA4: e-i |
| **Total** | | | **24 h** | |

> [!TIP]
> Las prácticas 3.1 a 3.6 y 3.8 a 3.10 se hacen en **kind**, sobre `ct-lab`. La 3.7 monta un clúster real en tres VM que reutilizarás en las UD04 y UD05. Escribe todos los manifiestos en ficheros dentro de `~/ud03/` y aplícalos con `kubectl apply -f`: así tendrás todo en Git.

---

## Práctica 3.1 · Primer clúster con kind

{{< practica num="3.1" tipo="Guiada" duracion="2 h" nivel="1" ra="RA4: a, b" entorno="ct-lab · Docker Engine · kind · kubectl" entrega="no" >}}

#### Objetivo

Crear un clúster de tres nodos con kind, conectar `kubectl` e identificar los componentes de la arquitectura.

#### Desarrollo

{{% steps %}}

1. **Instala `kubectl` y `kind`:**

    ```bash
    cd /tmp
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -m 0755 kubectl /usr/local/bin/kubectl
    curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/latest/download/kind-linux-amd64
    sudo install -m 0755 kind /usr/local/bin/kind
    kubectl version --client && kind version
    echo 'source <(kubectl completion bash)' >> ~/.bashrc
    echo 'alias k=kubectl; complete -o default -F __start_kubectl k' >> ~/.bashrc
    source ~/.bashrc
    ```

2. **Fichero de configuración del clúster** `~/ud03/kind-curso.yaml`. Reservamos ya los puertos 80 y 443 para la UD04:

    ```yaml
    kind: Cluster
    apiVersion: kind.x-k8s.io/v1alpha4
    name: curso
    nodes:
      - role: control-plane
        extraPortMappings:
          - containerPort: 30080
            hostPort: 80
          - containerPort: 30443
            hostPort: 443
      - role: worker
      - role: worker
    ```

3. **Crea el clúster:**

    ```bash
    kind create cluster --config ~/ud03/kind-curso.yaml
    kubectl cluster-info
    kubectl get nodes -o wide
    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
    ```

    Cada «nodo» es un contenedor de Docker que ejecuta systemd, kubelet y containerd.

4. **Identifica los componentes del plano de control:**

    ```bash
    kubectl get pods -n kube-system -o wide
    docker exec curso-control-plane ls /etc/kubernetes/manifests
    docker exec curso-control-plane crictl ps
    ```

    Relaciona cada Pod con la tabla de la teoría: `etcd`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, `kube-proxy` (uno por nodo), `coredns`, `kindnet` (el CNI de kind).

5. **Habla directamente con la API:**

    ```bash
    kubectl get --raw /healthz ; echo
    kubectl api-resources | head -20
    kubectl proxy --port 8001 &
    curl -s localhost:8001/api/v1/namespaces/kube-system/pods | jq '.items[].metadata.name'
    kill %1
    ```

6. **El kubeconfig:**

    ```bash
    kubectl config get-contexts
    kubectl config view --minify
    ```

7. **Prueba de fallo del plano de control.** Para el contenedor del plano de control y prueba `kubectl get nodes`; vuelve a arrancarlo:

    ```bash
    docker stop curso-control-plane
    kubectl get nodes          # error: no hay apiserver
    docker start curso-control-plane ; sleep 30 ; kubectl get nodes
    ```

{{% /steps %}}

#### Comprobación

- [ ] `kubectl get nodes` muestra tres nodos `Ready` (uno `control-plane`).
- [ ] Sabes decir en qué nodo se ejecutan etcd y el scheduler, y por qué hay un `kube-proxy` en cada nodo.
- [ ] Con el plano de control parado no funciona `kubectl`, pero los Pods de los nodos de trabajo siguen ejecutándose.

#### Errores habituales

- **`failed to create cluster: ... too many open files`**: sube los límites de inotify: `sudo sysctl fs.inotify.max_user_watches=524288 fs.inotify.max_user_instances=512` (y guárdalo en `/etc/sysctl.d/`).
- **El puerto 80 ya está en uso**: algún contenedor de la UD02 lo publica. Páralo antes de crear el clúster.

#### Ampliación

Instala **Minikube** con el *driver* `docker` y compara: número de nodos, complementos disponibles (`minikube addons list`) y tiempo de arranque.

---

## Práctica 3.2 · Pods y manifiestos YAML

{{< practica num="3.2" tipo="Guiada" duracion="2 h" nivel="1" ra="RA4: e, f" entorno="kind · kubectl" entrega="no" >}}

#### Objetivo

Crear Pods de forma imperativa y declarativa, trabajar con etiquetas y espacios de nombres, y depurar Pods que fallan.

#### Desarrollo

{{% steps %}}

1. **Imperativo y generador de plantillas:**

    ```bash
    kubectl run prueba --image=nginx:1.29-alpine
    kubectl get pods -o wide
    kubectl run web --image=nginx:1.29-alpine --port=80 --labels=app=web --dry-run=client -o yaml > ~/ud03/pod-web.yaml
    kubectl delete pod prueba
    ```

2. **Espacio de nombres de trabajo:**

    ```bash
    kubectl create namespace practicas
    kubectl config set-context --current --namespace=practicas
    ```

3. **Pod con dos contenedores** (`~/ud03/pod-sidecar.yaml`). El *sidecar* lee el registro que escribe el principal:

    ```yaml
    apiVersion: v1
    kind: Pod
    metadata:
      name: web-sidecar
      labels: {app: web, entorno: pruebas}
    spec:
      initContainers:
        - name: preparar
          image: busybox:1.37
          command: ["sh", "-c", "echo '<h1>Preparado por el init container</h1>' > /html/index.html"]
          volumeMounts: [{name: html, mountPath: /html}]
      containers:
        - name: nginx
          image: nginx:1.29-alpine
          ports: [{containerPort: 80}]
          volumeMounts:
            - {name: html, mountPath: /usr/share/nginx/html}
            - {name: logs, mountPath: /var/log/nginx}
        - name: lector-logs
          image: busybox:1.37
          command: ["sh", "-c", "touch /logs/access.log; tail -f /logs/access.log"]
          volumeMounts: [{name: logs, mountPath: /logs}]
      volumes:
        - {name: html, emptyDir: {}}
        - {name: logs, emptyDir: {}}
    ```

    ```bash
    kubectl apply -f ~/ud03/pod-sidecar.yaml
    kubectl get pod web-sidecar -w       # Init:0/1 → PodInitializing → Running (Ctrl+C)
    kubectl port-forward pod/web-sidecar 8080:80 &
    curl -s localhost:8080 ; curl -s localhost:8080
    kubectl logs web-sidecar -c lector-logs
    kubectl exec web-sidecar -c lector-logs -- wget -qO- localhost:80   # misma red: localhost
    kill %1
    ```

4. **Etiquetas y selectores:**

    ```bash
    kubectl get pods --show-labels
    kubectl label pod web-sidecar version=1
    kubectl get pods -l 'app=web,entorno in (pruebas,desarrollo)'
    kubectl explain pod.spec.containers.ports
    ```

5. **Depura tres Pods rotos.** Aplica cada uno, averigua el problema con `get`, `describe` y `logs` y corrígelo en el YAML:

    ```bash
    kubectl run roto1 --image=nginx:1.99-noexiste
    kubectl run roto2 --image=busybox:1.37 -- sh -c "echo arranco; exit 1"
    kubectl run roto3 --image=nginx:1.29-alpine --overrides='{"spec":{"containers":[{"name":"roto3","image":"nginx:1.29-alpine","resources":{"requests":{"cpu":"50"}}}]}}'
    kubectl get pods
    ```

6. **¿Se repara solo un Pod suelto?** Borra `web-sidecar` y comprueba que no vuelve. Ahí entran los Deployments.

{{% /steps %}}

#### Comprobación

- [ ] El Pod `web-sidecar` pasa por `Init` y muestra el HTML preparado por el *init container*.
- [ ] Explicas el estado de cada Pod roto: `ImagePullBackOff`, `CrashLoopBackOff` y `Pending` (`Insufficient cpu`).

#### Errores habituales

- **`error: unable to forward port`**: el Pod aún no está `Running`.
- **Indentación YAML**: un error de espacios produce `error converting YAML to JSON`. Usa un editor con resaltado y 2 espacios, nunca tabuladores.

#### Ampliación

Crea un Pod con `restartPolicy: Never` que ejecute `date` y termine. ¿En qué fase queda? ¿Y con `OnFailure` si el comando falla?

---

## Práctica 3.3 · ReplicaSets, Deployments y autocuración

{{< practica num="3.3" tipo="Guiada" duracion="2 h" nivel="1" ra="RA4: e, f, h" entorno="kind · kubectl" entrega="no" >}}

#### Objetivo

Desplegar una aplicación con un Deployment, comprobar la autocuración y el reparto entre nodos, y escalarla.

#### Desarrollo

{{% steps %}}

1. **Deployment + Service** (`~/ud03/hola.yaml`). La imagen muestra el nombre del Pod que responde:

    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: hola
      labels: {app: hola}
    spec:
      replicas: 3
      selector:
        matchLabels: {app: hola}
      template:
        metadata:
          labels: {app: hola}
        spec:
          containers:
            - name: hola
              image: registry.k8s.io/e2e-test-images/agnhost:2.39
              args: ["netexec", "--http-port=8080"]
              ports: [{containerPort: 8080}]
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: hola
    spec:
      selector: {app: hola}
      ports:
        - port: 80
          targetPort: 8080
    ```

    ```bash
    kubectl apply -f ~/ud03/hola.yaml
    kubectl get deploy,rs,pods -o wide
    ```

2. **La jerarquía Deployment → ReplicaSet → Pod:**

    ```bash
    kubectl describe rs -l app=hola | grep -E 'Controlled By|Replicas'
    kubectl get pod -l app=hola -o jsonpath='{.items[0].metadata.ownerReferences[0].kind}{"\n"}'
    ```

3. **Balanceo a través del Service:**

    ```bash
    kubectl run cliente --rm -it --image=busybox:1.37 --restart=Never -- \
      sh -c 'for i in 1 2 3 4 5 6; do wget -qO- http://hola/hostname; echo; done'
    ```

4. **Autocuración.** En una terminal observa los Pods; en otra borra uno:

    ```bash
    kubectl get pods -l app=hola -w
    kubectl delete pod $(kubectl get pod -l app=hola -o name | head -1)
    ```

5. **Fallo de un nodo.** Para un nodo de trabajo y mira qué pasa con sus Pods:

    ```bash
    docker stop curso-worker2
    kubectl get nodes -w       # NotReady a los ~40 s
    kubectl get pods -o wide -w   # al cabo de ~5 min se recrean en otro nodo
    docker start curso-worker2
    ```

    > [!NOTE]
    > Kubernetes espera unos 5 minutos (*toleration* `node.kubernetes.io/unreachable`) antes de desalojar los Pods de un nodo que no responde: puede ser un corte de red momentáneo. Ese tiempo se ajusta por Pod con `tolerationSeconds`.

6. **Escalado manual y declarativo:**

    ```bash
    kubectl scale deployment hola --replicas=6
    kubectl get pods -o wide        # repartidos entre los nodos de trabajo
    sed -i 's/replicas: 3/replicas: 4/' ~/ud03/hola.yaml && kubectl apply -f ~/ud03/hola.yaml
    ```

    ¿Por qué el `apply` ha dejado 4 y no 6? Porque el YAML es la fuente de verdad.

7. **Repartir réplicas entre nodos.** Añade a la plantilla:

    ```yaml
          topologySpreadConstraints:
            - maxSkew: 1
              topologyKey: kubernetes.io/hostname
              whenUnsatisfiable: DoNotSchedule
              labelSelector:
                matchLabels: {app: hola}
    ```

{{% /steps %}}

#### Comprobación

- [ ] El cliente recibe respuestas de al menos dos Pods distintos.
- [ ] Al borrar un Pod aparece otro con distinto nombre en segundos.
- [ ] Con un nodo parado, los Pods acaban recreándose en el otro nodo.
- [ ] Explicas por qué `apply` revierte el `scale` imperativo.

#### Ampliación

Convierte el Deployment en un ReplicaSet suelto (`kind: ReplicaSet`) y cambia la imagen. ¿Se actualizan los Pods? ¿Qué aporta el Deployment?

---

## Práctica 3.4 · Actualización progresiva y vuelta atrás

{{< practica num="3.4" tipo="Guiada" duracion="2 h" nivel="2" ra="RA4: g" entorno="kind · kubectl" entrega="ud03/p3.4/ con el YAML y la salida comentada de rollout history" >}}

#### Objetivo

Actualizar una aplicación sin corte de servicio, detectar una versión defectuosa y volver atrás.

#### Desarrollo

{{% steps %}}

1. **Aplicación versionada** (`~/ud03/versiones.yaml`): usa la imagen de ejemplo `podinfo`, que muestra su versión.

    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: podinfo
      annotations:
        kubernetes.io/change-cause: "Versión inicial 6.7.0"
    spec:
      replicas: 4
      revisionHistoryLimit: 5
      strategy:
        type: RollingUpdate
        rollingUpdate: {maxSurge: 1, maxUnavailable: 0}
      selector:
        matchLabels: {app: podinfo}
      template:
        metadata:
          labels: {app: podinfo}
        spec:
          containers:
            - name: podinfo
              image: ghcr.io/stefanprodan/podinfo:6.7.0
              ports: [{containerPort: 9898}]
              readinessProbe:
                httpGet: {path: /readyz, port: 9898}
                periodSeconds: 3
    ---
    apiVersion: v1
    kind: Service
    metadata: {name: podinfo}
    spec:
      selector: {app: podinfo}
      ports: [{port: 80, targetPort: 9898}]
    ```

2. **Tráfico continuo.** En una segunda terminal, deja un cliente consultando la versión:

    ```bash
    kubectl run vigia --image=busybox:1.37 --restart=Never -- \
      sh -c 'while true; do wget -qO- -T 1 http://podinfo/version 2>&1 | grep -o "\"version\": \"[^\"]*\"" || echo "FALLO"; sleep 0.5; done'
    kubectl logs -f vigia
    ```

3. **Actualiza** y observa la transición en la otra terminal:

    ```bash
    kubectl set image deployment/podinfo podinfo=ghcr.io/stefanprodan/podinfo:6.7.1
    kubectl annotate deployment/podinfo kubernetes.io/change-cause="Actualización a 6.7.1" --overwrite
    kubectl rollout status deployment/podinfo
    kubectl get rs -l app=podinfo
    ```

    El cliente pasa de 6.7.0 a 6.7.1 **sin ningún `FALLO`**.

4. **Una versión defectuosa.** Despliega una etiqueta que no existe:

    ```bash
    kubectl set image deployment/podinfo podinfo=ghcr.io/stefanprodan/podinfo:9.9.9
    kubectl annotate deployment/podinfo kubernetes.io/change-cause="Versión rota 9.9.9" --overwrite
    kubectl rollout status deployment/podinfo --timeout=60s
    kubectl get pods -l app=podinfo
    ```

    Hay un Pod nuevo en `ImagePullBackOff`, pero **siguen 4 Pods antiguos sirviendo** (`maxUnavailable: 0`). El cliente no ve fallos.

5. **Vuelta atrás:**

    ```bash
    kubectl rollout history deployment/podinfo
    kubectl rollout undo deployment/podinfo
    kubectl rollout status deployment/podinfo
    kubectl rollout history deployment/podinfo --revision=2
    ```

6. **Sin readinessProbe.** Quita la sonda del YAML, aplícalo y repite la actualización a 6.7.0 con `maxUnavailable: 2`. ¿Aparecen `FALLO` en el cliente? Explica por qué.

7. **Recreate.** Cambia la estrategia a `type: Recreate` (borra el bloque `rollingUpdate`) y actualiza. Cuenta los fallos.

{{% /steps %}}

#### Comprobación

- [ ] Evidencia del cliente sin fallos durante el *rolling update* con sonda.
- [ ] La versión rota no llega a dejar el servicio sin réplicas.
- [ ] `rollout history` con las causas de cambio y el *undo* funcionando.
- [ ] Explicación de los fallos sin sonda y con `Recreate`.

#### Errores habituales

- **`change-cause` vacío**: la anotación se pone después de cada cambio (o en el YAML de cada versión).
- `rollout undo` vuelve a la revisión **anterior**: si haces dos *undo* seguidos, vuelves a la rota.

#### Ampliación

Implementa un **canary**: un segundo Deployment `podinfo-canary` con 1 réplica de la versión nueva y la misma etiqueta `app: podinfo`. ¿Qué porcentaje del tráfico recibe? ¿Cómo lo promocionas?

---

## Práctica 3.5 · Configuración, secretos, sondas y recursos

{{< practica num="3.5" tipo="Guiada" duracion="2 h" nivel="2" ra="RA4: e, f" entorno="kind · kubectl" entrega="no" >}}

#### Objetivo

Separar configuración y secretos de la imagen, montarlos como variables y ficheros, y definir sondas, *requests* y *limits*.

#### Desarrollo

{{% steps %}}

1. **ConfigMap con una variable y un fichero completo de nginx:**

    ```bash
    mkdir -p ~/ud03/config && cd ~/ud03/config
    cat > default.conf <<'EOF'
    server {
        listen 80;
        location / { return 200 "Entorno: $entorno · Mensaje desde ConfigMap\n"; }
        location /salud { return 200 "ok\n"; }
        set $entorno "pruebas";
    }
    EOF
    kubectl create configmap web-config --from-file=default.conf --from-literal=ENTORNO=pruebas
    kubectl create secret generic web-secreto --from-literal=API_KEY='k8s-curso-2026'
    kubectl get secret web-secreto -o yaml
    kubectl get secret web-secreto -o jsonpath='{.data.API_KEY}' | base64 -d ; echo
    ```

2. **Deployment que lo usa todo** (`~/ud03/config/web.yaml`):

    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata: {name: web}
    spec:
      replicas: 2
      selector: {matchLabels: {app: web}}
      template:
        metadata: {labels: {app: web}}
        spec:
          containers:
            - name: nginx
              image: nginx:1.29-alpine
              env:
                - name: ENTORNO
                  valueFrom: {configMapKeyRef: {name: web-config, key: ENTORNO}}
                - name: API_KEY
                  valueFrom: {secretKeyRef: {name: web-secreto, key: API_KEY}}
              volumeMounts:
                - name: conf
                  mountPath: /etc/nginx/conf.d
                  readOnly: true
              startupProbe:
                httpGet: {path: /salud, port: 80}
                failureThreshold: 10
                periodSeconds: 2
              readinessProbe:
                httpGet: {path: /salud, port: 80}
                periodSeconds: 5
              livenessProbe:
                httpGet: {path: /salud, port: 80}
                periodSeconds: 10
              resources:
                requests: {cpu: 50m, memory: 32Mi}
                limits: {cpu: 200m, memory: 64Mi}
          volumes:
            - name: conf
              configMap:
                name: web-config
                items: [{key: default.conf, path: default.conf}]
    ```

    ```bash
    kubectl apply -f web.yaml
    POD=$(kubectl get pod -l app=web -o name | head -1)
    kubectl exec $POD -- env | grep -E 'ENTORNO|API_KEY'
    kubectl exec $POD -- cat /etc/nginx/conf.d/default.conf
    kubectl exec $POD -- wget -qO- localhost
    kubectl get pod -l app=web -o jsonpath='{.items[0].status.qosClass}' ; echo
    ```

3. **Cambiar la configuración.** Edita el ConfigMap (cambia «pruebas» por «producción» en `default.conf`) y aplícalo:

    ```bash
    kubectl create configmap web-config --from-file=default.conf --from-literal=ENTORNO=produccion \
      --dry-run=client -o yaml | kubectl apply -f -
    sleep 60 ; kubectl exec $POD -- cat /etc/nginx/conf.d/default.conf | grep set   # el fichero cambió
    kubectl exec $POD -- env | grep ENTORNO                                         # la variable NO
    kubectl rollout restart deployment/web
    ```

    > [!NOTE]
    > nginx tampoco relee su configuración solo: aunque el fichero cambie, hay que recargarlo. El `rollout restart` crea Pods nuevos con todo actualizado.

4. **Liveness en acción.** Rompe la ruta de salud de un Pod y observa el reinicio:

    ```bash
    kubectl exec $POD -- sh -c "sed -i 's#/salud#/roto#' /etc/nginx/conf.d/default.conf" \
      || echo "El volumen del ConfigMap es de solo lectura: buena señal"
    kubectl exec $POD -- nginx -s stop
    kubectl get pods -l app=web -w      # RESTARTS sube a 1
    ```

5. **Límite de memoria superado.** Ejecuta un Pod que reserve más de lo permitido:

    ```bash
    kubectl run gloton --image=polinux/stress --restart=Never \
      --overrides='{"spec":{"containers":[{"name":"g","image":"polinux/stress","args":["stress","--vm","1","--vm-bytes","150M"],"resources":{"limits":{"memory":"100Mi"}}}]}}'
    sleep 10 ; kubectl get pod gloton ; kubectl describe pod gloton | grep -A3 "Last State\|State:"
    ```

{{% /steps %}}

#### Comprobación

- [ ] La variable y el fichero llegan al contenedor; el Secret se decodifica con `base64 -d`.
- [ ] El fichero montado cambia solo; la variable solo tras `rollout restart`.
- [ ] El Pod reinicia al fallar la liveness y el `gloton` termina `OOMKilled`.
- [ ] Sabes qué QoS tiene el Deployment y por qué.

#### Errores habituales

- **`CreateContainerConfigError`**: el ConfigMap o la clave referenciada no existe. Lo dice `describe`.
- **Nombres no válidos**: los nombres de objetos solo admiten minúsculas, números, `-` y `.` (sin tildes ni mayúsculas).

#### Ampliación

Monta el Secret como fichero en `/run/secrets/api_key` con `defaultMode: 0400` y comprueba los permisos desde dentro.

---

## Práctica 3.6 · StatefulSets, DaemonSets, Jobs y CronJobs

{{< practica num="3.6" tipo="Guiada" duracion="2 h" nivel="2" ra="RA4: f" entorno="kind · kubectl" entrega="no" >}}

#### Objetivo

Usar cada controlador para el tipo de carga que le corresponde y comprobar sus garantías.

#### Desarrollo

{{% steps %}}

1. **StatefulSet con identidad estable** (`~/ud03/sts.yaml`):

    ```yaml
    apiVersion: v1
    kind: Service
    metadata: {name: nodos}
    spec:
      clusterIP: None
      selector: {app: nodos}
      ports: [{port: 80}]
    ---
    apiVersion: apps/v1
    kind: StatefulSet
    metadata: {name: nodo}
    spec:
      serviceName: nodos
      replicas: 3
      selector: {matchLabels: {app: nodos}}
      template:
        metadata: {labels: {app: nodos}}
        spec:
          containers:
            - name: web
              image: nginx:1.29-alpine
              command: ["sh", "-c", "echo \"Soy $(hostname)\" > /usr/share/nginx/html/index.html; date >> /usr/share/nginx/html/historial; exec nginx -g 'daemon off;'"]
              volumeMounts: [{name: datos, mountPath: /usr/share/nginx/html}]
      volumeClaimTemplates:
        - metadata: {name: datos}
          spec:
            accessModes: ["ReadWriteOnce"]
            resources: {requests: {storage: 100Mi}}
    ```

    ```bash
    kubectl apply -f ~/ud03/sts.yaml
    kubectl get pods -l app=nodos -w          # nodo-0, luego nodo-1, luego nodo-2
    kubectl get pvc
    kubectl run dns --rm -it --image=busybox:1.37 --restart=Never -- \
      sh -c 'nslookup nodos; wget -qO- nodo-1.nodos'
    ```

2. **Identidad y datos estables.** Borra `nodo-1`: vuelve con el **mismo nombre** y el **mismo volumen**:

    ```bash
    kubectl delete pod nodo-1
    kubectl wait --for=condition=Ready pod/nodo-1
    kubectl exec nodo-1 -- cat /usr/share/nginx/html/historial   # dos líneas: dos arranques
    kubectl scale sts nodo --replicas=1 ; kubectl get pvc         # los PVC no se borran
    ```

3. **DaemonSet: un Pod por nodo.**

    ```yaml
    apiVersion: apps/v1
    kind: DaemonSet
    metadata: {name: agente}
    spec:
      selector: {matchLabels: {app: agente}}
      template:
        metadata: {labels: {app: agente}}
        spec:
          tolerations:
            - key: node-role.kubernetes.io/control-plane
              effect: NoSchedule
          containers:
            - name: agente
              image: busybox:1.37
              command: ["sh", "-c", "while true; do echo \"$(date) agente en $NODO\"; sleep 30; done"]
              env:
                - name: NODO
                  valueFrom: {fieldRef: {fieldPath: spec.nodeName}}
    ```

    ```bash
    kubectl apply -f ~/ud03/ds.yaml
    kubectl get pods -l app=agente -o wide     # uno en cada uno de los 3 nodos
    ```

    Quita la *toleration* y vuelve a aplicar: ¿cuántos Pods hay ahora?

4. **Job con reintentos y paralelismo:**

    ```yaml
    apiVersion: batch/v1
    kind: Job
    metadata: {name: calculo-pi}
    spec:
      completions: 4
      parallelism: 2
      backoffLimit: 3
      ttlSecondsAfterFinished: 600
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: pi
              image: perl:5.40-slim
              command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(1500)"]
    ```

    ```bash
    kubectl apply -f ~/ud03/job.yaml
    kubectl get jobs -w
    kubectl logs job/calculo-pi | head -c 80 ; echo
    ```

5. **CronJob de copia** cada 2 minutos:

    ```yaml
    apiVersion: batch/v1
    kind: CronJob
    metadata: {name: copia}
    spec:
      schedule: "*/2 * * * *"
      timeZone: "Europe/Madrid"
      concurrencyPolicy: Forbid
      successfulJobsHistoryLimit: 3
      jobTemplate:
        spec:
          template:
            spec:
              restartPolicy: OnFailure
              containers:
                - name: copia
                  image: busybox:1.37
                  command: ["sh", "-c", "echo Copia simulada $(date) && sleep 5"]
    ```

    ```bash
    kubectl apply -f ~/ud03/cronjob.yaml
    kubectl create job copia-manual --from=cronjob/copia    # lanzarlo ahora
    kubectl get cronjob,jobs
    ```

{{% /steps %}}

#### Comprobación

- [ ] Los Pods del StatefulSet se llaman `nodo-0..2` y se crean en orden; `nodo-1.nodos` se resuelve por DNS.
- [ ] El historial de `nodo-1` conserva los dos arranques.
- [ ] El DaemonSet tiene un Pod por nodo (con la *toleration*).
- [ ] El Job completa 4 ejecuciones de 2 en 2; el CronJob genera trabajos cada 2 minutos.

#### Ampliación

Haz que el Job falle (`exit 1`) y observa cómo se reintenta hasta `backoffLimit` y queda `Failed`.

---

## Práctica 3.7 · Clúster de tres nodos con kubeadm

{{< practica num="3.7" tipo="Guiada" duracion="5 h" nivel="3" ra="RA4: c, d · RA2: a" entorno="Debian 13 ×3 · containerd · kubeadm/kubelet/kubectl 1.36 · Calico" entrega="ud03/p3.7-kubeadm.md: procedimiento, salidas de comprobación y comparación con un servicio gestionado" >}}

#### Objetivo

Montar un clúster de producción «de verdad» con un plano de control y dos nodos de trabajo, con red Calico, que usarás en el resto del curso.

#### Requisitos

Las VM `k8s-cp`, `k8s-w1` y `k8s-w2` del [entorno](/guia/entorno/) con IP fija en `192.168.56.0/24`, nombres en `/etc/hosts` y **una instantánea de cada una** antes de empezar ⚠️.

#### Desarrollo

{{% steps %}}

1. **En los tres nodos: desactiva la *swap*.** El kubelet no arranca con *swap* activa (salvo configuración expresa):

    ```bash
    sudo swapoff -a
    sudo sed -i '/\sswap\s/ s/^/#/' /etc/fstab
    free -h
    ```

2. **En los tres nodos: módulos y parámetros del núcleo.**

    ```bash
    cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
    overlay
    br_netfilter
    EOF
    sudo modprobe overlay && sudo modprobe br_netfilter
    cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
    net.bridge.bridge-nf-call-iptables  = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    net.ipv4.ip_forward                 = 1
    EOF
    sudo sysctl --system | grep -E 'ip_forward|bridge-nf'
    ```

3. **En los tres nodos: containerd con el *driver* de cgroups de systemd.**

    ```bash
    sudo apt install -y containerd
    sudo mkdir -p /etc/containerd
    containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
    sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
    grep -n SystemdCgroup /etc/containerd/config.toml
    sudo systemctl restart containerd && sudo systemctl enable containerd
    ```

    > [!IMPORTANT]
    > kubelet y containerd deben usar **el mismo** *driver* de cgroups. Con systemd como init, ambos deben usar `systemd`. Si no coinciden, los Pods del plano de control se reinician sin parar.

4. **En los tres nodos: repositorio de Kubernetes 1.36 y paquetes.**

    ```bash
    sudo apt install -y apt-transport-https ca-certificates curl gpg
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key | \
      sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' | \
      sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo apt update
    sudo apt install -y kubelet kubeadm kubectl
    sudo apt-mark hold kubelet kubeadm kubectl
    ```

    `apt-mark hold` evita que una actualización rutinaria cambie la versión de Kubernetes: las actualizaciones del clúster se hacen con `kubeadm upgrade`, en orden.

5. **En cada nodo: IP del kubelet.** En VirtualBox todas las VM tienen la misma IP en el adaptador NAT (`10.0.2.15`), así que hay que indicar la de la red del laboratorio (cambia la IP en cada nodo):

    ```bash
    echo 'KUBELET_EXTRA_ARGS="--node-ip=192.168.56.11"' | sudo tee /etc/default/kubelet
    ```

6. **Solo en `k8s-cp`: inicializa el plano de control.** La red de los Pods no puede solaparse con la del laboratorio:

    ```bash
    sudo kubeadm init \
      --apiserver-advertise-address=192.168.56.11 \
      --pod-network-cidr=10.244.0.0/16 \
      --node-name k8s-cp | tee ~/kubeadm-init.log
    mkdir -p ~/.kube
    sudo cp /etc/kubernetes/admin.conf ~/.kube/config
    sudo chown "$(id -u):$(id -g)" ~/.kube/config
    kubectl get nodes        # NotReady: falta la red
    kubectl get pods -n kube-system
    ```

    Guarda la orden `kubeadm join ...` del final del registro.

7. **Solo en `k8s-cp`: red con Calico** (operador de Tigera). Comprueba la última versión estable en las *releases* de Calico y ajústala:

    ```bash
    CALICO=v3.30.3
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/$CALICO/manifests/operator-crds.yaml
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/$CALICO/manifests/tigera-operator.yaml
    cat > calico.yaml <<'EOF'
    apiVersion: operator.tigera.io/v1
    kind: Installation
    metadata: {name: default}
    spec:
      calicoNetwork:
        ipPools:
          - name: default-ipv4-ippool
            cidr: 10.244.0.0/16
            blockSize: 26
            encapsulation: VXLANCrossSubnet
            natOutgoing: Enabled
            nodeSelector: all()
        nodeAddressAutodetectionV4:
          cidrs: ["192.168.56.0/24"]
    ---
    apiVersion: operator.tigera.io/v1
    kind: APIServer
    metadata: {name: default}
    spec: {}
    EOF
    kubectl create -f calico.yaml
    watch kubectl get pods -n calico-system      # todos Running (Ctrl+C)
    kubectl get nodes                            # k8s-cp Ready
    ```

8. **En `k8s-w1` y `k8s-w2`: únete al clúster** con la orden guardada:

    ```bash
    sudo kubeadm join 192.168.56.11:6443 --token <token> \
      --discovery-token-ca-cert-hash sha256:<hash>
    ```

    Si el *token* ha caducado (24 h), genera otra orden en `k8s-cp`: `kubeadm token create --print-join-command`.

9. **Comprobación del clúster** desde `k8s-cp`:

    ```bash
    kubectl get nodes -o wide
    kubectl label node k8s-w1 k8s-w2 node-role.kubernetes.io/worker=
    kubectl create deployment prueba --image=nginx:1.29-alpine --replicas=4
    kubectl get pods -o wide                 # repartidos en w1 y w2, IP 10.244.x.x
    kubectl expose deployment prueba --port=80
    kubectl run c --rm -it --image=busybox:1.37 --restart=Never -- wget -qO- prueba | head -4
    kubectl delete deployment,svc prueba
    ```

10. **Gestiona el clúster desde `ct-lab`.** Copia el kubeconfig y añádelo como un contexto más:

    ```bash
    # en ct-lab
    scp alumno@k8s-cp:.kube/config ~/.kube/kubeadm.conf
    KUBECONFIG=~/.kube/config:~/.kube/kubeadm.conf kubectl config view --flatten > /tmp/cfg && mv /tmp/cfg ~/.kube/config
    kubectl config get-contexts
    kubectl config rename-context kubernetes-admin@kubernetes kubeadm
    kubectl --context kubeadm get nodes
    ```

11. **Copia de seguridad de etcd** (en `k8s-cp`). Sin ella, perder el plano de control es perder el clúster:

    ```bash
    sudo apt install -y etcd-client
    sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
      --cacert=/etc/kubernetes/pki/etcd/ca.crt \
      --cert=/etc/kubernetes/pki/etcd/server.crt \
      --key=/etc/kubernetes/pki/etcd/server.key \
      snapshot save /root/etcd-$(date +%F).db
    sudo ls -lh /root/etcd-*.db
    ```

12. **Prueba de fallo de un nodo de trabajo.** Despliega 4 réplicas, apaga `k8s-w2` desde VirtualBox y vacía el nodo como haría un administrador:

    ```bash
    kubectl create deployment ha --image=nginx:1.29-alpine --replicas=4
    kubectl drain k8s-w2 --ignore-daemonsets --delete-emptydir-data   # mantenimiento planificado
    kubectl get pods -o wide                                          # todo en w1
    kubectl uncordon k8s-w2
    ```

{{% /steps %}}

#### Comprobación

- [ ] `kubectl get nodes -o wide`: tres nodos `Ready`, versión v1.36.x, `INTERNAL-IP` en 192.168.56.0/24 y *runtime* containerd.
- [ ] Todos los Pods de `kube-system` y `calico-system` en `Running`.
- [ ] Pods en ambos nodos de trabajo con IP de 10.244.0.0/16 que se comunican entre nodos.
- [ ] Fichero de *snapshot* de etcd.
- [ ] En `p3.7-kubeadm.md`, una tabla comparando tu clúster con EKS/GKE/AKS: quién gestiona etcd, actualizaciones, alta disponibilidad de la API, balanceadores y coste.

#### Errores habituales

- **`[ERROR Swap]`** o kubelet que no arranca: la *swap* sigue activa. `swapon --show` debe salir vacío.
- **`[ERROR FileContent--proc-sys-net-ipv4-ip_forward]`**: falta el `sysctl`.
- **Nodos con `INTERNAL-IP 10.0.2.15`**: no se configuró `--node-ip`. Corrígelo, `sudo systemctl restart kubelet`.
- **Pods de `kube-system` reiniciándose**: *driver* de cgroups distinto entre containerd y kubelet.
- **Pods en `ContainerCreating` con `failed to setup network`**: Calico aún no está listo o el CIDR no coincide con `--pod-network-cidr`.
- **Para empezar de cero**: `sudo kubeadm reset -f` en cada nodo, borra `/etc/cni/net.d` y `~/.kube`, o vuelve a la instantánea.

#### Ampliación

Actualiza el clúster a la siguiente versión menor siguiendo la guía oficial `kubeadm upgrade` (plano de control primero, luego cada nodo con `drain`/`uncordon`). Hazlo solo con instantáneas recientes.

---

## Práctica 3.8 · Escalado automático con HPA

{{< practica num="3.8" tipo="Guiada" duracion="2 h" nivel="2" ra="RA4: h" entorno="kind · metrics-server · HorizontalPodAutoscaler" entrega="ud03/p3.8/ con el YAML del HPA y la evolución de las réplicas durante la prueba de carga" >}}

#### Objetivo

Instalar metrics-server, configurar un HPA y comprobar con una prueba de carga cómo sube y baja el número de réplicas.

#### Desarrollo

{{% steps %}}

1. **metrics-server** (en kind hace falta aceptar los certificados autofirmados del kubelet):

    ```bash
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    kubectl -n kube-system patch deployment metrics-server --type=json \
      -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
    kubectl -n kube-system rollout status deployment metrics-server
    sleep 30 ; kubectl top nodes
    ```

2. **Aplicación que consume CPU** (ejemplo oficial de Kubernetes):

    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata: {name: php-apache}
    spec:
      selector: {matchLabels: {run: php-apache}}
      template:
        metadata: {labels: {run: php-apache}}
        spec:
          containers:
            - name: php-apache
              image: registry.k8s.io/hpa-example
              ports: [{containerPort: 80}]
              resources:
                requests: {cpu: 200m}
                limits: {cpu: 500m}
    ---
    apiVersion: v1
    kind: Service
    metadata: {name: php-apache}
    spec:
      selector: {run: php-apache}
      ports: [{port: 80}]
    ```

3. **HPA declarativo** (`~/ud03/hpa.yaml`):

    ```yaml
    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    metadata: {name: php-apache}
    spec:
      scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: php-apache}
      minReplicas: 1
      maxReplicas: 8
      metrics:
        - type: Resource
          resource:
            name: cpu
            target: {type: Utilization, averageUtilization: 50}
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 60
    ```

4. **Prueba de carga.** Terminal 1: `kubectl get hpa php-apache -w`. Terminal 2:

    ```bash
    kubectl run carga --image=busybox:1.37 --restart=Never -- \
      sh -c "while sleep 0.01; do wget -q -O- http://php-apache; done"
    ```

    Anota cada minuto el `%` de CPU y las réplicas. A los 5 minutos borra el generador (`kubectl delete pod carga`) y observa el descenso.

5. **Comprueba el cálculo** con los valores de un momento concreto: `⌈réplicas × uso / objetivo⌉`.

6. **Qué pasa sin *requests*.** Quita `requests` del Deployment, aplica y mira `kubectl get hpa`: `<unknown>`. `kubectl describe hpa` explica el motivo.

{{% /steps %}}

#### Comprobación

- [ ] `kubectl top pods` funciona.
- [ ] Tabla/gráfica con la evolución de CPU y réplicas: sube con la carga, baja tras quitarla (respetando la estabilización).
- [ ] Explicación del `<unknown>` sin *requests*.

#### Ampliación

Añade una segunda métrica de memoria al HPA y un `scaleUp` limitado a 2 Pods por minuto con `behavior.scaleUp.policies`.

---

## Práctica 3.9 · Empaquetar con Helm y Kustomize

{{< practica num="3.9" tipo="Guiada" duracion="2 h" nivel="2" ra="RA4: i" entorno="kind · Helm · Kustomize (kubectl -k)" entrega="no" >}}

#### Objetivo

Instalar software de terceros con Helm gestionando sus versiones, y adaptar tus propios manifiestos a varios entornos con Kustomize.

#### Desarrollo

{{% steps %}}

1. **Instala Helm:**

    ```bash
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    helm version
    ```

2. **Un chart de terceros con valores propios:**

    ```bash
    helm repo add podinfo https://stefanprodan.github.io/podinfo
    helm repo update
    helm show values podinfo/podinfo > valores-por-defecto.yaml
    cat > mis-valores.yaml <<'EOF'
    replicaCount: 2
    ui:
      message: "Desplegado con Helm en el curso"
      color: "#0b6e8a"
    resources:
      requests: {cpu: 50m, memory: 32Mi}
    EOF
    helm install demo podinfo/podinfo -n helm-demo --create-namespace -f mis-valores.yaml
    helm list -n helm-demo
    kubectl get all -n helm-demo
    ```

3. **Ver lo que genera un chart sin instalarlo:** `helm template demo podinfo/podinfo -f mis-valores.yaml | less`.

4. ***Upgrade*, historial y *rollback*:**

    ```bash
    helm upgrade demo podinfo/podinfo -n helm-demo -f mis-valores.yaml --set replicaCount=4
    helm history demo -n helm-demo
    helm rollback demo 1 -n helm-demo
    kubectl get deploy -n helm-demo        # vuelve a 2 réplicas
    ```

5. **Tu propio chart.** Genera el esqueleto y estúdialo:

    ```bash
    helm create hola-chart
    tree hola-chart
    helm lint hola-chart
    helm install hola ./hola-chart -n helm-demo --set service.type=ClusterIP
    ```

6. **Kustomize: base y entornos.**

    ```bash
    mkdir -p ~/ud03/kustom/{base,overlays/desarrollo,overlays/produccion} && cd ~/ud03/kustom
    cp ~/ud03/hola.yaml base/hola.yaml
    cat > base/kustomization.yaml <<'EOF'
    resources: [hola.yaml]
    labels:
      - pairs: {proyecto: curso}
    EOF
    cat > overlays/desarrollo/kustomization.yaml <<'EOF'
    resources: [../../base]
    namespace: desarrollo
    namePrefix: dev-
    replicas: [{name: hola, count: 1}]
    EOF
    cat > overlays/produccion/kustomization.yaml <<'EOF'
    resources: [../../base]
    namespace: produccion
    replicas: [{name: hola, count: 4}]
    images:
      - name: registry.k8s.io/e2e-test-images/agnhost
        newTag: "2.40"
    EOF
    kubectl create namespace desarrollo ; kubectl create namespace produccion
    kubectl kustomize overlays/produccion | less
    kubectl apply -k overlays/desarrollo
    kubectl apply -k overlays/produccion
    kubectl get deploy -A -l proyecto=curso
    ```

7. **Limpieza:** `helm uninstall demo hola -n helm-demo`, `kubectl delete -k overlays/desarrollo`, `kubectl delete -k overlays/produccion`.

{{% /steps %}}

#### Comprobación

- [ ] `helm history` con tres revisiones y el *rollback* devolviendo 2 réplicas.
- [ ] `helm lint` sin errores en tu chart.
- [ ] Dos entornos desplegados desde la misma base: 1 réplica `dev-hola` y 4 réplicas `hola`.

#### Ampliación

Convierte los manifiestos de MiTienda en un chart propio con `values.yaml` para la imagen, las réplicas y los recursos de cada servicio.

---

## Práctica 3.10 · MiTienda en Kubernetes

{{< practica num="3.10" tipo="Proyecto" duracion="3 h" nivel="3" ra="RA4: e, f, g, h, i" entorno="kind (o el clúster kubeadm) · imágenes de la práctica 2.8" entrega="mitienda/k8s/ + docs/03-kubernetes.md con evidencias · Hito H3" >}}

#### Objetivo

Desplegar MiTienda completa de forma declarativa, con la base de datos como StatefulSet, la API con sondas y actualización progresiva, y comprobar su comportamiento ante fallos y versiones nuevas.

#### Requisitos

Imágenes `mitienda-api:1.0.0` y `mitienda-web:1.0.0` construidas en la práctica 2.8. Descarga los manifiestos y estúdialos antes de aplicarlos:

{{< descarga "recursos/mitienda/k8s/00-namespace.yaml" >}}
{{< descarga "recursos/mitienda/k8s/01-config.yaml" >}}
{{< descarga "recursos/mitienda/k8s/10-postgres.yaml" >}}
{{< descarga "recursos/mitienda/k8s/20-cache.yaml" >}}
{{< descarga "recursos/mitienda/k8s/30-api.yaml" >}}
{{< descarga "recursos/mitienda/k8s/40-web.yaml" >}}

```bash
cd ~/curso/mitienda && mkdir -p k8s && cd k8s
for f in 00-namespace 01-config 10-postgres 20-cache 30-api 40-web 50-gateway 60-hpa 70-networkpolicies; do
  wget -q "https://lorenalresusta.github.io/Contenedores/recursos/mitienda/k8s/$f.yaml"
done
```

#### Desarrollo

{{% steps %}}

1. **Carga las imágenes en kind** (en kubeadm, usa las del registro privado: ver ampliación):

    ```bash
    kind load docker-image mitienda-api:1.0.0 mitienda-web:1.0.0 --name curso
    ```

2. **Espacio de nombres, secreto y script de inicio** (los que no van a Git):

    ```bash
    kubectl apply -f 00-namespace.yaml
    kubectl -n mitienda create secret generic db-cred --from-literal=password="$(cat ../secrets/db_password.txt)"
    kubectl -n mitienda create configmap db-init --from-file=init.sql=../db/init.sql
    ```

3. **Despliega en orden:**

    ```bash
    kubectl apply -f 01-config.yaml -f 10-postgres.yaml -f 20-cache.yaml
    kubectl -n mitienda rollout status statefulset/db
    kubectl apply -f 30-api.yaml -f 40-web.yaml
    kubectl -n mitienda get all
    ```

4. **Prueba la aplicación:**

    ```bash
    kubectl -n mitienda port-forward svc/web 8080:80 &
    curl -s localhost:8080/api/salud | jq
    for i in $(seq 6); do curl -s localhost:8080/api/info | jq -r .contenedor; done
    ```

5. **Autocuración y dependencia.** Borra un Pod de la API y el Pod de la base de datos:

    ```bash
    kubectl -n mitienda delete pod -l app=api --wait=false | head -1
    kubectl -n mitienda delete pod db-0
    kubectl -n mitienda get pods -w
    ```

    Mientras `db-0` vuelve, los Pods de la API pasan a **no listos** (readiness con `/api/salud`) pero **no se reinician** (liveness con `/api/info`). Compruébalo en la columna `READY` y `RESTARTS`.

6. **Persistencia en el StatefulSet.** Compra dos unidades, borra `db-0`, espera y verifica que el stock se conserva.

7. **Versión nueva de la API.** Construye la 1.1.0 (cambia `APP_VERSION` en el Dockerfile y la variable en `01-config.yaml`), cárgala en kind y actualiza sin corte con un cliente consultando `/api/info` en bucle, como en la práctica 3.4. Después provoca una actualización a una etiqueta inexistente y vuelve atrás.

8. **Escalado.** Aplica `60-hpa.yaml` (HPA y PDB). Comprueba que con `kubectl drain` de un nodo nunca quedan menos de 2 réplicas de la API.

9. **Documenta** en `docs/03-kubernetes.md`: orden de despliegue, decisiones (por qué StatefulSet para `db`, por qué dos sondas distintas en la API, qué estrategia de actualización), evidencias y cómo se vuelve atrás.

{{% /steps %}}

#### Comprobación

- [ ] Todos los Pods `Running` y `READY` en el espacio `mitienda`.
- [ ] `/api/info` responde desde al menos dos Pods.
- [ ] Al borrar `db-0`, la API deja de estar lista sin reiniciarse y se recupera sola; los datos se conservan.
- [ ] Actualización a 1.1.0 sin fallos y *rollback* de la versión rota.
- [ ] El PDB impide bajar de 2 réplicas durante el `drain`.

#### Errores habituales

- **Pods de la API en `CreateContainerConfigError`**: falta el Secret `db-cred`.
- **`db-0` en `Pending`**: no hay StorageClass por defecto (kind trae `standard`; en kubeadm se instala en la UD04).
- **Pods rechazados con `violates PodSecurity "restricted"`**: el espacio de nombres exige el estándar *restricted* (UD05). Revisa el `securityContext` del manifiesto que hayas cambiado.
- **`ErrImageNeverPull` o `ImagePullBackOff` en kind**: no has hecho `kind load docker-image` de esa etiqueta exacta.

#### Ampliación

Despliega en el clúster **kubeadm** usando las imágenes del registro privado: crea en cada nodo `/etc/containerd/certs.d/registro.local:5000/hosts.toml` con la CA del registro, un Secret `docker-registry` y `imagePullSecrets` en los Deployments.
