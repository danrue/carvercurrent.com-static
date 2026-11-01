#!/usr/bin/env python3
"""Build the GitHub Pages front end into _site/.

    python3 tools/build_site.py && python3 -m http.server -d _site

The newsletter PDFs are NOT copied into the site; every issue links to its
archive.org item. Old /pub/... URLs keep working through 404.html, which
redirects them to the matching archive.org file.
"""
import html
import json
import os
import shutil
import sys
from itertools import groupby

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog  # noqa: E402

ROOT = catalog.ROOT
OUT = os.path.join(ROOT, "_site")
SITE_SRC = os.path.join(ROOT, "site")
e = html.escape
SEARCH_URL = "https://archive.org/search?query=subject%3A%22Villager+Tower%22&sort=date"


def page(title, body, desc="", head=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{head}<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="masthead">
  <a href="/" class="brand">Carver Current</a>
  <nav><a href="/pub/villager_tower/">Villager Tower</a><a href="/pub/history/">Local History</a></nav>
</header>
<main>
{body}
</main>
<footer>
  <p>Carver, Minnesota. Documents are hosted by the
  <a href="https://archive.org/">Internet Archive</a>.</p>
</footer>
</body>
</html>
"""


def write(path, text):
    full = os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


def issue_li(i, with_year=False):
    num = f'<span class="num">#{e(i.number)}</span> ' if i.number else ""
    label = f"{i.short} {i.year}" if with_year else i.short
    return f'<li>{num}<a href="{e(i.download_url)}">{e(label)}</a></li>'


def build_villager_tower(issues):
    dated = [i for i in issues if i.year]
    index = [i for i in issues if not i.year]
    first, last = dated[0], dated[-1]

    years = []
    toc = []
    for year, group in groupby(dated, key=lambda i: i.year):
        group = list(group)
        names = sorted({i.masthead for i in group})
        toc.append(f'<a href="#y{year}">{year}</a>')
        years.append(f"""<section class="year" id="y{year}">
  <h2>{year} <span class="vol">Volume {catalog.volume(year)}</span>
  <span class="name">{e(" / ".join(names))}</span></h2>
  <ul class="issues">
    {"".join(issue_li(i) for i in group)}
  </ul>
</section>""")

    index_link = "".join(f'browse the <a href="{e(i.download_url)}">{e(i.title)}</a> or ' for i in index)

    body = f"""
<section class="hero">
  <img src="/logo.jpg" alt="Villager Tower masthead: a grain elevator" width="300">
  <div>
    <h1>Villager Tower</h1>
    <p class="lede">The community newsletter of Carver, Minnesota:
    {len(dated)} issues from {e(first.short)} {first.year} to {e(last.short)} {last.year}.
    It began as the <em>Carver Gazette</em> and became the <em>Villager Tower</em> in 1988.</p>
    <p class="note">Looking for a name or topic? {index_link[0].upper() + index_link[1:]}<a
    href="{e(SEARCH_URL)}">search every issue</a> at the Internet Archive.</p>
  </div>
</section>
<input type="search" id="filter" placeholder="Filter by year, month or issue number" aria-label="Filter issues">
<nav class="years">{"".join(toc)}</nav>
{"".join(years)}
<script>
const f = document.getElementById('filter');
f.addEventListener('input', () => {{
  const q = f.value.trim().toLowerCase();
  document.querySelectorAll('section.year').forEach(sec => {{
    const yearHit = sec.id.slice(1).includes(q);
    let any = false;
    sec.querySelectorAll('li').forEach(li => {{
      const hit = !q || yearHit || li.textContent.toLowerCase().includes(q);
      li.hidden = !hit; any = any || hit;
    }});
    sec.hidden = !any;
  }});
}});
</script>
"""
    write("/pub/villager_tower/index.html",
          page("Villager Tower", body, "Every issue of Carver, Minnesota's community newsletter, 1983–2024."))


def build_history():
    items = []
    for d in catalog.HISTORY:
        by = f'<span class="by">{e(d.author)}</span> · ' if d.author else ""
        items.append(f'<li><a href="{e(d.url)}">{e(d.title)}</a><br>'
                     f'{by}<span class="when">{e(d.note)}</span></li>')
        if d.local:
            dst = os.path.join(OUT, d.local)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, d.local), dst)
    body = f"""
<h1>Local History</h1>
<ul class="docs">{"".join(items)}</ul>
"""
    write("/pub/history/index.html", page("Local History", body, "Histories of Carver, Minnesota."))


def build_home(issues):
    latest = [i for i in issues if i.number][-6:][::-1]
    body = f"""
<section class="hero">
  <img src="/logo.jpg" alt="Villager Tower masthead: a grain elevator" width="300">
  <div>
    <h1>Carver Current</h1>
    <p class="lede">An archive for Carver, Minnesota: forty years of the
    <em>Villager Tower</em> community newsletter, and histories of the town.</p>
    <p><a class="button" href="/pub/villager_tower/">Browse the Villager Tower</a>
    <a class="button secondary" href="/pub/history/">Local History</a></p>
  </div>
</section>
<h2>Final issues</h2>
<ul class="issues">{"".join(issue_li(i, with_year=True) for i in latest)}</ul>
"""
    write("/index.html", page("Carver Current", body, "An archive for Carver, Minnesota."))
    write("/pub/index.html", page("Archive", """
<h1>Archive</h1>
<ul class="docs">
<li><a href="/pub/villager_tower/">Villager Tower</a> (newsletter, 1983–2024)</li>
<li><a href="/pub/history/">Local History</a></li>
</ul>"""))


def build_404(issues):
    redirects = {i.old_path: i.download_url for i in issues}
    redirects.update(catalog.EXTRA_REDIRECTS)
    # Runs in <head>, before anything renders: a known old URL goes straight to
    # its new home and the visitor never sees this page. (GitHub Pages can't
    # send a real HTTP redirect, so the status is still 404 for non-browsers.)
    head = f"""<script>
(function () {{
  var R = {json.dumps(redirects, separators=(",", ":"))};
  var p = decodeURIComponent(location.pathname).replace(/\\/+$/, '');
  if (R[p]) {{
    document.documentElement.className = 'redirecting';
    location.replace(R[p]);
  }}
}})();
</script>
<style>.redirecting body {{ visibility: hidden; }}</style>
"""
    body = """
<h1>Page not found</h1>
<p>That page isn’t here. Try the <a href="/pub/villager_tower/">Villager Tower archive</a>
or the <a href="/">home page</a>.</p>
"""
    write("/404.html", page("Carver Current", body, head=head))


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    for f in os.listdir(SITE_SRC):
        shutil.copy2(os.path.join(SITE_SRC, f), OUT)
    issues = catalog.issues()
    build_home(issues)
    build_villager_tower(issues)
    build_history()
    build_404(issues)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    print(f"built {OUT}: {len(issues)} issues, {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
