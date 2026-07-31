# tomashaufer3.github.io

Personal academic webpage — Tomáš Haufer, quantitative economic history.

Live at <https://tomashaufer3.github.io/>.

## What this is

A hand-written static site. **No build step, no dependencies, nothing to
install.** Five HTML files and one stylesheet. Edit a file, commit, push — that
is the whole deployment process.

There is no JavaScript anywhere on the site, by design: the abstract toggles on
the research page use the native `<details>` element, so everything works with
scripting disabled and prints correctly.

## Preview locally

From the repository root:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000>.

Use a server rather than opening the files directly — links and assets are
root-relative (`/assets/...`), so `file://` will not resolve them.

## Layout

```
index.html          Home
research.html       Publications, working papers, work in progress
cv.html             Web CV (prints cleanly) + link to the PDF
substack.html       A Diary of an Econ Student (Substack)
404.html            Not-found page, served automatically by GitHub Pages
robots.txt          Permissive — see "Staying out of search" below
.nojekyll           Tells GitHub to serve the files as-is, no Jekyll pass
assets/css/site.css The entire design system, tokens at the top
assets/fonts/       Self-hosted EB Garamond (+ OFL.txt)
assets/img/         Favicon, portrait, Charles University and CERGE-EI logos
assets/img/CUcoat/  Vendor logo source art — gitignored, not served
assets/img/photo/   Original photographs — gitignored, not served
files/theses/       Legions position paper, Laffer curve BA thesis
files/term-papers/  Written in Time, referee performance
files/articles/     The two Moody's commentaries
files/haufer-cv.pdf The CV PDF
```

Every page is built from the same three pieces: a `.site-header`, one or more
full-bleed `.band` sections each wrapping a width-capped `.shell`, and a
`.site-footer`. Inner pages (Research, CV, Writing) put a `.page-grid` inside
the band — a narrow left column for the title and a short standfirst, the
content down the right. 404 skips the grid, because a title column beside three
lines of text reads as a mistake.

## Fonts

EB Garamond, self-hosted from `assets/fonts/`, SIL Open Font License 1.1 (the
licence text ships alongside the files in `OFL.txt`). Nothing is loaded from a
third party at runtime.

The `@font-face` declarations live at the top of `site.css` rather than in a
separate file, so the site still makes exactly one stylesheet request.

Four files, 224 KB total, but a visitor never downloads all four. The browser
picks by `unicode-range` and style, so a page with no italic fetches no italic,
and the 114 KB `latin-ext` file arrives only because Czech diacritics need it:

```
ebgaramond-var-normal-latin.woff2         44 KB
ebgaramond-var-normal-latin-ext.woff2    114 KB   ← á š č ř ž live here
ebgaramond-var-italic-latin.woff2         25 KB
ebgaramond-var-italic-latin-ext.woff2     45 KB
```

Two things worth knowing before changing any of this:

- These are **variable** font files. The CDN served byte-identical files for
  weight 400 and weight 600, so each subset ships once and the face declares
  `font-weight: 400 700`; asking for 600 interpolates from the same file. Do not
  add separate weight files without checking they actually differ.
- **Do not drop the `latin-ext` subset.** It is what carries `á š č ř ž ě ů ý`.
  Without it, every Czech name on the site falls back to a different typeface
  in the middle of a word.

`html { font-size: 111% }` in `site.css` is not arbitrary: Garamond's x-height
is 0.425 of the em where Georgia's is 0.475, so it reads about 11% smaller at
the same nominal size. The root compensates so that everything measured in
`rem` stays proportionate. If you ever swap the typeface, re-measure and adjust
that one number.

To regenerate the font files (e.g. to add a weight), fetch the Google Fonts
CSS with a modern browser user-agent — without one the API serves TTF instead of
woff2 — then download the `latin` and `latin-ext` `woff2` URLs it lists:

```
https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap
```

Note that Python's `urllib` fails on this machine with a certificate error
(a local root CA that OpenSSL rejects); PowerShell's `Invoke-WebRequest` uses
the Windows certificate store and works.

**Both marks are cut from these files too.** `assets/img/favicon.svg` (the TH
monogram) and `assets/img/th-mark.svg` (the header pilcrow) carry real EB
Garamond outlines rather than `<text>`, because both render in an isolated
context with no access to the webfont — `<text>` would fall back to whatever
serif the platform has and the metrics would shift between Windows, macOS and
Linux. To regenerate after a font update (needs `fonttools` and `brotli`, the
latter to read woff2):

