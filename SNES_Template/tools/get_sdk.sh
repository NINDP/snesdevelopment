#!/bin/sh
set -eu
project_dir=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
target_dir="$project_dir/third_party/pvsneslib"
if [ -f "$target_dir/devkitsnes/snes_rules" ]; then
    printf 'SDK exists: %s\n' "$target_dir"
    exit 0
fi
case $(uname -s) in
    Darwin) package=pvsneslib_460_64b_darwin_release.zip ;;
    Linux) package=pvsneslib_460_64b_linux_release.zip ;;
    *) printf 'Download PVSnesLib 4.6.0 for this OS from the official release page.\n'; exit 1 ;;
esac
temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT HUP INT TERM
curl --fail --location --max-time 60 \
    "https://github.com/alekmaul/pvsneslib/releases/download/4.6.0/$package" \
    --output "$temp_dir/sdk.zip"
unzip -q "$temp_dir/sdk.zip" -d "$temp_dir/sdk"
mkdir -p "$project_dir/third_party"
mv "$temp_dir/sdk/pvsneslib" "$target_dir"
printf 'SDK ready. Build with:\nPVSNESLIB_HOME="%s" make\n' "$target_dir"
