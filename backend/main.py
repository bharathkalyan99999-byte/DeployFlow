from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from datetime import datetime
import subprocess
import socket


app = FastAPI(
    title="DeployFlow API",
    description="Self-Service Application Deployment Platform",
    version="0.5.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Temporary in-memory deployment history
deployment_history = []

# Local Kubernetes port-forward processes
port_forward_processes = {}


class DeploymentRequest(BaseModel):
    application_name: str
    environment: str
    cpu: str
    memory: str
    replicas: int


@app.get("/")
def home():
    return {
        "message": "Welcome to DeployFlow API"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/deployments")
def create_deployment(deployment: DeploymentRequest):

    # Connect to the local Kind cluster
    config.load_kube_config(context="kind-deployflow")

    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    # Kubernetes Deployment
    deployment_spec = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=deployment.application_name,
            labels={
                "app": deployment.application_name,
                "environment": deployment.environment
            }
        ),
        spec=client.V1DeploymentSpec(
            replicas=deployment.replicas,
            selector=client.V1LabelSelector(
                match_labels={
                    "app": deployment.application_name
                }
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": deployment.application_name,
                        "environment": deployment.environment
                    }
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name=deployment.application_name,
                            image="nginx:latest",
                            resources=client.V1ResourceRequirements(
                                requests={
                                    "cpu": deployment.cpu,
                                    "memory": deployment.memory
                                },
                                limits={
                                    "cpu": deployment.cpu,
                                    "memory": deployment.memory
                                }
                            )
                        )
                    ]
                )
            )
        )
    )

    # Create or update Deployment
    try:
        apps_v1.create_namespaced_deployment(
            namespace="default",
            body=deployment_spec
        )
        deployment_action = "created"

    except ApiException as e:
        if e.status == 409:
            apps_v1.replace_namespaced_deployment(
                name=deployment.application_name,
                namespace="default",
                body=deployment_spec
            )
            deployment_action = "updated"
        else:
            raise

    # Kubernetes Service
    service_spec = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=deployment.application_name
        ),
        spec=client.V1ServiceSpec(
            selector={
                "app": deployment.application_name
            },
            ports=[
                client.V1ServicePort(
                    protocol="TCP",
                    port=80,
                    target_port=80
                )
            ],
            type="NodePort"
        )
    )

    # Create or update Service
    try:
        core_v1.create_namespaced_service(
            namespace="default",
            body=service_spec
        )
        service_action = "created"

    except ApiException as e:
        if e.status == 409:
            core_v1.replace_namespaced_service(
                name=deployment.application_name,
                namespace="default",
                body=service_spec
            )
            service_action = "updated"
        else:
            raise

    # Record deployment history
    history_entry = {
        "application_name": deployment.application_name,
        "environment": deployment.environment,
        "cpu": deployment.cpu,
        "memory": deployment.memory,
        "replicas": deployment.replicas,
        "deployment": deployment_action,
        "service": service_action,
        "image": "nginx:latest",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    deployment_history.append(history_entry)

    return {
        "message": "Deployment completed successfully",
        "application_name": deployment.application_name,
        "environment": deployment.environment,
        "deployment": deployment_action,
        "service": service_action,
        "replicas": deployment.replicas,
        "image": "nginx:latest"
    }


@app.get("/deployments/{application_name}")
def get_deployment_status(application_name: str):

    config.load_kube_config(context="kind-deployflow")
    apps_v1 = client.AppsV1Api()

    try:
        deployment = apps_v1.read_namespaced_deployment(
            name=application_name,
            namespace="default"
        )

    except ApiException as e:
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Deployment '{application_name}' not found"
            )

        raise HTTPException(
            status_code=502,
            detail="Could not retrieve deployment from Kubernetes"
        )

    desired = deployment.spec.replicas or 0
    ready = deployment.status.ready_replicas or 0
    available = deployment.status.available_replicas or 0

    if ready == desired and desired > 0:
        status = "Running"
    elif ready > 0:
        status = "Partially Running"
    else:
        status = "Pending"

    return {
        "application_name": application_name,
        "status": status,
        "replicas": desired,
        "ready_replicas": ready,
        "available_replicas": available
    }


@app.get("/deployments")
def get_deployment_history():

    return {
        "count": len(deployment_history),
        "deployments": deployment_history
    }


@app.get("/deployments/{application_name}/logs")
def get_deployment_logs(application_name: str):

    config.load_kube_config(context="kind-deployflow")

    core_v1 = client.CoreV1Api()

    try:
        pods = core_v1.list_namespaced_pod(
            namespace="default",
            label_selector=f"app={application_name}"
        )

    except ApiException:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve pods from Kubernetes"
        )

    if not pods.items:
        raise HTTPException(
            status_code=404,
            detail=f"No pods found for deployment '{application_name}'"
        )

    pod_logs = []

    for pod in pods.items:

        pod_name = pod.metadata.name

        try:
            logs = core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace="default",
                tail_lines=100
            )

            # Ensure logs are returned as clean text
            if isinstance(logs, bytes):
                logs = logs.decode("utf-8", errors="replace")

            elif isinstance(logs, str) and logs.startswith(("b'", 'b"')):
                try:
                    import ast
                    decoded_logs = ast.literal_eval(logs)
                    if isinstance(decoded_logs, bytes):
                        logs = decoded_logs.decode("utf-8", errors="replace")
                except (ValueError, SyntaxError, UnicodeDecodeError):
                    pass

            pod_logs.append({
                "pod": pod_name,
                "logs": logs
            })

        except ApiException:
            pod_logs.append({
                "pod": pod_name,
                "logs": "",
                "error": "Could not retrieve logs for this pod"
            })

    return {
        "application_name": application_name,
        "pod_count": len(pod_logs),
        "pods": pod_logs
    }


@app.get("/deployments/{application_name}/access")
def get_deployment_access(application_name: str):

    config.load_kube_config(context="kind-deployflow")

    core_v1 = client.CoreV1Api()

    try:
        service = core_v1.read_namespaced_service(
            name=application_name,
            namespace="default"
        )

    except ApiException as e:
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{application_name}' not found"
            )

        raise HTTPException(
            status_code=502,
            detail="Could not retrieve service from Kubernetes"
        )

    # Check for an existing port-forward
    existing = port_forward_processes.get(application_name)

    if existing:
        process = existing.get("process")
        local_port = existing.get("port")

        if process and process.poll() is None:
            return {
                "application_name": application_name,
                "service": service.metadata.name,
                "service_type": service.spec.type,
                "port": local_port,
                "url": f"http://localhost:{local_port}"
            }

        # Remove stale port-forward information
        port_forward_processes.pop(application_name, None)

    # Find an available local port
    local_port = None

    for candidate in range(8090, 8191):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", candidate))
                local_port = candidate
                break
            except OSError:
                continue

    if local_port is None:
        raise HTTPException(
            status_code=500,
            detail="No available local port found"
        )

    # Start kubectl port-forward
    process = subprocess.Popen(
        [
            "kubectl",
            "--context",
            "kind-deployflow",
            "port-forward",
            f"service/{application_name}",
            f"{local_port}:80"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    port_forward_processes[application_name] = {
        "process": process,
        "port": local_port
    }

    # Give kubectl time to establish the tunnel
    import time
    time.sleep(1)

    if process.poll() is not None:
        port_forward_processes.pop(application_name, None)

        raise HTTPException(
            status_code=500,
            detail="Could not start Kubernetes port-forward"
        )

    return {
        "application_name": application_name,
        "service": service.metadata.name,
        "service_type": service.spec.type,
        "port": local_port,
        "url": f"http://localhost:{local_port}"
    }
