/**
 * build-google-form.gs — Path A automation.
 *
 * Builds a Google Form for one device variant DIRECTLY from the canonical
 * questions.json in mkadie/NeedsBoard, and links it to a responses Sheet.
 *
 * Setup (first time — create a new form):
 *   1. https://script.google.com -> New project -> paste this file.
 *   2. Set VARIANT_ID below; leave FORM_ID blank.
 *   3. Run buildForm(). Authorize when prompted.
 *   4. Read the Execution log for the published URL, edit URL, and Sheet URL.
 *      Embed the form on the static site via Send -> <> (iframe).
 *
 * Refresh later (UPDATE the existing form in place — keeps its URL, embed, and
 * responses Sheet):
 *   - Paste the form's id into FORM_ID (from the edit URL:
 *     https://docs.google.com/forms/d/<FORM_ID>/edit), then run buildForm().
 *     It rewrites the title, description (incl. doc link), and questions on the
 *     SAME form, so the tssfaa.com embed updates automatically — no re-embed.
 *   - Caveat: a full question rebuild can add columns to the responses Sheet for
 *     historical responses. For a tiny tweak (e.g. just the doc link), editing
 *     the form's description by hand is simpler and leaves the Sheet untouched.
 *
 * To export a batch of responses for the feedback-integrate workflow:
 *   - paste the responses Sheet URL into RESPONSES_SHEET_URL, run exportBatch(),
 *     copy the logged JSON into the workflow's args.feedback.
 */

const QUESTIONS_URL = 'https://raw.githubusercontent.com/mkadie/NeedsBoard/main/docs/feedback/questions.json';
const VARIANT_ID = 'involuntary-nonverbal-mvp';
const FORM_ID = '';             // blank = create a new form; set to update an existing form in place
const RESPONSES_SHEET_URL = ''; // paste after buildForm() logs it, then run exportBatch()

function loadRegistry_() {
  const resp = UrlFetchApp.fetch(QUESTIONS_URL, { muteHttpExceptions: true });
  if (resp.getResponseCode() !== 200) {
    throw new Error('Could not fetch questions.json (HTTP ' + resp.getResponseCode() + ')');
  }
  return JSON.parse(resp.getContentText());
}

function resolveIds_(reg, variant) {
  const ids = variant.order.slice();
  (reg.alwaysInclude || []).forEach(function (a) { if (ids.indexOf(a) === -1) ids.push(a); });
  return ids;
}

function buildForm() {
  const reg = loadRegistry_();
  const variant = reg.variants[VARIANT_ID];
  if (!variant) {
    throw new Error('Unknown variant "' + VARIANT_ID + '". Known: ' + Object.keys(reg.variants).join(', '));
  }

  const updating = !!FORM_ID;
  let form;
  if (updating) {
    form = FormApp.openById(FORM_ID);          // update the existing form in place
    const items = form.getItems();
    for (let i = items.length - 1; i >= 0; i--) form.deleteItem(items[i]); // clear old questions
  } else {
    form = FormApp.create('T-Rex Talk — ' + variant.title + ' feedback');
  }

  form.setTitle('T-Rex Talk — ' + variant.title + ' feedback');
  let desc = reg.intro;
  if (variant.docUrl) desc += '\n\n' + (reg.docLinkLabel || 'Read about this device') + ': ' + variant.docUrl;
  desc += '\n\nAnonymous. Everything is optional.';
  form.setDescription(desc);
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false);
  form.setProgressBar(false);

  resolveIds_(reg, variant).forEach(function (qid) {
    const q = reg.questions[qid];
    if (!q) { Logger.log('skip unknown question id: ' + qid); return; }
    const opts = (variant.optionOverrides && variant.optionOverrides[qid]) || q.options || [];
    addItem_(form, q, opts);
  });

  if (!updating) {
    const ss = SpreadsheetApp.create('T-Rex Talk feedback — ' + variant.title);
    form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
    Logger.log('Responses Sheet: ' + ss.getUrl());
  } else {
    Logger.log('Updated existing form in place — responses Sheet and embed unchanged.');
  }

  Logger.log((updating ? 'Updated' : 'Created') + ' form.');
  Logger.log('Published URL : ' + form.getPublishedUrl());
  Logger.log('Edit URL      : ' + form.getEditUrl());
  if (!updating) Logger.log('Embed: open the edit URL, Send -> <> to copy the iframe.');
}

function addItem_(form, q, opts) {
  switch (q.type) {
    case 'single': {
      const it = form.addMultipleChoiceItem().setTitle(q.text).setRequired(false);
      if (opts.length) it.setChoiceValues(opts);
      if (q.help) it.setHelpText(q.help);
      break;
    }
    case 'multi': {
      const it = form.addCheckboxItem().setTitle(q.text).setRequired(false);
      if (opts.length) it.setChoiceValues(opts);
      if (q.help) it.setHelpText(q.help);
      break;
    }
    case 'contact': {
      if (opts.length) form.addCheckboxItem().setTitle(q.text).setChoiceValues(opts).setRequired(false);
      form.addTextItem().setTitle('Email (only if you ticked a box above)').setRequired(false);
      break;
    }
    default: { // 'text'
      const it = form.addParagraphTextItem().setTitle(q.text).setRequired(false);
      if (q.help) it.setHelpText(q.help);
    }
  }
}

/** Dump the responses Sheet as JSON for the feedback-integrate workflow. */
function exportBatch() {
  if (!RESPONSES_SHEET_URL) throw new Error('Set RESPONSES_SHEET_URL first (from the buildForm log).');
  const sheet = SpreadsheetApp.openByUrl(RESPONSES_SHEET_URL).getSheets()[0];
  const values = sheet.getDataRange().getValues();
  if (values.length < 2) { Logger.log('[]'); return; }
  const header = values[0];
  const items = [];
  for (let r = 1; r < values.length; r++) {
    const parts = [];
    for (let c = 0; c < header.length; c++) {
      const key = String(header[c]);
      const val = values[r][c];
      if (key.toLowerCase() === 'timestamp') continue;
      if (val === '' || val === null) continue;
      parts.push(key + ': ' + val);
    }
    if (parts.length) items.push({ id: 'fb' + r, text: parts.join('\n') });
  }
  Logger.log('variant: ' + VARIANT_ID);
  Logger.log(JSON.stringify(items, null, 2));
}
