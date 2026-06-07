# Survey Integration — deploying the feedback forms on tssfaa.com

**Audience:** the Claude instance working on the tssfaa.com website project (and
Michael). This is a self-contained handoff: it tells you what the forms are,
where the single source of truth lives, how to deploy them on a **static HTML
site**, and how responses flow back into the integration workflow.

tssfaa.com is a hand-maintained **static HTML** site (no CMS, no server-side
form processing). So the deployment must not assume a backend. Two supported
paths below; **Path A (Google Form embed) is recommended** because it needs zero
backend and writes straight to a Google Sheet, which is what the workflow reads.

---

## 1. Single source of truth

All form content is data, not hand-written HTML. The canonical file is:

- **`docs/feedback/questions.json`** in `mkadie/NeedsBoard`.
  Raw URL (lives on `main`):
  `https://raw.githubusercontent.com/mkadie/NeedsBoard/main/docs/feedback/questions.json`

It defines a question bank, and per device **variant** an ordered list of which
questions appear, plus per-variant option overrides. A question added to
`alwaysInclude` appears on **every** form (that's how the "what can we do to make
this form better?" question works).

Human-readable previews of each form are the generated
`docs/feedback/form-<variant>.md` files. Never hand-edit those or the deployed
forms directly — **edit `questions.json` and regenerate**, so the website, the
markdown previews, and the workflow never drift.

Current variants: `involuntary-nonverbal-mvp` (live) and `sip-and-puff` (draft).

### Question schema (from questions.json)

```jsonc
"some_id": {
  "category": "wording | product | config | context | meta",
  "type": "text | single | multi | contact",
  "text": "The question shown to the user.",
  "help": "Optional note shown under the question. \n\n = paragraph break.",
  "options": ["only for single | multi | contact"]
}
```

`category` is guidance for the workflow; the workflow re-classifies anyway, so it
does **not** need to be carried through the live form.

---

## 2. Accessibility is non-negotiable

This is an assistive-technology audience — several respondents use screen
readers, switches, or have motor/anxiety constraints. Any deployed form MUST:

- Be operable by keyboard alone and by screen reader (proper `<label for>`,
  `<fieldset>`/`<legend>` for choice groups, visible focus styles).
- State up front that it is **anonymous** and **everything is optional**.
- Avoid required fields, timers, CAPTCHAs, and login walls.
- Use high-contrast text and large tap targets.

Google Forms is reasonably accessible out of the box; a custom HTML form (Path B)
must be built to these rules (the generator below does this).

---

## 3. Path A — Google Form embed (recommended)

Zero backend. The form auto-creates a Google Sheet of responses.

### A1. Generate the Google Form from questions.json (automated)

Use the Apps Script in [`survey/build-google-form.gs`](./survey/build-google-form.gs):

1. Go to <https://script.google.com> → New project. Paste the script.
2. Set `VARIANT_ID` at the top (e.g. `'involuntary-nonverbal-mvp'`).
3. Run `buildForm()`. Authorize when prompted.
4. The Execution log prints the Form's **published URL**, **edit URL**, and the
   linked **Sheet URL**. The form is built entirely from the live questions.json.

Re-run it whenever questions.json changes to rebuild the form (or hand-edit the
Google Form for small tweaks — but prefer regenerating to stay in sync).

> Prefer not to script it? You can build the Google Form by hand from the
> `form-<variant>.md` preview — but the script keeps it in sync for free.

### A2. Embed it in the static site

1. In the Google Form editor: **Send → `< >` (embed HTML)** → copy the
   `<iframe>`.
2. Create a page in the website repo, e.g. `feedback-mvp.html` (and later
   `feedback-sip-and-puff.html`), matching the site's existing page template
   (same header/nav/footer as `signup-form.html`).
3. Paste the iframe into the page body. Give the iframe a `title` attribute for
   screen readers, e.g. `title="Involuntary Non-Verbal device feedback form"`,
   and `width="100%"` with a generous `height`.
4. Link it from the nav and from the relevant device section (the MVP page links
   to `feedback-mvp.html`).
5. Commit/deploy the static page as the site is normally deployed.

That's the whole deployment for Path A.

---

## 4. Path B — native styled HTML form (when you want full control)

Use this if a Google-branded iframe doesn't fit the design. Still no traditional
backend — submissions go to a Google Apps Script "web app" endpoint that appends
to a Sheet.

1. **Generate the page:** `node survey/build-html-form.js involuntary-nonverbal-mvp`
   reads questions.json and writes an accessible, self-styled
   `survey/dist/feedback-involuntary-nonverbal-mvp.html` whose `<form action>` is
   a placeholder you replace with your endpoint URL.
2. **Deploy the endpoint:** in Apps Script, paste
   [`survey/apps-script.gs`](./survey/apps-script.gs), create/choose a Sheet,
   then **Deploy → New deployment → Web app**, "Execute as me", "Anyone".
   Copy the web-app URL.
3. Put that URL in the generated page's `<form action>` (or pass it:
   `node survey/build-html-form.js <variant> <endpointURL>`).
