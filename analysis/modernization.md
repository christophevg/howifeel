# How I Feel — Modernization Plan

Migration plan produced by the legacy-modernization engagement,
2026-09-02. Consumes `functional.md` (behaviour contract), `issues.md`
(dispositions), `testing.md` (the referee). Target decisions are the
owner's (Gate 1, recorded in §3); ecosystem-reality deviations were
flagged and **confirmed by the owner at Gate 2** (decision record in
`issues.md` §6). Revised after critical-client review (milestone
sequencing, suite-blackout prevention, contract-completion).

## 1. Ground rules

- **Behaviour preservation.** The migrated app is externally
  indistinguishable from the legacy app, except for the sanctioned
  exceptions in `issues.md` (buckets A/A\*) — each with its gate test.
- **Test-driven invariance.** The characterization suite
  (`testing.md`) is the referee: green at every step or the step does
  not land. Expectation changes are separate commits.
- **No feature work.** TODO.md wishes, new endpoints, new pages: out of
  scope (§14).
- **Presentation change limits.** JS/CSS dependencies may be upgraded
  as long as the user experience is fundamentally unchanged (owner
  decision, Gate 1); locally owned presentation code may be refactored
  while UX stays identical; no new frameworks or bundlers.
- **Data untouched.** The production MongoDB is off-limits: no writes,
  no migrations, no deletes. The only data-layer addition is a unique
  index on `users.user` (BUG-1) — created at deploy time (M6) **after a
  mandatory duplicate scan** (GAP-9; duplicates abort deployment and go
  to the owner for per-case resolution). Document contents are never
  modified. Local `howifeel` data and the `howifeel_test` scratch
  database are the only write targets during development.
- **Spec hygiene.** Implementers verify exact versions/flags against
  current package docs before pinning (`[verify]` markers below).

## 2. Current stack ("what we migrate away from")

| Aspect | Today | Source |
|---|---|---|
| Language/runtime | Python (no version pinned in repo; legacy env was 3.8-era) | requirements, git history |
| Web framework | Flask 3.0.3 | requirements.txt |
| JSON API | Flask-RESTful 0.3.10 (7 endpoints) | api.py, requirements.txt |
| Auth | Flask-Login 0.6.3 (session cookie) | auth.py, requirements.txt |
| Datastore | MongoDB via pymongo 4.8.0, sync, module-level client | data.py |
| Concurrency | eventlet 0.36.1 `monkey_patch()` at app import | `__init__.py` |
| Server | gunicorn 22.0.0, `-k eventlet -w 1` | Makefile.local; **owner-confirmed production command:** `gunicorn -k eventlet -b 127.0.0.1:5009 --chdir /app/apps/howifeel howifeel:app` (in a container; render.com no longer in the path) |
| Config | env vars `APP_SECRET_KEY` (prod only), `MONGODB_URI` (prod + local), `LOG_LEVEL`; python-dotenv 1.0.1 (.env, .env.local) | setup.py, `__init__.py` |
| Frontend | Jinja templates + jQuery 3.6.0 + Bootstrap 5.1.3 (CDN, SRI) + vendored notify.js | pages/, static/ |
| Packaging | requirements.base.txt (unpinned) + requirements.txt (freeze); Makefile.local targets; **no pyproject** | repo |
| Tests | none (characterization suite is precursor M0) | issues.md P |

## 3. Target stack (owner decisions, Gate 1; deviations confirmed Gate 2)

