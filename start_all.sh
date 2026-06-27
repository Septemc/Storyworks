#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "Storyworks Unified Launcher"
echo "start_all.sh now delegates to the unified workspace launcher."

exec ./start.sh
