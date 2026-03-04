#!/usr/bin/env bash
# scripts/run_tests.sh — One-command test runner for the Ethos Aegis
#
# Usage:
#   bash scripts/run_tests.sh              # full suite, verbose
#   bash scripts/run_tests.sh --fast       # fail immediately on first error
#   bash scripts/run_tests.sh --coverage   # run with coverage report (requires pytest-cov)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "════════════════════════════════════════════════════════════════════════"
echo "  ETHOS AEGIS — Test Suite"
echo "  Repository: $REPO_ROOT"
echo "════════════════════════════════════════════════════════════════════════"

# Ensure pytest is available
if ! python -m pytest --version &>/dev/null; then
    echo "▸ pytest not found — installing..."
    pip install pytest --break-system-packages -q
fi

PYTEST_ARGS="-v --tb=short"

# Parse optional flags
for arg in "$@"; do
    case $arg in
        --fast)
            PYTEST_ARGS="$PYTEST_ARGS --exitfirst"
            echo "  Mode: FAST (fail on first error)"
            ;;
        --coverage)
            pip install pytest-cov --break-system-packages -q
            PYTEST_ARGS="$PYTEST_ARGS --cov=ethos_aegis --cov-report=term-missing"
            echo "  Mode: COVERAGE"
            ;;
    esac
done

echo ""
python -m pytest tests/test_suite.py $PYTEST_ARGS

EXIT_CODE=$?

echo ""
echo "════════════════════════════════════════════════════════════════════════"
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✓ ALL TESTS PASSED — The Sovereign Integrity Mesh is verified."
else
    echo "  ✗ TESTS FAILED — Review output above."
fi
echo "════════════════════════════════════════════════════════════════════════"

exit $EXIT_CODE