4. Drop the page into the website repo, link it, deploy.

The form does a normal full-page POST to the endpoint (no CORS/JS needed); the
endpoint appends a row and returns a thank-you page.

---

## 5. The response → workflow contract

Whichever path, responses land in a **Google Sheet, one row per response**. To
turn a batch into doc/product changes, feed it to the `feedback-integrate`
workflow (in the NeedsBoard repo) as:

```js
{ variant: 'involuntary-nonverbal-mvp', feedback: [ /* items */ ] }
```

- **Use one Google Form (and Sheet) per variant**, so the variant is implicit —
  pass it explicitly when running the workflow.
- **One feedback item per response** keeps a person's context together. Each
  item is `{ id, text }` where `text` is the response's answers (Q/A pairs are
  fine). The workflow clusters across items and classifies each itself.
- Export a batch with the `exportBatch()` helper included in
  `survey/build-google-form.gs` (logs the response sheet as a JSON array ready to
  paste as the workflow's `feedback`), or just copy the new rows.

The workflow then emits: doc-edit PRs, product deltas (GitHub issues +
`PRODUCT_BACKLOG.md`), and "you said / we did" lines for the mailing list. The
`meta` category routes "improve this form" answers back to `questions.json`.

---

## 6. Keeping in sync (the rule)

```
questions.json  ──▶  form-*.md (preview)        [node docs/feedback/build-forms.js]
              └────▶  Google Form / HTML page   [rebuild via Path A or B]
              └────▶  workflow classification
```

When questions change: edit `questions.json`, run
`node docs/feedback/build-forms.js`, then rebuild the live form (re-run the Apps
Script, or re-run `build-html-form.js`). One edit, three outputs stay aligned.

---

## 7. File manifest — what to bring into the website project

Copy these from `mkadie/NeedsBoard` (or fetch the raw URLs):

| File | Why the website project needs it |
|------|----------------------------------|
| `survey_integration.md` (this file) | The handoff guide |
| `docs/feedback/questions.json` | **Source of truth** for all questions |
| `docs/feedback/form-involuntary-nonverbal-mvp.md` | Human-readable preview of the MVP form |
| `docs/feedback/form-sip-and-puff.md` | Preview of the sip-and-puff form (draft) |
| `survey/build-google-form.gs` | Path A: auto-build the Google Form + export helper |
| `survey/build-html-form.js` | Path B: generate an accessible native HTML form |
| `survey/apps-script.gs` | Path B: the Sheet-writing endpoint |

The website project does **not** need the firmware, the workflow, or the rest of
NeedsBoard — only the files above. If you only do Path A, you can skip
`build-html-form.js` and `apps-script.gs`.

---

## 8. First deploy checklist (MVP)

- [ ] Build the MVP Google Form (Path A1) and confirm it writes to a Sheet
- [ ] Create `feedback-mvp.html` from the site template, embed the iframe (with a
      `title`), link it from nav + the MVP section
- [ ] Verify anonymous submission works end-to-end and a row appears in the Sheet
- [ ] Confirm keyboard + screen-reader operability
- [ ] Hold the `sip-and-puff` form until its terminology question set is confirmed
- [ ] When responses accrue, run `feedback-integrate { variant, feedback }`
