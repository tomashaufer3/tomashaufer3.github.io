#!/usr/bin/env python3
"""
Build the four district maps under the home-page chart from the thesis repository.

Writes the block between ``<!-- MAPS:BEGIN -->`` and ``<!-- MAPS:END -->`` in index.html.

Source, all in the thesis repository (default ``!!!CERGE/.Thesis/Legions``):

* geometry: the 1910 court-district polygons of the Czech lands, exactly as the docs site
  draws them (``utils/docs/build_docs.py::_district_map``)
* values: ``data/interim/intensity/intensity_okres.csv`` (``run_intensities.py``), one row
  per census okres, the same table the docs site's "Intensity maps" read

The maps are coloured here, in Python, so they are complete without JavaScript. The small
inline script after them only adds the hover readout and the highlight across the four panels.

Usage::

    python tools/build_maps.py [path/to/Legions]
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SITE = Path(__file__).resolve().parents[1]
LEGIONS = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    SITE.parents[1] / "!!!CERGE" / ".Thesis" / "Legions"

#: (column, title, unit for the readout, ramp, floating scale)
PANELS = [
    ("matice_own_z", "Matice",
     "Members of the land’s own national society per inhabitant, standardised (z)", "navy", True),
    ("theatre_per_1000", "Amateur theatre",
     "Czech amateur-theatre companies active per 1,000 inhabitants, 1880–1913", "navy", False),
    ("legion_per_1000", "Legionnaires", "Legionnaires per 1,000 inhabitants", "navy", False),
    ("desertion_per_1000_leg", "Desertion",
     "Deserters per 1,000 legionnaires, shrunk; grey under 20 legionnaires", "red", True),
]
BG = "#f4f0e6"      # --cream-deep, the .band--alt background the maps sit on
#: both ramps start at the background, so a district at the bottom of a scale reads as
#: empty rather than as a white patch on the cream page
RAMPS = {"navy": [BG, "#003657"], "red": [BG, "#d22d40", "#5e1019"]}
MISSING = "#d9d6cf"
GRID = 1.0          # the docs site's own grid (about 1 km); see the merge below
FMT = ["{:+.2f}", "{:.2f}", "{:.1f}", "{:.1f}"]


def ramp(stops: list[str], t: float) -> str:
    t = min(1.0, max(0.0, t))
    rgb = [tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) for s in stops]
    seg = min(int(t * (len(rgb) - 1)), len(rgb) - 2)
    u = t * (len(rgb) - 1) - seg
    a, b = rgb[seg], rgb[seg + 1]
    return "#" + "".join(f"{round(x + (y - x) * u):02x}" for x, y in zip(a, b))


def stitch(edges: set[tuple]) -> str:
    """Chain undirected segments into polylines (as the docs builder does)."""
    adj: dict[tuple, list[tuple]] = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    left, out = set(edges), []

    def walk(start):
        chain, cur = [start], start
        while True:
            nxt = None
            for c in adj[cur]:
                key = (cur, c) if (cur, c) in left else (c, cur)
                if key in left:
                    left.discard(key)
                    nxt = c
                    break
            if nxt is None:
                return chain
            chain.append(nxt)
            cur = nxt

    for odd_first in (True, False):
        for node in adj:
            if odd_first and len(adj[node]) % 2 == 0:
                continue
            while any(((node, c) in left or (c, node) in left) for c in adj[node]):
                ch = walk(node)
                if len(ch) > 1:
                    out.append("M" + "L".join(f"{x:g},{y:g}" for x, y in ch))
    return "".join(out)


def main() -> None:
    sys.path.insert(0, str(LEGIONS))
    import utils.docs.build_docs as bd                       # noqa: E402

    geom = bd._district_map()
    paths = {u: d for u, d in geom["paths"].items() if u.startswith("cc")}
    xw = pd.read_csv(LEGIONS / "data/final/geo/okres_census_crosswalk.csv") \
        .set_index("okres_id")["census_okres_id"]
    ok = pd.read_csv(LEGIONS / "data/interim/intensity/intensity_okres.csv") \
        .set_index("census_okres_id")
    key = {u: xw.get(int(geom["parent"][u][2:])) for u in paths}   # court → census okres
    missing = [u for u, k in key.items() if k is None]
    if missing:
        raise SystemExit(f"courts without a census okres: {missing[:5]}")

    # Merge the courts into census okresy by parity: an edge is on a shape's boundary when
    # that shape's polygons use it an odd number of times. A shared interior edge is used
    # twice and cancels; the rare edge that overlapping or spiked rings use three times
    # still counts, so no boundary is left with a gap. The frontier is the same rule over
    # all polygons at once. GRID = 1 is the docs site's own grid, on which neighbouring
    # courts share their border vertex for vertex; a coarser grid collapsed short edges
    # onto each other and broke the frontier into twenty pieces.
    count: dict[tuple, dict[int, int]] = {}
    for u, d in paths.items():
        k = int(key[u])
        for ring in re.findall(r"M([^Z]+)Z", d):
            pts = [(round(float(a) / GRID), round(float(b) / GRID))
                   for a, b in (p.split(",") for p in ring.split("L"))]
            for a, b in zip(pts, pts[1:] + pts[:1]):
                if a == b:
                    continue
                e = tuple(sorted([a, b]))
                per = count.setdefault(e, {})
                per[k] = per.get(k, 0) + 1
    unit_edges: dict[int, set] = {}
    for e, per in count.items():
        for k, c in per.items():
            if c % 2:
                unit_edges.setdefault(k, set()).add(e)
    shapes = {k: stitch(es) for k, es in unit_edges.items()}
    frame = stitch({e for e, per in count.items() if sum(per.values()) % 2})

    xy = np.array([p for es in unit_edges.values() for e in es for p in e], float)
    (x0, y0), (x1, y1) = xy.min(0) - 2, xy.max(0) + 2
    vb = f"{x0:g} {y0:g} {x1 - x0:g} {y1 - y0:g}"

    ranges = []
    for col, _t, _u, _r, floating in PANELS:
        s = ok[col].dropna()
        ranges.append((float(np.percentile(s, 3)) if floating else 0.0, float(np.percentile(s, 97))))

    def fill(i: int, k) -> str:
        col, _t, _u, rmp, _f = PANELS[i]
        v = ok[col].get(k) if k is not None else None
        if v is None or pd.isna(v):
            return MISSING
        lo, hi = ranges[i]
        return ramp(RAMPS[rmp], (float(v) - lo) / (hi - lo))

    defs = ("<defs>" + "".join(f'<path id="mp{k}" d="{d}"/>' for k, d in shapes.items())
            + f'<path id="mpframe" d="{frame}"/></defs>')

    # One map, four views. Each view is its own layer of <use> references with the fills
    # written in, so the first view (Matice) is complete without JavaScript; the buttons,
    # which only work with it, are hidden until the script shows them.
    layers, scales, tabs = [], [], []
    for i, (col, title, unit, rmp, _f) in enumerate(PANELS):
        off = "" if i == 0 else " off"
        uses_ = "".join(f'<use href="#mp{k}" data-k="{k}" fill="{fill(i, k)}"/>' for k in shapes)
        layers.append(f'<g class="map-layer{off}" data-v="{i}">{uses_}</g>')
        lo, hi = ranges[i]
        grad = ", ".join(ramp(RAMPS[rmp], t / 4) for t in range(5))
        scales.append(
            f'<div class="map-scale{off}" data-v="{i}"><span class="map-unit">{html.escape(unit)}</span>'
            f'<span>{FMT[i].format(lo)}</span>'
            f'<i style="background:linear-gradient(90deg, {grad})"></i>'
            f'<span>{FMT[i].format(hi)}</span></div>')
        pressed = "true" if i == 0 else "false"
        tabs.append(f'<button type="button" class="map-tab" data-v="{i}" '
                    f'aria-pressed="{pressed}">{html.escape(title)}</button>')

    data = {str(int(k)): [str(r["okres_cs"])] + [None if pd.isna(r[c]) else round(float(r[c]), 3)
                                                  for c, *_ in PANELS]
            for k, r in ok.iterrows()}
    n = ok["legion_per_1000"].notna().sum()
    block = f"""<!-- MAPS:BEGIN — generated by tools/build_maps.py; edit the script, not this block -->
          <figure class="maps-figure">
            <p class="chart-title">Nationalism, the Legion and desertion, by district</p>
            <p class="chart-sub">Czech lands, {n} census districts of 1910</p>
            <div class="map-tabs" role="group" aria-label="Map view" hidden>{''.join(tabs)}</div>
            <svg class="map" viewBox="{vb}" role="img" aria-label="Map of the Czech lands by 1910 census district">
              {defs}{''.join(layers)}<use class="map-frame" href="#mpframe"/><use class="map-hl off" href="#mpframe"/></svg>
            {''.join(scales)}
            <figcaption class="chart-readout maps-readout" aria-live="polite">
              <span class="chart-when">Hover a district</span>
              <span class="chart-vals"></span>
            </figcaption>
            <p class="maps-note">Each view has its own scale, up to the 97th percentile.
              Definitions are provisional.
              <a href="https://tomashaufer3.github.io/legions-docs/#descriptives" target="_blank" rel="noopener">Court
              districts, settlements and the per-Czech-speaker view</a>.</p>
          </figure>

          <script>
          /* View buttons and hover readout for the map above; its first view is complete
             without this. */
          (function () {{
            var fig = document.currentScript.previousElementSibling;
            var D = {json.dumps(data, ensure_ascii=False, separators=(",", ":"))};
            var T = {json.dumps([t for _c, t, _u, _r, _f in PANELS], ensure_ascii=False)};
            var F = [function (v) {{ return (v >= 0 ? '+' : '\u2212') + Math.abs(v).toFixed(2); }},
                     function (v) {{ return v.toFixed(2); }},
                     function (v) {{ return v.toFixed(1); }},
                     function (v) {{ return v.toFixed(1); }}];
            var map = fig.querySelector('.map'), tabs = fig.querySelector('.map-tabs');
            var hl = fig.querySelector('.map-hl');
            var when = fig.querySelector('.chart-when'), vals = fig.querySelector('.chart-vals');
            var idle = when.textContent, cur = null;
            function view(v) {{
              fig.querySelectorAll('[data-v]').forEach(function (el) {{
                var on = el.getAttribute('data-v') === String(v);
                if (el.classList.contains('map-tab')) el.setAttribute('aria-pressed', on);
                else el.classList.toggle('off', !on);
              }});
            }}
            function show(k) {{
              if (k === cur) return;
              cur = k;
              /* one outline drawn over the map, moved to the district: cheaper and
                 steadier than fading the other 147 */
              if (!k || !D[k]) {{ hl.classList.add('off');
                when.textContent = idle; vals.innerHTML = ''; return; }}
              hl.setAttribute('href', '#mp' + k);
              hl.classList.remove('off');
              when.textContent = D[k][0];
              vals.innerHTML = T.map(function (t, i) {{
                var v = D[k][i + 1];
                return t + '&nbsp;<b>' + (v === null ? '\u2013' : F[i](v)) + '</b>';
              }}).join(' &middot; ');
            }}
            tabs.hidden = false;
            tabs.addEventListener('click', function (e) {{
              var b = e.target.closest('.map-tab');
              if (b) view(b.getAttribute('data-v'));
            }});
            map.addEventListener('pointerover', function (e) {{
              var k = e.target.getAttribute && e.target.getAttribute('data-k');
              show(k || null);
            }});
            /* a tap fires leave straight after it: keep the tapped district's numbers */
            map.addEventListener('pointerleave', function (e) {{
              if (e.pointerType !== 'touch') show(null);
            }});
          }})();
          </script>
          <!-- MAPS:END -->"""

    idx = SITE / "index.html"
    s = idx.open(encoding="utf-8", newline="").read()       # keep the file's line endings
    if "\r\n" in s:
        block = block.replace("\n", "\r\n")
    new, k = re.subn(r"<!-- MAPS:BEGIN.*?<!-- MAPS:END -->", lambda m: block, s, flags=re.S)
    if k != 1:
        raise SystemExit("index.html has no MAPS:BEGIN / MAPS:END markers")
    idx.open("w", encoding="utf-8", newline="").write(new)
    print(f"{n} districts, {len(paths)} court polygons, block {len(block) / 1000:.0f} kB")
    for (col, *_), (lo, hi) in zip(PANELS, ranges):
        print(f"  {col}: {lo:.3f} .. {hi:.3f}")


if __name__ == "__main__":
    main()
