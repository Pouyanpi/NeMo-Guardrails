#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || ! -d "$1" || -L "$1" || ! "$2" =~ ^[0-9][0-9A-Za-z.+]*$ ]]; then
  echo "Expected an artifact directory and library version." >&2
  exit 1
fi

artifact_dir="$1"
library_version="$2"
shopt -s nullglob dotglob
artifacts=("$artifact_dir"/*)
if [[ ${#artifacts[@]} -ne 2 ]]; then
  echo "Expected exactly one library wheel and one source distribution." >&2
  exit 1
fi

for artifact in "${artifacts[@]}"; do
  if [[ ! -f "$artifact" || -L "$artifact" ]]; then
    echo "Only regular library distribution files may be published." >&2
    exit 1
  fi
  case "$artifact" in
    "$artifact_dir/nemoguardrails-$library_version-py3-none-any.whl"|"$artifact_dir/nemoguardrails-$library_version.tar.gz") ;;
    *)
      echo "Unexpected artifact; refusing library publication." >&2
      exit 1
      ;;
  esac
done
