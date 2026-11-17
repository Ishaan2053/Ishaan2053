#!/usr/bin/env python3
"""Keep the profile README current.

1. Renders the `git log --stat` activity card (stats, isometric contribution
   calendar, weekday habits, languages) to profile/stats-{dark,light}.svg.
2. Rewrites the SHIPPED block in README.md with the latest merged public PRs.
3. Rewrites the HASHNODE block in README.md with the latest blog posts.

  GH_TOKEN=... python scripts/update_profile.py Ishaan2053
  python scripts/update_profile.py Ishaan2053 --mock   # card preview only, no API, README untouched
"""
import datetime as dt
import email.utils
import json
import os
import random
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

W = 840
FEED_URL = os.environ.get("FEED_URL", "https://ishaan2053.hashnode.dev/rss.xml")
MAX_POSTS, MAX_PRS = 2, 5
FONT = 'ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace'
THEMES = {
    "dark": dict(bg="#0d1117", bar="#161b22", border="#30363d", text="#e6edf3", dim="#8b949e",
                 accent="#3fb950", empty="#1c2128", levels=["#0e4429", "#006d32", "#26a641", "#56d364"],
                 dots=["#ff7b72", "#d29922", "#3fb950"]),
    "light": dict(bg="#ffffff", bar="#f6f8fa", border="#d0d7de", text="#1f2328", dim="#656d76",
                  accent="#1a7f37", empty="#e6e9ed", levels=["#aceebb", "#4ac26b", "#2da44e", "#116329"],
                  dots=["#cf222e", "#9a6700", "#1a7f37"]),
}
QUERY = """
query($login: String!) {
  user(login: $login) {
    pullRequests(states: MERGED, first: 40, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes { title url mergedAt repository { nameWithOwner isPrivate } }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      commitContributionsByRepository(maxRepositories: 100) {
        contributions { totalCount }
        repository { primaryLanguage { name } }
      }
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# ---------------------------------------------------------------- data

def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise SystemExit(f"GitHub API error: {body['errors']}")
    user = body["data"]["user"]
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    langs = {}
    for item in cc["commitContributionsByRepository"]:
        lang = (item["repository"].get("primaryLanguage") or {}).get("name")
        if lang:
            langs[lang] = langs.get(lang, 0) + item["contributions"]["totalCount"]
    prs = [
        dict(title=n["title"], url=n["url"], date=n["mergedAt"][:10], repo=n["repository"]["nameWithOwner"])
        for n in user["pullRequests"]["nodes"]
        if n["mergedAt"] and not n["repository"]["isPrivate"]
    ]
    prs.sort(key=lambda p: p["date"], reverse=True)
    return dict(
        total=cal["totalContributions"],
        commits=cc["totalCommitContributions"],
        prs=cc["totalPullRequestContributions"],
        reviews=cc["totalPullRequestReviewContributions"],
        langs=langs,
        weeks=[[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]],
        merged=prs[:MAX_PRS],
    )


def mock():
    rnd = random.Random(2053)
    today = dt.date.today()
    start = today - dt.timedelta(days=364 + (today.weekday() + 1) % 7)
    weeks, d = [], start
    while d <= today:
        week, busy = [], rnd.random() < 0.6  # bursts of work, then quiet weeks
        for _ in range(7):
            if d > today:
                break
            if d.weekday() < 5:
                n = rnd.choice([0, 2, 4, 7, 12]) if busy else rnd.choice([0, 0, 0, 1, 2])
            else:
                n = rnd.choice([0, 0, 0, 3]) if busy else 0
            week.append((d.isoformat(), n))
            d += dt.timedelta(days=1)
        weeks.append(week)
    total = sum(n for w in weeks for _, n in w)
    return dict(total=total, commits=int(total * 0.8), prs=96, reviews=41, weeks=weeks, merged=[],
                langs={"TypeScript": 520, "Python": 310, "Go": 90, "JavaScript": 60})


def fetch_posts(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    posts = []
    for item in root.iter("item"):
        title, link, pub = item.findtext("title"), item.findtext("link"), item.findtext("pubDate")
        if title and link and pub:
            posts.append(dict(title=title.strip(), url=link.strip(),
                              date=email.utils.parsedate_to_datetime(pub).date().isoformat()))
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts[:MAX_POSTS]


# ---------------------------------------------------------------- card

def shade(hex_color, factor):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02x}{:02x}{:02x}".format(*(int(v * factor) for v in (r, g, b)))


def streaks(days):
    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    tail = days[:-1] if days and days[-1][1] == 0 else days  # today may not have a commit yet
    current = 0
    for _, n in reversed(tail):
        if not n:
            break
        current += 1
    return longest, current


def render(data, theme):
    c = THEMES[theme]
    days = [d for w in data["weeks"] for d in w]
    active = sum(1 for _, n in days if n)
    longest, current = streaks(days)
    nonzero = sorted(n for _, n in days if n) or [1]
    cuts = [nonzero[int(len(nonzero) * q)] for q in (0.25, 0.5, 0.75)]
    by_weekday = [0] * 7
    for date, n in days:
        by_weekday[dt.date.fromisoformat(date).weekday()] += n

    def level(n):
        return 1 + sum(n > cut for cut in cuts) if n else 0

    H = 492
    p = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">GitHub activity, last 12 months</title>
<desc id="d">{data["total"]:,} contributions, {data["commits"]:,} commits, {data["prs"]:,} pull requests, {data["reviews"]:,} reviews, active on {active} of {len(days)} days. Shown as an isometric contribution calendar.</desc>
<style>
text{{font-family:{FONT};font-size:14px}}
.t{{fill:{c["text"]}}}.d{{fill:{c["dim"]}}}.a{{fill:{c["accent"]}}}.b{{font-weight:700}}.s{{font-size:12px}}
.in,.w{{opacity:0;animation:show .4s ease-out forwards}}
@keyframes show{{to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.in,.w{{animation:none;opacity:1}}}}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>
<path d="M.5 38V10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V38z" fill="{c["bar"]}" stroke="{c["border"]}"/>
<circle cx="22" cy="19" r="5.5" fill="{c["dots"][0]}"/><circle cx="42" cy="19" r="5.5" fill="{c["dots"][1]}"/><circle cx="62" cy="19" r="5.5" fill="{c["dots"][2]}"/>
<text class="d" x="{W / 2}" y="24" text-anchor="middle" font-size="13">Ishaan2053@github: ~</text>
<text x="32" y="74"><tspan class="a b">$</tspan><tspan class="t"> git log --stat --since="1 year ago"</tspan></text>''']

    # stats, top right
    stats = [("contributions", f"{data['total']:,}"), ("commits", f"{data['commits']:,}"),
             ("pull requests", f"{data['prs']:,}"), ("reviews", f"{data['reviews']:,}"),
             ("active days", f"{active} of {len(days)}"), ("longest streak", f"{longest} days"),
             ("current streak", f"{current} days")]
    for i, (k, v) in enumerate(stats):
        y = 74 + i * 22
        p.append(f'<g class="in" style="animation-delay:{0.2 + 0.08 * i:.2f}s">'
                 f'<text class="a b" x="556" y="{y}">{k}</text><text class="t" x="808" y="{y}" text-anchor="end">{v}</text></g>')

    # isometric calendar
    hw, hh, tw, th = 12.4, 5.3, 11.0, 4.7
    ox, oy = 32 + 6 * hw + tw, 132
    for wi, week in enumerate(data["weeks"]):
        offset = 7 - len(week) if wi == 0 else 0
        cubes = []
        for di, (date, n) in enumerate(week):
            d = offset + di
            lv = level(n)
            h = 2 + lv * 6
            top = c["levels"][lv - 1] if lv else c["empty"]
            cx, cy = ox + (wi - d) * hw, oy + (wi + d) * hh
            f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
            cubes.append(
                f'<g><title>{date}: {n}</title>'
                f'<path fill="{shade(top, .62)}" d="M{f(cx - tw)} {f(cy - h)}L{f(cx)} {f(cy - h + th)}V{f(cy + th)}L{f(cx - tw)} {f(cy)}z"/>'
                f'<path fill="{shade(top, .8)}" d="M{f(cx)} {f(cy - h + th)}L{f(cx + tw)} {f(cy - h)}V{f(cy)}L{f(cx)} {f(cy + th)}z"/>'
                f'<path fill="{top}" d="M{f(cx)} {f(cy - h - th)}L{f(cx + tw)} {f(cy - h)}L{f(cx)} {f(cy - h + th)}L{f(cx - tw)} {f(cy - h)}z"/></g>')
        p.append(f'<g class="w" style="animation-delay:{0.6 + wi * 0.025:.3f}s">{"".join(cubes)}</g>')

    # weekday habits, bottom left
    peak = max(by_weekday) or 1
    busiest = by_weekday.index(peak)
    for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        y = 336 + i * 17
        bw = max(2, round(150 * by_weekday[i] / peak))
        cls = "a b" if i == busiest else "d"
        p.append(f'<g class="in" style="animation-delay:{1.6 + 0.06 * i:.2f}s"><text class="{cls} s" x="32" y="{y}">{name}</text>'
                 f'<rect x="66" y="{y - 9}" width="{bw}" height="9" rx="2" fill="{c["accent"] if i == busiest else c["levels"][1]}"/>'
                 f'<text class="d s" x="{66 + bw + 8}" y="{y}">{by_weekday[i]:,}</text></g>')

    # languages + footer
    fy = H - 22
    total_lang = sum(data["langs"].values())
    if total_lang:
        top_langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:4]
        langs = " · ".join(f"{name} {round(100 * n / total_lang)}%" for name, n in top_langs)
        p.append(f'<text class="s" x="32" y="{fy}"><tspan class="a b">commits by language</tspan><tspan class="t" dx="12">{langs}</tspan></text>')
    p.append(f'<text class="d s" x="{W - 32}" y="{fy}" text-anchor="end">updated {dt.date.today().isoformat()}</text>')
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------------- readme

def md_escape(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([\\`*_\[\]<>|])", r"\\\1", text)
    return text.replace("@", "@​")  # never ping anyone from a PR or post title


def replace_block(readme, tag, lines):
    pattern = re.compile(rf"(<!-- {tag}:START -->).*?(<!-- {tag}:END -->)", re.S)
    if not pattern.search(readme):
        print(f"README has no {tag} block, skipping")
        return readme
    body = "\n".join(lines)
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", readme)


def update_readme(path, merged, posts):
    with open(path, encoding="utf-8") as f:
        readme = original = f.read()
    if merged:
        readme = replace_block(readme, "SHIPPED", [
            f"- `{p['date']}` [{md_escape(p['title'])}]({p['url']}) · {p['repo']}" for p in merged])
    if posts:
        readme = replace_block(readme, "HASHNODE", [
            f"- `{p['date']}` [{md_escape(p['title'])}]({p['url']})" for p in posts])
    if readme != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(readme)
        print("updated README.md")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    login = args[0] if args else os.environ.get("GITHUB_REPOSITORY_OWNER", "Ishaan2053")
    is_mock = "--mock" in sys.argv
    if is_mock:
        data = mock()
    else:
        token = os.environ.get("GH_TOKEN")
        if not token:
            raise SystemExit("Set GH_TOKEN (a personal access token) or pass --mock")
        data = fetch(login, token)
    os.makedirs("profile", exist_ok=True)
    for theme in THEMES:
        with open(f"profile/stats-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(render(data, theme))
    print(f"wrote profile/stats-dark.svg and profile/stats-light.svg ({data['total']} contributions)")
    if is_mock:
        return
    try:
        posts = fetch_posts(FEED_URL)
    except Exception as exc:  # a feed outage should not break the card update
        print(f"could not read {FEED_URL}: {exc}")
        posts = []
    update_readme("README.md", data["merged"], posts)


if __name__ == "__main__":
    main()
