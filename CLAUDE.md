# CLAUDE.md — plonemeeting.portal.core

The main application package behind **Délibérations.be / iA.Délib citizen
portal**. It exposes municipal decisions and publications coming from
`Products.PloneMeeting` (iA.Délib backend) to the public, through a
Plone 6.1 site styled by `plonetheme.deliberations`.

This is its **own git repository**, checked out by `mr.developer` into
`src/plonemeeting.portal.core/` of the `buildout.pm.portal` shell. Edits
here go upstream — they do **not** belong to the buildout repo.

- Upstream: https://github.com/IMIO/plonemeeting.portal.core
- Issues: https://github.com/IMIO/plonemeeting.portal.core/issues
- End-user docs: https://docs.imio.be/iadelib/deliberations.be/
- License: GPLv2

## Stack

- **Plone**: 6.1.x (classic, not Volto)
- **Python**: 3.11 / 3.12 (`python_requires=">=3.11"`)
- **Content types**: Dexterity
- **Listings**: `eea.facetednavigation`
- **Frontend bundle**: webpack + pnpm (see `browser/resources/`)
- Distributed on PyPI as `plonemeeting.portal.core`; current dev version
  in `setup.py` (`2.4.2.dev0` at time of writing — single source of
  truth, do not duplicate elsewhere).

## Layout

```
src/plonemeeting/portal/core/        ← all importable code
├── behaviors/        Dexterity behaviors (autopublish, supersede, …)
├── browser/          views, viewlets, page templates, JS/CSS bundle
│   ├── configure.zcml
│   ├── overrides/    z3c.jbot template overrides
│   ├── resources/    pnpm/webpack source — edit here, NOT in static/
│   ├── static/       compiled bundle — generated, never hand-edit
│   └── templates/    .pt page templates
├── content/          Dexterity content types: Institution, Meeting,
│                     Item, Publication, file
├── events/           zope event subscribers
├── faceted/          eea.facetednavigation criteria + XML configs for
│                     decisions / publications listings
├── filters/          custom faceted filters
├── migrations/       imio.migrator upgrade steps (migrate_to_NNNN.py)
├── profiles/
│   ├── default/      GS install profile (types, workflows, registry, …)
│   ├── demo/         optional demo content
│   └── uninstall/    GS uninstall profile
├── rest/             plone.restapi services + serializers
├── tests/            zope.testrunner test suite
├── viewlets/         page viewlets (logo, generation links, …)
├── widgets/          z3c.form widgets (color picker, image)
├── locales/          i18n (FR is the only translated locale)
├── adapters.py       adapters wired in adapters.zcml
├── cache.py          plone.memoize helpers
├── config.py         constants — folder ids, headers, mappings, mimetypes
├── interfaces.py     marker / browser layer interfaces
├── patches.py        monkey patches (auto-imported from __init__)
├── setuphandlers.py  GS post_install / uninstall / demo handlers
├── sync_utils.py     ⭐ sync logic from PloneMeeting REST API
├── testing.py        plone.app.testing layers + fixtures
├── utils.py          shared helpers (api urls, group ids, translators…)
└── vocabularies.py   all named vocabularies (registered in configure.zcml)
```

The four content types are: **Institution** (a municipality/CPAS site),
**Meeting**, **Item** (a decision inside a meeting), and **Publication**
(an administrative publication independent of meetings). Each has its
own DC workflow under `profiles/default/workflows/<type>_workflow/`.

## Common commands

You normally develop this package from the **buildout shell** at the
repo root (`buildout.pm.portal`), not from inside this directory:

```bash
# from /home/aduchene/Projects/iMio/pmportal24_dev
bin/instance fg                        # run portal at http://localhost:8080
bin/test                               # runs THIS package's tests by default
bin/test -t test_publication           # filter by test name
bin/test -m plonemeeting.portal.core.tests.test_publication

# upgrade steps
bin/instance run scripts/run_portal_upgrades.py
```

The `Makefile` here is for **standalone** development of the package
(creates its own venv, runs `test-6.1.cfg`). Most of the time you do
not need it — work through the buildout shell instead.

```bash
make buildout         # standalone bootstrap (rare)
make test             # bin/test in standalone venv
make resources        # pnpm run build — compile browser/resources → static/
make resources-watch  # webpack dev server with live reload
```

### Frontend bundle

Everything in `browser/static/` is **generated**. Source lives in
`browser/resources/` and is built with pnpm + webpack
(`webpack.config.js`). After editing resources:

1. `make resources` (or `pnpm run build` from `browser/resources/`)
2. The build bumps `last_compilation` in `profiles/default/registry.xml`
3. Re-import the registry profile in Plone (or upgrade step) to refresh
   cache busters.

For live editing, use `make resources-watch` and access the site via
http://localhost:3000 (the webpack dev server proxies to Plone — going
to :8080 directly will not show your changes).

## Code style

Two tools, run on demand (no pre-commit, no tox, no CI hooks). Install them
however you like — `pipx install ruff zpretty`, `uvx`, or your editor.

- **Ruff** for Python — config in `pyproject.toml` `[tool.ruff]`.
  `line-length = 120` (kept from the old flake8 setting); rules `F,E,W,UP,I`;
  `E501`/`E203` ignored; isort: `from-first`, `no-sections`, one import per
  line, two blank lines after imports.