```python
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc.transform import Transform
from fontTools.varLib.instancer import instantiateVariableFont

SRC   = "assets/fonts/ebgaramond-var-normal-latin.woff2"
WGHT  = 500     # a shade heavier than body: white-on-navy eats serifs at 400
TRACK = 40      # letterspacing, font units
CAP_H, BASELINE, CENTRE = 24.0, 38.0, 32.0     # target, in the 64-unit box

f  = instantiateVariableFont(TTFont(SRC), {"wght": WGHT}, inplace=True)
gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]

rec, x = RecordingPen(), 0
for ch in "TH":
    gs[cmap[ord(ch)]].draw(TransformPen(rec, Transform().translate(x, 0)))
    x += hmtx[cmap[ord(ch)]][0] + TRACK

bp = BoundsPen(gs); rec.replay(bp)
xmin, ymin, xmax, ymax = bp.bounds
s = CAP_H / (ymax - ymin)
t = (Transform().translate(CENTRE, BASELINE).scale(s, -s)
     .translate(-(xmin + xmax) / 2, -ymin))

out = SVGPathPen(gs, ntos=lambda v: f"{round(v, 2):g}")
rec.replay(TransformPen(out, t))
print(out.getCommands())
```

The favicon uses that path as-is: cap height 24, baseline 38, letters spanning
x 6.8–57.2, red rule beneath at the same width, on a white tile with a hairline
border. The border matters — a `#FFFFFF` tile against light browser chrome has
no edge, and the mark falls apart into three floating shapes without it.

The header pilcrow comes out of the same script with the loop body run once for
`U+00B6` instead of the two letters, and a transform that flips the glyph into
its own bounding box rather than fitting it to a square:

```python
rec = RecordingPen()
gs[cmap[0x00B6]].draw(rec)
bp = BoundsPen(gs); rec.replay(bp)
xmin, ymin, xmax, ymax = bp.bounds
t = Transform().translate(-xmin, ymax).scale(1, -1)   # y-up -> y-down, origin at 0,0
# viewBox is then "0 0 {xmax-xmin:.0f} {ymax-ymin:.0f}"  ->  "0 0 544 945"
```

That tight viewBox is the point: the mark has no built-in margin, so CSS can
set its height and let the 544:945 ratio settle the width, and it can sit as
close to the name as the design wants.

## Images

**The logos.** `assets/img/cu-logo-en.svg` is the Charles University seal with
its English wordmark, converted from the official PDF in `assets/img/CUcoat/`;
`assets/img/cerge-logo.svg` is the CERGE-EI mark. Both are recoloured to
`--cu-navy` so they sit with the palette — the CERGE file originally carried its
fill in an internal `<style>` block, which some renderers ignore, so the fill is
flattened onto the root element instead.

They appear together in the footer, separated by a hairline, and are matched on
optical weight rather than width: the seal is tall and circular, the CERGE
wordmark wide and horizontal, so equal widths would leave the seal tiny.

They are deliberately **not** in the site header. An institutional mark sitting
next to your own name at the top of a page is the visual grammar of an official
University page; this is a personal one. In the footer it reads as "I work
here", which is accurate — CERGE-EI is a joint workplace of Charles University
and the Economics Institute of the Czech Academy of Sciences.

Still to settle: check the University's visual-identity rules for personal
pages, and whether recolouring the mark is allowed.

**The two marks.** `assets/img/favicon.svg` is the TH monogram — your initials
in the site's own EB Garamond on a white tile, with the red rule beneath. A
monogram is exactly right for a browser tab, where there is no room for a name
and the mark has to stand in for one.

`assets/img/th-mark.svg` is the header mark, and it is deliberately *not* the
same thing. It sits beside your name spelled out in full, so repeating the same
two letters next to it would say nothing twice. It is a pilcrow in CU red: the
scribe's mark for "a new argument begins here", older than printing, and a
statement about the work rather than about the person — which is the only thing
a mark next to a name has any business being.

It has no frame. A box around it turned it into a logo; without one it is a
piece of type sitting in the margin, which is what a pilcrow has always been.
Its viewBox is the glyph's own bounding box rather than a square, so it carries
no invisible padding and can sit flush against the name — which also means its
size lives entirely in CSS (`height` on `.brand-mark`, `width: auto`).

See the recipe under **Fonts** for how both are cut from the font files.

**The portrait.** `assets/img/tomas-haufer-portrait.jpg` is an 800×1000 crop of
`photo/54899135309_7d62aa7f34_o.jpg`, the tightest frame in the set. 4:5, face
centred, eyes on the upper third. The earlier crop held about as much corridor
as it did subject, which made it read as a snapshot taken in a building rather
than as a portrait.

