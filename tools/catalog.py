"""Catalog of everything in pub/, and where each file lives on archive.org.

Shared by build_site.py (GitHub Pages front end) and mk_ia_manifest.py
(archive.org upload spreadsheet). The PDFs themselves stay in the repo as the
source of truth; the published site only links to archive.org.
"""
import os
import re
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VT_DIR = os.path.join(ROOT, "pub", "villager_tower")

# How the newsletter's creator is credited on the site. (She described
# herself in the final issue as its "editor, creator and owner".)
EDITOR = "Ricki Yvonne Schultz"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MON_RE = "|".join(MONTHS)

ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
         (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"),
         (4, "IV"), (1, "I")]


def roman(n):
    out = ""
    for v, s in ROMAN:
        while n >= v:
            out += s
            n -= v
    return out


def volume(year):
    """Volume I began November 1983."""
    return roman(int(year) - 1982)


@dataclass
class Issue:
    filename: str      # Villager_Tower_376_2021-September-October.pdf
    identifier: str    # archive.org item id
    title: str         # Villager Tower #376, September–October 2021
    short: str         # September–October (for listings)
    masthead: str      # Carver Gazette | Villager Tower
    number: str        # "376", or "" for special editions
    year: str          # "2021"
    date: str          # "2021-09"

    @property
    def details_url(self):
        return f"https://archive.org/details/{self.identifier}"

    @property
    def download_url(self):
        return f"https://archive.org/download/{self.identifier}/{self.filename}"

    @property
    def old_path(self):
        return f"/pub/villager_tower/{self.filename}"


def identifier_for(filename):
    return filename[:-4].lower().replace("_", "-")


def parse(filename):
    stem = filename[:-4]
    masthead = "Carver Gazette" if stem.startswith("Carver_Gazette") else "Villager Tower"
    ident = identifier_for(filename)

    m = re.match(r"(Carver_Gazette|Villager_Tower)_(\d{3})_(\d{4})[-_](.*)$", stem)
    if m:
        number = str(int(m.group(2)))
        year, rest = m.group(3), m.group(4)
        months = re.findall(MON_RE, rest)
        if not months:
            raise ValueError(f"no month in {filename}")
        years = re.findall(r"\d{4}", rest)  # trailing year: span crosses New Year
        span = "–".join(months)
        when = f"{span} {year}" + (f"–{years[-1]}" if years else "")
        extra = re.sub(rf"({MON_RE}|\d{{4}})", "", rest).strip("-_ ").replace("-", " ").replace("_", " ")
        short = span + (f" ({extra})" if extra else "")
        title = f"{masthead} #{number}, {when}" + (f" ({extra})" if extra else "")
        date = f"{year}-{MONTHS.index(months[0]) + 1:02d}"
        return Issue(filename, ident, title, short, masthead, number, year, date)

    m = re.match(r"Villager_Tower_(\d{4})-Special-Edition-(.*)$", stem)
    if m:
        year, name = m.group(1), m.group(2).replace("-", " ")
        return Issue(filename, ident, f"{masthead} Special Edition: {name} ({year})",
                     f"Special Edition: {name}", masthead, "", year, year)

    raise ValueError(f"unrecognized filename: {filename}")


def issues():
    """All newsletter issues, oldest first (specials sorted into their year)."""
    out = [parse(f) for f in os.listdir(VT_DIR) if f.endswith(".pdf")]
    return sorted(out, key=lambda i: (i.date or "9999", int(i.number or 0), i.filename))


@dataclass
class Doc:
    title: str
    author: str
    note: str
    url: str           # where the site links to (the PDF itself)
    cover: str = ""    # site image path
    blurb: str = ""    # HTML


HISTORIC_CARVER_PDF = ("https://archive.org/download/historic-carver-on-the-minnesota-river/"
                       "Historic%20Carver%20On%20the%20Minnesota.pdf")
SHERIFFS_PDF = ("https://archive.org/download/the-sheriffs-of-carver-county/"
                "The_Sheriffs_of_Carver_County.pdf")

# Books by John von Walter, hosted on archive.org.
BOOKS = [
    Doc("Historic Carver on the Minnesota River", "John von Walter", "2024",
        HISTORIC_CARVER_PDF, "/img/covers/historic-carver.jpg",
        "John von Walter spent 10 to 15 years documenting the history of the city of "
        "Carver. Printed copies are available from the "
        '<a href="https://www.carvercountyhistoricalsociety.org/">Carver County Historical '
        "Society</a> in Waconia, with proceeds split between the Society and the non-profit "
        "Carver-on-the-Minnesota, under whose umbrella the work was made. The digital "
        "edition is dedicated to the public domain."),
    Doc("The Sheriffs of Carver County", "John von Walter", "2005",
        SHERIFFS_PDF, "/img/covers/sheriffs.jpg",
        "<em>The First 150 Years: 1855–2005.</em> A history of a century and a half of "
        "Carver County sheriffs."),
]

# The Carver Historic District guides (2011, 2012, 2016 editions, in
# pub/history/) were drafts of Historic Carver on the Minnesota River, which
# contains 82-88% of their text. They stay in the repo but aren't listed;
# their old URLs redirect to the book.
HISTORY = BOOKS

# Elsewhere on the web.
LINKS = [
    ("John Marvig: Carver’s historic bridges", "https://johnmarvigbridges.org/Carver.html"),
    ("Carver County Historical Society", "https://www.carvercountyhistoricalsociety.org/"),
    ("City of Carver", "https://www.cityofcarver.com/"),
]

# Old URLs that aren't files we serve, mapped to their new home.
EXTRA_REDIRECTS = {
    "/pub/history/Carver_Historic_District_2010.pdf": HISTORIC_CARVER_PDF,
    "/pub/history/Carver_Historic_District_2011.pdf": HISTORIC_CARVER_PDF,
    "/pub/history/Carver_Historic_District_2012.pdf": HISTORIC_CARVER_PDF,
    "/pub/history/Carver_Historic_District_2016.pdf": HISTORIC_CARVER_PDF,
    "/pub/history/Historic_Carver.pdf": HISTORIC_CARVER_PDF,
    "/pub/history/The_Sheriffs_of_Carver_County.pdf": SHERIFFS_PDF,
}

# Old WordPress pages (no file extension, so these get real redirect pages).
PAGE_REDIRECTS = {
    "/carver-history/": "/pub/history/",
    "/villager-tower/": "/pub/villager_tower/",
}
