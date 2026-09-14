---
name: readme-polish
description: Reformat an existing README.md into a polished, scannable GitHub-native style — centered hero with badges, GFM admonitions, collapsible details, tables, sparing emoji-headers. Use when the user says a README is "bland"/"plain" and wants it made more engaging, or explicitly asks to restyle a README. Never invent or change facts — formatting only.
---

# README Polish

Reformat an existing README into a polished, GitHub-native style. This is a
**formatting pass, not a rewrite** — every factual claim, caveat, and
command in the original must survive byte-for-byte equivalent in meaning.
No new promises, no softened warnings, no invented features.

## Style target

Modeled on well-regarded open-source READMEs: professional but warm, dense
with signal, easy to scan in 10 seconds and easy to read in full.

Reference READMEs (fetch and skim these, don't guess at the style from
memory):
- https://raw.githubusercontent.com/Azure-Samples/serverless-chat-langchainjs/refs/heads/main/README.md
- https://raw.githubusercontent.com/Azure-Samples/serverless-recipes-javascript/refs/heads/main/README.md
- https://raw.githubusercontent.com/sinedied/run-on-output/refs/heads/main/README.md
- https://raw.githubusercontent.com/sinedied/smoke/refs/heads/main/README.md

- **Centered hero** (`<div align="center">`): title with one sparing emoji,
  a one-line tagline, real badges only (license, language/runtime version,
  build status — only if a real CI exists, never a fabricated badge), and
  a nav link row to the section anchors that matter most.
- **GFM admonitions** in place of plain "note:" prose — use the exact
  syntax from https://github.com/orgs/community/discussions/16925:
  ```
  > [!NOTE]
  > ...
  > [!TIP]
  > ...
  > [!IMPORTANT]
  > ...
  > [!WARNING]
  > ...
  ```
  Match severity to content: `NOTE` for background/context, `TIP` for a
  helpful shortcut, `IMPORTANT` for something the reader must not miss to
  use the project correctly, `WARNING` for a real cost/risk (money, data
  loss, breaking behavior). Don't admonition-ify everything — plain prose
  stays plain prose where nothing is being flagged.
- **`<details>` / `<summary>`** for content that's genuinely optional to
  read up front — alternative install paths, multiple config shapes,
  advanced options. Keep the recommended/default path `<details open>`,
  collapse the rest. Don't hide anything a first-time reader needs.
- **Tables** for anything that's naturally column data (config keys,
  file/path listings, comparison rows) — replaces a bullet list once
  there are 2+ real columns of information, not just to look fancier.
- **Sparing emoji**, section headings only (one per `##`), never scattered
  through body prose. If unsure whether an emoji adds scanability or just
  noise, leave it off.
- Section order stays whatever the project's README already uses — this
  skill restyles, it doesn't reorganize content unless asked to.

## Process

1. Read the target README in full before changing anything.
2. Fetch and skim the reference READMEs above (`WebFetch`, asking for
   structure/tone/admonition/emoji usage) — or any additional ones the
   user points at for this pass — rather than guessing at the style from
   memory.
3. Rewrite section by section, preserving every fact, command, caveat,
   and link. Where the original said something plainly that now fits an
   admonition, convert it — don't delete it in the process.
4. Only include badges/details/tables backed by something real in the
   repo (an actual `LICENSE` file, an actual CI config, an actual version
   file) — never decorative claims about the project that aren't true.
5. Diff-check yourself: every fact in the old version should map to
   exactly one place in the new version. If something got dropped, put it
   back.
6. **Do not commit unless the user explicitly asks.** This is a
   formatting pass the user reviews before it becomes part of history.

## When NOT to use

- The README is factually stale (docs don't match the code) — fix that
  first as a content problem; this skill only restyles accurate content.
- The user wants content added/removed, not just restyled — that's a
  normal edit, not this skill.
</content>
