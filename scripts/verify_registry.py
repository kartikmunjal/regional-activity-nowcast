#!/usr/bin/env python3
"""Verify provider series IDs listed in the registry."""

from __future__ import annotations

import argparse
from pathlib import Path

from regional_activity_nowcast.data import load_series_registry, verify_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="config/series_registry.yml")
    parser.add_argument("--states", nargs="*", default=None)
    parser.add_argument("--out", default="report/registry_verification.csv")
    args = parser.parse_args()

    registry = load_series_registry(args.registry)
    result = verify_registry(registry, states=args.states)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
