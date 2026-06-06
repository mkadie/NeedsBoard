export const meta = {
  name: 'feedback-integrate',
  description: 'Cluster community feedback on the Involuntary Non-Verbal (MVP) docs, map each theme to base docs, draft + adversarially verify edits, and emit PR-ready doc edits, product deltas (GitHub issues + backlog rows), and a "you said / we did" changelog for the mailing list.',
  phases: [
    { title: 'Cluster' },
    { title: 'Analyze' },
    { title: 'Verify' },
    { title: 'Synthesize' },
  ],
}

// ---------------------------------------------------------------------------
// Input. Pass feedback via Workflow's `args`. Accepts any of:
//   - an array of strings
//   - an array of {id?, text|body, channel?, date?}
//   - { feedback: [...] }
//   - a single string blob (split on blank lines or "---")
// ---------------------------------------------------------------------------
function normalizeFeedback(input) {
  if (!input) return []
  if (input && typeof input === 'object' && Array.isArray(input.feedback)) {
    return normalizeFeedback(input.feedback)
  }
  if (Array.isArray(input)) {
    return input.map((it, i) => typeof it === 'string'
      ? { id: `fb${i + 1}`, text: it, channel: 'unknown', date: 'unknown' }
      : {
          id: it.id || `fb${i + 1}`,
          text: it.text || it.body || '',
          channel: it.channel || 'unknown',
          date: it.date || 'unknown',
        })
  }
  if (typeof input === 'string') {
    return input
      .split(/\n-{3,}\n|\n{2,}/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((t, i) => ({ id: `fb${i + 1}`, text: t, channel: 'unknown', date: 'unknown' }))
  }
  return []
}

// Base documents an analyzer may need to read to place / sanity-check a theme.
const BASE_DOCS = [
  'involuntary_nonverbal_mvp.md',
  'custom_processor_description.md',
  'README.md',
  'GUIDE_FOR_TEACHERS.md',
  'HISTORY.md',
  'menu_system.md',
  'hardware_limitations.md',
  'config.txt',
]

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const THEMES_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['themes'],
  properties: {
    themes: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['id', 'title', 'summary', 'feedback_ids', 'frequency', 'representative_quotes'],
        properties: {
          id: { type: 'string' },
          title: { type: 'string' },
          summary: { type: 'string' },
          feedback_ids: { type: 'array', items: { type: 'string' } },
          frequency: { type: 'integer' },
          representative_quotes: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  },
}

const ANALYSIS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['theme_id', 'title', 'category', 'rationale', 'affected_docs', 'proposed_edits'],
  properties: {
    theme_id: { type: 'string' },
    title: { type: 'string' },
    category: { type: 'string', enum: ['wording', 'product', 'config', 'out_of_scope'] },
    rationale: { type: 'string' },
    affected_docs: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['path', 'why'],
        properties: { path: { type: 'string' }, why: { type: 'string' } },
      },
    },
    proposed_edits: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['path', 'location_hint', 'current_excerpt', 'proposed_text', 'edit_summary'],
        properties: {
          path: { type: 'string' },
          location_hint: { type: 'string' },
          current_excerpt: { type: 'string' },
          proposed_text: { type: 'string' },
          edit_summary: { type: 'string' },
        },
      },
    },
    product_requirement: {
      type: ['object', 'null'],
      additionalProperties: false,
      required: ['title', 'description', 'priority'],
      properties: {
        title: { type: 'string' },
        description: { type: 'string' },
        priority: { type: 'string', enum: ['low', 'medium', 'high'] },
      },
    },
    config_change: {
      type: ['object', 'null'],
      additionalProperties: false,
      required: ['key', 'proposed_value', 'why'],
      properties: {
        key: { type: 'string' },
        proposed_value: { type: 'string' },
        why: { type: 'string' },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['theme_id', 'recommendation', 'conflicts', 'violates_minimum_philosophy', 'breaks_terminology', 'notes'],
  properties: {
    theme_id: { type: 'string' },
    recommendation: { type: 'string', enum: ['accept', 'revise', 'reject'] },
    conflicts: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['doc', 'description', 'severity'],
        properties: {
          doc: { type: 'string' },
          description: { type: 'string' },
          severity: { type: 'string', enum: ['low', 'medium', 'high'] },
        },
      },
    },
    violates_minimum_philosophy: { type: 'boolean' },
    breaks_terminology: { type: 'boolean' },
    revised_edits: {
      type: ['array', 'null'],
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['path', 'location_hint', 'current_excerpt', 'proposed_text', 'edit_summary'],
        properties: {
          path: { type: 'string' },
          location_hint: { type: 'string' },
          current_excerpt: { type: 'string' },
          proposed_text: { type: 'string' },
          edit_summary: { type: 'string' },
        },
      },
    },
    notes: { type: 'string' },
  },
}

