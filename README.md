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
assets/img/         Favicon and the Charles University emblem
assets/img/CUcoat/  Source art for the emblem — gitignored, not served
files/              PDFs (CV)
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

## The Charles University emblem

`assets/img/cu-emblem.svg` is the served file: a single-colour vector of the
historical seal, traced from the University's official artwork in
`assets/img/CUcoat/`. It appears twice — as a faint watermark behind the About
column on the home page, and beside the affiliation line in every footer.

The `CUcoat/` sources are **gitignored**: this repository has to be public for
Pages, and republishing the University's source art is a separate thing from
using the emblem to show affiliation. They live on disk (and in Dropbox) only,
so a fresh clone will not have them. Nothing on the site loads them — if you
ever need to retrace the SVG, fetch the artwork from the University again.

It is deliberately **not** in the site header. An institutional emblem sitting
next to your own name at the top of a page is the visual grammar of an official
University page; this is a personal one. Beside a footer address it reads as "I
work here", which is what is being claimed.

One thing still to settle before this goes public: check the University's
visual-identity rules for personal pages. The emblem is currently drawn in
`--cu-navy`, matching the site rather than the official colour.

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

**The contact address.** The footer carries a plain email address. `noindex`
keeps the page out of search, but the page is still public and scrapable —
worth a decision before this goes live, and it has to be made in five files.

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
