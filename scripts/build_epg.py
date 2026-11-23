#!/usr/bin/env python3
"""Build a merged XMLTV EPG for CyberTV.

This script deliberately does not invent EPG IDs or programmes. It merges
real source feeds, preserves their channel IDs, and reports which playlist
channels have an exact tvg-id match. Playlist stream URLs are never needed.
"""
from __future__ import annotations
import gzip
import io
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCES = [
    ("Japan merged EPG", "https://skinred78.github.io/jp-iptv-epg/jp-epg-merged.xml"),
    ("ABEMA", "https://raw.githubusercontent.com/dbghelp/Abema-TV-EPG/refs/heads/main/abema.xml"),
    ("EPGShare JP1", "https://epgshare01.online/epgshare01/epg_ripper_JP1.xml.gz"),
    ("EPGShare JP2", "https://epgshare01.online/epgshare01/epg_ripper_JP2.xml.gz"),
    ("EPG.pw Japan", "https://epg.pw/xmltv/epg_JP.xml.gz"),
]
OUT = Path("public")
OUT.mkdir(exist_ok=True)
TIMEOUT = 90

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CyberTV-Japan-EPG/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return data

def parse_xml(data: bytes, label: str):
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise RuntimeError(f"{label}: invalid XML: {e}") from e
    if root.tag != "tv":
        raise RuntimeError(f"{label}: root element is {root.tag!r}, expected 'tv'")
    return root

def child_key(node, tag):
    return ET.tostring(node, encoding="unicode")

def main():
    playlist = json.loads(Path("config/channel-mapping.json").read_text(encoding="utf-8"))
    # Existing explicit tvg-ids are authoritative. Do not guess IDs for other rows.
    playlist_ids = {c["tvg_id"] for c in playlist if c.get("tvg_id")}
    channels, programmes = {}, {}
    source_stats = []
    failures = []

    for label, url in SOURCES:
        try:
            root = parse_xml(fetch(url), label)
            ch_count = prog_count = 0
            for ch in root.findall("channel"):
                cid = ch.get("id")
                if cid and cid not in channels:
                    channels[cid] = ch
                    ch_count += 1
            for p in root.findall("programme"):
                cid = p.get("channel")
                if not cid:
                    continue
                # Keep first valid programme for a channel/start/stop/title key.
                title = " ".join((p.findtext("title") or "").split())
                key = (cid, p.get("start", ""), p.get("stop", ""), title)
                if key not in programmes:
                    programmes[key] = p
                    prog_count += 1
            source_stats.append((label, ch_count, prog_count))
            print(f"OK {label}: +{ch_count} channels, +{prog_count} programmes")
        except Exception as e:
            failures.append((label, str(e)))
            print(f"WARNING {label}: {e}", file=sys.stderr)

    if not channels or not programmes:
        raise SystemExit("No usable EPG data retrieved; refusing to publish.")

    root = ET.Element("tv", {"source-info-name": "CyberTV Japan merged EPG",
                             "source-info-url": "https://github.com/beierstores-bot/CyberTV-Japan-EPG"})
    for cid in sorted(channels):
        root.append(channels[cid])
    for key in sorted(programmes):
        root.append(programmes[key])

    # Exact ID coverage only. A channel name match is not automatically treated
    # as proof that two providers refer to the same service.
    matched_ids = playlist_ids.intersection(channels.keys())
    report = {
        "playlist_channel_count": len(playlist),
        "playlist_channels_with_tvg_id": len(playlist_ids),
        "exact_tvg_id_matches": len(matched_ids),
        "exact_tvg_id_unmatched": sorted(playlist_ids - matched_ids),
        "playlist_channels_without_tvg_id": [
            {"name": c["name"], "group": c["group"], "source_id": c["source_id"]}
            for c in playlist if not c.get("tvg_id")
        ],
        "source_results": [
            {"source": label, "new_channels": ch, "new_programmes": pg}
            for label, ch, pg in source_stats
        ],
        "source_failures": [{"source": a, "error": b} for a, b in failures],
        "note": "Only exact tvg-id matches are counted. No guessed channel IDs or synthetic programmes."
    }
    (OUT / "coverage-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with gzip.open(OUT / "CYBERTV_JAPAN_MASTER.xml.gz", "wb", compresslevel=9) as f:
        f.write(xml_bytes)
    print(f"Published locally: {len(channels)} EPG channel IDs, {len(programmes)} programmes")
    print(f"Playlist exact-ID coverage: {len(matched_ids)}/{len(playlist_ids)} IDs")
    print("Unmatched playlist channels are listed in public/coverage-report.json")

if __name__ == "__main__":
    main()
