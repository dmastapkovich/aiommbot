#!/usr/bin/env bash
# Clone the reference sources listed in .agents/references.md into .refs/.
#
#   sync-refs.sh              clone what is missing, leave existing clones alone
#   sync-refs.sh --update     also fetch the default branch of every existing clone
#   sync-refs.sh --purge      delete .refs/ entirely
#   sync-refs.sh <filter>...  restrict to entries whose <org>/<repo> matches a filter
#
# Clones are shallow: --depth=1, single branch, blobless. github.com/<org>/<repo> lands at
# .refs/<org>/<repo>, so a source URL maps to a local path without lookup. An empty template keeps
# the clones free of hooks — nothing here is ever committed from.

set -eu

repo_root=$(cd -- "$(dirname -- "$0")/../.." && pwd)
manifest="$repo_root/.agents/references.md"
refs_dir="$repo_root/.refs"
work_dir=${TMPDIR:-/tmp}
template_dir="$work_dir/sync-refs.template"
jobs=${SYNC_REFS_JOBS:-4}

update=0
purge=0
filters=""

for arg in "$@"; do
  case "$arg" in
    --update) update=1 ;;
    --purge) purge=1 ;;
    -h | --help)
      sed -n '2,9p' "$0" | cut -c 3-
      exit 0
      ;;
    -*)
      echo "sync-refs: unknown option $arg" >&2
      exit 2
      ;;
    *) filters="$filters $arg" ;;
  esac
done

if [ "$purge" -eq 1 ]; then
  rm -rf -- "$refs_dir"
  echo "sync-refs: removed $refs_dir"
  exit 0
fi

[ -f "$manifest" ] || {
  echo "sync-refs: no manifest at $manifest" >&2
  exit 1
}

# Every manifest row starts with a link to a GitHub repository; that link is the entry.
slug_list="$work_dir/sync-refs.slugs"
grep -oE '^\| \[[^]]+\]\(https://github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\)' "$manifest" |
  grep -oE 'github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+' |
  sed 's#github\.com/##' |
  sort -u >"$slug_list"

if [ -n "$filters" ]; then
  kept="$work_dir/sync-refs.kept"
  : >"$kept"
  for filter in $filters; do
    grep -F "$filter" "$slug_list" >>"$kept" || true
  done
  sort -u "$kept" -o "$slug_list"
fi

count=$(wc -l <"$slug_list" | tr -d ' ')
[ "$count" -gt 0 ] || {
  echo "sync-refs: nothing to do" >&2
  exit 1
}

sync_one() {
  slug=$1
  target="$refs_dir/$slug"
  if [ -d "$target/.git" ]; then
    if [ "$update" -eq 1 ]; then
      if git -C "$target" fetch --depth=1 --quiet origin HEAD &&
        git -C "$target" reset --hard --quiet FETCH_HEAD; then
        echo "updated  $slug"
      else
        echo "FAILED   $slug (update)"
      fi
    else
      echo "present  $slug"
    fi
    return 0
  fi
  mkdir -p -- "$(dirname -- "$target")"
  rm -rf -- "$target"
  if git clone --quiet --depth=1 --single-branch --filter=blob:none \
    --template="$template_dir" "https://github.com/$slug.git" "$target"; then
    echo "cloned   $slug"
  else
    rm -rf -- "$target"
    echo "FAILED   $slug (clone)"
  fi
}

mkdir -p -- "$template_dir"

export -f sync_one
export refs_dir update template_dir

log="$work_dir/sync-refs.log"
xargs -P "$jobs" -I {} bash -c 'sync_one "$@"' _ {} <"$slug_list" | tee "$log"

failures=$(grep -c '^FAILED' "$log" || true)
echo
echo "sync-refs: $count entries, $(du -sh "$refs_dir" 2>/dev/null | cut -f1) on disk, $failures failed"
[ "$failures" -eq 0 ]
