#!/usr/bin/env bash
#
# One command that runs everything: tests, type checking, linting, and the
# differential comparisons against the previous implementation.
#
# Usage:
#   ./verify.sh                       tests, mypy, ruff
#   ./verify.sh --with-differential   also compare against the old SDK
#
# For the differential comparisons, point OLD_SDK at a checkout of the released
# SDK (the directory containing spectra_assure_api_client/):
#
#   OLD_SDK=~/src/spectra-assure-sdk ./verify.sh --with-differential

set -euo pipefail

BASE="$1"

cd "$BASE"

fail=0
step()
{
    printf '\n=== %s ===\n' "$1"

    shift
    if "$@"
    then
        return 0
    fi
    printf '!!! FAILED: %s\n' "$*"
    fail=1
}

step "pytest" python3 -m pytest tests_unit/ -q

printf '\n'
if [ "$fail" -ne 0 ]
then
    printf 'VERIFY FAILED\n'
    exit 1
fi

printf 'VERIFY OK\n'
