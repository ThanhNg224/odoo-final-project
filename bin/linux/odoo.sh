#!/bin/bash

# Set the root directory (2 levels up from this script)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PYTHON="$ROOT/.venv/bin/python"
ODOO="$ROOT/src/odoo/odoo-bin"
CONFIG="$HOME/odoo-final-project/odoo.cfg"

# Run Odoo
"$PYTHON" "$ODOO" -c "$CONFIG" "$@"

