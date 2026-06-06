# Feedback Form — Involuntary Non-Verbal (MVP)

This is the question set for the **primary feedback form on tssfaa.com**. Build
it as a web form backed by a Google Sheet (e.g. Google Forms, or any form tool
that writes to a Sheet) so responses aggregate into one place. That Sheet is the
input to the `feedback-integrate` workflow.

## Design rules for the form

- **Anonymous by default.** No login. Contact details are the last, optional
  question only.
- **Everything optional.** Every question can be skipped. Say so at the top.
- **Low pressure, plain language.** No jargon, no "required" asterisks, no
  progress-shaming. This audience freezes under pressure — the form must not add
  any.
- **Short.** Better a few honest answers than an abandoned long form.
- Each question below is tagged with the integration category it feeds
  (`wording` / `product` / `config` / `context`) so the workflow can route it.

## Intro text (shown above the form)

> We're building this device *with* you, not just for you. There are no wrong
> answers, nothing is required, and you can stay completely anonymous. Tell us
> as much or as little as you like — even one sentence helps the people who come
> after you.

## Questions

1. **Which best describes you?** *(context — optional, single choice)*
   - I experience involuntary non-verbal moments myself
   - Family member / friend
   - Teacher / aide
   - Speech, occupational, or mental-health professional
   - Other

2. **When your words won't come, what do you most need to be able to say?**
   *(product / wording — free text)*
   Examples are welcome: *"I need a minute," "Can you write it down?", "I'm OK."*

3. **The emergency message currently says:** *"Please stand back. I cannot speak
   right now, but I am OK. Crowding me makes it worse. Thank you."* **Does this
   wording work for you? What would you change?** *(wording — free text)*

4. **What would make a device feel safe to pull out in public — and what would
   make it worse?** *(product — free text)*

5. **How would you most want to trigger it?** *(config / product — multi-choice +
   free text)*
   - A dial you turn and press (the default)
   - A touch screen
   - One big button
   - Something else: ____

6. **Is anything in the documentation wrong, confusing, or not true to your
   experience?** *(wording — free text)*

7. **What's missing? What do you wish it did?** *(product — free text)*

8. **Anything else you want us to know?** *(context — free text)*

9. **Optional — stay in touch.** *(context)*
   - [ ] Add me to the mailing list for updates
   - [ ] I'd like to join the test group
   - Email (only if you checked a box above): ____

## How responses flow

```
tssfaa.com form  ->  Google Sheet (one row per response)
                       └─ export / paste a batch  ->  Workflow: feedback-integrate
                                                        ├─ PR-ready doc edits
                                                        ├─ product deltas -> GitHub issues + PRODUCT_BACKLOG.md
                                                        └─ "you said / we did" -> mailing list (close the loop)
```
