#!/usr/bin/env bash
# Local verification (replaces CI — this repo intentionally has no GitHub Actions).
# Run from anywhere: bash skills/verify-skill/verify.sh   (exit 0 = all passed)
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
pass=0; fail=0; skip=0
ok(){ pass=$((pass+1)); echo "PASS  $*"; }
ko(){ fail=$((fail+1)); echo "FAIL  $*"; }
sk(){ skip=$((skip+1)); echo "SKIP  $*"; }
cd "$ROOT" || exit 2

echo "== required files"
for f in README.md README_zh.md LICENSE .claude-plugin/marketplace.json .claude-plugin/plugin.json; do
  if [ -s "$f" ]; then ok "$f"; else ko "missing $f"; fi
done
if [ -d .github/workflows ]; then ko ".github/workflows exists (no CI allowed)"; else ok "no GitHub Actions workflows"; fi

echo "== SKILL.md frontmatter"
for s in skills/*/SKILL.md; do
  if python3 - "$s" <<'PY'
import sys,re,os
t=open(sys.argv[1],encoding="utf-8").read()
m=re.match(r"---\n(.*?)\n---\n",t,re.S); assert m,"no frontmatter"
fm=m.group(1)
nm=re.search(r"^name:\s*(\S+)\s*$",fm,re.M); assert nm,"no name"
name=nm.group(1); assert re.fullmatch(r"[a-z0-9-]{1,64}",name),"bad name"
assert name==os.path.basename(os.path.dirname(sys.argv[1])),"name != dir"
d=re.search(r"^description:\s*(.*)$",fm,re.M); assert d,"no description"
desc=d.group(1).strip()
if desc in (">-",">","|","|-"):
    desc=" ".join(l.strip() for l in fm[d.end():].splitlines() if l.startswith(" "))
assert desc and len(desc)<=1024,"empty/too long description"
assert len(t[m.end():].strip())>50,"empty body"
PY
  then ok "frontmatter $s"; else ko "frontmatter $s"; fi
done

echo "== JSON (.claude-plugin)"
if python3 - <<'PY'
import json,os
m=json.load(open(".claude-plugin/marketplace.json")); p=json.load(open(".claude-plugin/plugin.json"))
assert m["name"] and m["owner"]["name"] and m["plugins"]
for e in m["plugins"]:
    assert e["name"] and e["source"] and ".." not in e["source"] and os.path.isdir(e["source"])
assert p["name"]==m["plugins"][0]["name"]
assert p.get("version")==m["plugins"][0].get("version")
PY
then ok "marketplace.json / plugin.json valid and consistent"; else ko "plugin JSON"; fi

echo "== attribution"
if [ -f ATTRIBUTION.md ]; then
  for f in README.md README_zh.md; do
    if grep -q 'ATTRIBUTION.md' "$f"; then ok "$f links ATTRIBUTION.md"; else ko "$f does not link ATTRIBUTION.md"; fi
  done
  for d in skills/*/; do
    [ -d "$d/references" ] || continue
    if grep -q 'ATTRIBUTION.md' "$d/SKILL.md"; then ok "$d SKILL.md links ATTRIBUTION.md"; else ko "$d SKILL.md missing attribution link"; fi
  done
  for k in '人类最强编导' '给我两秒就好' 'douyin.com/video/'; do
    if grep -q "$k" ATTRIBUTION.md; then ok "ATTRIBUTION.md mentions $k"; else ko "ATTRIBUTION.md missing $k"; fi
  done
else
  if ls skills/*/references/* >/dev/null 2>&1; then ko "third-party transcript present but no ATTRIBUTION.md"; else sk "no third-party content, ATTRIBUTION.md not required"; fi
fi

echo "== markdown links (relative targets exist)"
if python3 - <<'PY'
import re,os,glob,sys
bad=0
files=[f for f in glob.glob("**/*.md",recursive=True) if not f.startswith(".git/")]
for f in files:
    t=open(f,encoding="utf-8").read()
    t=re.sub(r"```.*?```","",t,flags=re.S)
    for u in re.findall(r"\]\(([^)\s]+)\)",t):
        if re.match(r"[a-z]+:",u) or u.startswith("#"): continue
        p=os.path.normpath(os.path.join(os.path.dirname(f),u.split("#")[0]))
        if not os.path.exists(p): print("  broken:",f,"->",u); bad+=1
sys.exit(1 if bad else 0)
PY
then ok "no broken relative links"; else ko "broken relative links"; fi

echo "== shell scripts (bash -n / shellcheck)"
scripts=$(find . -name '*.sh' -not -path './.git/*')
for f in $scripts; do if bash -n "$f"; then ok "bash -n $f"; else ko "bash -n $f"; fi; done
if command -v shellcheck >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  if shellcheck -S warning $scripts; then ok "shellcheck"; else ko "shellcheck"; fi
else sk "shellcheck not installed"; fi

echo
echo "passed=$pass failed=$fail skipped=$skip"
[ "$fail" -eq 0 ]
