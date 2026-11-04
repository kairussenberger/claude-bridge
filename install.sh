#!/usr/bin/env bash
# Install the ClaudeBridge add-in into Autodesk Fusion (macOS) and put the
# `fusion` client on PATH. Safe to re-run: it overwrites the add-in files.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
ADDINS="$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns"
BIN="$HOME/.local/bin"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "install.sh is macOS-only; on Windows copy addin/ClaudeBridge to" >&2
  echo "  %APPDATA%\\Autodesk\\Autodesk Fusion 360\\API\\AddIns\\ClaudeBridge" >&2
  exit 1
fi
if [[ ! -d "$(dirname "$ADDINS")" ]]; then
  echo "Fusion API folder not found at: $(dirname "$ADDINS")" >&2
  echo "Is Autodesk Fusion installed and has it been launched once?" >&2
  exit 1
fi

mkdir -p "$ADDINS/ClaudeBridge" "$BIN"
cp "$REPO/addin/ClaudeBridge/ClaudeBridge.py" "$REPO/addin/ClaudeBridge/ClaudeBridge.manifest" "$ADDINS/ClaudeBridge/"
chmod +x "$REPO/fusion.py"
ln -sf "$REPO/fusion.py" "$BIN/fusion"

echo "Installed add-in -> $ADDINS/ClaudeBridge"
echo "Linked client    -> $BIN/fusion"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "NOTE: $BIN is not on PATH; call $REPO/fusion.py directly or add it.";; esac
echo
echo "Next (manual, in Fusion): Shift+S -> Add-Ins tab -> ClaudeBridge -> Run (optionally tick 'Run on Startup')."
echo "Then verify: fusion --ping"
