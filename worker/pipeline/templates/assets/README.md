# Report assets

Everything the PDF report draws with, vendored into the repo. Nothing here is fetched at render
time: WeasyPrint resolves these paths against `worker/pipeline/templates/`, and the report is
generated on a worker that may have no network at all. It also means the report an inspector
downloads in 2030 looks the same as the one generated today.

Rebuilt by `worker/pipeline/templates/assets/fetch.sh`.

| File | What | Source | Licence |
|---|---|---|---|
| `fonts/IBMPlexSans-Regular.ttf`, `fonts/IBMPlexSans-SemiBold.ttf` | The report's only typeface | [IBM/plex](https://github.com/IBM/plex) `packages/plex-sans/fonts/complete/ttf/` | **SIL Open Font License 1.1**, full text in `fonts/OFL.txt` |
| `icons/circle-check.svg`, `circle-x.svg`, `circle-question-mark.svg`, `triangle-alert.svg`, `scale.svg` | Section marks: passed, violation, not verifiable, note, masthead | [lucide-icons/lucide](https://github.com/lucide-icons/lucide) `icons/` | **ISC**, full text in `icons/LICENSE` |

## Why these

**IBM Plex Sans** for a large x-height and figures that cannot be confused at 9 pt — this report
is read on a phone, and half of what it says is numbers and rule references. It also carries
**₹ (U+20B9)**, which the Section 36 penalty footer needs and many otherwise good faces do not.
Two weights, ~200 KB each; WeasyPrint subsets what it embeds, so the PDF pays for the glyphs it
uses and not the file. Embedding the face rather than naming it is what keeps the report
identical on a Windows laptop, an inspector's phone and the Debian container.

**Lucide** because the icons are stroked SVG paths with `stroke="currentColor"`, so they take the
colour of the section they sit in with no per-icon CSS, and each one is under 400 bytes inlined.

**No emblem, seal or crest.** The State Emblem of India is protected by the State Emblem of India
(Prohibition of Improper Use) Act, 2005, and a compliance report that looks like it was issued by
a government body when it was not is worse than one with no mark at all. The masthead uses a
balance scale — weights and measures, which is what Legal Metrology is.

**No stock photography and no decorative images.** The only pictures in the report are the
inspector's own photographs, and they are there as evidence.
