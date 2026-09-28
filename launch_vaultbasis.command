#!/bin/bash
# VaultBasis Edge — Launcher
# Removes macOS quarantine flag (if present) and launches the application.
# Works on macOS 13 Ventura, 14 Sonoma, and 15 Sequoia.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/VaultBasis-Edge-v0.1.0-preview-macOS"

echo ""
echo "  VaultBasis — Design Partner Preview"
echo "  ──────────────────────────────────"
echo ""

# Check the file exists
if [ ! -f "$APP" ]; then
  echo "  ✗  Could not find the application file."
  echo "     Expected: $APP"
  echo ""
  echo "  Make sure this script and the VaultBasis application"
  echo "  file are in the same folder, then try again."
  echo ""
  read -n 1 -s -r -p "  Press any key to close..."
  exit 1
fi

# Ensure executable permission
chmod +x "$APP"

# Remove quarantine attribute (needed on macOS Sequoia and for some Sonoma setups)
if xattr "$APP" 2>/dev/null | grep -q "com.apple.quarantine"; then
  echo "  Clearing macOS security flag (you may be asked for your password)..."
  xattr -d com.apple.quarantine "$APP"
  echo "  ✓  Done."
fi

echo "  Starting VaultBasis..."
echo ""

# Launch the application
"$APP"

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo ""
  echo "  The application exited with an error (code $EXIT_CODE)."
  echo "  Please reply to the email that contained this download"
  echo "  and include the text above so we can help you."
  echo ""
  read -n 1 -s -r -p "  Press any key to close..."
fi
