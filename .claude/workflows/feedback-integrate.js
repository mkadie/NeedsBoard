export const meta = {
  name: 'feedback-integrate',
  description: 'Variant-aware feedback integration. Clusters a feedback batch for a chosen device variant, maps themes to that variant\'s base docs, drafts + adversarially verifies edits under the variant\'s terminology + philosophy rules, and emits PR-ready doc edits, product deltas (GitHub issues + backlog rows), and a "you said / we did" changelog for the mailing list.',
  phases: [
    { title: 'Cluster' },
    { title: 'Analyze' },
    { title: 'Verify' },
    { title: 'Synthesize' },
  ],
}

// ===========================================================================
// VARIANT REGISTRY  — edit this block to add a device/variant.
// (Workflow scripts have no filesystem access, so the registry lives here.
//  Keep docs/feedback/*.md forms in sync with the formFile paths below.)
// ===========================================================================
const SHARED_BASE_DOCS = ['README.md', 'GUIDE_FOR_TEACHERS.md', 'HISTORY.md', 'menu_system.md']
const DEFAULT_VARIANT = 'involuntary-nonverbal-mvp'

const VARIANTS = {
  'involuntary-nonverbal-mvp': {
    displayName: 'Involuntary Non-Verbal (MVP)',
    doc: 'involuntary_nonverbal_mvp.md',
    formFile: 'docs/feedback/form-involuntary-nonverbal-mvp.md',
    baseDocs: ['involuntary_nonverbal_mvp.md', 'custom_processor_description.md', 'hardware_limitations.md', 'config.txt'],
    audienceNote:
      'Primary readers are the people who live with the condition; secondary are clinicians, teachers, and families. Voice is warm second-person.',
    terminologyRules:
      'Use "involuntary non-verbal" throughout. "selective mutism" is permitted ONLY as the single up-front clinical reference.',
    philosophyGuardrail:
      'The MVP is the MINIMUM useful build. Reject scope creep that erases its difference from a full Fruit Jam — such features belong on a carrier board, not the core module.',
  },

  'sip-and-puff': {
    displayName: 'Sip-and-Puff (breath-controlled)',
    // Base docs default to this repo (NeedsBoard); the related repo is SipNPuff.
    doc: 'TODO: sip-and-puff variant doc (not yet written)',
    formFile: 'docs/feedback/form-sip-and-puff.md',
    relatedRepo: 'https://github.com/mkadie/SipNPuff',
    baseDocs: ['custom_processor_description.md', 'README.md'],
    audienceNote:
      'Both the person who uses the device AND caregivers fill out feedback. Users have limited mobility/strength and may be verbal or non-verbal.',
    terminologyRules:
      'Do NOT invent or assume a label. The community-preferred terms are being gathered from the form (Question 1). Until confirmed, default to respectful, person-led language and avoid "wheelchair-bound", "suffers from", "confined to". Flag any wording that presumes a term.',
    philosophyGuardrail:
      'Safety and reliability come first: this input modality is on the medical-grade path (IEC 62304 / FDA Class II direction). Reject changes that compromise per-user calibration, redundant pressure sensing, or the safety MCU. This variant is NOT bound by the MVP "minimum" philosophy.',
    status: 'draft — terminology being gathered via the form',
  },
}

// ===========================================================================
// Input. Pass via Workflow args:
//   { variant: '<id>', feedback: [...] }   (variant defaults to DEFAULT_VARIANT)
// feedback accepts: array of strings | array of {id?,text|body,channel?,date?}
//   | { feedback:[...] } | a single text blob (split on blank lines / "---").
// ===========================================================================
function pickArgs(input) {
  let variant = DEFAULT_VARIANT
  let rawFeedback = input
  if (input && typeof input === 'object' && !Array.isArray(input) && ('variant' in input || 'feedback' in input)) {
    if (input.variant) variant = input.variant
    rawFeedback = input.feedback
  }
  return { variant, rawFeedback }
}

function normalizeFeedback(input) {
  if (!input) return []
  if (input && typeof input === 'object' && Array.isArray(input.feedback)) return normalizeFeedback(input.feedback)
  if (Array.isArray(input)) {
    return input.map((it, i) => typeof it === 'string'
      ? { id: `fb${i + 1}`, text: it, channel: 'unknown', date: 'unknown' }
      : { id: it.id || `fb${i + 1}`, text: it.text || it.body || '', channel: it.channel || 'unknown', date: it.date || 'unknown' })
  }
  if (typeof input === 'string') {
    return input.split(/\n-{3,}\n|\n{2,}/).map((s) => s.trim()).filter(Boolean)
      .map((t, i) => ({ id: `fb${i + 1}`, text: t, channel: 'unknown', date: 'unknown' }))
  }
  return []
}

// ===========================================================================
// Schemas
// ===========================================================================
const THEMES_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['themes'],
  properties: {
    themes: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'title', 'summary', 'feedback_ids', 'frequency', 'representative_quotes', 'cross_variant'],
        properties: {
          id: { type: 'string' },
          title: { type: 'string' },
          summary: { type: 'string' },
          feedback_ids: { type: 'array', items: { type: 'string' } },
          frequency: { type: 'integer' },
          representative_quotes: { type: 'array', items: { type: 'string' } },
          cross_variant: { type: 'boolean', description: 'true if this likely applies to ALL devices, not just this variant' },
        },
      },
    },
  },
}

