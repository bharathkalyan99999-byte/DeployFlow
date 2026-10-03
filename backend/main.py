from fastapi import FastAPI
from pydantic import BaseModel
from kubernetes import client, config

app = FastAPI(
    title="DeployFlow API",
    description="Self-Service Application Deployment Platform",
    version="0.3.0"
)


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

    except client.exceptions.ApiException as e:
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

    except client.exceptions.ApiException as e:
        if e.status == 409:
            core_v1.replace_namespaced_service(
                name=deployment.application_name,
                namespace="default",
                body=service_spec
            )
            service_action = "updated"
        else:
            raise

    return {
        "message": "Deployment completed successfully",
        "application_name": deployment.application_name,
        "environment": deployment.environment,
        "deployment": deployment_action,
        "service": service_action,
        "replicas": deployment.replicas,
        "image": "nginx:latest"
    }
