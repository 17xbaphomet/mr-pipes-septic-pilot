#!/usr/bin/env bash
set -euo pipefail
VERSION="1.14.0"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools/rhubarb"
OPT="/opt/rhubarb"
URL="https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v${VERSION}/Rhubarb-Lip-Sync-${VERSION}-Linux.zip"
echo "==> Rhubarb Lip Sync ${VERSION}"
mkdir -p "$TOOLS"
if [[ ! -x "$OPT/rhubarb" ]]; then
  if [[ ! -f "$TOOLS/rhubarb" ]]; then
    tmp="$(mktemp -d)"
    curl -L --fail -o "$tmp/rhubarb.zip" "$URL"
    unzip -q "$tmp/rhubarb.zip" -d "$tmp"
    src="$tmp/Rhubarb-Lip-Sync-${VERSION}-Linux"
    cp -a "$src/rhubarb" "$TOOLS/"
    cp -a "$src/res" "$TOOLS/"
    rm -rf "$tmp"
  fi
  mkdir -p "$OPT"
  cp -a "$TOOLS/rhubarb" "$OPT/"
  cp -a "$TOOLS/res" "$OPT/"
  chmod +x "$OPT/rhubarb"
fi
[[ -x "$OPT/rhubarb" ]] && ln -sfn "$OPT/rhubarb" /usr/local/bin/rhubarb 2>/dev/null || true
cat > "$ROOT/.env.rhubarb" <<EOF
export RHUBARB_BIN=${OPT}/rhubarb
export RHUBARB_RES=${OPT}/res
export PATH=${OPT}:\$PATH
EOF
"$OPT/rhubarb" --version
