#!/bin/sh

set -eu

repo_root=$(git rev-parse --show-toplevel)
hooks_path=$(git config --local --get core.hooksPath || true)

if [ -n "$hooks_path" ] && [ "$hooks_path" != ".githooks" ]; then
  echo "core.hooksPath is already set to '$hooks_path'." >&2
  echo "Merge .githooks/pre-commit into that hook path, or unset it before retrying." >&2
  exit 1
fi

git config --local core.hooksPath .githooks
chmod +x "$repo_root/.githooks/pre-commit"

echo "Installed repository hooks from .githooks."
echo "Commits will scan only staged changes with Betterleaks."
