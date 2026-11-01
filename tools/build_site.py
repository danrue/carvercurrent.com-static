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
import posixpath
import re
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


def page(title, body, desc="", head="", banner=""):
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
{banner}<main>
{body}
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <div class="f-brand">
      <a href="/" class="brand">Carver Current</a>
      <p>Community News and Views<br>Carver, Minnesota</p>
    </div>
    <nav class="f-nav" aria-label="Footer">
      <a href="/pub/villager_tower/">Villager Tower</a>
      <a href="/pub/history/">Local History</a>
    </nav>
    <p class="f-note">Newsletters and books are preserved at the
    <a href="https://archive.org/details/@mndrue">Internet Archive</a>, where they can be read and searched online.</p>
  </div>
</footer>
</body>
</html>
"""


def relativize(path, text):
    """Rewrite root-relative links ("/pub/...") relative to the page at `path`,
    so the site works at any URL prefix (its own domain, github.io/<repo>/,
    or straight from disk)."""
    here = posixpath.dirname(path)

    def rel(m):
        target = m.group(2)
        r = posixpath.relpath(target, here)
        if target.endswith("/"):
            r = "./" if r == "." else r + "/"
        return f'{m.group(1)}="{r}"'
    return re.sub(r'(href|src)="(/(?!/)[^"]*)"', rel, text)


def write(path, text, relative=True):
    if relative:
        text = relativize(path, text)
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


def docs_list():
    items = []
    for d in catalog.HISTORY:
        by = f'<span class="by">{e(d.author)}</span> · ' if d.author else ""
        items.append(f'<li><a href="{e(d.url)}">{e(d.title)}</a><br>'
                     f'{by}<span class="when">{e(d.note)}</span></li>')
    return f'<ul class="docs">{"".join(items)}</ul>'


def banner(cls, title, sub):
    return f"""<section class="banner {cls}">
  <div class="banner-text">
    <h1>{title}</h1>
    <p>{sub}</p>
  </div>
</section>
"""


def build_history():
    for d in catalog.HISTORY:
        if d.local:
            dst = os.path.join(OUT, d.local)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, d.local), dst)

    books = "".join(f"""
<article class="book">
  <a href="{e(d.url)}" class="cover"><img src="{e(d.cover)}" alt="Cover of {e(d.title)}" width="200"></a>
  <div>
    <h3><a href="{e(d.url)}">{e(d.title)}</a></h3>
    <p class="meta">{e(d.author)} · {e(d.note)}</p>
    <p>{d.blurb}</p>
  </div>
</article>""" for d in catalog.BOOKS)

    editions = "".join(f"""
<li><a href="{e(d.url)}"><img src="{e(d.cover)}" alt="" width="160"><span>{e(d.short)}</span></a></li>"""
                       for d in catalog.DISTRICT)

    links = "".join(f'<li><a href="{e(u)}">{e(t)}</a></li>' for t, u in catalog.LINKS)

    body = f"""
<section class="hist">
  <h2>Books</h2>
  {books}
</section>

<section class="hist">
  <h2>Carver Historic District</h2>
  <p>Guides to the historic homes and businesses of downtown Carver, which is listed on the
  National Register of Historic Places.</p>
  <ul class="editions">{editions}</ul>
</section>

<section class="hist">
  <h2>Heritage Preservation</h2>
  <article class="story">
    <a href="/dr-william-a-griffin-house/" class="thumb"><img src="/img/griffin/400-oak-after.jpg" alt="The restored Dr. William A. Griffin House" width="240"></a>
    <div>
      <h3><a href="/dr-william-a-griffin-house/">Dr. William A. Griffin House</a></h3>
      <p class="meta">2012 Carver Heritage Preservation Award</p>
      <p>The restoration of the circa 1858 home of Carver County’s first practicing physician,
      at 400 Oak Street. Story and photographs by John von Walter.</p>
    </div>
  </article>
</section>

<section class="hist">
  <h2>More Carver history</h2>
  <ul class="links">{links}</ul>
</section>
"""
    write("/pub/history/index.html",
          page("Local History", body, "Histories of Carver, Minnesota.",
               banner=banner("main-street", "Local History", "Carver on the Minnesota River")))

    with open(os.path.join(ROOT, "pages", "dr-william-a-griffin-house.html")) as f:
        article = f.read()
    write("/dr-william-a-griffin-house/index.html",
          page("Dr. William A. Griffin House", f'<article class="prose">{article}</article>',
               "2012 Carver Heritage Preservation Award: the Dr. William A. Griffin House."))


def build_page_redirects():
    for old, new in catalog.PAGE_REDIRECTS.items():
        path = old + "index.html"
        target = posixpath.relpath(new, posixpath.dirname(path)) + "/"
        write(path, f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Carver Current</title>
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
<script>location.replace({json.dumps(target)} + location.hash);</script>
</head><body><p><a href="{target}">Continue</a></p></body></html>
""", relative=False)


