#!/usr/bin/env python3
"""Make archive.org match pub/villager_tower/, slowly and verifiably.

    python3 tools/ia_sync.py            # upload missing/mismatched items
    python3 tools/ia_sync.py --check    # only report, upload nothing

For each issue: if the archive.org item already has a PDF with the same MD5
as the repo copy, skip it. Otherwise upload it with `ia upload`, then wait
before the next one. archive.org's spam filter rejects new accounts that
create items quickly, so on a rate/spam rejection this backs off for a while
and retries.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog  # noqa: E402

PAUSE = 60          # starting seconds between uploads (grows after rejections)
MAX_PAUSE = 10 * 60
BACKOFF = 15 * 60   # seconds to wait after a rate/spam rejection
MAX_BACKOFFS = 8

SUBJECTS = ["Villager Tower", "Carver Gazette", "Carver, Minnesota", "community newsletter"]
DESCRIPTION = ("Community newsletter of Carver, Minnesota "
               "(published as the Carver Gazette 1983–1987, then the Villager Tower).")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def remote_md5(issue):
    url = f"https://archive.org/metadata/{issue.identifier}/files"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            files = json.load(r).get("result", [])
    except Exception:
        return None
    for f in files:
        if f.get("name") == issue.filename:
            return f.get("md5")
    return None


def upload(issue, path):
    cmd = ["ia", "upload", issue.identifier, path, "--retries", "3",
           "--metadata=mediatype:texts", "--metadata=collection:opensource",
           "--metadata=language:eng", f"--metadata=title:{issue.title}",
           f"--metadata=description:{issue.title}. {DESCRIPTION}"]
    if issue.date:
        cmd.append(f"--metadata=date:{issue.date}")
    if issue.number:
        cmd.append(f"--metadata=issue:{issue.number}")
    for s in SUBJECTS:
        cmd.append(f"--metadata=subject:{s}")
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout + p.stderr
    ok = p.returncode == 0 and "error uploading" not in out
    throttled = "reduce your request rate" in out or "appears to be spam" in out
    return ok, throttled, out.strip().splitlines()[-1:] if out.strip() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only")
    args = ap.parse_args()

    issues = catalog.issues()
    todo = []
    for n, i in enumerate(issues, 1):
        path = os.path.join(catalog.VT_DIR, i.filename)
        local, remote = md5(path), remote_md5(i)
        state = "ok" if remote == local else ("MISMATCH" if remote else "missing")
        if state != "ok":
            todo.append((i, path))
        print(f"[{n}/{len(issues)}] {state:8} {i.identifier}", flush=True)
    print(f"\n{len(issues) - len(todo)} verified, {len(todo)} to upload", flush=True)
    if args.check or not todo:
        return

    backoffs, pause = 0, PAUSE
    for n, (i, path) in enumerate(todo, 1):
        while True:
            ok, throttled, last = upload(i, path)
            if ok:
                print(f"uploaded {n}/{len(todo)} {i.identifier}", flush=True)
                backoffs = 0
                break
            if throttled and backoffs < MAX_BACKOFFS:
                backoffs += 1
                pause = min(pause * 2, MAX_PAUSE)
                print(f"throttled on {i.identifier}; waiting {BACKOFF // 60} min "
                      f"(backoff {backoffs}/{MAX_BACKOFFS}); pace now {pause}s", flush=True)
                time.sleep(BACKOFF)
                continue
            print(f"FAILED {i.identifier}: {last}", flush=True)
            if throttled:
                sys.exit("giving up: archive.org keeps rejecting uploads")
            break
        time.sleep(pause)
    print("done; re-run with --check to verify", flush=True)


if __name__ == "__main__":
    main()
