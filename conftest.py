"""Ensure the repo root is on sys.path before any test imports."""
import sys, os
_REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
_SDK  = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
for p in (_REPO, _SDK):
    if p not in sys.path:
        sys.path.insert(0, p)
# Force ethos_aegis to resolve from repo root, not any stale cached import
for key in [k for k in sys.modules if k.startswith("ethos_aegis")]:
    del sys.modules[key]
