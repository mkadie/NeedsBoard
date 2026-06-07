/**
 * apps-script.gs — Path B endpoint.
 *
 * Receives submissions from a native HTML feedback form (built by
 * build-html-form.js) and appends them to a Google Sheet. No CORS/JS needed:
 * the HTML form does a normal full-page POST and this returns a thank-you page.
 *
 * Deploy:
 *   1. https://script.google.com -> New project -> paste this file.
 *   2. Set SHEET_ID to your responses Spreadsheet's id (from its URL), or leave
 *      blank and bind the script to a Sheet (Extensions -> Apps Script).
 *   3. Deploy -> New deployment -> Web app:
 *        Execute as: Me     Who has access: Anyone
 *   4. Copy the web-app URL; put it in the form's <form action> (or pass it to
 *      build-html-form.js as the 2nd argument).
 *
 * Each row is: [Timestamp, variant, response_json]. The workflow export step
 * parses response_json into feedback items.
 */

const SHEET_ID = ''; // optional: paste responses Spreadsheet id; blank = active sheet

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss = SHEET_ID ? SpreadsheetApp.openById(SHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheets()[0];
    const params = (e && e.parameter) || {};
    if (sheet.getLastRow() === 0) sheet.appendRow(['Timestamp', 'variant', 'response_json']);
    sheet.appendRow([new Date(), params.variant || '', JSON.stringify(params)]);
    return HtmlService.createHtmlOutput(
      '<!doctype html><meta charset="utf-8"><title>Thank you</title>' +
      '<body style="font:18px system-ui;max-width:40rem;margin:3rem auto;padding:1rem">' +
      '<h1>Thank you</h1><p>Your feedback was received. You can close this page.</p></body>'
    );
  } catch (err) {
    return HtmlService.createHtmlOutput('<h1>Sorry</h1><p>Something went wrong saving your response. Please try again.</p>');
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return HtmlService.createHtmlOutput('<p>This endpoint accepts feedback form submissions via POST.</p>');
}
