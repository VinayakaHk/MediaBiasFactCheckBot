"""
MediaBiasFactCheckBot Dashboard - Homepage (Status & Health)

This is the main entry point for the Streamlit multi-page app.
Pages in streamlit/pages/ are automatically picked up as sidebar navigation.
"""

import os
import re
from datetime import datetime

import streamlit as st
import docker
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

st.set_page_config(
    page_title="MBFC Bot Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar branding
st.sidebar.title("📊 MBFC Bot")
st.sidebar.markdown("---")
st.sidebar.caption("MediaBiasFactCheckBot Dashboard")

# --- Main content: Status page ---

st.title("🟢 System Status")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh every 30 seconds using streamlit-autorefresh or fallback
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30000, limit=None, key="status_refresh")
except ImportError:
    # Fallback: use Streamlit's native fragment rerun (no full page reload)
    pass

MONGODB_URI = os.environ.get("MONGODB", "mongodb://localhost:27017")
COMPOSE_PROJECT = "mediabiasfactcheckbot"
CRON_LOG_PATH = "/app/cron.log"  # mounted read-only from host


# --- Docker SDK helpers ---

@st.cache_resource
def get_docker_client():
    """Connect to Docker daemon via mounted socket."""
    try:
        return docker.DockerClient(base_url="unix:///var/run/docker.sock")
    except Exception:
        return None


def get_project_containers(client) -> list:
    """Get containers belonging to this compose project."""
    if not client:
        return []
    try:
        return client.containers.list(
            all=True,
            filters={"label": f"com.docker.compose.project={COMPOSE_PROJECT}"}
        )
    except Exception:
        return []


def get_container_stats_live(container) -> dict:
    """Get live resource stats for a container."""
    try:
        stats = container.stats(stream=False)
        # Calculate CPU %
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
        num_cpus = stats["cpu_stats"].get("online_cpus", 1)
        cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0 if system_delta > 0 else 0.0

        # Memory
        mem_usage = stats["memory_stats"].get("usage", 0)
        mem_limit = stats["memory_stats"].get("limit", 1)
        mem_percent = (mem_usage / mem_limit) * 100.0

        # Network I/O
        networks = stats.get("networks", {})
        net_rx = sum(v.get("rx_bytes", 0) for v in networks.values())
        net_tx = sum(v.get("tx_bytes", 0) for v in networks.values())

        return {
            "cpu_percent": f"{cpu_percent:.2f}%",
            "mem_usage": f"{mem_usage / 1024 / 1024:.1f} MiB",
            "mem_limit": f"{mem_limit / 1024 / 1024 / 1024:.2f} GiB",
            "mem_percent": f"{mem_percent:.1f}%",
            "net_rx": f"{net_rx / 1024 / 1024:.2f} MB",
            "net_tx": f"{net_tx / 1024 / 1024:.2f} MB",
        }
    except Exception as e:
        return {"error": str(e)}


