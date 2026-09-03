# How I Feel — Test-Driven Migration Plan

Characterization test plan for the legacy-modernization engagement,
2026-09-02. The suite is built **before any migration work**, green
against the **current** application, and becomes the migration's referee
and sign-off condition at every step. Revised after critical-client
review (milestone alignment, gate expressibility, suite-blackout
prevention).

Inputs: `functional.md` (behaviour contract — its §7 inventory is the
matrix source), `issues.md` (buckets → held gates), Gate 1 decisions
(pytest + real server over HTTP approved by owner; local MongoDB only;
production data untouchable), Gate 2 decisions (all approved — the
A\* strings in the gate table are final; see `issues.md` §6).

## 1. Principles

- **Black-box.** Every test observes the system only through real HTTP
  against a really running server: pages, JSON API, manifest, static
  assets, status codes, headers, cookies. No imports of application
  code; the datastore is used only as *arrange* and *state-set-up*
  (§3.3), never as *assert*.
- **Characterization, not TDD.** The suite pins today's behaviour as
  ground truth. A red test against the *old* app means the spec was
  wrong — fix the test first, never the old app.
- **Invariance.** Test cases never change across the migration; only
  the system-under-test start command changes (one fixture variable).
  If a test must change, that is a sanctioned-change event with its own
  commit and its gate reference — never folded into a porting commit.
- **Gates, not wart-pinning.** For every issue dispositioned A/A\* we
  write a **held test now** that asserts the *fixed* behaviour
  (xfail/skip with reason + milestone). There is deliberately **no**
  green test that requires buggy behaviour. Where current behaviour
  would be pinned by a matrix row and the issue is sanctioned to
  change, the gate supersedes the green row until activation.
