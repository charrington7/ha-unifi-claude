# Built on your Home Assistant Green when you install the app.
# python:3.13-slim is published for both aarch64 (Green) and amd64.
FROM python:3.13-slim

# Pinned versions so an update never changes behavior without you choosing it.
# The shared package holds the HTTP-only setting this app relies on (0.6.42 or newer).
ARG UNIFI_NETWORK_MCP_VERSION=0.48.1
ARG UNIFI_MCP_RELAY_VERSION=0.3.21
ARG UNIFI_MCP_SHARED_VERSION=0.6.42

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install \
        "unifi-network-mcp==${UNIFI_NETWORK_MCP_VERSION}" \
        "unifi-mcp-relay==${UNIFI_MCP_RELAY_VERSION}" \
        "unifi-mcp-shared==${UNIFI_MCP_SHARED_VERSION}"

COPY run.py /run.py

CMD ["python3", "-u", "/run.py"]