const SYNTHESIS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['summary', 'doc_edits', 'product_deltas', 'changelog_entries'],
  properties: {
    summary: { type: 'string' },
    doc_edits: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['path', 'edits'],
        properties: {
          path: { type: 'string' },
          edits: {
            type: 'array',
            items: {
              type: 'object',
              additionalProperties: false,
              required: ['current_excerpt', 'proposed_text', 'edit_summary'],
              properties: {
                current_excerpt: { type: 'string' },
                proposed_text: { type: 'string' },
                edit_summary: { type: 'string' },
              },
            },
          },
        },
      },
    },
    product_deltas: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['issue_title', 'issue_body', 'priority', 'backlog_row'],
        properties: {
          issue_title: { type: 'string' },
          issue_body: { type: 'string' },
          priority: { type: 'string', enum: ['low', 'medium', 'high'] },
          backlog_row: { type: 'string' },
        },
      },
    },
    changelog_entries: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['you_said', 'we_did'],
        properties: {
          you_said: { type: 'string' },
          we_did: { type: 'string' },
        },
      },
    },
  },
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------
const feedback = normalizeFeedback(args)
if (!feedback.length) {
  log('No feedback supplied. Pass feedback via Workflow args (array of items or a text blob).')
  return { error: 'no_feedback', themes: [], synthesis: null }
}
const byId = {}
for (const f of feedback) byId[f.id] = f
log(`Integrating ${feedback.length} feedback item(s).`)

// 1. Cluster --------------------------------------------------------------
phase('Cluster')
const clustered = await agent(
  `You are triaging community feedback on the T-Rex Talk "Involuntary Non-Verbal (MVP)" AAC device and its documentation.

Raw feedback batch (JSON):
${JSON.stringify(feedback, null, 2)}

Cluster these into a SMALL set of coherent themes. Merge items that make the same underlying point. For each theme record the contributing feedback ids, a short title, a 1-2 sentence summary, the count of supporting items, and 1-3 short verbatim quotes. Return ONLY the structured object.`,
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
      `You are integrating ONE theme of user feedback into the T-Rex Talk project.

THEME:
${JSON.stringify(theme, null, 2)}

ORIGINATING FEEDBACK ITEMS:
${JSON.stringify(items, null, 2)}

Base documents in this repository you may consult (read the ones relevant to this theme):
${BASE_DOCS.map((d) => '  - ' + d).join('\n')}

Steps:
1. Read the relevant base doc(s).
2. Classify the theme as exactly one of: "wording" (doc text change), "product" (hardware/firmware feature or behavior), "config" (a default / config.txt change), or "out_of_scope".
3. List which base doc(s) it affects and why.
4. If it implies doc text changes, draft concrete proposed edits (path, location hint, an excerpt of current text, the proposed replacement text, a one-line summary). Keep the project's warm second-person voice and ALWAYS use the preferred term "involuntary non-verbal".
5. If it implies a product/feature change, fill product_requirement. If a config/default change, fill config_change. Otherwise set them null.

Design guardrail: the MVP is the MINIMUM useful build. Resist scope creep that would erase its difference from a full Fruit Jam — such things belong on a carrier board, not the core module. Return ONLY the structured object.`,
      { schema: ANALYSIS_SCHEMA, label: `analyze:${theme.id}`, phase: 'Analyze' },
    )
  },
  (analysis, theme) =>
    agent(
      `You are an adversarial reviewer checking a proposed feedback integration BEFORE it is applied. Default to skepticism.

PROPOSED ANALYSIS + EDITS:
${JSON.stringify(analysis, null, 2)}

Read the affected base doc(s) in the repository and stress-test each proposed edit:
- Does it CONFLICT with or contradict existing content elsewhere in the docs?
- Does it VIOLATE the "minimum viable" philosophy (adds cost / power / scope that belongs on a carrier board or a Fruit Jam)?
- Does it BREAK the terminology rule? The docs must use "involuntary non-verbal"; "selective mutism" is permitted as the single up-front reference only.
- Is the proposed wording accurate and in-voice?

Recommend "accept", "revise" (supply corrected revised_edits), or "reject" (explain in notes). Return ONLY the structured object.`,
      { schema: VERDICT_SCHEMA, label: `verify:${theme.id}`, phase: 'Verify' },
    ).then((verdict) => ({ analysis, verdict })),
)

const kept = results.filter(Boolean).filter((r) => r.verdict.recommendation !== 'reject')
const rejected = results.filter(Boolean).filter((r) => r.verdict.recommendation === 'reject')
log(`${kept.length} theme(s) kept, ${rejected.length} rejected by adversarial review.`)
if (!kept.length) {
  return { themes, results, synthesis: null, note: 'All themes rejected on review.' }
}

// 4. Synthesize ready-to-use artifacts ------------------------------------
phase('Synthesize')
const synthesis = await agent(
  `You are producing the final integration artifacts from verified feedback themes.

VERIFIED THEMES (analysis + verdict — use revised_edits wherever the verdict says "revise"):
${JSON.stringify(kept, null, 2)}

Produce three ready-to-use sets of artifacts:
1. doc_edits — consolidated, de-duplicated edits grouped by file path, ready to apply as a PR.
2. product_deltas — for every "product" or "config" theme, a ready-to-file GitHub issue (title + markdown body that includes the originating ask), a priority, and a one-line PRODUCT_BACKLOG.md row.
3. changelog_entries — warm, plain-language "you said / we did" pairs for the mailing list. Strip ALL personal or identifying information.

Return ONLY the structured object.`,
  { schema: SYNTHESIS_SCHEMA, label: 'synthesize', phase: 'Synthesize' },
)

return { themes, results, kept, rejected, synthesis }
