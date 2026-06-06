# Feedback Form Template

Every device variant gets its own feedback form on tssfaa.com, built from this
template. The goal: **shared questions stay identical across variants** (so the
`feedback-integrate` workflow can spot cross-device themes), and only the
device-specific block changes.

To add a variant's form: copy this file to `form-<variant-id>.md`, keep the
shared block verbatim, and fill in the variant-specific block. Register the
`formFile` path in `.claude/workflows/feedback-integrate.js`.

## Design rules (all forms)

- **Anonymous by default.** No login. Contact is the last, optional question.
- **Everything optional.** Say so at the top. No required asterisks.
- **Plain language, short.** Better a few honest answers than an abandoned form.
- Each question is tagged with the integration category it feeds
  (`wording` / `product` / `config` / `context`) so the workflow can route it.
- One backing **Google Sheet per form**, each carrying a `variant` column, or one
  combined Sheet with a `variant` column. Either way the workflow takes
  `{ variant, feedback }`.

## Intro text

> We're building this device *with* you, not just for you. There are no wrong
> answers, nothing is required, and you can stay completely anonymous. Tell us as
> much or as little as you like — even one sentence helps the people who come
> after you.

## Shared questions — KEEP IDENTICAL ACROSS VARIANTS

1. **Which best describes you?** *(context)* — person who uses it / family / teacher
   / professional / other.
2. **When you can't get the words out, what do you most need to be able to say?**
   *(product / wording)*
3. **The emergency message currently says:** *"Please stand back. I cannot speak
   right now, but I am OK. Crowding me makes it worse. Thank you."* **Does this
   wording work? What would you change?** *(wording)*
4. **What would make a device feel safe to use in public — and what would make it
   worse?** *(product)*
5. **Is anything in the documentation wrong, confusing, or not true to your
   experience?** *(wording)*
6. **What's missing? What do you wish it did?** *(product)*
7. **Anything else you want us to know?** *(context)*
8. **Optional — stay in touch.** *(context)* — mailing list opt-in / join test
   group / email (only if a box is checked).

## Variant-specific block — REPLACE PER VARIANT

> Insert the questions unique to this device here — input modality, screen,
> physical form, setup, anything that doesn't generalize. Tag each with its
> category. Keep it short.

## How responses flow

```
tssfaa.com form  ->  Google Sheet (variant column)
                       └─ batch  ->  Workflow: feedback-integrate { variant, feedback }
                                       ├─ PR-ready doc edits (variant or shared docs)
                                       ├─ product deltas -> GitHub issues + PRODUCT_BACKLOG.md
                                       └─ "you said / we did" -> mailing list
```
