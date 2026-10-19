.DEFAULT_GOAL := help

GATEWAY_COMPOSE_FILE := docker-compose-gateway.yaml
COMPOSE_FILE          ?= docker-compose.yaml
COMPOSE              := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || (command -v docker-compose >/dev/null 2>&1 && echo "docker-compose"))
IMAGE_NAME           := opencode-devbox
IMAGE_TAG            := $(shell grep -m1 'image: $(IMAGE_NAME):' $(COMPOSE_FILE) | sed 's/.*://')
PLATFORMS            := linux/amd64,linux/arm64
PROJECT_NAME         ?= $(notdir $(CURDIR))

export PROJECT_NAME

.PHONY: help gateway-up gateway-down build build-multiarch

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

gateway-up: ## Start the Traefik gateway (creates the external traefik-net network)
	$(COMPOSE) -f $(GATEWAY_COMPOSE_FILE) up -d

gateway-down: ## Stop the Traefik gateway
	$(COMPOSE) -f $(GATEWAY_COMPOSE_FILE) down

build: ## Rebuild the opencode devbox image for the host's native arch
	$(COMPOSE) -f $(COMPOSE_FILE) build

build-multiarch: ## Build amd64+arm64 with buildx (needs --push or --load to keep the result)
	docker buildx build --platform $(PLATFORMS) -t $(IMAGE_NAME):$(IMAGE_TAG) .