The background is desaturated, flattened and very slightly blurred; the subject
is untouched. There is no segmentation model here, so the mask is geometric — a
soft ellipse over the head and torso widening into a band at the shoulders,
blurred by 9% of the frame width so no edge shows. The script is
`portrait.py` in the session scratchpad; the recipe is: crop at
`x0 = 544 − 400`, full height, then `Color 0.34 · Contrast 0.80 · Brightness
1.06 · GaussianBlur 1.1` outside the mask. If you ever want it done properly,
export a masked version from Photoshop and drop it in under the same name.

It is matted rather than framed: a hairline outer rule, a wide margin of paper,
and the photograph inside on a hairline of its own, with the bottom margin cut
deeper than the top the way real mounts are. A lancet arch used to sit behind
it, drawn larger than the picture so its apex rose above and its legs ran down
either side; that read as a second unrelated outline nearby rather than as a
frame, and two frames competing is worse than one.

**Gitignored sources.** `CUcoat/` and `photo/` hold the originals — the vendor
logo artwork and the full-size photographs. The repository has to be public for
Pages, and neither the University's source art nor six near-identical 800 KB
frames belong in it. They live on disk and in Dropbox only, so a fresh clone
will not have them.

## PDFs

`files/` carries about 12 MB. It nearly carried 124 MB: the exports of the two
long papers embed figures at three to eight times the resolution they are
displayed at, and one of them was **107 MB — over GitHub's 100 MB hard limit**,
which would have rejected the push outright.

Both were rewritten with PyMuPDF, resizing each embedded image to roughly 200
DPI at its actual size on the page and re-encoding as JPEG at quality 84. Text
stays vector and is untouched; the figures are visually identical at reading
size. The Written in Time write-up went 107 MB → 6.9 MB, the Laffer thesis
15 MB → 3.8 MB.

**Before adding a PDF, check its size.** A raw LaTeX export with bitmap figures
will be far larger than it needs to be, and anything over 100 MB cannot be
pushed at all.

## Making changes

**Adding a paper.** Open `research.html`. There is a copy-me block in a comment
above the lists, with the rules for which parts are optional. The middot
separators between metadata fields are generated by CSS, so adding or removing a
`<span>` never leaves a stray separator behind.

**Adding a CV row.** Same idea in `cv.html` — one two-column pattern, repeated.
The year column uses tabular figures so ranges line up down the page.

**Retuning the design.** Every colour and rhythm value is a CSS custom property
at the top of `assets/css/site.css`. To drop the red rubrication entirely, set
`--rubric: var(--ink)`.

**Changing the navigation.** The `<header class="site-header">` block is
duplicated in all five HTML files — the cost of having no build step. Keep the
markup byte-identical (only `aria-current="page"` differs) so a change is a
find-and-replace across the five. The same is true of the
`<footer class="site-footer">` block, where nothing differs at all.

**The contact address.** The footer carries `tomas.haufer@cerge-ei.cz` in
plain text on all five pages. `noindex` keeps the page out of search, but the
page is still public and scrapable. The institutional address is the right one
to expose — it can be abandoned; a personal one cannot. Nothing else from the
CV belongs here: no home address, no phone number, no date of birth.

**Content is sourced, not invented.** Every date, title, figure and link on
the site comes from the CVs, the thesis documentation site, or the Substack
about page. Two things were deliberately left off: the `/legions-docs/` note
about a target journal, which is an ambition rather than a fact, and the
personal details above. The home page also carries no figure — the one that
used to be there was built from invented data, which on a research page is
worse than no figure at all. The `.chart` styles are still in the stylesheet
for when there is a real one.

## Staying out of search

Every page carries `<meta name="robots" content="noindex, nofollow">` in its
`<head>`. That tag is the mechanism.

`robots.txt` is deliberately **permissive**. Do not add `Disallow: /` to it: that
stops crawlers from fetching the pages, which means they never read the `noindex`
tag, and a URL linked from anywhere else can stay indexed indefinitely. Allowing
the crawl and serving `noindex` is what actually gets a page dropped. A
`Disallow` here would also cover the whole domain, including the unrelated
`/legions-docs/` project site.

To make the site findable later, remove the `robots` meta tag from all five
files. Consider adding a `sitemap.xml` at the same time.

## Deployment

GitHub Pages serves the `main` branch root. Push and it goes live in about a
minute.

Note that Pages requires the repository to be **public** on a free plan. Search
invisibility comes from `noindex`, not from repository visibility — nothing
private belongs in here.