# Front pages shown on the home page: (issue number, caption).
TIMELINE = [
    ("1", "The first <em>Carver Gazette</em>"),
    ("51", "Renamed <em>Villager Tower</em>"),
    ("100", "Issue one hundred"),
    ("173", ""),
    ("268", ""),
    ("408", "The final issue"),
]


def build_home(issues):
    dated = [i for i in issues if i.year]
    by_num = {i.number: i for i in issues if i.number}
    top = banner("tracks", "Carver Current", "Community News and Views — Carver, Minnesota")

    fronts = []
    for num, caption in TIMELINE:
        i = by_num[num]
        month = i.short.split("–")[0].split(" ")[0]
        fronts.append(f"""<li><a href="{e(i.download_url)}">
  <img src="/img/issues/{int(num):03d}.jpg" alt="Front page of {e(i.title)}" width="220" loading="lazy">
  <span class="yr">{e(i.year)}</span>
  <span class="cap">{caption or e(f"#{num}, {month}")}</span></a></li>""")

    shelf = [(d.url, d.cover, d.title, f"{d.author} · {d.note}" if d.author else d.note)
             for d in catalog.BOOKS + catalog.DISTRICT[:1]]
    shelf.append(("/dr-william-a-griffin-house/", "/img/griffin/400-oak-after.jpg",
                  "Dr. William A. Griffin House", "2012 Heritage Preservation Award"))
    shelf_html = "".join(f"""<li><a href="{e(u)}">
  <span class="img"><img src="{e(c)}" alt="" loading="lazy"></span>
  <span class="t">{e(t)}</span><span class="m">{e(m)}</span></a></li>""" for u, c, t, m in shelf)

    body = f"""
<p class="intro">An archive for Carver, Minnesota: forty years of the town’s community
newsletter, and the books and stories that tell its history.</p>

<section class="home-section">
  <div class="section-head">
    <h2><a href="/pub/villager_tower/">Villager Tower</a></h2>
    <a class="more" href="/pub/villager_tower/">All {len(dated)} issues →</a>
  </div>
  <p>City council and township news, local events, and the people of Carver, published from
  {dated[0].year} to {dated[-1].year}.</p>
  <ol class="timeline">{"".join(fronts)}</ol>
</section>

<section class="home-section">
  <div class="section-head">
    <h2><a href="/pub/history/">Local History</a></h2>
    <a class="more" href="/pub/history/">More local history →</a>
  </div>
  <ul class="shelf">{shelf_html}</ul>
</section>
"""
    write("/index.html", page("Carver Current", body,
                              "Community News and Views — Carver, Minnesota.", banner=top))
    write("/pub/index.html", page("Archive", """
<h1>Archive</h1>
<ul class="docs">
<li><a href="/pub/villager_tower/">Villager Tower</a> (newsletter, 1983–2024)</li>
<li><a href="/pub/history/">Local History</a></li>
</ul>"""))


def build_404(issues):
    redirects = {i.old_path: i.download_url for i in issues}
    redirects.update(catalog.EXTRA_REDIRECTS)
    # GitHub serves this page for any missing URL, at any depth, so relative
    # links can't work here. Instead: match old URLs on their /pub/... part,
    # work out the site's prefix from the URL, and inline the stylesheet.
    #
    # The redirect runs in <head>, before anything renders: a known old URL
    # goes straight to its new home and the visitor never sees this page.
    # (GitHub Pages can't send a real HTTP redirect, so the status is still
    # 404 for non-browsers.)
    css = open(os.path.join(SITE_SRC, "style.css")).read()
    head = f"""<script>
var BASE = (function () {{
  var R = {json.dumps(redirects, separators=(",", ":"))};
  var p = decodeURIComponent(location.pathname).replace(/\\/+$/, '');
  var i = p.indexOf('/pub/');
  var base = i >= 0 ? p.slice(0, i)
           : /\\.github\\.io$/.test(location.hostname) ? '/' + p.split('/')[1] : '';
  var to = R[i >= 0 ? p.slice(i) : p];
  if (to) {{
    document.documentElement.className = 'redirecting';
    location.replace(to.charAt(0) === '/' ? base + to : to);
  }}
  return base;
}})();
</script>
<style>.redirecting body {{ visibility: hidden; }}
{css}</style>
"""
    body = """
<h1>Page not found</h1>
<p>That page isn’t here. Try the <a href="/pub/villager_tower/">Villager Tower archive</a>
or the <a href="/">home page</a>.</p>
<script>
document.querySelectorAll('a[href^="/"]').forEach(function (a) {
  a.setAttribute('href', BASE + a.getAttribute('href'));
});
</script>
"""
    html404 = page("Carver Current", body, head=head).replace(
        '<link rel="stylesheet" href="/style.css">', "")
    write("/404.html", html404, relative=False)


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    shutil.copytree(SITE_SRC, OUT, dirs_exist_ok=True)
    issues = catalog.issues()
    build_home(issues)
    build_villager_tower(issues)
    build_history()
    build_page_redirects()
    build_404(issues)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    print(f"built {OUT}: {len(issues)} issues, {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
