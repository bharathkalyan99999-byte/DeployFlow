def generate_deployment_manifest(
    application_name: str,
    environment: str,
    cpu: str,
    memory: str,
    replicas: int,
):
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {application_name}
  labels:
    app: {application_name}
    environment: {environment}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {application_name}
  template:
    metadata:
      labels:
        app: {application_name}
        environment: {environment}
    spec:
      containers:
        - name: {application_name}
          image: nginx:latest
          resources:
            requests:
              cpu: "{cpu}"
              memory: "{memory}"
            limits:
              cpu: "{cpu}"
              memory: "{memory}"
"""
