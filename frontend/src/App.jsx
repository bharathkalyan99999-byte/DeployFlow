import { useState } from "react";

import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [form, setForm] = useState({
    application_name: "",
    environment: "development",
    cpu: "500m",
    memory: "512Mi",
    replicas: 2,
  });

  const [deployment, setDeployment] = useState(null);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState(null);
  const [access, setAccess] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const updateForm = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const waitForDeployment = async (applicationName) => {
    const maxAttempts = 20;
    const delay = 1000;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const response = await fetch(
        `${API_BASE_URL}/deployments/${applicationName}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not retrieve deployment status");
      }

      setStatus(data);

      if (data.status === "Running") {
        return data;
      }

      await new Promise((resolve) => setTimeout(resolve, delay));
    }

    throw new Error("Deployment is taking too long to become ready");
  };

  const refreshDeploymentData = async (applicationName) => {
    try {
      const readyStatus = await waitForDeployment(applicationName);

      const [logsResponse, accessResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/deployments/${applicationName}/logs`),
        fetch(`${API_BASE_URL}/deployments/${applicationName}/access`),
      ]);

      const logsData = await logsResponse.json();
      const accessData = await accessResponse.json();

      if (!logsResponse.ok) {
        throw new Error(logsData.detail || "Could not retrieve logs");
      }

      if (!accessResponse.ok) {
        throw new Error(
          accessData.detail || "Could not retrieve access URL"
        );
      }

      setStatus(readyStatus);
      setLogs(logsData);
      setAccess(accessData);
    } catch (err) {
      setError(err.message);
    }
  };

  const deployApplication = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setDeployment(null);
    setStatus(null);
    setLogs(null);
    setAccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/deployments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...form,
          replicas: Number(form.replicas),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Deployment failed");
      }

      setDeployment(data);

      await refreshDeploymentData(form.application_name);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="brand">DeployFlow</div>
          <div className="subtitle">
            Self-Service Application Deployment Platform
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          Local Kubernetes
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <p className="eyebrow">DEPLOYMENT CONTROL CENTER</p>

            <h1>Deploy applications without touching Kubernetes.</h1>

            <p className="hero-text">
              Configure your application, deploy it to the local Kubernetes
              cluster, and monitor the result from one dashboard.
            </p>
          </div>
        </section>

        <section className="grid">
          <div className="card deploy-card">
            <div className="card-header">
              <div>
                <h2>New Deployment</h2>
                <p>Configure your application resources.</p>
              </div>
            </div>

            <form onSubmit={deployApplication}>
              <label>
                Application Name

                <input
                  type="text"
                  placeholder="my-app"
                  value={form.application_name}
                  onChange={(e) =>
                    updateForm("application_name", e.target.value)
                  }
                  required
                />
              </label>

              <label>
                Environment

                <select
                  value={form.environment}
                  onChange={(e) =>
                    updateForm("environment", e.target.value)
                  }
                >
                  <option value="development">Development</option>
                  <option value="staging">Staging</option>
                  <option value="production">Production</option>
                </select>
              </label>

              <div className="two-column">
                <label>
                  CPU

                  <input
                    type="text"
                    value={form.cpu}
                    onChange={(e) => updateForm("cpu", e.target.value)}
                  />
                </label>

                <label>
                  Memory

                  <input
                    type="text"
                    value={form.memory}
                    onChange={(e) =>
                      updateForm("memory", e.target.value)
                    }
                  />
                </label>
              </div>

              <label>
                Replicas

                <input
                  type="number"
                  min="1"
                  max="10"
                  value={form.replicas}
                  onChange={(e) =>
                    updateForm("replicas", e.target.value)
                  }
                />
              </label>

              <button type="submit" disabled={loading}>
                {loading ? "Deploying..." : "Deploy Application"}
              </button>
            </form>

            {error && <div className="error">{error}</div>}
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <h2>Deployment Status</h2>
                <p>Live Kubernetes deployment information.</p>
              </div>
            </div>

            {!status ? (
              <div className="empty-state">
                Deploy an application to view its status.
              </div>
            ) : (
              <div className="status-panel">
                <div className="status-main">
                  <span
                    className={`status-badge ${
                      status.status === "Running"
                        ? "running"
                        : "pending"
                    }`}
                  >
                    {status.status}
                  </span>

                  <strong>{status.application_name}</strong>
                </div>

                <div className="metrics">
                  <div>
                    <span>Desired</span>
                    <strong>{status.replicas}</strong>
                  </div>

                  <div>
                    <span>Ready</span>
                    <strong>{status.ready_replicas}</strong>
                  </div>

                  <div>
                    <span>Available</span>
                    <strong>{status.available_replicas}</strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {access && (
          <section className="card access-card">
            <div>
              <p className="eyebrow">APPLICATION ACCESS</p>

              <h2>Your application is available</h2>

              <p>
                Service: <strong>{access.service}</strong>
              </p>
            </div>

            <a
              className="access-button"
              href={access.url}
              target="_blank"
              rel="noreferrer"
            >
              Open Application →
            </a>
          </section>
        )}

        {logs && (
          <section className="card logs-card">
            <div className="card-header">
              <div>
                <h2>Pod Logs</h2>

                <p>
                  {logs.pod_count} pod
                  {logs.pod_count !== 1 ? "s" : ""} detected
                </p>
              </div>
            </div>

            <div className="logs">
              {logs.pods.map((pod) => (
                <div className="pod-log" key={pod.pod}>
                  <div className="pod-name">{pod.pod}</div>
                  <pre>{pod.logs}</pre>
                </div>
              ))}
            </div>
          </section>
        )}

        {deployment && !error && (
          <section className="success-message">
            <span>✓</span>
            Deployment completed successfully.
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
