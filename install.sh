#!/usr/bin/env bash
# Install skills from this repo into ~/.claude/skills (or ./.claude/skills with --project).
#
# The repo layout mirrors ~/.claude/skills: each skill is a folder containing SKILL.md.
# Install copies each folder verbatim.
#
# Usage:
#   ./install.sh                  install every skill
#   ./install.sh d2 html-deck     install only the named skills
#   ./install.sh --list           list available skills and which are installed
#   ./install.sh --project        install to ./.claude/skills instead of ~/.claude/skills
#   ./install.sh --link           symlink instead of copy (edits in this repo are live)
#   ./install.sh --dry-run        print what would happen, do nothing

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.claude/skills"
MODE="copy"
DRY_RUN=0
LIST=0
TARGETS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) DEST="$REPO_DIR/.claude/skills" ;;
    --link)    MODE="link" ;;
    --dry-run) DRY_RUN=1 ;;
    --list|-l) LIST=1 ;;
    -h|--help)
      sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    --*)
      echo "unknown flag: $1" >&2
      exit 2
      ;;
    *)
      TARGETS+=("$1")
      ;;
  esac
  shift
done

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '  would: %s\n' "$*"
  else
    "$@"
  fi
}

# Discover available skills: any folder with SKILL.md at its root.
declare -a AVAILABLE
while IFS= read -r -d '' d; do
  AVAILABLE+=("$(basename "$d")")
done < <(find "$REPO_DIR" -maxdepth 2 -mindepth 2 -name SKILL.md -printf '%h\0')

if [[ ${#AVAILABLE[@]} -eq 0 ]]; then
  echo "no skills found in $REPO_DIR" >&2
  exit 1
fi

# Sort for stable output.
IFS=$'\n' AVAILABLE=($(printf '%s\n' "${AVAILABLE[@]}" | sort)); unset IFS

# Pull the single-line description out of a SKILL.md frontmatter.
read_description() {
  sed -n '/^---$/,/^---$/{s/^description: *//p}' "$1" | head -1 |
    sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"
}

if [[ $LIST -eq 1 ]]; then
  # Find longest name for alignment.
  maxlen=0
  for name in "${AVAILABLE[@]}"; do
    (( ${#name} > maxlen )) && maxlen=${#name}
  done
  # Installed dir may be either ~/.claude/skills or ./.claude/skills; show both.
  for name in "${AVAILABLE[@]}"; do
    desc="$(read_description "$REPO_DIR/$name/SKILL.md")"
    # Truncate long descriptions.
    if (( ${#desc} > 90 )); then desc="${desc:0:87}..."; fi
    marker=""
    [[ -e "$HOME/.claude/skills/$name"     ]] && marker="$marker [user]"
    [[ -e "$REPO_DIR/.claude/skills/$name" ]] && marker="$marker [project]"
    printf "  %-*s  %s%s\n" "$maxlen" "$name" "$desc" "$marker"
  done
  exit 0
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("${AVAILABLE[@]}")
fi

mkdir -p "$DEST"
echo "installing to $DEST (mode: $MODE)"

for name in "${TARGETS[@]}"; do
  src="$REPO_DIR/$name"
  dst="$DEST/$name"

  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "  skip $name: no $name/SKILL.md" >&2
    continue
  fi

  run rm -rf "$dst"
  if [[ "$MODE" == "link" ]]; then
    run ln -sfn "$src" "$dst"
  else
    run cp -R "$src" "$dst"
  fi
  echo "  installed $name"
done

echo "done. Claude Code picks up changes live within the current session."
