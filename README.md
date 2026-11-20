[DeployFlow_README.md](https://github.com/user-attachments/files/35140519/DeployFlow_README.md)
# DeployFlow

## Self-Service Kubernetes Application Deployment Platform

DeployFlow is a cloud-native web platform that simplifies application deployment to Kubernetes through a self-service dashboard.

Instead of manually creating Kubernetes resources and running `kubectl` commands, users can configure an application, choose resource requirements and replica count, deploy it, monitor its status, view pod logs, and access the deployed application from a single interface.

> **Current MVP:** DeployFlow runs locally using a Kind Kubernetes cluster and deploys an Nginx container as the application workload.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Technology Stack](#technology-stack)
5. [Deployment Workflow](#deployment-workflow)
6. [API Endpoints](#api-endpoints)
7. [Example Deployment](#example-deployment)
8. [Running the Project Locally](#running-the-project-locally)
9. [Docker](#docker)
10. [Project Validation](#project-validation)
11. [Current Scope](#current-scope)
12. [Future Improvements](#future-improvements)
13. [Skills Demonstrated](#skills-demonstrated)
14. [Author](#author)

---

## Project Overview

DeployFlow demonstrates how a self-service deployment workflow can be implemented using React, FastAPI, Docker, and Kubernetes.

The platform connects a web dashboard to a FastAPI backend, which uses the Kubernetes Python client to create and monitor Kubernetes resources.

### Core Capabilities

- Self-service application deployment
- CPU and memory configuration
- Replica configuration
- Environment selection
- Automatic Kubernetes Deployment creation
- Automatic Kubernetes Service creation
- Deployment readiness monitoring
- Pod status monitoring
- Pod log retrieval
- Local application access through port forwarding
- Dockerized frontend and backend

---

## Architecture

```text
                         User
                           |
                           v
                +----------------------+
                |  React Web Dashboard |
                +----------------------+
                           |
                           | REST API
                           v
                +----------------------+
                |    FastAPI Backend   |
                +----------------------+
                           |
                           | Kubernetes Python Client
                           v
                +----------------------+
                |  Kind Kubernetes     |
                |      Cluster         |
                +----------------------+
                     |            |
                     v            v
              +------------+  +---------+
              | Deployment |  | Service |
              +------------+  +---------+
                     |
                     v
                +-----------+
                | Kubernetes|
                |   Pods    |
                +-----------+
                     |
                     v
                +------------+
                |   Nginx    |
                | Application|
                +------------+
                     |
                     v
              Local Port Forward
                     |
                     v
                   Browser
```

### Architecture Flow

**React Dashboard → FastAPI → Kubernetes API → Deployment/Service → Pods → Nginx → Port Forward → Browser**

---

## Key Features

### Self-Service Deployment

Users configure deployments through the web dashboard without manually creating Kubernetes manifests.

### Resource Configuration

Each deployment can specify:

- CPU requests and limits
- Memory requests and limits
- Number of replicas
- Deployment environment

### Kubernetes Automation

The FastAPI backend uses the Kubernetes Python client to create and manage:

- Kubernetes Deployments
- Kubernetes Services
- Kubernetes Pods

### Deployment Monitoring

The dashboard displays deployment information including:

- Deployment status
- Desired replicas
- Ready replicas
- Available replicas

### Pod Log Monitoring

DeployFlow retrieves logs from running Kubernetes pods and displays them directly in the dashboard.

### Application Access

After deployment, DeployFlow creates a local Kubernetes port-forward so the deployed application can be opened directly from the dashboard.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI, Uvicorn |
| Kubernetes Integration | Kubernetes Python Client |
| Containerization | Docker |
| Orchestration | Kubernetes, Kind |
| CLI | kubectl |
| Application Workload | Nginx |

---

## Deployment Workflow

1. User opens the DeployFlow dashboard.
2. User configures the application:
   - Application name
   - Environment
   - CPU
   - Memory
   - Replicas
3. React sends a REST API request.
4. FastAPI validates and processes the request.
5. A Kubernetes Deployment is created.
6. A Kubernetes Service is created.
7. Kubernetes schedules the Pods.
8. DeployFlow monitors deployment readiness.
9. Pod logs are retrieved.
10. A local port-forward is created.
11. The user opens the deployed application.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | API welcome message |
| `GET` | `/health` | Backend health check |
| `POST` | `/deployments` | Create a Kubernetes deployment |
| `GET` | `/deployments` | Retrieve deployment history |
| `GET` | `/deployments/{application_name}` | Retrieve deployment status |
| `GET` | `/deployments/{application_name}/logs` | Retrieve pod logs |
| `GET` | `/deployments/{application_name}/access` | Generate application access |

---

## Example Deployment

### Request

```json
{
  "application_name": "portfolio-test",
  "environment": "development",
  "cpu": "100m",
  "memory": "128Mi",
  "replicas": 2
}
```

### Response

```json
{
  "message": "Deployment completed successfully",
  "application_name": "portfolio-test",
  "environment": "development",
  "deployment": "created",
  "service": "created",
  "replicas": 2,
  "image": "nginx:latest"
}
```

### Deployment Monitoring

A successful deployment returns live Kubernetes information such as:

```text
Status:    Running
Desired:   2
Ready:     2
Available: 2
```

The dashboard also displays logs retrieved from the running pods.

---

## Running the Project Locally

### Prerequisites

Install:

- Node.js
- Python 3
- Docker
- kubectl
- Kind

### 1. Create the Kubernetes Cluster

```bash
kind create cluster --name deployflow
```

Verify the cluster:

```bash
kubectl --context kind-deployflow get nodes
```

### 2. Start the Backend

Open a terminal:

```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 3. Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the dashboard at:

```text
http://localhost:5173
```

### 4. Deploy an Application

From the dashboard:

1. Enter an application name.
2. Select an environment.
3. Configure CPU and memory.
4. Select the number of replicas.
5. Click **Deploy Application**.
6. Monitor deployment status.
7. View pod logs.
8. Open the deployed application.

---

## Docker

DeployFlow includes Dockerfiles for both the frontend and backend.

### Build the Backend

```bash
docker build -t deployflow-backend ./backend
```

### Build the Frontend

```bash
docker build -t deployflow-frontend ./frontend
```

---

## Project Validation

The complete deployment workflow has been tested locally through the actual React dashboard.

### Tested Flow

```text
React Dashboard
       |
       v
FastAPI Backend
       |
       v
Kubernetes Deployment
       |
       v
2 Running Pods
       |
       v
Kubernetes Service
       |
       v
Port Forward
       |
       v
Nginx Application
       |
       v
HTTP 200 OK
```

### Verified Results

- Deployment status: **Running**
- Desired replicas: **2**
- Ready replicas: **2**
- Available replicas: **2**
- Logs displayed from both Kubernetes pods
- Application access link generated
- Deployed Nginx application opened successfully
- Application returned **HTTP 200 OK**

This validates the complete workflow from the frontend dashboard to the running Kubernetes application.

---

## Current Scope

DeployFlow is currently a local Kubernetes self-service deployment platform using Kind.

The current MVP demonstrates:

- Kubernetes automation
- REST API development
- Containerization
- Deployment monitoring
- Pod log monitoring
- Application access
- Cloud-native architecture
- Full-stack integration

The current implementation deploys `nginx:latest` as the application image.

---

## Future Improvements

Potential improvements include:

- Custom container image selection
- User authentication and authorization
- Persistent deployment history
- Deployment rollback
- Application scaling controls
- Resource usage metrics
- Prometheus and Grafana integration
- CI/CD pipeline integration
- Multiple Kubernetes environments
- Cloud Kubernetes support using AKS, EKS, or GKE

---

## Skills Demonstrated

- React application development
- REST API development
- Python and FastAPI
- Kubernetes
- Docker
- Container orchestration
- Kubernetes Python Client
- Infrastructure automation
- Deployment monitoring
- Application logging
- Cloud-native architecture
- Full-stack application integration

---

## Author

**Bharath Kalyan Voggu**

BTech — Computer Science and Business Systems

MSc — Computer Science and Technology with Business Development
