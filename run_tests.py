#!/usr/bin/env python
"""
Zero-dependency test runner (also works under pytest).

    python run_tests.py
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
import time
import traceback


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    import tests as test_pkg

    passed = failed = 0
    failures: list[tuple[str, str]] = []
    start = time.perf_counter()

    for info in pkgutil.iter_modules(test_pkg.__path__):
        if not info.name.startswith("test_"):
            continue
        module = importlib.import_module(f"tests.{info.name}")
        for fn_name in sorted(dir(module)):
            if not fn_name.startswith("test_"):
                continue
            fn = getattr(module, fn_name)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
                print(f"  PASS  {info.name}.{fn_name}")
            except Exception:  # noqa: BLE001
                failed += 1
                failures.append((f"{info.name}.{fn_name}", traceback.format_exc()))
                print(f"  FAIL  {info.name}.{fn_name}")

    elapsed = time.perf_counter() - start
    print("\n" + "=" * 64)
    for name, tb in failures:
        print(f"--- {name} ---\n{tb}")
    print(f"Total: {passed + failed}  Passed: {passed}  Failed: {failed}  "
          f"Time: {elapsed:.2f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
