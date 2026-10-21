.DEFAULT_GOAL := help

GATEWAY_COMPOSE_FILE := docker-compose-gateway.yaml
COMPOSE_FILE          ?= docker-compose.yaml
COMPOSE              := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || (command -v docker-compose >/dev/null 2>&1 && echo "docker-compose"))
PLATFORMS            := linux/amd64,linux/arm64
PUSH                 ?= 0
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

build-multiarch: ## Build amd64+arm64 from compose config with buildx (PUSH=1 to push)
	@docker buildx version 2>/dev/null | grep -q 'buildx' || { \
		echo "error: docker buildx is required for multi-arch builds."; \
		echo "Install the Docker buildx plugin: https://docs.docker.com/build/install-buildx/"; \
		exit 1; \
	}
	docker buildx bake -f $(COMPOSE_FILE) \
		--set "opencode.platform=$(PLATFORMS)" \
		$(if $(filter 1,$(PUSH)),--push,--set "opencode.output=type=cacheonly")
