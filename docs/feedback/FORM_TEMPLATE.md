# Feedback Forms — how the system works

Feedback forms are **data-driven**. You don't hand-write them — you edit one
registry and regenerate.

```
questions.json   ─ node build-forms.js ─▶   form-<variant>.md   ─▶  build on tssfaa.com
   (source of truth)                          (generated; do not edit by hand)
```

- **`questions.json`** — the canonical question bank plus, per variant, the
  ordered list of question ids and any per-variant option overrides.
- **`build-forms.js`** — `node docs/feedback/build-forms.js` regenerates every
  `form-<variant>.md`.
- **`form-<variant>.md`** — generated artifacts. The on-screen tssfaa.com form is
  built from these; the matching Google Sheet feeds the `feedback-integrate`
  workflow as `{ variant, feedback }`.

## Adding questions dynamically

| You want to… | Do this in `questions.json` |
|---|---|
| Add a question to **every** form | Add it to `questions`, then add its id to **`alwaysInclude`** |
| Add a **shared** body question to some forms | Add it to `questions`, reference its id in each variant's `order` |
| Add a **variant-specific** question | Add it to `questions`, reference its id only in that variant's `order` |
| Change wording for **all** forms | Edit the question's `text`/`help` once |
| Change options for **one** variant | Add it under that variant's `optionOverrides` |

Then run `node docs/feedback/build-forms.js`. Keep shared questions truly shared
so the workflow can spot **cross-device themes**.

## Question fields

```jsonc
"some_id": {
  "category": "wording | product | config | context | meta",
  "type": "text | single | multi | contact",
  "text": "The question.",
  "help": "Optional explanation (rendered as an indented note). Use \n\n for paragraphs.",
  "options": ["only for single/multi/contact"]
}
```

`category` routes the answer in the integration workflow. **`meta`** is feedback
about the form itself (e.g. the "what can we do to make this form better?"
question on every form) — it improves `questions.json`, not the device docs.

## Variant fields

```jsonc
"variant-id": {
  "title": "Display name",
  "docUrl": "https://…",             // link to this device's documentation,
                                     //   shown in the intro of every form
  "status": "DRAFT",                 // optional; shown in the heading
  "statusBanner": "…",               // optional blockquote under the heading
  "preamble": "## Section\n…",        // optional markdown before the questions
  "order": ["q1", "q2", …],          // body questions, in order
  "optionOverrides": { "q1": [...] } // per-variant option lists
}
```

`alwaysInclude` questions are appended after `order` on every form. The
top-level `docLinkLabel` sets the link text used for every variant's `docUrl`
(e.g. "New here? Read about this device").
