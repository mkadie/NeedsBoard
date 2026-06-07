#!/usr/bin/env node
// build-html-form.js — Path B generator.
//
// Generate an accessible, self-styled standalone HTML feedback form for one
// variant, from the canonical docs/feedback/questions.json.
//
// Usage:
//   node survey/build-html-form.js <variant-id> [appsScriptWebAppURL]
//
// Output: survey/dist/feedback-<variant-id>.html
// The form POSTs to the Apps Script web app (survey/apps-script.gs).

const fs = require('fs')
const path = require('path')

const variantId = process.argv[2]
const endpoint = process.argv[3] || 'REPLACE_WITH_APPS_SCRIPT_WEB_APP_URL'
if (!variantId) {
  console.error('Usage: node survey/build-html-form.js <variant-id> [appsScriptWebAppURL]')
  process.exit(1)
}

const reg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'docs', 'feedback', 'questions.json'), 'utf8'))
const variant = reg.variants[variantId]
if (!variant) {
  console.error('Unknown variant "' + variantId + '". Known: ' + Object.keys(reg.variants).join(', '))
  process.exit(1)
}

const ids = variant.order.slice()
for (const a of reg.alwaysInclude || []) if (!ids.includes(a)) ids.push(a)

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const mdLite = (s) => esc(s).replace(/\*([^*]+)\*/g, '<em>$1</em>')

let body = ''
ids.forEach((qid, i) => {
  const q = reg.questions[qid]
  if (!q) return
  const opts = (variant.optionOverrides && variant.optionOverrides[qid]) || q.options || []
  const name = `q${i + 1}_${qid}`
  const help = q.help ? `<p class="help" id="${name}-help">${mdLite(q.help)}</p>` : ''
  const desc = q.help ? ` aria-describedby="${name}-help"` : ''
  const cat = `<span class="cat">(${esc(q.category)})</span>`

  if (q.type === 'single' || q.type === 'multi' || q.type === 'contact') {
    const inputType = q.type === 'single' ? 'radio' : 'checkbox'
    const choices = opts.map((o, ci) => {
      const cid = `${name}_${ci}`
      return `    <div class="choice"><input type="${inputType}" id="${cid}" name="${name}" value="${esc(o)}"><label for="${cid}">${esc(o)}</label></div>`
    }).join('\n')
    const email = q.type === 'contact'
      ? `\n    <div class="field"><label for="${name}_email">Email (only if you ticked a box above)</label><input type="email" id="${name}_email" name="${name}_email" autocomplete="email"></div>`
      : ''
    body += `  <fieldset class="q">\n    <legend>${mdLite(q.text)} ${cat}</legend>\n${help ? '    ' + help + '\n' : ''}${choices}${email}\n  </fieldset>\n`
  } else {
    body += `  <div class="q field">\n    <label for="${name}">${mdLite(q.text)} ${cat}</label>\n${help ? '    ' + help + '\n' : ''}    <textarea id="${name}" name="${name}" rows="3"${desc}></textarea>\n  </div>\n`
  }
})

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>T-Rex Talk — ${esc(variant.title)} feedback</title>
<style>
  :root{--fg:#111;--bg:#fff;--muted:#555;--line:#bbb;--focus:#0b5fff}
  body{font:18px/1.5 system-ui,"Segoe UI",Roboto,Arial,sans-serif;color:var(--fg);background:var(--bg);max-width:720px;margin:0 auto;padding:1.25rem}
  h1{font-size:1.5rem}
  .intro{background:#f3f6ff;border-left:4px solid var(--focus);padding:.75rem 1rem;border-radius:6px}
  fieldset.q,.q.field{border:1px solid var(--line);border-radius:8px;padding:1rem;margin:1rem 0}
  legend,label{font-weight:600}
  .cat{font-weight:400;color:var(--muted);font-size:.85em}
  .help{color:var(--muted);font-weight:400;margin:.4rem 0 .6rem}
  .choice{display:flex;align-items:flex-start;gap:.5rem;margin:.35rem 0}
  .choice label{font-weight:400}
  textarea,input[type=email]{width:100%;font:inherit;padding:.5rem;border:1px solid var(--line);border-radius:6px;box-sizing:border-box}
  input,textarea,button{min-height:44px}
  :focus-visible{outline:3px solid var(--focus);outline-offset:2px}
  button{font:inherit;font-weight:700;background:var(--focus);color:#fff;border:0;border-radius:8px;padding:.75rem 1.5rem;cursor:pointer}
</style>
</head>
<body>
<h1>${esc(variant.title)} — feedback</h1>
<p class="intro">${mdLite(reg.intro)}<br><strong>Anonymous. Everything is optional.</strong></p>
<form action="${esc(endpoint)}" method="POST">
  <input type="hidden" name="variant" value="${esc(variantId)}">
${body}  <button type="submit">Send feedback</button>
</form>
</body>
</html>
`

const outDir = path.join(__dirname, 'dist')
fs.mkdirSync(outDir, { recursive: true })
const outFile = path.join(outDir, `feedback-${variantId}.html`)
fs.writeFileSync(outFile, html)
console.log('wrote ' + path.relative(process.cwd(), outFile))
if (endpoint.startsWith('REPLACE')) console.log('NOTE: set the form action — pass the Apps Script web-app URL as the 2nd argument.')