def check_mongodb() -> tuple[bool, str]:
    """Check MongoDB connectivity."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        server_info = client.server_info()
        version = server_info.get("version", "unknown")
        db = client.reddit
        collections = db.list_collection_names()
        doc_counts = {col: db[col].estimated_document_count() for col in collections}
        client.close()
        return True, f"MongoDB {version} — Collections: {doc_counts}"
    except (ConnectionFailure, Exception) as e:
        return False, f"Connection failed: {e}"


def get_cron_status() -> dict:
    """Check cron job status from the mounted cron.log."""
    info = {"exists": False, "lines": 0, "last_modified": "", "tail": "", "size_kb": 0}
    try:
        stat = os.stat(CRON_LOG_PATH)
        info["exists"] = True
        info["size_kb"] = round(stat.st_size / 1024, 1)
        info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        with open(CRON_LOG_PATH, "r", errors="replace") as f:
            lines = f.readlines()
            info["lines"] = len(lines)
            tail_lines = lines[-10:] if len(lines) >= 10 else lines
            raw_tail = "".join(tail_lines)
            info["tail"] = re.sub(r'\x1b\[[0-9;]*m', '', raw_tail)
    except (FileNotFoundError, OSError):
        pass
    return info


# --- Layout ---

docker_client = get_docker_client()

# Health overview cards
st.markdown("### 🏥 Health Overview")

col1, col2, col3, col4 = st.columns(4)

containers = get_project_containers(docker_client)
bot_container = next((c for c in containers if "bot" in c.labels.get("com.docker.compose.service", "")), None)
mongo_container = next((c for c in containers if "mongodb" in c.labels.get("com.docker.compose.service", "")), None)

with col1:
    if bot_container and bot_container.status == "running":
        st.metric("Bot Container", "🟢 Running", bot_container.status)
    elif bot_container:
        st.metric("Bot Container", "🔴 " + bot_container.status.title(), "")
    else:
        st.metric("Bot Container", "⚫ Not Found", "")

with col2:
    if mongo_container and mongo_container.status == "running":
        st.metric("MongoDB", "🟢 Running", mongo_container.status)
    elif mongo_container:
        st.metric("MongoDB", "🔴 " + mongo_container.status.title(), "")
    else:
        st.metric("MongoDB", "⚫ Not Found", "")

with col3:
    mongo_ok, mongo_detail = check_mongodb()
    if mongo_ok:
        st.metric("DB Connection", "🟢 Connected", "Ping OK")
    else:
        st.metric("DB Connection", "🔴 Failed", "")

with col4:
    cron_info = get_cron_status()
    if cron_info["exists"]:
        st.metric("Cron Log", "🟢 Active", cron_info["last_modified"])
    else:
        st.metric("Cron Log", "🟡 Not Found", "")

st.markdown("---")

# --- Container Details ---
st.markdown("### 🐳 Container Details")

if containers:
    for container in containers:
        service = container.labels.get("com.docker.compose.service", container.name)
        status_emoji = "🟢" if container.status == "running" else "🔴"

        with st.expander(f"{status_emoji} **{container.name}** ({service}) — {container.status}", expanded=True):
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**General Info**")
                try:
                    image_name = container.image.tags[0] if container.image.tags else container.image.short_id
                except Exception:
                    image_name = container.attrs.get("Config", {}).get("Image", "unknown")
                st.text(f"Service:    {service}")
                st.text(f"Image:      {image_name}")
                st.text(f"Status:     {container.status}")
                st.text(f"Created:    {container.attrs['Created'][:19]}")
                st.text(f"Started:    {container.attrs['State'].get('StartedAt', 'N/A')[:19]}")
                st.text(f"Restarts:   {container.attrs.get('RestartCount', 0)}")
                # Ports
                ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
                port_str = ", ".join(
                    f"{k} → {v[0]['HostPort']}" for k, v in ports.items() if v
                ) if ports else "None"
                st.text(f"Ports:      {port_str}")

            with col_b:
                st.markdown("**Resource Usage (Live)**")
                if container.status == "running":
                    with st.spinner("Fetching stats..."):
                        live_stats = get_container_stats_live(container)
                    if "error" not in live_stats:
                        st.text(f"CPU:        {live_stats['cpu_percent']}")
                        st.text(f"Memory:     {live_stats['mem_usage']} / {live_stats['mem_limit']} ({live_stats['mem_percent']})")
                        st.text(f"Net RX:     {live_stats['net_rx']}")
                        st.text(f"Net TX:     {live_stats['net_tx']}")
                    else:
                        st.text(f"Error: {live_stats['error']}")
                else:
                    st.text("Container not running")

            # Environment (filtered for safety)
            config = container.attrs.get("Config", {})
            env_vars = config.get("Env", [])
            safe_env = [e for e in env_vars if not any(
                s in e.split("=")[0].upper() for s in ["SECRET", "PASSWORD", "TOKEN", "KEY", "CLIENT"]
            )]
            with st.expander("Environment Variables (non-sensitive)", expanded=False):
                for ev in safe_env:
                    st.text(f"  {ev[:80]}")

            # Command
            st.markdown("**Command**")
            entrypoint = config.get("Entrypoint") or []
            cmd = config.get("Cmd") or []
            st.code(" ".join(entrypoint + cmd), language="bash")

            # Logs
            if container.status == "running":
                with st.expander("Recent Logs (last 20 lines)", expanded=False):
                    try:
                        logs = container.logs(tail=20).decode("utf-8", errors="replace")
                        st.code(logs, language="text")
                    except Exception as e:
                        st.text(f"Could not fetch logs: {e}")
else:
    if docker_client:
        st.warning("No containers found for this compose project.")
    else:
        st.error(
            "Cannot connect to Docker daemon. "
            "Ensure `/var/run/docker.sock` is mounted in the dashboard container."
        )

st.markdown("---")

# --- MongoDB Details ---
st.markdown("### 🗄️ MongoDB Status")
if mongo_ok:
    st.success(mongo_detail)
else:
    st.error(mongo_detail)

st.markdown("---")

# --- Cron Job Status ---
st.markdown("### ⏰ Auto Post News (Cron)")
if cron_info["exists"]:
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric("Log Size", f"{cron_info['size_kb']} KB")
    with col_c2:
        st.metric("Total Lines", cron_info["lines"])
    with col_c3:
        st.metric("Last Modified", cron_info["last_modified"])

    st.markdown("**Recent Log Output:**")
    st.code(cron_info["tail"], language="text")
else:
    st.info("cron.log not mounted or not found at /app/cron.log")

st.markdown("---")
st.caption("Auto-refreshes every 30 seconds • Powered by Streamlit")
