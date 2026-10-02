ARG GO_VERSION=1.27.1
ARG NODE_MAJOR=20
ARG OPENTOFU_VERSION=1.13.0
ARG UV_VERSION=0.12.22

# ---------- Stage: Go (copy only the toolchain, no docs/tests) ----------
FROM golang:${GO_VERSION}-bookworm AS go
RUN rm -rf /usr/local/go/test /usr/local/go/doc /usr/local/go/api

# ---------- Stage: Node + npm packages (no cache) ----------
FROM node:${NODE_MAJOR}-bookworm-slim AS node
ARG OPENCODE_VERSION=1.18.34
ARG OPENSPEC_VERSION=1.13.0
RUN npm install -g opencode-ai@${OPENCODE_VERSION} @fission-ai/openspec@${OPENSPEC_VERSION} \
    && npm cache clean --force \
    && rm -rf /root/.npm /tmp/*

# ---------- Stage: downloaded binaries (kubectl, helm, yq) ----------
FROM ubuntu:24.04 AS tools
ARG TARGETARCH=amd64
ARG HELM_VERSION=4.0.0
ARG KUBECTL_VERSION=1.37.0
ARG YQ_VERSION=4.53.6
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl wget \
    && rm -rf /var/lib/apt/lists/*

RUN cd /tmp \
    && curl -fsSL -O "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
    && curl -fsSL -O "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl.sha256" \
    && echo "$(cat kubectl.sha256)  kubectl" | sha256sum -c - \
    && install -m 0755 kubectl /out-kubectl

RUN cd /tmp \
    && curl -fsSL -O "https://get.helm.sh/helm-v${HELM_VERSION}-linux-${TARGETARCH}.tar.gz" \
    && curl -fsSL -O "https://get.helm.sh/helm-v${HELM_VERSION}-linux-${TARGETARCH}.tar.gz.sha256sum" \
    && sha256sum -c "helm-v${HELM_VERSION}-linux-${TARGETARCH}.tar.gz.sha256sum" \
    && tar -xzf "helm-v${HELM_VERSION}-linux-${TARGETARCH}.tar.gz" \
    && install -m 0755 "linux-${TARGETARCH}/helm" /out-helm

RUN cd /tmp \
    && wget -q "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_${TARGETARCH}" -O yq \
    && wget -q "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/checksums" -O checksums \
    && EXPECTED=$(grep "^yq_linux_${TARGETARCH}  " checksums | awk '{print $19}') \
    && echo "${EXPECTED}  yq" | sha256sum -c - \
    && install -m 0755 yq /out-yq

# ---------- Official images for static binaries ----------
FROM ghcr.io/opentofu/opentofu:${OPENTOFU_VERSION}-minimal AS tofu
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------- Final image ----------
FROM ubuntu:24.04

ARG PYTHON_VERSION=3.14
ARG OPENCODE_VERSION=1.18.34
ARG GO_VERSION=1.27.1

LABEL org.opencontainers.image.title="opencode-devbox" \
      org.opencontainers.image.description="Dev environment: Go, OpenTofu, Node.js, Python, OpenCode, OpenSpec, kubectl, helm, make" \
      org.opencontainers.image.version="${OPENCODE_VERSION}"

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/home/ubuntu \
    GO_VERSION=${GO_VERSION} \
    OPENCODE_VERSION=${OPENCODE_VERSION} \
    GOPATH=/home/ubuntu/go \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy \
    PATH=/usr/local/go/bin:/home/ubuntu/go/bin:${PATH}

# Essential packages only (no software-properties-common, gnupg, python-dev, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    fd-find \
    git \
    jq \
    less \
    make \
    ripgrep \
    tree \
    unzip \
    vim-tiny \
    zip \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Binaries copied from the other stages
COPY --from=tools /out-kubectl /usr/local/bin/kubectl
COPY --from=tools /out-helm    /usr/local/bin/helm
COPY --from=tools /out-yq      /usr/local/bin/yq
COPY --from=tofu  /usr/local/bin/tofu /usr/local/bin/tofu
COPY --from=uv    /uv /usr/local/bin/uv
COPY --from=go    /usr/local/go /usr/local/go

# Node (binary + global modules) without apt/nodesource
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && ln -s ../lib/node_modules/opencode-ai/bin/opencode /usr/local/bin/opencode \
    && ln -s ../lib/node_modules/@fission-ai/openspec/bin/openspec.js /usr/local/bin/openspec

# Standalone Python via uv (no deadsnakes PPA, no -dev packages, no get-pip)
RUN uv python install ${PYTHON_VERSION} \
    && PY="$(uv python find ${PYTHON_VERSION})" \
    && ln -s "$PY" /usr/local/bin/python3 \
    && ln -s "$PY" /usr/local/bin/python \
    && rm -rf /root/.cache

RUN install -d -o ubuntu -g ubuntu \
        /workspace \
        ${GOPATH}/src \
        ${GOPATH}/bin \
        ${HOME}/.config/opencode \
        ${HOME}/.local/share/opencode \
        ${HOME}/.local/state/opencode

USER ubuntu
WORKDIR /workspace
EXPOSE 4096

CMD ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]