const ANALYSIS_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['theme_id', 'title', 'category', 'scope', 'rationale', 'affected_docs', 'proposed_edits'],
  properties: {
    theme_id: { type: 'string' },
    title: { type: 'string' },
    category: { type: 'string', enum: ['wording', 'product', 'config', 'meta', 'out_of_scope'] },
    scope: { type: 'string', enum: ['variant', 'shared'], description: 'shared = applies across all devices' },
    rationale: { type: 'string' },
    affected_docs: {
      type: 'array',
      items: { type: 'object', additionalProperties: false, required: ['path', 'why'], properties: { path: { type: 'string' }, why: { type: 'string' } } },
    },
    proposed_edits: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['path', 'location_hint', 'current_excerpt', 'proposed_text', 'edit_summary'],
        properties: {
          path: { type: 'string' }, location_hint: { type: 'string' }, current_excerpt: { type: 'string' },
          proposed_text: { type: 'string' }, edit_summary: { type: 'string' },
        },
      },
    },
    product_requirement: {
      type: ['object', 'null'], additionalProperties: false, required: ['title', 'description', 'priority'],
      properties: { title: { type: 'string' }, description: { type: 'string' }, priority: { type: 'string', enum: ['low', 'medium', 'high'] } },
    },
    config_change: {
      type: ['object', 'null'], additionalProperties: false, required: ['key', 'proposed_value', 'why'],
      properties: { key: { type: 'string' }, proposed_value: { type: 'string' }, why: { type: 'string' } },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['theme_id', 'recommendation', 'conflicts', 'violates_philosophy', 'breaks_terminology', 'notes'],
  properties: {
    theme_id: { type: 'string' },
    recommendation: { type: 'string', enum: ['accept', 'revise', 'reject'] },
    conflicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['doc', 'description', 'severity'],
        properties: { doc: { type: 'string' }, description: { type: 'string' }, severity: { type: 'string', enum: ['low', 'medium', 'high'] } },
      },
    },
    violates_philosophy: { type: 'boolean' },
    breaks_terminology: { type: 'boolean' },
    revised_edits: {
      type: ['array', 'null'],
      items: {
        type: 'object', additionalProperties: false,
        required: ['path', 'location_hint', 'current_excerpt', 'proposed_text', 'edit_summary'],
        properties: {
          path: { type: 'string' }, location_hint: { type: 'string' }, current_excerpt: { type: 'string' },
          proposed_text: { type: 'string' }, edit_summary: { type: 'string' },
        },
      },
    },
    notes: { type: 'string' },
  },
}

const SYNTHESIS_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['summary', 'doc_edits', 'product_deltas', 'changelog_entries'],
  properties: {
    summary: { type: 'string' },
    doc_edits: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['path', 'edits'],
        properties: {
          path: { type: 'string' },
          edits: {
            type: 'array',
            items: {
              type: 'object', additionalProperties: false, required: ['current_excerpt', 'proposed_text', 'edit_summary'],
              properties: { current_excerpt: { type: 'string' }, proposed_text: { type: 'string' }, edit_summary: { type: 'string' } },
            },
          },
        },
      },
    },
    product_deltas: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['issue_title', 'issue_body', 'priority', 'backlog_row'],
        properties: {
          issue_title: { type: 'string' }, issue_body: { type: 'string' },
          priority: { type: 'string', enum: ['low', 'medium', 'high'] }, backlog_row: { type: 'string' },
        },
      },
    },
    changelog_entries: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['you_said', 'we_did'],
        properties: { you_said: { type: 'string' }, we_did: { type: 'string' } },
      },
    },
  },
}

// ===========================================================================
// Run
// ===========================================================================
const { variant: variantId, rawFeedback } = pickArgs(args)
const variant = VARIANTS[variantId]
if (!variant) {
  log(`Unknown variant "${variantId}". Known: ${Object.keys(VARIANTS).join(', ')}.`)
  return { error: 'unknown_variant', knownVariants: Object.keys(VARIANTS) }
}
if (variant.status) log(`WARNING: variant "${variantId}" is ${variant.status} — verify its registry entry before trusting output.`)

const feedback = normalizeFeedback(rawFeedback)
if (!feedback.length) {
  log('No feedback supplied. Pass { variant, feedback } via Workflow args.')
  return { error: 'no_feedback', variant: variantId, themes: [] }
}
const byId = {}
for (const f of feedback) byId[f.id] = f
const allDocs = [...new Set([...variant.baseDocs, ...SHARED_BASE_DOCS])]
log(`Integrating ${feedback.length} item(s) for variant "${variant.displayName}".`)

