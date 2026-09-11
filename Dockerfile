FROM ubuntu:24.04

ARG GO_VERSION=1.27.1
ARG NODE_MAJOR=20
ARG OPENCODE_VERSION=1.18.27
ARG OPENSPEC_VERSION=1.12.0
ARG OPENTOFU_VERSION=1.12.6
ARG PYTHON_VERSION=3.14
ARG TARGETARCH=amd64

LABEL org.opencontainers.image.title="opencode-devbox" \
      org.opencontainers.image.description="Dev environment: Go, OpenTofu, Node.js, Python, OpenCode, OpenSpec"

ENV DEBIAN_FRONTEND=noninteractive
ENV USER=ubuntu
ENV HOME=/home/ubuntu
ENV GO_VERSION=${GO_VERSION}
ENV OPENCODE_VERSION=${OPENCODE_VERSION}
ENV GOPATH=${HOME}/go
ENV PATH=/usr/local/go/bin:${GOPATH}/bin:${PATH}

# Repos base + PPA deadsnakes Python + tools cli
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dnsutils \
    fd-find \
    git \
    gnupg \
    htop \
    iputils-ping \
    jq \
    less \
    lsb-release \
    nano \
    net-tools \
    ripgrep \
    software-properties-common \
    tree \
    unzip \
    vim \
    wget \
    zip \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    && rm -rf /var/lib/apt/lists/*

# yq
RUN wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${TARGETARCH:-amd64} -O /usr/bin/yq \
    && chmod +x /usr/bin/yq

# Python 3.14 and pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION} \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1

# Node.js, OpenCode & OpenSpec
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g opencode-ai@${OPENCODE_VERSION} @fission-ai/openspec@${OPENSPEC_VERSION}

# Go
RUN curl -fSL \
        -o /tmp/go.tar.gz \
        "https://go.dev/dl/go${GO_VERSION}.linux-${TARGETARCH:-amd64}.tar.gz" \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

# OpenTofu
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://get.opentofu.org/opentofu.gpg \
        | tee /etc/apt/keyrings/opentofu.gpg > /dev/null \
    && curl -fsSL https://packages.opentofu.org/opentofu/tofu/gpgkey \
        | gpg --no-tty --batch --dearmor \
        -o /etc/apt/keyrings/opentofu-repo.gpg \
    && chmod a+r \
        /etc/apt/keyrings/opentofu.gpg \
        /etc/apt/keyrings/opentofu-repo.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/opentofu.gpg,/etc/apt/keyrings/opentofu-repo.gpg] https://packages.opentofu.org/opentofu/tofu/any/ any main" \
        > /etc/apt/sources.list.d/opentofu.list \
    && echo "deb-src [signed-by=/etc/apt/keyrings/opentofu.gpg,/etc/apt/keyrings/opentofu-repo.gpg] https://packages.opentofu.org/opentofu/tofu/any/ any main" \
        >> /etc/apt/sources.list.d/opentofu.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends "tofu=${OPENTOFU_VERSION}*" \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN mkdir -p \
        ${GOPATH}/src \
        ${GOPATH}/bin \
        ${HOME}/.config/opencode \
        ${HOME}/.local/share/opencode \
        ${HOME}/.local/state/opencode \
    && chown -R ${USER}:${USER} \
        ${HOME} \
        /workspace

USER ${USER}

WORKDIR /workspace

EXPOSE 4096

CMD ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]