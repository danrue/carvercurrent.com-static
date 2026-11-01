#!/usr/bin/env python3
"""Write an `ia upload --spreadsheet` CSV: one archive.org item per issue.

    python3 tools/mk_ia_manifest.py > villager_tower_ia.csv
    ia upload --spreadsheet=villager_tower_ia.csv --retries 5

Rights/creator fields are intentionally unset until the copyright holder's
wishes are confirmed; they can be added to existing items with `ia metadata`.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog  # noqa: E402

DESCRIPTION = ("Community newsletter of Carver, Minnesota "
               "(published as the Carver Gazette 1983–1987, then the Villager Tower).")

w = csv.writer(sys.stdout)
w.writerow(["identifier", "file", "title", "date", "issue", "mediatype", "collection",
            "language", "subject[0]", "subject[1]", "subject[2]", "subject[3]",
            "description"])
for i in catalog.issues():
    w.writerow([i.identifier, os.path.relpath(os.path.join(catalog.VT_DIR, i.filename)),
                i.title, i.date, i.number, "texts", "opensource", "eng",
                "Villager Tower", "Carver Gazette", "Carver, Minnesota",
                "community newsletter", f"{i.title}. {DESCRIPTION}"])
