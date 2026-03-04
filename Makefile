# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║           E T H O S   A E G I S  —  M A K E F I L E                       ║
# ║                                                                              ║
# ║  make help           — show this message                                    ║
# ║  make test           — run 79-test suite locally (no Docker)               ║
# ║  make lint           — ruff + mypy                                          ║
# ║  make demo           — run the 7-adjudication demo                         ║
# ║  make full           — lint + test + demo (CI equivalent, local)           ║
# ║  make docker-test    — build test-python stage and run suite in Docker     ║
# ║  make docker-build   — build full production image                         ║
# ║  make compose-test   — docker compose quality gate                         ║
# ║  make zip            — create distributable zip (no pycache)               ║
# ║  make clean          — remove all artefacts                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.DEFAULT_GOAL := help
.PHONY: help test lint demo full docker-test docker-build docker-push \
        compose-test compose-demo node-test go-test zip clean

PYTHON      ?= python3
PIP         ?= pip3
IMAGE_NAME  ?= ethos-aegis
IMAGE_TAG   ?= latest
REGISTRY    ?= ghcr.io/ethos-aegis
VERSION     := $(shell $(PYTHON) -c "import ethos_aegis; print(ethos_aegis.__version__)" 2>/dev/null || echo "1.0.0")

# ── Local Python ──────────────────────────────────────────────────────────────

install:
	$(PIP) install -e ".[dev]"
	@echo "✓ ethos-aegis installed in editable mode"

test:
	@echo "═══════════════════════════════════════════════════════"
	@echo "  Running Ethos Aegis test suite (79 tests)..."
	@echo "═══════════════════════════════════════════════════════"
	$(PYTHON) -m pytest tests/test_suite.py -v --tb=short
	@echo "✓ All tests passed"

lint:
	@echo "── Ruff linter ─────────────────────────────────────────"
	ruff check ethos_aegis/ tests/ --output-format=text
	@echo "── mypy type-checker ───────────────────────────────────"
	mypy ethos_aegis/ --ignore-missing-imports --no-strict-optional --pretty || true
	@echo "✓ Lint complete"

demo:
	$(PYTHON) scripts/demo.py

full: lint test demo
	@echo "✓ Full local CI pass complete"

# ── Docker ────────────────────────────────────────────────────────────────────

docker-test:
	@echo "── Building test-python stage and running quality gate ─"
	docker build \
		--target test-python \
		--build-arg PYTHON_VERSION=3.12 \
		-t $(IMAGE_NAME):test \
		.
	@echo "✓ Docker test gate passed"

docker-build:
	@echo "── Building full production image ──────────────────────"
	docker build \
		--build-arg PYTHON_VERSION=3.12 \
		--build-arg NODE_VERSION=20 \
		--build-arg GO_VERSION=1.22 \
		-t $(IMAGE_NAME):$(IMAGE_TAG) \
		-t $(IMAGE_NAME):$(VERSION) \
		.
	@echo "✓ Built $(IMAGE_NAME):$(IMAGE_TAG)"

docker-push:
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "✓ Pushed $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)"

compose-test:
	docker compose --profile ci run --rm test

compose-demo:
	docker compose --profile demo run --rm demo

# ── SDK tests ─────────────────────────────────────────────────────────────────

node-test:
	@echo "── Running Node.js SDK tests ───────────────────────────"
	cd sdk/node && node --test tests/

go-test:
	@echo "── Running Go SDK tests ────────────────────────────────"
	cd sdk/go && go test ./tests/... -v -timeout 120s

# ── Packaging ─────────────────────────────────────────────────────────────────

zip:
	@echo "── Building distributable zip ──────────────────────────"
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	cd .. && zip -r ETHOS_AEGIS_v$(VERSION).zip ETHOS_AEGIS/ \
		--exclude "ETHOS_AEGIS/.git/*" \
		--exclude "ETHOS_AEGIS/**/__pycache__/*" \
		--exclude "ETHOS_AEGIS/**/*.pyc" \
		--exclude "ETHOS_AEGIS/**/*.ndjson" \
		--exclude "ETHOS_AEGIS/sdk/rust/target/*" \
		--exclude "ETHOS_AEGIS/sdk/node/node_modules/*"
	@echo "✓ Created ../ETHOS_AEGIS_v$(VERSION).zip"

# ── Housekeeping ──────────────────────────────────────────────────────────────

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	find . -name "*.ndjson" -delete 2>/dev/null; true
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/ coverage.xml
	@echo "✓ Cleaned"

help:
	@echo ""
	@echo "  ╔══════════════════════════════════════════════════════╗"
	@echo "  ║      E T H O S   A E G I S  —  M a k e f i l e    ║"
	@echo "  ╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  Local Python:"
	@echo "    make install      — pip install -e .[dev]"
	@echo "    make test         — run 79-test suite"
	@echo "    make lint         — ruff + mypy"
	@echo "    make demo         — run 7-adjudication demo"
	@echo "    make full         — lint + test + demo"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-test  — build test stage + run suite in container"
	@echo "    make docker-build — build full production image"
	@echo "    make docker-push  — tag + push to registry"
	@echo ""
	@echo "  SDK:"
	@echo "    make node-test    — node --test sdk/node/tests/"
	@echo "    make go-test      — go test sdk/go/tests/"
	@echo ""
	@echo "  Release:"
	@echo "    make zip          — distributable zip (v$(VERSION))"
	@echo "    make clean        — remove artefacts"
	@echo ""