- **Gate kinds** (after critical review — three expressibility classes):
  - **HTTP gate** — assertable through the suite's interface; held with
    strict xfail on the legacy app.
  - **Era-skip gate** — asserts fixed behaviour that only becomes
    deterministic post-fix (G-INV's race row, T-E9): written now,
    *skipped* on legacy (exempt from xfail-strict), activated at its
    milestone.
  - **Non-HTTP gate** — not expressible over HTTP (G-PW: the UI
    pre-checks before the guarded code path is reachable): verified at
    the **code-review tier** (a checklist row in `modernization.md` §13
    milestone exit, verified by reading the ported source), not by a
    held HTTP test.
- **Green = sign-off.** A milestone exits only with the full suite
  green (held gates remain held, era-skip gates remain skipped, until
  their fix lands).

## 2. In-process vs. subprocess — decision

**Decision: subprocess running the real server, driven over HTTP.**
Rejected in-process invocation because:

- (a) **the legacy code mutates the test process at import time** —
  `howifeel/__init__.py` calls `eventlet.monkey_patch()` at import
  (patching socket/threading/ssl globally);
- (b) **old and new stacks need different serving machinery** —
  legacy: `gunicorn -k eventlet -w 1 howifeel:app`; target:
  `uvicorn howifeel:app`. A subprocess speaking HTTP is bit-identical
  across both.

Honest costs: per-session server boot (~1–3 s, paid once per pytest
session via a session-scoped fixture); debugging uses captured server
logs rather than in-process traces; one managed child process.

**System-under-test commands (the single invariance point):**

| Era | Start command |
|---|---|
| Legacy (today) | `gunicorn -k eventlet -w 1 -b 127.0.0.1:<port> howifeel:app` (mirrors the production command's worker flags; production binds 127.0.0.1:5009 with `--chdir /app/apps/howifeel`) |
| Target (migration) | `uvicorn --host 127.0.0.1 --port <port> howifeel:app` (with `--app-dir` where a working-dir change is needed) |

The harness reads the command from a single documented place; swapping
eras touches one line, zero test bodies. **The SUT command swaps to
uvicorn only once all routes are ported (end of M4)** — no hybrid
system ever has to satisfy the full suite.

## 3. Test harness

- **Runner:** pytest, installed in a dedicated **legacy virtualenv** —
  the suite must not depend on the new stack's tooling; it runs before
  the migration exists.
- **Legacy environment bootstrap (day-one commands, from DOC-1's gap):**
  ```
  pyenv virtualenv 3.8.12 howifeel-test   # or any 3.8 venv
  pip install -r requirements-legacy.txt  # pinned legacy deps (below)
  ```
  where `tests/requirements-legacy.txt` is a **pinned copy of the
  current `requirements.txt` plus `pytest` and `requests`**, kept in
  the repo until M6 (so the legacy SUT stays reproducible even after
  the root requirements files are superseded at M1 — critical-client
  finding #14).
- **HTTP client:** `requests` (session object; cookies persist
  automatically — needed for login flows).
- **SUT fixture** (session-scoped):
  1. validate isolation guard (below);
  2. set env for the child: `MONGODB_URI=mongodb://localhost:27017/howifeel_test`,
     `APP_SECRET_KEY=<test value>`, `LOG_LEVEL=WARNING`,
     `SESSION_COOKIE_SECURE=false` (harness override — see G-COOKIE);
  3. start the SUT subprocess on an ephemeral port, capture stdout/stderr
     to a log file;
  4. poll `GET /` until HTTP 200 (readiness), timeout 30 s → hard failure.
- **Isolation guard (default, blocking):** the harness **refuses to
  run** unless the datastore is explicitly declared scratch:
  - `MONGODB_URI` host must be `localhost`/`127.0.0.1`;
  - database name must be exactly `howifeel_test` (the owner's local
    `howifeel` database contains real data — the default name is
    therefore *rejected*, not used);
  - any remote URI (production or otherwise) aborts the session before
    a byte is sent.
- **State isolation:** dedicated `howifeel_test` database; collections
  (`users`, `invitations`) dropped between test modules (function-scope
  reset via fixtures where cheaper); **the harness creates the
  `users.user` unique index as an arrange step** from M3 onward (data
  writes are arrange, never assert); no other datastore is touched; no
  external services are called in tests (gravatar URLs are asserted as
  *generated ids*, never fetched).
- **Capture protocol:** every response captured verbatim: status code,
  all headers (content-type, location, set-cookie shape), and the body
  as **bytes**; JSON bodies parsed only after byte-level capture.
  Assertions reference the captured artifact.
- **File layout:**
  ```
  tests/
    conftest.py                # SUT fixture, isolation guard, HTTP helpers
    helpers.py                 # login(), signup(), create_invitation() …
    requirements-legacy.txt    # pinned legacy deps + pytest + requests
    test_pages.py              # T-P*
    test_api.py                # T-A*
    test_artifacts.py          # T-S* (manifest, static, content types)
    test_errors.py             # T-E* (error paths, auth)
    test_gates_*.py            # G-* held gates (one module per gate)
  ```
- **Where `make test` lives at M0:** the repo `Makefile` is currently a
  one-line harness shim; the suite's `test` target ships as
  `Makefile.local::test` at M0 and moves into the new project Makefile
  at M1 (`modernization.md` §4).
- **Environmental preconditions (stated plainly):** local MongoDB
  reachable on `localhost:27017`; Python 3.8 venv with the legacy
  requirements + `pytest` + `requests`; no network access needed
  (CDN/gravatar never fetched; all tests offline-capable).

## 4. Coverage boundary — what the suite deliberately does not pin

**Cannot be observed over the black-box HTTP interface** (routed
explicitly). (The T-E15 gate description's phrase "split from G-API" is
provenance from the review round; normatively, G-DBFAIL stands alone as
defined in §6.)

| Unobservable item | Where it lives | Verification route |
|---|---|---|
| JS-built DOM: mood cards, following cards, follower/invitation tables, notifications, pull-to-refresh, mood-grid layout (BUG-8's visual half), Q-12 notification text (client-side only — T-Q4 is a browser-tier row, not an HTTP row) | client JS + templates | **Manual browser sign-off tier** (owner-approved choice — Gate 1's F4 question: pytest + real server over HTTP; browser tier for unobservable DOM behaviour): checklist in `modernization.md` §9 executed per presentation milestone |
| XSS payload inertness in the DOM (SEC-3's output half) | client JS | Manual browser tier: inject payload, confirm inert rendering |
| PWA install behaviour (manifest consumption) | browser | Manual sign-off (manifest bytes + content type *are* tested — T-S1/T-GATE) |
| BUG-4's assert-guard removal (G-PW) — unreachable through the UI (pre-checked in `ui.py`) | `user.py` | **Code-review tier**: ported `change_password` uses an explicit check (modernization.md §13 M3 exit item) |
| Session-cookie signing details (itsdangerous payload) | framework internals | Out of scope; session *behaviour* is fully covered via HTTP (login/logout/401/redirect) |
| CDN asset integrity (Bootstrap/jQuery bytes) | external | Out of scope — pinned only as reference attributes in HTML |
| Gravatar image correctness | external service | Out of scope (id generation is covered; image rendering is not) |
| Server log wording (e.g. `unknown link requested: …`) | logs | Not asserted (implementation detail); BUG-12 covered by lint-level check, not a test |

Not pinned by choice (rewritten internals): module structure, Mongo
query formulation, template internals — except where they surface in
responses (e.g. the manifest's declared fields, §5 T-S rows).

## 5. Test matrix

Derived one-to-one from `functional.md` §7 (complete surface & operation
inventory). Status column: **green** = characterization (pin today);
**gate** = held until its fix (issues.md ID in parentheses).

### 5.1 Pages (T-P)

| ID | Case | Key assertions |
|---|---|---|
| T-P1 | `GET /` anonymous | 200; contains hero text "No really, how are you feeling?"; Login button → `/login`; invitation-mode note; About links; header Login visible |
| T-P2 | `GET /` logged in | 200; Login button absent |
| T-P3 | `GET /login` | 200; form fields `username`/`password`; in-form brand block + "Please sign in" heading present; site header suppressed |
| T-P4 | `POST /login` valid | 302 → `/mood`; session cookie set; `/mood` then 200 |
| T-P5 | `POST /login` invalid | 200; body contains exactly `Incorrect username and/or password.` |
| T-P6 | `GET /logout` logged in | 302 → `/`; subsequent `/mood` → redirect to login |
| T-P7 | `GET /signup` (no invitation) | 302 → `/` |
| T-P8 | `GET /signup/<bad-uuid>` | 302 → `/` |
| T-P9 | `GET /signup/<valid invitation>` | 200; "Choose your Username and Password"; in-form brand block; header suppressed |
| T-P10 | `POST /signup/<valid invitation>` new username | 302 → `/mood`; logged in; invitation consumed (`/signup/<same>` now redirects) |
| T-P11 | `POST /signup` password mismatch | 200; body contains exactly `Invalid username and/or passwords do not match.`; invitation still valid |
| T-P12 | `GET /me` | 200; three sections; email field pre-filled; header menu present |
| T-P13 | `POST /me` scope=profile with email | 200; body contains exactly `Profile successfully updated.` |
| T-P14 | `POST /me` scope=password correct old + match | 200; exactly `Password successfully changed.`; old password no longer works, new does |
| T-P15 | `POST /me` scope=password wrong old | 200; exactly `Old or new passwords do not match.` |
| T-P16 | `GET /mood` | 200; four-card container present |
| T-P17 | `GET /followers` | 200; Add-Follower form + table present |
| T-P18 | `GET /following` | 200; container present |
| T-P19 | `GET /mood/<link>` anonymous | 200; owner's mood value present in page source |
| T-P20 | `GET /mood/<link>` unknown | gate G-VIEW (BUG-9): currently 200 + not-found page; gate asserts 404 |
| T-P21 | `GET /about/whatisthis`, `/about/whatsnew` | 200; headings "What is this?" / "What's new?" |
| T-P22 | `GET /about/<unknown>` | 404; 404 page copy present |
| T-P23 | `GET /<unknown-url>` | 404; 404 page copy present |
| T-P24 | anonymous `GET /mood` | 302 → login; **assert the parsed query parameter** `next == "/mood"` (do not pin the URL-encoded raw string — critical-review fix #9) |
| T-P25 | login with `?next=/mood` | 302 → `/mood` (same-host next honoured) |
| T-P26 | login with foreign `?next=https://evil.example` | 400; bare framework body (not the styled 404 page) |
| T-P27 | POST to GET-only page routes (`/logout`, `/mood`) | 405; bare framework body (pinned per critical-review finding #18) |
| T-P28 | `POST /login` with missing password field | gate G-ME (BUG-16): currently 500; gate asserts validation-failure feedback string |

### 5.2 JSON API (T-A) — full shape contract

| ID | Case | Key assertions |
|---|---|---|
| T-A1 | `GET /api/mood` (unset) | 200; body verbatim `null` |
| T-A2 | `POST /api/mood` `{"mood":"ok"}` then GET | 200; `null` → `"ok"`; **success body bytes pinned at M0 baseline** (functional.md §4.13 convention) |
| T-A3 | `POST /api/mood` unknown value | gate G-MOOD (BUG-2): currently stored verbatim; gate asserts 400 + `Invalid mood.` |
| T-A4 | `GET /api/followers` after add | 200; `[{"name": …, "link": …}]` exact shape |
| T-A5 | `POST /api/followers` valid | 200; then GET contains it; **response body bytes pinned at M0 baseline; post-fix expectation changes with G-LINK (SEC-4 contract delta: returns created object)** |
| T-A6 | `POST /api/followers` falsy name/link | 400; JSON body `{"message": "Invalid follower information"}` |
| T-A7 | `DELETE /api/link/<link>` | 200; GET no longer contains it; `/mood/<link>` → not-found path |
| T-A8 | `GET /api/invitations` after invite | 200; `{"invitation","invited","from"}` shape, uuid format |
| T-A9 | `POST /api/invitations` | 200; returns the created invitation object |
| T-A10 | `DELETE /api/invitation/<uuid>` | 200; GET list empty; signup with it now redirects |
| T-A11 | `GET /api/me/following` | gate G-FOLLOWING (SEC-2): shape reduced to `{"user","mood","gravatar"}` for followed users |
| T-A12 | `POST /api/me/following` body username | 200; GET /api/me/following contains user; `/following` page data resolves mood |
| T-A13 | `DELETE /api/me/following/<name>` | 200; user gone from GET |
| T-A14 | anonymous `GET /api/mood` | 401; JSON error body — **exact bytes pinned at M0 baseline** |
| T-A15 | anonymous call per remaining endpoint | 401 each |
| T-A16 | `POST /api/mood` missing key / `POST /api/followers` non-dict / `POST /api/invitations` missing key | gate G-API (BUG-6): currently 500; gate asserts 400 JSON with approved per-endpoint messages |
| T-A17 | non-JSON body to an API endpoint | 400/415 framework response (pins the invalid-JSON taxonomy — functional.md §4.13) |

### 5.3 Artifacts & declared formats (T-S)

Literal pin sources: the manifest's exact JSON is embedded in
`tests/fixtures/manifest-legacy.json` at M0 (copied byte-for-byte from
the served artifact — the deliverable prose is not the byte source);
post-fix manifest expectations live in `manifest-target.json` (G-MANIFEST).

| ID | Case | Key assertions |
|---|---|---|
| T-S1 | `GET /manifest.json` content type | gate G-MANIFEST (FE-1): currently `text/html`; gate asserts manifest media type |
| T-S2 | `GET /manifest.json` body | byte-parity with the M0-captured fixture (see above); 🔒 body update sanctioned by G-MANIFEST (icon paths) |
| T-S3 | each declared icon URL | gate G-MANIFEST (FE-1): currently 404; gate asserts 200 + `image/png` |
| T-S4 | shipped **stable** assets: all 4 CSS files, `notify.js`, all 4 images | 200; correct content types; **byte-hash pinned** — these are never edited by a sanctioned change |
| T-S5 | JS files `mood.js`, `followers.js`, `ajax.js` | 200 + correct content type; **content NOT hash-pinned** — M5 sanctioned fixes (BUG-8, SEC-3, SEC-4, SEC-6) edit them; each change rides its gate/expectation-change commit (critical-review fix #7) |
| T-S6 | every page's CDN references | integrity attributes byte-pinned per `functional.md` §5 (upgrade = sanctioned change, T-S5-style exemption) |

### 5.4 Auth, flows & config (T-E, G-BOOT)

| ID | Case | Key assertions |
|---|---|---|
| T-E1 | signup with **existing** username | gate G-AUTH (BUG-1): currently takeover succeeds (verifies overwrite); gate asserts rejection with existing feedback string + victim password intact |
| T-E2 | signup with empty password | gate G-AUTH (BUG-13): currently account created; gate asserts rejection |
| T-E3 | login for user with passwordless document | gate G-AUTH (BUG-11): currently 500; gate asserts clean failure |
| T-E5 | `POST /me` unknown/missing scope | gate G-ME (BUG-5): 400 instead of 500 |
| T-E6 | dead `next` hidden inputs | gate G-FLOW (BUG-7): inputs removed from rendered forms |
| T-E7 | bad `next` does not consume invitation / log in | gate G-FLOW (BUG-10): state unchanged after 400 |
| T-E8 | invitation revoke by non-owner | gate G-INV (SEC-5): other user's invitation survives |
| T-E9 | concurrent signup, same invitation | **era-skip gate** (G-INV/GAP-6): skipped on legacy SUT (race may serialize → XPASS risk, critical-review finding #6); deterministic post-fix verification at M3 — asserts exactly one account |
| T-E10 | duplicate follower link rejected / server-generated link; POST returns created object | gate G-LINK (SEC-4 contract delta) |
| T-E11 | username/mood/name charset+length validation per GAP-10 rules | gate G-XSS (SEC-3/GAP-5): rejects with sanctioned strings |
| T-E12 | app boot without `APP_SECRET_KEY` | gate G-BOOT (SEC-1): process exits non-zero with clear error |
| T-E13 | app boot with invalid `MONGODB_URI` variants (srv/no-path) | gate G-BOOT (GAP-1): clear startup error |
| T-E14 | app boot with invalid `LOG_LEVEL` | gate G-BOOT (GAP-4): warning + INFO fallback, app boots |
| T-E15 | Mongo unreachable (stopped) request path | gate G-DBFAIL (GAP-2, split from G-API — critical-review fix #3): bounded-time error, not ~30 s hang |
| T-E16 | non-owner cannot view others' invitations | part of G-INV scoping (GET already scoped — characterization) |
| T-E17 | crafted `POST /me` profile update without email field | gate G-ME (BUG-14): `email` never stored as `null`; pages keep rendering |
| T-E18 | `GET /about/<existing>` forced template fault | gate G-ABOUT (BUG-15): non-TemplateNotFound errors → 500, not 404 |
| T-GATE | isolation-guard negative test | harness run with a non-local `MONGODB_URI` aborts the session before any request (proves §8 acceptance item 3) |

### 5.5 Keep-as-is quirks (green characterization, from `functional.md` §9 C-bucket)

| ID | Pins | Interface |
|---|---|---|
| T-Q1 | Q-7: "What's new?" copy announces the mood as "Ok" (verbatim) | HTTP |
| T-Q2 | Q-8: gravatar id empty without email (`…/avatar/?d=mp` shape) | HTTP |
| T-Q3 | Q-14: `POST /api/me/following/<x>` ignores path segment, uses body | HTTP |
| T-Q4 | Q-12: error notification string `Whoops, someting went wrong:\n…` (typo verbatim — kept per Gate 2 decision) | **browser tier** (string exists only client-side; moved from HTTP matrix per critical-review fix #4) |
| T-Q5 | Q-17: invitations/followers delete buttons ASCII `x`; unfollow uses ✕ | browser tier |

## 6. Gated bug tests (held gates)

Written **now**, held per class (§1) with reason + milestone; activated
in the same commit as the fix. A\* gates carry the owner-approved
strings recorded in `issues.md` §6 (Gate 2, all approved 2026-09-02).

| Gate | Class | Asserts (fixed behaviour) | Issues | Milestone |
|---|---|---|---|---|
| G-BOOT | HTTP | boot refuses unset `APP_SECRET_KEY`; config errors for URI/LOG_LEVEL | SEC-1, GAP-1, GAP-4 | **M2** (boot/data code exists here — critical-review fix #1) |
| G-DBFAIL | HTTP | DB-down request → bounded-time error, not ~30 s hang | GAP-2 | **M2** (split from G-API — fix #3) |
| G-AUTH | HTTP | duplicate-username signup rejected (existing string); empty password rejected; passwordless doc → clean failure. *(Index existence is an arrange-step, not an assertion — critical-review fix #5)* | BUG-1, BUG-13, BUG-11 | M3 |
| G-API | HTTP | wrong-shaped bodies → 400 JSON with approved messages (never 500) | BUG-3, BUG-6 | M3 |
| G-ME | HTTP | `/me` dispatch 400 on bad scope; email never stored as `None`; missing password field → validation feedback | BUG-5, BUG-14, BUG-16 | M3 |
| G-ABOUT | HTTP | about-route: `TemplateNotFound` → 404; other faults propagate (500) | BUG-15 | M3 (with expectation-change commit) |
| G-INV | HTTP + era-skip | ownership-filtered revoke; atomic invitation consume (T-E9 skip-on-legacy) | SEC-5, GAP-6 | M3 |
| G-PW | **code-review tier** | ported `change_password` uses explicit check (no assert) — verified by reading source at M3 exit | BUG-4 | M3 |
| G-MOOD | HTTP + browser | mood whitelist 400 + `Invalid mood.`; client null-mood guard (`No mood set.`) | BUG-2 | M4 |
| G-FOLLOWING | HTTP | reduced followed-user shape `{user, mood, gravatar}`; `Unknown user.` on nonexistent target | SEC-2, GAP-5 | M4 |
| G-LINK | HTTP | duplicate link rejected; server-side generation; POST returns created object; client half lands **in M4** (moved from M5 — critical-review fix #13) | SEC-4 | M4 |
| G-XSS | HTTP | identity charset validation rejects payloads per GAP-10 rules | SEC-3 (server half), GAP-5 | M4 |
| G-VIEW | HTTP | unknown link → 404 (same page body) | BUG-9 | M4 |
| G-FLOW | HTTP | `next` validated before side effects; dead inputs gone | BUG-7, BUG-10 | M4 |
| G-MANIFEST | HTTP | manifest media type; 8 icons 200 `image/png`; updated manifest body (icon paths) | FE-1 | M5 |
| G-COOKIE | HTTP (config) | production default `Secure`+`SameSite=Lax` asserted via config (env knob `SESSION_COOKIE_SECURE=false` keeps the plain-HTTP suite alive — critical-review fix #10) | SEC-7 | M5 |
| G-AJAX | browser tier | guarded JSON parse + GET error handlers; fallback notification `Whoops, someting went wrong:\nUnknown error` (byte-pinned in browser sign-off checklist) | SEC-6 | M5 |

**Not expressible through the HTTP interface** (verified in the browser
tier or code-review tier instead): BUG-8 (layout classes), SEC-3
output-side inertness, SEC-6 (client error-handler robustness), BUG-4
(G-PW, code-review tier), DOC-1 — see §4 table.

## 7. Execution & maintenance rules

- **Run:** `make test` (Makefile.local target at M0; project Makefile
  from M1), optionally `TEST=tests/test_api.py::T_A2`.
- **Budget:** full suite < 2 minutes (one server boot per session;
  per-test cost is HTTP + local Mongo).
- **Red suite = stop.** No porting commit proceeds on a red suite.
- **Expectation changes are separate commits**, each referencing its
  issue ID and gate; never folded into porting commits.
- **Flaky = defect** — with the documented exception of era-skip gates
  (T-E9), which are *skipped*, never xfail-strict, on the legacy SUT.
- The suite runs offline (no CDN/gravatar fetches).

## 8. Acceptance criteria — "the precursor is done"

1. Every row of §5 that is marked green passes against the **current**
   legacy app (started via the legacy command in §2); success-body and
   error-body bytes baseline-captured (T-A2/A5/A14 etc.).
2. All gates exist per class: HTTP gates held (xfail-strict), era-skip
   gates skipped with reason, non-HTTP gates recorded as checklist rows
   in `modernization.md` §13.
3. Harness invariance documented: swapping eras = swapping the SUT
   command; isolation guard proven by T-GATE (non-local URI aborts).
4. Baseline recorded: run log + commit hash of the green baseline run.
5. No production data touched: guard active, test database
   `howifeel_test` only (owner constraint from Gate 1).

---

*Cross-references: behaviours — `functional.md`; issues & buckets —
`issues.md`; migration milestones consuming this suite —
`modernization.md` §13.*