- **zpretty** for templates / ZCML / XML (`.pt`, `.zcml`, `.xml`).
- `make lint` → `ruff check .` (report-only). `make format` → `ruff format` +
  `ruff check --fix` + `zpretty`. The repo is **not** reformatted yet, so
  `make format` is the deliberate one-time reformat (large diff); after zpretty
  runs, don't assert exact attribute order in tests.
- File header: `# -*- coding: utf-8 -*-` is conventional across the
  package — keep it on new modules for consistency.
- Translations: import `_` from `plonemeeting.portal.core` (and
  `plone_` for the `plone` domain). Wrap user-visible strings.

## Adding things

- **A new content type**: Dexterity schema in `content/<type>.py` →
  factory in `content/configure.zcml` → FTI under
  `profiles/default/types/<Type>.xml` → register in
  `profiles/default/types.xml` → workflow under
  `profiles/default/workflows/` if needed → tests under
  `tests/test_ct_<type>.py`.
- **A new view**: template under `browser/templates/`, class under
  `browser/`, `browser:page` directive in `browser/configure.zcml`.
- **A new vocabulary**: factory class in `vocabularies.py`, register as
  a `<utility>` in the top-level `configure.zcml` with the
  `plonemeeting.portal.vocabularies.<name>` naming convention.
- **A new upgrade step**: create `migrations/migrate_to_NNNN.py`
  subclassing `PlonemeetingMigrator` (it already exposes
  `_re_apply_faceted_configs`, `_update_role_mappings`, the QI
  installer, and current language). Wire it through
  `migrations/configure.zcml` and `profiles/default/metadata.xml`.
- **A new dependency**: add to `install_requires` in `setup.py`, pin in
  the buildout's `versions.cfg`, add to `eggs +=` in the buildout's
  `base.cfg`, and (if a sibling `src/*` package) declare in
  `sources.cfg` + `auto-checkout`.

## Testing

- Test layer in `testing.py` (uses `plone.app.testing`); base test case
  in `tests/portal_test_case.py`.
- `mockito` is a test dep (see `extras_require["test"]`).
- Per-CT tests follow `test_ct_<type>.py`; behavior tests follow
  `test_<feature>.py`.
- `bin/test` from the buildout root runs this package's suite by
  default — that is configured in the buildout's `dev.cfg [test]`
  section, not here.

## Dependencies worth knowing

These are pulled in as `install_requires` and shape the behavior of the
package — when something feels magical, it is usually one of them:

- `Products.PloneMeeting` — **upstream backend**, queried via REST. Sync
  logic is centralized in `sync_utils.py` (~14 KB) and
  `browser/sync.py` (~19 KB).
- `collective.timestamp` — eIDAS timestamping of published items.
- `collective.autopublishing` — scheduled publication workflow
  transitions (used by `behaviors/autopublish.py`).
- `collective.documentgenerator>=4.0` — POD template rendering;
  default templates declared in `config.DEFAULT_DOCUMENTGENERATOR_TEMPLATES`.
- `collective.excelexport>=2.0` — XLSX exports of listings.
- `collective.exportimport` — content import/export.
- `collective.z3cform.datagridfield>=3.0.2` — used by `Institution`
  (category mappings) and other configuration grids.
- `eea.facetednavigation>=16.2` — listings; configs in `faceted/config/`.
- `imio.helpers`, `imio.migrator`, `imio.pyutils` — IMIO helpers
  (`imio.migrator.Migrator` is the base of upgrade steps).
- `imio.omnia.core`, `imio.omnia.assistant`, `imio.omnia.tinymce` —
  AI assistant (TinyMCE integration). Assistant is enabled on
  `Publication` and `Item` (since 2.4.1).
- `plone.formwidget.hcaptcha` — captcha on the public contact form.
- `plone.restapi` — used for both consuming PloneMeeting and exposing
  endpoints under `rest/`.
- `z3c.jbot` — template overrides under `browser/overrides/`.

## Pitfalls

- **Do not edit `browser/static/`** — regenerated by webpack. Source is
  in `browser/resources/`. `DEVELOP.rst` is explicit about this.
- **Faceted configs are XML files** under `faceted/config/`. Importing
  them is done by `PlonemeetingMigrator._re_apply_faceted_configs` —
  use that from upgrade steps rather than reimplementing.
- **`patches.py` is auto-imported** from `__init__.py` (`assert
  patches`). Anything you add there runs at import time of the package
  — keep it minimal and side-effect-aware.
- **Folder ids are french-facing**: `decisions`, `publications`,
  `config`, `faceted_decisions`, `faceted_publications` — they appear
  in URLs (see `config.py`). Don't rename without a migration.
- **i18n is FR-only.** When adding strings, update
  `locales/plonemeeting.portal.core.pot` via
  `bin/update_locale` (entry point declared in `setup.py`) and sync
  the `fr/LC_MESSAGES/*.po`.
- **`Institution` validates external HTTP at form save time**
  (`content/institution.py` imports `requests` and reaches the
  PloneMeeting backend for vocab calls — see `get_api_url_for_*`
  helpers). Keep tests offline by mocking those.
- **The "Item" CT means "decision item" inside a meeting**, not a
  generic listing item. Don't confuse it with Publication, which is
  standalone.
- **`DEMO_INSTITUTION_IDS = ["belle-ville"]`** (`config.py`) is
  hard-coded — the demo profile creates this institution, several
  tests rely on its presence.
