# syntax=docker/dockerfile:1

ARG GO_VERSION
ARG OPENTOFU_VERSION
ARG UV_VERSION

# ---------- Go toolchain ----------
FROM golang:${GO_VERSION}-bookworm AS go

# ---------- OpenTofu ----------
FROM ghcr.io/opentofu/opentofu:${OPENTOFU_VERSION}-minimal AS tofu

# ---------- uv ----------
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------- Final image ----------
FROM docker/sandbox-templates:opencode

ARG OPENCODE_VERSION
ARG OPENSPEC_VERSION
ARG HELM_VERSION
ARG KUBECTL_VERSION
ARG YQ_VERSION
ARG PYTHON_VERSION

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fd-find \
        git \
        glab \
        jq \
        less \
        make \
        ripgrep \
        tree \
        unzip \
        vim-tiny \
        wget \
        zip \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY --from=go   /usr/local/go          /usr/local/go
COPY --from=tofu /usr/local/bin/tofu    /usr/local/bin/tofu
COPY --from=uv   /uv                    /usr/local/bin/uv

# kubectl
RUN ARCH="$(dpkg --print-architecture)" \
    && cd /tmp \
    && curl -fsSLO "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl" \
    && curl -fsSLO "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl.sha256" \
    && echo "$(cat kubectl.sha256)  kubectl" | sha256sum -c - \
    && install -m 0755 kubectl /usr/local/bin/kubectl

# helm
RUN ARCH="$(dpkg --print-architecture)" \
    && cd /tmp \
    && curl -fsSLO "https://get.helm.sh/helm-v${HELM_VERSION}-linux-${ARCH}.tar.gz" \
    && curl -fsSLO "https://get.helm.sh/helm-v${HELM_VERSION}-linux-${ARCH}.tar.gz.sha256sum" \
    && sha256sum -c "helm-v${HELM_VERSION}-linux-${ARCH}.tar.gz.sha256sum" \
    && tar -xzf "helm-v${HELM_VERSION}-linux-${ARCH}.tar.gz" \
    && install -m 0755 "linux-${ARCH}/helm" /usr/local/bin/helm

# yq (the checksums file lists multiple hashes per artifact; field 19 is SHA-256)
RUN ARCH="$(dpkg --print-architecture)" \
    && cd /tmp \
    && wget -q "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_${ARCH}" -O yq \
    && wget -q "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/checksums" -O checksums \
    && EXPECTED=$(awk -v f="yq_linux_${ARCH}" '$1 == f { print $19 }' checksums) \
    && printf '%s' "$EXPECTED" | grep -Eq '^[0-9a-f]{64}$' \
    && echo "${EXPECTED}  yq" | sha256sum -c - \
    && install -m 0755 yq /usr/local/bin/yq

# OpenCode and OpenSpec (keep the version pinned to the Compose devbox).
RUN npm install -g \
        "@opencode/cli@${OPENCODE_VERSION}" \
        "@fission-ai/openspec@${OPENSPEC_VERSION}" \
    && npm cache clean --force \
    && rm -rf /root/.npm /tmp/*

# Standalone Python managed by uv.
ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy
RUN uv python install "${PYTHON_VERSION}" \
    && PY="$(uv python find "${PYTHON_VERSION}")" \
    && ln -sf "$PY" /usr/local/bin/python3 \
    && ln -sf "$PY" /usr/local/bin/python \
    && rm -rf /root/.cache

RUN install -d -o agent -g agent \
        /home/agent/workspace \
        /home/agent/go/src \
        /home/agent/go/bin \
        /home/agent/.cache \
        /home/agent/.config/opencode \
        /home/agent/.local/share/opencode \
        /home/agent/.local/state/opencode

ENV GOPATH=/home/agent/go \
    PATH=/usr/local/go/bin:/home/agent/go/bin:$PATH

USER agent
WORKDIR /home/agent/workspace

EXPOSE 4096

ENTRYPOINT ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]
CMD []
