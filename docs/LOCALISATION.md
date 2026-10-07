# English-first, bilingual website

- New visitors see British English. The shared language control switches all three experiences to Simplified Chinese and remembers the choice in `zhitu-language` local storage.
- `frontend/src/i18n.ts` supplies reactive text translations from `frontend/src/locales/zh.json`. Internal tab IDs and saved profile option values remain stable across language changes. Add new interface copy to the translation catalogue.
- API requests send the selected `Accept-Language`. `backend/app/localisation.py` holds the language in a request-scoped context, not a process-wide mutable setting. Error messages, public persona profiles, model output instructions and PDF/Word labels follow this context.
- English and Chinese public persona facts are separate curated files. Keep them factually consistent; do not invent grades, language-test results, research experience or admissions motivations.
- Switching languages never rewrites uploaded CVs, saved experience, prior conversations or completed AI results. Source quotations and CV body content stay in their source language to preserve factual verification. New generated explanations use the selected language.
- Verification: run `pytest` in `backend` and `pnpm build` in `frontend`. `test_localisation.py` covers default language, API validation messages, concurrent request isolation, English fact checks, international CV headers and bilingual exports.

No database migration or new front-end dependency is required for this change.
