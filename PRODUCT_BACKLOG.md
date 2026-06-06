# Product Backlog — driven by user feedback

This is the high-level running list of product changes the **end device** should
make, derived from community feedback. It is the companion to GitHub Issues:

- **GitHub Issues** (mkadie/NeedsBoard) hold the actionable, assignable detail.
- **This file** is the at-a-glance view of where the product is headed and why.

Both are produced by the `feedback-integrate` workflow: each `product` or
`config` theme yields a GitHub issue *and* a one-line row here, tied back to the
feedback that prompted it. Wording-only feedback goes straight to doc PRs, not
here.

The workflow is **variant-aware**: every issue and backlog row is prefixed with
its variant (e.g. `[Involuntary Non-Verbal (MVP)]`, `[Sip-and-Puff]`, or
`[shared]` for cross-device items). GitHub issues should also carry a
`variant:<id>` label.

## How a row gets here

```
form responses (Google Sheet)
   -> Workflow: feedback-integrate
        -> product_deltas
             -> file GitHub issue   (actionable detail)
             -> append row below     (this file)
philosophy gate: anything that erases the MVP's difference from a Fruit Jam
belongs on a carrier board, not the core module — such items are marked
[carrier] rather than [core].
```

## Backlog

| Priority | Variant | Scope | Item | From feedback | Issue |
|----------|---------|-------|------|---------------|-------|
| _(none yet — first batch pending)_ | | | | | |

## Done

| Shipped | Item | Issue |
|---------|------|-------|
| _(nothing yet)_ | | |