// 1. Cluster --------------------------------------------------------------
phase('Cluster')
const clustered = await agent(
  `You are triaging community feedback on the T-Rex Talk "${variant.displayName}" AAC device and its documentation.

${variant.audienceNote}

Raw feedback batch (JSON):
${JSON.stringify(feedback, null, 2)}

Cluster these into a SMALL set of coherent themes. Merge items that make the same underlying point. For each theme record the contributing feedback ids, a short title, a 1-2 sentence summary, the count of supporting items, 1-3 short verbatim quotes, and whether it likely applies to ALL devices (cross_variant=true) versus just this one. Return ONLY the structured object.`,
  { schema: THEMES_SCHEMA, label: 'cluster', phase: 'Cluster' },
)
const themes = clustered.themes || []
log(`Found ${themes.length} theme(s).`)

// 2+3. Analyze each theme, then adversarially verify (pipeline, no barrier)
const results = await pipeline(
  themes,
  (theme) => {
    const items = (theme.feedback_ids || []).map((id) => byId[id]).filter(Boolean)
    return agent(
      `You are integrating ONE theme of user feedback for the T-Rex Talk "${variant.displayName}" variant.

${variant.audienceNote}

THEME:
${JSON.stringify(theme, null, 2)}

ORIGINATING FEEDBACK ITEMS:
${JSON.stringify(items, null, 2)}

Documents in this repository you may consult (read the ones relevant to this theme).
This variant's docs:
${variant.baseDocs.map((d) => '  - ' + d).join('\n')}
Shared docs (apply across all devices):
${SHARED_BASE_DOCS.map((d) => '  - ' + d).join('\n')}

Steps:
1. Read the relevant doc(s).
2. Classify the theme as exactly one of: "wording" / "product" / "config" / "meta" / "out_of_scope". Use "meta" for feedback ABOUT THE FORM ITSELF (the "what can we do to make this form better?" question) — those edits target docs/feedback/questions.json, not the device docs.
3. Set scope: "shared" if the change belongs in a shared doc (applies to all devices), else "variant".
4. List which doc(s) it affects and why.
5. If it implies doc text changes, draft concrete proposed edits (path, location hint, current-text excerpt, proposed replacement, one-line summary). Keep the project's voice.
6. If it implies a product/feature change, fill product_requirement; if a config/default change, fill config_change; else null.

TERMINOLOGY RULES for this variant: ${variant.terminologyRules}
DESIGN GUARDRAIL for this variant: ${variant.philosophyGuardrail}

Return ONLY the structured object.`,
      { schema: ANALYSIS_SCHEMA, label: `analyze:${theme.id}`, phase: 'Analyze' },
    )
  },
  (analysis, theme) =>
    agent(
      `You are an adversarial reviewer checking a proposed feedback integration for the "${variant.displayName}" variant BEFORE it is applied. Default to skepticism.

PROPOSED ANALYSIS + EDITS:
${JSON.stringify(analysis, null, 2)}

Read the affected doc(s) and stress-test each proposed edit:
- Does it CONFLICT with or contradict existing content elsewhere?
- Does it VIOLATE this variant's design guardrail? → ${variant.philosophyGuardrail}
- Does it BREAK this variant's terminology rules? → ${variant.terminologyRules}
- If scope="shared", is the edit truly device-agnostic (won't break another variant)?
- Is the proposed wording accurate and in-voice?

Recommend "accept", "revise" (supply corrected revised_edits), or "reject" (explain in notes). Set violates_philosophy and breaks_terminology accordingly. Return ONLY the structured object.`,
      { schema: VERDICT_SCHEMA, label: `verify:${theme.id}`, phase: 'Verify' },
    ).then((verdict) => ({ analysis, verdict })),
)

const kept = results.filter(Boolean).filter((r) => r.verdict.recommendation !== 'reject')
const rejected = results.filter(Boolean).filter((r) => r.verdict.recommendation === 'reject')
log(`${kept.length} theme(s) kept, ${rejected.length} rejected by adversarial review.`)
if (!kept.length) return { variant: variantId, themes, results, synthesis: null, note: 'All themes rejected on review.' }

// 4. Synthesize ready-to-use artifacts ------------------------------------
phase('Synthesize')
const synthesis = await agent(
  `You are producing the final integration artifacts for the T-Rex Talk "${variant.displayName}" variant.

VERIFIED THEMES (analysis + verdict — use revised_edits wherever the verdict says "revise"):
${JSON.stringify(kept, null, 2)}

Produce three ready-to-use sets of artifacts:
1. doc_edits — consolidated, de-duplicated edits grouped by file path, ready to apply as a PR.
2. product_deltas — for every "product" or "config" theme, a ready-to-file GitHub issue (title + markdown body including the originating ask), a priority, and a one-line PRODUCT_BACKLOG.md row. PREFIX every issue_title and backlog_row with "[${variant.displayName}]" (or "[shared]" when the theme's scope is shared).
3. changelog_entries — warm, plain-language "you said / we did" pairs for the mailing list, with ALL personal/identifying info stripped.

Return ONLY the structured object.`,
  { schema: SYNTHESIS_SCHEMA, label: 'synthesize', phase: 'Synthesize' },
)

return { variant: variantId, themes, results, kept, rejected, synthesis }