| Aspect | Target | Rationale / notes |
|---|---|---|
| Language | Python **3.13** | Required floor of Quart 0.23.1 (research-verified; **confirmed Gate 2** #11); security support to 2029-10 |
| Framework | **Quart 0.23.1** (owner directive) | Flask-shaped async; migration path documented by Quart itself |
| Concurrency | **asyncio** (owner directive); eventlet deleted | eventlet dead-ended (gunicorn removed worker class 26.0; upstream support ends 2027-04) |
| Datastore driver | **PyMongo `AsyncMongoClient`** (4.17+), *not* Motor | Deviation from the "Migrate to Motor" directive, **confirmed (Gate 2 #9)**: Motor is deprecated (2025-05), EoL 2026-05, critical-fix-only; MongoDB's official replacement, identical call names (`find_one`, `update_one`, `$push/$pull`, `upsert=True`…) |
| Auth | **quart-auth 0.11.0** (Quart author, maintained) | Flask-Login is Flask-only; its `flask_patch` path does not support an async user loader — **confirmed (Gate 2 #10)**. Consequence: **all users are logged out once at cutover** (auth cookie changes) |
| Server | **uvicorn** (owner directive): `uvicorn --host 127.0.0.1 --port 5009 --app-dir /app/apps/howifeel howifeel:app` | Quart documents uvicorn as supported for plain HTTP; `--app-dir` replaces `--chdir`; 1 worker (event-loop concurrency), `$WEB_CONCURRENCY` overridable |
| Project management | **uv**: `pyproject.toml` + `uv.lock`, standard Makefile targets | Owner directive; house standard |
| Frontend | jQuery → latest 3.x, Bootstrap → latest 5.x, notify.js stays vendored | "Upgrade as long as UX fundamentally unchanged" (Gate 1); SRI hashes re-pinned |
| Interface protocol | unchanged: all URLs, API shapes, session-cookie semantics | `functional.md` contract |
| Data layer | MongoDB unchanged; schema unchanged; unique index on `users.user` added (BUG-1, GAP-9 pre-scan) | §1 data rule |

Quart sessions use Flask's exact session machinery (verified at source:
same cookie name `session`, same itsdangerous signing) — the existing
*session* cookie semantics carry over; the *auth* cookie does not
(quart-auth issues its own signed cookie; one-time logout accepted,
Gate 2 #10).

## 4. Project skeleton (M1)

- `pyproject.toml` (uv-managed). **Runtime deps:** `quart`, `quart-auth`,
  `pymongo` (async extra per `[verify]` at implementation), `bcrypt`,
  `python-dotenv`, **and `uvicorn`** (it is the production server — it
  must not sit in dev deps; critical-review finding #11). **Dev deps:**
  `pytest`, `requests`. `uv.lock` committed. `requires-python = ">=3.13"`.
- Makefile (project-owned, standard targets): `run` (uvicorn, local),
  `test`, `lint`, `check`, `help`; the M0-era `Makefile.local::test`
  target moves here; legacy `Makefile.local` serve/requirements targets
  retire.
- Entrypoints unchanged: module `howifeel`, app object `app`.
- **M1 scope (re-scoped per critical-review finding #1): skeleton
  only.** No legacy-code edits: the legacy app continues to boot under
  gunicorn+eventlet untouched. Deliverables: pyproject + lock +
  Makefile + `tests/requirements-legacy.txt` (pinned legacy env copy) +
  a Quart "hello" proof-of-boot (separate scratch module, not the
  howifeel app).
- **M1 exit:** M0 suite green via **legacy** SUT (G-BOOT still held —
  it moves to M2); uv toolchain functional (uv lock/sync run clean);
  Quart hello-boot works; pyproject's dep set installs on Python 3.13.
- The M1 deletion list of the previous revision is **moved to M2/M6**:
  the root `requirements.txt`/`requirements.base.txt` are superseded
  but **kept until M6** (they define the legacy SUT environment for
  M1–M5; `tests/requirements-legacy.txt` mirrors them). Deleting them
  earlier would strand the referee suite (critical-review finding #14).

## 5. Migration strategy

Ordering: **suite first (M0)**, then data/backend (M2–M4) so behavioural
parity is proven server-side, then presentation (M5) so visual deltas
never confound behavioural tests. Every milestone exits suite-green
(held gates stay held). Test cases never change; only the SUT command
swaps — **once, at the end of M4**, when all routes are ported
(critical-review finding #2).

**Hybrid-era rule:** during M2–M3 the repo temporarily contains both
stacks: the legacy app (untouched, served by gunicorn — the suite's
SUT) and the growing Quart app (not yet the SUT). The suite stays green
against the legacy SUT throughout; target-side code is proven by its
own gates at M4's cutover of the SUT command.

Porting rules (async conversion):

- Every Flask import → Quart; `request.form`/`get_json` → awaited.
- `render_template` → awaited; context processor supplies
  `current_user` to templates (quart-auth pattern).
- Sync DB calls → awaited AsyncMongoClient calls; client created lazily
  per process (never at import).
- Flask-RESTful resources → plain async views: same URL rules, same
  methods; **JSON error bodies reproduced** (see risk R-2).
- `User.to_json()` called explicitly where a `User` is returned; the
  RESTFUL_JSON ObjectEncoder machinery is deleted with Flask-RESTful.
- Everything not listed as changing stays byte-identical where
  observable (templates' contract strings, API shapes, page copy).

## 6. Per-module porting plan & sanctioned-fix table

### `howifeel/__init__.py`
Drop: `eventlet` import + `monkey_patch()` (M2 — with the module
becoming the Quart app; the legacy copy stays untouched for the suite
until M4's SUT swap), Flask-RESTful `Api`, `ObjectEncoder`. Add: Quart
app, quart-auth, fail-fast config (G-BOOT). `SECRET_KEY` semantics
carry over (same config name, same signing).

### `setup.py`
Rename → `logging.py` in the new tree (module named `setup.py` confuses
packaging — deletion/rename list §11). Fix GAP-4 (LOG_LEVEL validation).

### `data.py`
AsyncMongoClient; URI parsing via `urllib.parse` (GAP-1);
`serverSelectionTimeoutMS=5000` (GAP-2); lazy per-process client.
**dnspython preserved** (RUN-4, `[verify]` whether prod URI is srv).

### `user.py`
Methods become async (`find`, `validates`, `change_password`, `update`,
`follow`, `unfollow`, …) — same semantics. Fixes: explicit
old-password check (BUG-4, code-review tier), `None`-password guard
(BUG-11), third-party serialization split (SEC-2: `to_third_party_json()`
= `{user, mood, gravatar}`), identity validation (SEC-3/GAP-10),
email-`None` coercion + gravatar guard (BUG-14), unique-index reliance
for BUG-1.

### `invitations.py`
Async; `revoke` gains `from` ownership filter (SEC-5); signup consumes
atomically via `find_one_and_delete` **on the validated signup path**
(after validation passes, before account creation — GAP-6; consuming
before validation would break T-P11).

### `api.py`
Flask-RESTful → async views, same paths. Auth decorator via quart-auth's
`login_required`. Fixes: shape validation → 400 JSON `{"message": …}`
with the approved per-endpoint messages (BUG-6), mood whitelist (BUG-2/
G-MOOD), follower-link uniqueness + server-side generation **and the
new POST-response contract** (SEC-4/G-LINK — API and client half land
together in M4), following shape (SEC-2), `Unknown user.` on
nonexistent follow target (GAP-5).

### `auth.py`
quart-auth equivalent of the login manager; `before_request` loads user
data async; template `current_user` via context processor.

### `ui.py`
Async views; same routes/statuses/copy. Fixes: 404 on unknown link
(BUG-9), `next` validated before side effects (BUG-10), `/me` dispatch
400 (BUG-5), missing-field page POSTs → validation feedback (BUG-16),
email-`None` coercion (BUG-14), about-route catches only
`TemplateNotFound` (BUG-15 — sanctioned 404→500 delta for other faults,
G-ABOUT), signup duplicate/empty rejection (BUG-1/13), dead `next`
inputs removed (BUG-7), `logger.warning` (BUG-12).

### `pages/` (templates)
Byte-identical where observable, except: dead `next` inputs removed;
manifest served as static artifact with manifest media type (FE-1);
icon set added (approved, Gate 2 #5); JS templates refactored to
`textContent`/`data-*` (SEC-3 output half, M5).

### `static/` (JS/CSS)
`mood.js`: `Object.keys(moods).length` (BUG-8), null-mood guard (BUG-2
client half, `No mood set.`); `ajax.js`: guarded parse + GET error
handlers (SEC-6); `followers.js`: use server-generated link from the
POST response (SEC-4 client half, M4); CDN bumps with re-pinned SRI
(M5). `notify.js` stays vendored.

### Sanctioned-fix table (A/A\* only — the migration's allowed deltas)

| Fix | Where | Milestone | Gate | Approved user-visible string |
|---|---|---|---|---|
| Fail-fast on unset `APP_SECRET_KEY` | boot | M2 | G-BOOT | *(none — boot error, dev-facing)* |
| Clear config errors for URI / `LOG_LEVEL` | boot | M2 | G-BOOT | *(none — startup errors)* |
| Bounded DB-failure error path | data.py | M2 | G-DBFAIL | *(none — error path)* |
| Duplicate-username signup rejection | signup | M3 | G-AUTH | `Invalid username and/or passwords do not match.` (existing, reuse) |
| Empty-password rejection | signup | M3 | G-AUTH | same existing string |
| Passwordless-doc clean failure | login | M3 | G-AUTH | *(none — behaves as wrong password)* |
| Wrong-shaped API bodies → 400 JSON | api.py | M3 | G-API | `Invalid mood.` / `Invalid follower information` / `Missing invited.` / `Unknown user.` (approved, Gate 2 #1/#12) |
| `/me` bad scope → 400 | ui.py | M3 | G-ME | *(none — direct API clients only)* |
| Missing page-POST password field → feedback | ui.py | M3 | G-ME | existing strings (BUG-16) |
| `email: None` coercion (unbrick) | ui.py/user.py | M3 | G-ME | *(none — crash removal)* |
| About-route error narrowing (bare except → TemplateNotFound only) | ui.py | M3 | G-ABOUT | *(none — status change only; 404→500 for non-template faults; expectation-change commit)* |
| Explicit old-password check (assert removal) | user.py | M3 | G-PW (code-review tier) | *(none — unreachable via UI)* |
| Ownership-filtered invitation revoke | invitations | M3 | G-INV | *(none)* |
| Atomic invitation consume (validated path) | signup | M3 | G-INV | *(none; races resolved)* |
| Mood whitelist | api.py | M4 | G-MOOD | `Invalid mood.` (approved, Gate 2 #1) |
| Client null-mood neutral state | mood.js | M4 | G-MOOD (browser tier) | `No mood set.` (approved, Gate 2 #12) |
| Unknown link → 404 | ui.py | M4 | G-VIEW | *(none — same page body)* |
| `next` validated first; dead inputs removed | ui.py/templates | M4 | G-FLOW | *(none)* |
| Reduced followed-user shape | api.py | M4 | G-FOLLOWING | *(none — payload, not copy)* |
| `Unknown user.` on following a nonexistent user | api.py | M4 | G-FOLLOWING | `Unknown user.` (approved, Gate 2 #1) |
| Link uniqueness (global) + server-side generation; POST returns created object; client half | api.py/JS | M4 | G-LINK | `Invalid follower information` (existing, reuse) |
| Identity charset/length validation (GAP-10 rules) | signup/api | M4 | G-XSS | existing strings (per field) |
| Manifest media type + icon set + body update | ui.py/static | M5 | G-MANIFEST | *(none — metadata)* |
| Cookie `Secure` + `SameSite=Lax` (env-configurable; prod default on) | config | M5 | G-COOKIE | *(none)* (flags approved, GET logout kept — Gate 2 #6) |
| Client error-handler hardening | ajax.js | M5 | G-AJAX (browser tier) | `Whoops, someting went wrong:\nUnknown error` (approved, Gate 2 #2; typo kept, #3) |
| `moods.length` → `Object.keys(moods).length` | mood.js | M5 | G-MOOD (browser tier) | *(none — layout only)* |
| `logger.warn` → `logger.warning` | ui.py | M3 | *(none — log-side only)* | *(none — not user-visible; suite-wide parity)* |
| Encoder fallback import fix | __init__.py | M3 | G-API | *(none — latent path; exercised by G-API's 400-JSON rows)* |

No A/A\* item lacks a string cell or a gate. Non-A items (C/B) appear in
§10 and are not migrated deltas.

## 7. Presentation workstream (M5)

| Library | From | Target | Notes |
|---|---|---|---|
| Bootstrap | 5.1.3 (CDN, SRI) | latest 5.x (`[verify]` exact at implementation) | visual parity check; re-pin SRI |
| jQuery | 3.6.0 (CDN, SRI) | latest 3.x | re-pin SRI |
| notify.js | vendored 2015 | stays | no maintained drop-in; isolated usage |

Local refactor scope: template-literal HTML → `textContent`/`data-*`
(SEC-3 output half); ajax error guards (SEC-6); index-page markup
cleanup (`fs-7`, stray closers — cosmetic table). Constraints: no new
frameworks, no bundler, CDN-with-SRI model kept. Verification: manual
browser sign-off tier (`testing.md` §4) — checklist per page: mood
cards render + switch, following cards render, follower and invitation
tables render, notifications fire (success + error), pull-to-refresh,
unknown-link page, 404 page. **FE-1 icons (approved, Gate 2 #5):** one
source icon rendered at 8 declared sizes, placed under the static tree,
manifest paths updated.

## 8. Runtime & deployment

| Aspect | Today (owner-confirmed) | Target |
|---|---|---|
| Server | `gunicorn -k eventlet -w 1 -b 127.0.0.1:5009 --chdir /app/apps/howifeel howifeel:app` (container) | `uvicorn --host 127.0.0.1 --port 5009 --app-dir /app/apps/howifeel howifeel:app` (workers: 1 default, `$WEB_CONCURRENCY` overridable) |
| Python | unpinned | 3.13 (pinned in pyproject + container image `[verify]` image rebuild flow) |
| Env vars | `APP_SECRET_KEY` (prod), `MONGODB_URI` (prod+local), `LOG_LEVEL` | unchanged names/semantics; dev now also requires `APP_SECRET_KEY` (any value); **new:** `SESSION_COOKIE_SECURE` (prod default true; test harness sets false) |
| Datastore | production MongoDB (untouched) + local | same; unique index on `users.user` created at deploy time **after GAP-9 duplicate scan** |

**Deployment-fact carryover table** (silent drops break deployments —
every row has a decision):

| Fact | Today | Decision |
|---|---|---|
| eventlet worker class | `-k eventlet` | **drop** — eventlet deleted (owner-directed asyncio) |
| `--chdir /app/apps/howifeel` | container layout | **preserve** as `--app-dir /app/apps/howifeel` |
| bind 127.0.0.1:5009 | container port contract | **preserve** exactly |
| single worker | `-w 1` | **preserve** (1 uvicorn worker; scale via `$WEB_CONCURRENCY` if ever needed) |
| `dnspython` dependency | present in freeze only | **preserve** in target deps (srv-URI support) `[verify]` prod URI scheme |
| `python-dotenv` + `.env`/`.env.local` loading | present (3 `load_dotenv` calls today) | **preserve** via `quart[dotenv]`; consolidate to one load point |
| `MONGODB_URI` fallback `mongodb://localhost:27017/howifeel` | works locally | **preserve** (owner: local instance holds howifeel data) |
| `APP_SECRET_KEY` unset in dev | boots with `"local"` today | **change** — dev must set one (fail-fast); value itself is operator's choice |
| `LOG_LEVEL` | env-selectable | **preserve** + validation (GAP-4) |
| MongoDB index state | none created by app | **change**: unique index on `users.user` at deploy time — **only after the GAP-9 duplicate scan passes; duplicates abort deploy for owner resolution** |
| uvicorn | absent | **runtime dependency** (container entrypoint — critical-review fix #11) |

## 9. Behaviour-parity checklist

Same source rows as the test matrix (`testing.md` §5 — derived from
`functional.md` §7). Annotation: ✅ automated · 🔒 sanctioned change
(gate) · 👁 manual (browser tier).

| Row | Test | Status |
|---|---|---|
| Landing page (anon/auth) | T-P1/P2 | ✅ |
| Login/out incl. next | T-P3–P6, T-P24–P26 | ✅ (T-E7 🔒 G-FLOW, T-P28 🔒 G-ME) |
| Signup incl. invitation lifecycle | T-P7–P11, T-A10 | ✅ (T-E1/E2 🔒 G-AUTH, T-E9 era-skip 🔒 G-INV) |
| Settings: profile/password/invitations | T-P12–P15 | ✅ (T-E5 🔒 G-ME, T-E17 🔒 G-ME; password-guard fix verified at code tier) |
| Mood mgmt + API | T-P16, T-A1–A3 | ✅ (T-A3 🔒 G-MOOD) |
| Followers + links | T-P17, T-A4–A7, T-E10 | 🔒 G-LINK ✅ rest |
| Following | T-P18, T-A11–A13 | 🔒 G-FOLLOWING ✅ |
| Public mood view | T-P19/P20 | ✅ (T-P20 🔒 G-VIEW) |
| About/404/unknown pages | T-P21–P23, T-Q1 | ✅ (T-E18 🔒 G-ABOUT) |
| Manifest + icons + static | T-S1–S6 | 🔒 G-MANIFEST ✅ |
| API auth (401s) | T-A14/A15 | ✅ |
| Malformed-input handling | T-A16/A17, T-E3/E5 | 🔒 G-API/G-ME ✅ |
| Boot config behaviour | T-E12–E14 | 🔒 G-BOOT (M2) |
| DB-failure behaviour | T-E15 | 🔒 G-DBFAIL (M2) |
| Cookie attributes | (gate) | 🔒 G-COOKIE |
| XSS rejection (server) | T-E11 | 🔒 G-XSS |
| XSS inertness (DOM), layout fix, client error handling, client copy strings (T-Q4/T-Q5), PWA install | — | 👁 browser tier (M5 sign-off) |

## 10. Preserved warts (deliberately unchanged)

- Q-7 "What's new?" copy says the new mood is "Ok" (value is `nok`) — C.
- Q-8 email edge states (cleared email → MD5-of-empty id) — C.
- Q-14 `POST /api/me/following/<x>` ignores the path segment — C.
- Q-12 "someting" typo — C (**confirmed at Gate 2 #3**: kept verbatim,
  including in the new fallback string).
- Q-17 `x` vs `✕` glyphs — C.
- GAP-7 unbounded growth; GAP-8 bcrypt 72-byte limit — C (documented).
- GAP-3 following-bypasses-revocation — C during migration
  (**confirmed at Gate 2 #8**; post-migration feature work if desired).
- GET-only logout — C (**confirmed at Gate 2 #6**, tied to SEC-7).
- Rate limiting absent — C (**confirmed at Gate 2 #7**; revisit
  post-migration if wanted).

## 11. Deletions & renames (exact list, approval required)

Per milestone, each verified by a grep-empty criterion before exit:

- **M0:** none (pure addition of `tests/`).
- **M2:** delete `eventlet` import + `monkey_patch()` call **from the
  new Quart `__init__.py`** (the legacy tree stays untouched and
  runnable until M4's SUT swap); delete module-level `MongoClient` in
  the new `data.py` (replaced by lazy async client); rename `setup.py`
  → `logging.py` in the new tree.
- **M3:** delete Flask-RESTful `Api`/resources in the new `api.py` +
  `ObjectEncoder`; delete `assert` guard (BUG-4).
- **M4:** delete dead hidden `next` inputs in `login.html`/`signup.html`;
  **legacy stack becomes dead code** — delete the legacy entrypoint
  path (Flask app construction, Flask-Login, sync pymongo usage).
- **M6:** delete root `requirements.txt` + `requirements.base.txt`
  (superseded since M1 by pyproject + lock; kept until now for the
  legacy SUT — critical-review fix #14); retire `Makefile.local`
  legacy targets.
- **M5:** delete `window.location.reload(true)` deprecated call.
- Nothing else is renamed or removed; templates otherwise byte-stable.

## 12. Risks & mitigations

| # | Risk | Mitigation |
|---|---|---|
| R-1 | Async conversion drift: missed `await`s silently change behaviour | `RuntimeWarning: coroutine was never awaited` treated as failure; suite green; grep for un-awaited calls at each milestone exit |
| R-2 | Error-body contract drift: Flask-RESTful emits `{"message": …}` JSON for aborts; plain Quart aborts emit HTML — the client JS parses `.message` | Dedicated parity rows (T-A6/T-A14/T-A16); explicit JSON error handler producing `{"message": …}` for all API aborts; M0 byte-baseline of all error bodies |
| R-3 | Auth migration: Flask-Login → quart-auth changes the auth cookie → one-time logout for all users | Owner-approved consequence (Gate 2 #10); cutover note; session-cookie machinery itself is Flask-identical (verified) |
| R-4 | Flask-Login's `current_user` used in 6 templates | context-processor injection tested by T-P1/P12 (header/menu render) |
| R-5 | Motor→AsyncMongoClient API differences beyond names | API-name parity verified in research; implementer re-verifies cursor/`to_list` shapes per call site |
| R-6 | uvicorn/Quart serving differences (headers, chunking) | T-S4 byte-hash pins on stable assets; status/header assertions throughout |
| R-7 | Production deploy breakage via dropped environmental facts | §8 carryover table — every row decided |
| R-8 | Data-layer change touching production | Only additive index; **GAP-9 duplicate-scan aborts deploy on dirty data**; everything else local-only (isolation guard) |
| R-9 | Quart version moves (0.23.1 current) | versions pinned in lockfile; `[verify]` at implementation |
| R-10 | Suite drift during porting | invariance rule + separate expectation commits (`testing.md` §7) |
| R-11 | `SESSION_COOKIE_SECURE=true` kills the plain-HTTP suite at M5 | env knob (prod default true, harness false); G-COOKIE asserts the production default (critical-review fix #10) |
| R-12 | Hybrid-era confusion (two stacks in-tree, M2–M4) | explicit rule in §5: legacy SUT stays the referee until M4; target code is not the SUT until all routes are ported |

## 13. Milestones

| M | Content | Exit criteria |
|---|---|---|
| **M0** | Characterization suite against legacy app | `testing.md` §8 all 5 acceptance items; byte baselines captured; baseline recorded |
| **M1** | uv skeleton only: pyproject + lock + Makefile + `tests/requirements-legacy.txt`; Quart hello-boot in a scratch module | M0 suite green via **legacy** SUT (all gates held/skipped as designed); uv lock/sync clean on 3.13; scratch Quart module serves; no legacy file modified |
| **M2** | New Quart app shell + async data layer: AsyncMongoClient, URI parsing (GAP-1), timeout (GAP-2), boot fail-fast (SEC-1, GAP-4); `user.py` async; eventlet/monkey-patch dropped **in the new app** | G-BOOT + G-DBFAIL un-held and green (target app); full suite still green via **legacy** SUT; new app boots under uvicorn with data layer working |
| **M3** | JSON API port (Flask-RESTful → views), auth backend, signup/invitation fixes, about-route narrowing, `/me` fixes | G-AUTH, G-API, G-ME, G-ABOUT, G-INV green; G-PW code-review check done; suite green via legacy SUT |
| **M4** | Page routes port + remaining server gates (mood whitelist, following shape, link rules + client half, validation, 404, next-flow) — **SUT command swaps to uvicorn at end of M4** | G-MOOD, G-FOLLOWING, G-LINK, G-XSS, G-VIEW, G-FLOW green; full suite green via **uvicorn** SUT |
| **M5** | Presentation: template/JS refactor, CDN upgrades, manifest/icons, cookie flags | G-MANIFEST, G-COOKIE green; suite green; browser-tier sign-off checklist complete |
| **M6** | Cutover: container image + deploy command swap (uvicorn entrypoint); GAP-9 duplicate scan → production index creation; README "Run & Deploy" section (DOC-1); delete root requirements files (§11) | deployment carryover table fully applied; prod smoke: login → set mood → view via link |

## 14. Explicitly out of scope

- All TODO.md feature wishes (mood customization, profile expansion,
  i18n, FAQ content, copy-link buttons, confirmation dialogs, …).
- New API surface (OpenAPI docs, versioning), CSRF tokens (post-migration
  option per Gate 2 #6), rate limiting (Gate 2 #7: C, revisit optional).
- GAP-3 redesign (link-tracked following) — post-migration feature
  (Gate 2 #8).
- Schema redesign, datastore migration, user-data changes.
- CI/packaging/publishing setup beyond the project's Makefile.
- Test-suite *additions* beyond the precursor and its gates.

---

*Decisions referenced: Gate 1 (owner, §3); Gate 2 record (all approved
2026-09-02) — `issues.md` §6; critical-client review fixes folded
(2026-09-02, two personas). Cross-references: behaviours —
`functional.md`; gates — `testing.md` §6.*