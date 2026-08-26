#!/bin/sh
# Installs a pre-commit hook that normalizes typography before every commit.
# Re-run this any time you re-clone the repo (git hooks are not version-controlled).

set -e
root=$(git rev-parse --show-toplevel)
hook="$root/.git/hooks/pre-commit"

cat > "$hook" <<'HOOK'
#!/bin/sh
# Normalize quotes and em dashes, then re-stage anything that changed.
# Skip with: git commit --no-verify

staged_html=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.html$' || true)
[ -z "$staged_html" ] && exit 0

python3 tools/typography.py || exit 1

# re-stage only files that were already staged and that the script rewrote
for f in $staged_html; do
  [ -f "$f" ] && ! git diff --quiet -- "$f" && git add "$f" && echo "typography: re-staged $f"
done

exit 0
HOOK

chmod +x "$hook"
echo "Installed pre-commit hook at .git/hooks/pre-commit"
