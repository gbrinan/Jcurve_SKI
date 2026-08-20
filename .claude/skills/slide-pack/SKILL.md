---
name: slide-pack
version: "1.1.0"
description: "Turn a plan, prompt, or markdown document into a self-contained HTML slide deck for sharing with a team. Use for '슬라이드로 만들어줘', '발표용으로 정리해줘', '패키징 결과를 보여주자', or any request to present a document to colleagues."
argument-hint: 'slide-pack agent-plan.md | slide-pack 이 폴더의 기획서를 슬라이드로'
allowed-tools: Read, Write, Glob
user-invocable: true
---

# slide-pack — self-contained HTML slide decks

Convert a document (plan, prompt, README, interview summary) into a **single HTML file**
that opens in a browser with no server and no network. Removal-first: do not transcribe
the document, keep only what the presentation needs.

## Where the templates are

Look for `assets/template-sk-ci.html` in this order and use the first that exists:

1. `<this skill's folder>/assets/`
2. `./assets/`

## Format rules

1. **Self-contained.** No CDN, no web fonts, no external images. All CSS and JS inline.
   One file on a shared drive must open by double-click.
2. **Structure.** One slide = one `<section class="slide">`. 16:9, centered.
3. **Navigation.** ←/→ arrows, spacebar, click. Page indicator bottom-right.
4. **Density limit.**
   - One message per slide, at most 5 bullets, one line each
   - Tables at most 6 rows — over that, show "대표 N건 + 전체는 원문 참조"
   - Compress to keywords; never paste sentences from the source
5. **Name the SSOT.** The last slide states the source document's path. A deck is a
   summary, not the original — when the source changes, regenerate.
6. **Do not reinvent the theme.** Pick a template:
   - Internal sharing (default): `assets/template.html` (dark)
   - Presentation (SK CI): `assets/template-sk-ci.html` — design tokens live in
     `DESIGN.md`; never invent a color or size that is not there
7. **Presentation extras** (SK CI theme):
   - Slide titles are claims, not topics — one sentence that asserts something
   - Three or more parts: add `slide divider` sections
   - First slide names the presenters and their split; last slide names the source

## Procedure

1. Read the source and map its section structure.
2. Draft the slide outline first: title + one per section + closing (source path).
   **Never exceed 10 slides** — merge or drop sections instead.
3. Compress each slide to the density limit. Point dropped material at the source
   on the closing slide.
4. Fill the chosen template. Write the file next to the source as
   `<source-stem>-deck.html`.
5. Report the slide count and what was dropped.

## What not to do

- Do not summarize by deleting the specifics. A slide saying "여러 이슈가 있음" is worse
  than no slide. Keep the number, the name, the amount.
- Do not carry `(미정)` markers into a deck silently — if the source has open questions,
  give them their own slide.
