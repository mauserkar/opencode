FROM ubuntu:24.04

ARG TARGETARCH=amd64

ARG GO_VERSION=1.27.1
ARG NODE_MAJOR=20
ARG OPENCODE_VERSION=1.18.27
ARG OPENSPEC_VERSION=1.12.0
ARG OPENTOFU_VERSION=1.12.6
ARG PYTHON_VERSION=3.14
ARG YQ_VERSION=v4.53.6

LABEL org.opencontainers.image.title="opencode-devbox" \
      org.opencontainers.image.description="Dev environment: Go, OpenTofu, Node.js, Python, OpenCode, OpenSpec" \
      org.opencontainers.image.version="${OPENCODE_VERSION}"

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/ubuntu
ENV GO_VERSION=${GO_VERSION}
ENV OPENCODE_VERSION=${OPENCODE_VERSION}
ENV GOPATH=${HOME}/go
ENV PATH=/usr/local/go/bin:${GOPATH}/bin:${PATH}

# Repos base + PPA Python + tools cli
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
RUN cd /tmp \
    && wget -q "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_${TARGETARCH}" -O yq \
    && wget -q "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/checksums" -O checksums \
    && EXPECTED=$(grep "^yq_linux_${TARGETARCH}  " checksums | awk '{print $19}') \
    && echo "${EXPECTED}  yq" | sha256sum -c - \
    && install -m 0755 yq /usr/bin/yq \
    && rm -f yq checksums

# Python and pip
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

# Golang
RUN curl -fSL -o /tmp/go.tar.gz "https://go.dev/dl/go${GO_VERSION}.linux-${TARGETARCH}.tar.gz" \
    && curl -fsSL "https://go.dev/dl/?mode=json&include=all" -o /tmp/go.json \
    && EXPECTED=$(python3 -c 'import json,os;d=json.load(open("/tmp/go.json"));v=os.environ["GO_VERSION"];a=os.environ["TARGETARCH"];fn="go%s.linux-%s.tar.gz"%(v,a);print(next(f["sha256"] for r in d if r["version"]=="go"+v for f in r["files"] if f["filename"]==fn))') \
    && echo "${EXPECTED}  /tmp/go.tar.gz" | sha256sum -c - \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz /tmp/go.json

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
    && chown -R ubuntu:ubuntu \
        ${HOME} \
        /workspace

USER ubuntu

WORKDIR /workspace

EXPOSE 4096

CMD ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]