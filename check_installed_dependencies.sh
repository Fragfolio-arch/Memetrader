#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

OUTPUT_FILE="dependency_report.txt"
rm -f "$OUTPUT_FILE"

echo "Dependency report generated on $(date)" > "$OUTPUT_FILE"
echo "Repository root: $ROOT_DIR" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

dirs=(
  "mcp-wrappers/solana/solana-agent-kit"
  "mcp-wrappers/solana/dexranger-skill"
  "mcp-wrappers/sui/sui-agent-kit"
  "mcp-wrappers/sui/sui-trader-mcp"
  "mcp-wrappers/social/twitter-alpha-sentiment-tracker-v2"
  "external-repos/social/twikit"
  "external-repos/sui/capybot"
  "external-repos/sui/HoneyPotDetectionOnSui"
  "external-repos/base/defi-trading-mcp"
  "external-repos/base/pumpclaw"
  "external-repos/security/Rug-Killer-On-Solana"
  "external-repos/security/solana-rugchecker"
)

for dir in "${dirs[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "Skipping missing repo: $dir" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    continue
  fi

  echo "=================================================================" >> "$OUTPUT_FILE"
  echo "Repository: $dir" >> "$OUTPUT_FILE"
  echo "Path: $ROOT_DIR/$dir" >> "$OUTPUT_FILE"

  cd "$ROOT_DIR/$dir"

  if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    echo "\nPython dependency check:" >> "$OUTPUT_FILE"

    if [ -d ".venv" ] || [ -d "venv" ]; then
      venv_dir=""
      if [ -d ".venv" ]; then
        venv_dir=".venv"
      else
        venv_dir="venv"
      fi
      echo "Virtual environment found: $venv_dir" >> "$OUTPUT_FILE"
      if [ -x "$venv_dir/bin/python" ]; then
        echo "Installed python packages (freeze):" >> "$OUTPUT_FILE"
        "$venv_dir/bin/python" -m pip freeze >> "$OUTPUT_FILE" 2>&1 || echo "Failed to run pip freeze in $venv_dir" >> "$OUTPUT_FILE"
      else
        echo "Virtual environment python executable missing in $venv_dir" >> "$OUTPUT_FILE"
      fi
    else
      echo "No virtual environment found." >> "$OUTPUT_FILE"
      if command -v python3 >/dev/null 2>&1; then
        echo "Declared Python dependencies in requirements.txt / pyproject.toml:" >> "$OUTPUT_FILE"
        if [ -f "requirements.txt" ]; then
          cat requirements.txt >> "$OUTPUT_FILE"
        elif [ -f "pyproject.toml" ]; then
          cat pyproject.toml >> "$OUTPUT_FILE"
        fi
      else
        echo "Python not available to inspect dependencies." >> "$OUTPUT_FILE"
      fi
    fi
  fi

  if [ -f "package.json" ]; then
    echo "\nNode dependency check:" >> "$OUTPUT_FILE"
    if [ -d "node_modules" ]; then
      echo "Installed node_modules detected." >> "$OUTPUT_FILE"
      if command -v npm >/dev/null 2>&1; then
        echo "npm list --depth=0:" >> "$OUTPUT_FILE"
        npm list --depth=0 >> "$OUTPUT_FILE" 2>&1 || echo "npm list failed for $dir" >> "$OUTPUT_FILE"
      elif command -v pnpm >/dev/null 2>&1; then
        echo "pnpm list --depth=0:" >> "$OUTPUT_FILE"
        pnpm list --depth=0 >> "$OUTPUT_FILE" 2>&1 || echo "pnpm list failed for $dir" >> "$OUTPUT_FILE"
      else
        echo "No npm/pnpm available to list installed Node packages." >> "$OUTPUT_FILE"
      fi
    elif [ -d "pnpm_modules" ]; then
      echo "pnpm_modules directory detected." >> "$OUTPUT_FILE"
      if command -v pnpm >/dev/null 2>&1; then
        echo "pnpm list --depth=0:" >> "$OUTPUT_FILE"
        pnpm list --depth=0 >> "$OUTPUT_FILE" 2>&1 || echo "pnpm list failed for $dir" >> "$OUTPUT_FILE"
      else
        echo "No pnpm available to inspect pnpm_modules." >> "$OUTPUT_FILE"
      fi
    else
      echo "No installed node_modules found." >> "$OUTPUT_FILE"
      echo "Declared Node dependencies from package.json:" >> "$OUTPUT_FILE"
      jq -r '.dependencies, .devDependencies | keys | .[]' package.json 2>/dev/null >> "$OUTPUT_FILE" || {
        echo "Package names are not available via jq; displaying raw package.json dependencies." >> "$OUTPUT_FILE"
        python3 -c 'import json,sys; d=json.load(sys.stdin); print("dependencies:\n"+"\n".join(d.get("dependencies",{}).keys())); print("devDependencies:\n"+"\n".join(d.get("devDependencies",{}).keys()))' < package.json >> "$OUTPUT_FILE" 2>/dev/null || true
      }
    fi
  fi

  echo "" >> "$OUTPUT_FILE"
  cd "$ROOT_DIR"
done

echo "Dependency check complete. Output written to $OUTPUT_FILE"
