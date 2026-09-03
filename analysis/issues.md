# How I Feel — Issues Analysis

Analysis of the legacy codebase at commit `7aec49b` (master), 2026-09-02.
Findings were produced by three independent discovery sweeps (security,
code review, edge-case hunt) and **every claim below was verified against
source** before entering this document (verification report C1–C37; three
claims were corrected during verification and are reflected here).
Critical-client review (two audience personas) added BUG-14–BUG-16 and
refined the validation-rule decisions.

**Decision status:** all decisions were resolved at Gate 2 — the owner
approved the full decision inventory on 2026-09-02 (record in §6). No
open decisions remain; the only open items are `[verify]`-marked
implementation-time facts (noted where they occur).

## 1. Disposition policy

Every issue receives exactly one disposition bucket:

| Bucket | Meaning |
|---|---|
| **P** | Precursor — work required *before* the migration starts (here: the characterization test suite) |
| **A** | Fix during migration, zero/negligible user impact (latent crashes, dead code, contract corrections, hardening matching modern defaults) |
| **A\*** | Fix during migration but **user-visible** (new error/state/wording) — owner approval of the exact string at Gate 2 |
| **B** | Fix immediately after migration |
| **C** | Keep as-is (owner-confirmed) |

Severity scale: **High** (security/data-integrity today) · **Medium**
(user-visible breakage in a realistic flow, or real security vector) ·
**Low** (edge case, cosmetic, latent) · **Info** (no direct action).

Gate-test IDs (G-…) refer to held tests defined in `testing.md` §6.
Sweep-step labels (S-1..S-4) are procedure-step provenance, not
requirements.

## 2. Summary table

| ID | Issue | Sev | Bucket |
|---|---|---|---|
| BUG-1 | Signup with existing username overwrites that account's password → account takeover | High | A |
| BUG-2 | Mood values unvalidated; `null`/unknown mood breaks mood page and Following page | Medium | A\* |
| BUG-3 | `ObjectEncoder` fallback references unbound `json` → latent 500 | Low | A |
| BUG-4 | `assert` used as old-password guard in `change_password` (fails open under `-O`) | Low | A |
| BUG-5 | `/me` POST dispatch raises on missing/unknown `scope` → 500 | Low | A |
| BUG-6 | API POST endpoints return 500 instead of 400 on wrong-shaped bodies | Low | A\* (messages) |
| BUG-7 | Dead hidden `next` inputs in login/signup forms | Low | A |
| BUG-8 | `moods.length` is `undefined` → broken mood-grid layout classes | Low | A |
| BUG-9 | Unknown `/mood/<link>` served with status 200 instead of 404 | Low | A |
| BUG-10 | Unsafe-`next` abort happens *after* login/invitation-consumption side effects | Low | A |
| BUG-11 | `validates()` crashes (`TypeError`) on a user document without a password field | Low | A |
| BUG-12 | Deprecated `logger.warn()` used | Low | A |
| BUG-13 | Empty-password accounts creatable through normal signup | Medium | A |
| BUG-14 | Profile update with absent email field stores `email: null` → `gravatar` raises → every authenticated page 500s for that user (permanent, no self-service recovery) | Medium | A |
| BUG-15 | Bare `except:` in `/about/<page>` masks every error class as 404 | Low | A |
| BUG-16 | Missing password field on page POSTs (`/login`, `/signup`, `/me` password scope) → 500 | Low | A |
| SEC-1 | `APP_SECRET_KEY` falls back to hardcoded `"local"` → forgeable sessions when unset | High | A |
| SEC-2 | `GET /api/me/following` exposes followed users' email, full social graph and all their secret mood links | High | A |
| SEC-3 | Stored XSS: unvalidated usernames/moods/names rendered into inline-JS and jQuery HTML sinks | Medium | A\* |
| SEC-4 | Follower links: client-side non-CSPRNG, user-editable, no uniqueness → ambiguous/wrong-person resolution | Medium | A\* |
| SEC-5 | Invitation revocation lacks ownership check (any holder of the UUID can revoke) | Low | A |
| SEC-6 | Client error handlers crash silently on non-JSON error bodies; GET failures fully silent | Medium | A\* |
| SEC-7 | No CSRF tokens; GET-only logout; no `Secure`/`SameSite` cookie attributes | Low | A (flags) / C (rest) |
| SEC-8 | No rate limiting or lockout on `/login` | Low | C |
| FE-1 | PWA manifest served as `text/html`; all 8 declared icons 404 | Medium | A\* |
| GAP-1 | Fragile db-name parsing from `MONGODB_URI` (empty name for srv URIs) | Low | A |
| GAP-2 | No `serverSelectionTimeoutMS` → ~30 s hangs when MongoDB is unreachable | Low | A |
| GAP-3 | Following bypasses link revocation (README promises the opposite) | Medium | C |
| GAP-4 | Invalid `LOG_LEVEL` value crashes the app at import | Low | A |
| GAP-5 | No identity validation: whitespace-only usernames accepted; follow accepts any/duplicate/nonexistent names | Low | A\* |
| GAP-6 | Invitation single-use race (check-then-act, not atomic consume) | Low | A |
| GAP-7 | Unbounded growth: followers/following arrays, invitations never expire | Info | C |
| GAP-8 | bcrypt silently truncates passwords at 72 bytes | Info | C |
| RUN-1 | eventlet deprecated (gunicorn removed worker class in v26, 2026-05; upstream support ends 2027-04) | High* | migration |
| RUN-2 | Flask-RESTful effectively unmaintained (last release 2023, untested on Flask 3.x) | High* | migration |
| RUN-3 | Pinned dependency set predates current fix releases (Werkzeug 3.0.3, gunicorn 22.0.0, Jinja2 3.1.4, …) | Medium | migration |
| RUN-4 | `dnspython` pinned only in the freeze, required solely for `mongodb+srv://` URIs (environment-coupled) | Low | A |
| RUN-5 | No Python version pinned anywhere in the repo | Low | migration |
| DOC-1 | README stale as setup documentation (Heroku/`Procfile`/`server.py`/`src/` layout, 3-mood description; no env-var docs) | Low | A |

\* RUN-1/RUN-2 are rated against the migration's success, not current
exploitability: they are the stated reason for the modernization.

## 3. Per-issue entries

### Functional bugs (BUG-)

**BUG-1 — Signup account takeover.** Where: `ui.py::signup` (POST) +
`user.py::User.change_password`. Observed (verified): signup performs no
username-existence check; `change_password` executes
`update_one({"user": username}, {"$set": {"password": …}}, upsert=True)`
— for an existing username this silently replaces the victim's password;
`login_user(user)` then logs the attacker in as the victim. No unique
index exists (`create_index`: 0 occurrences repo-wide; TODO.md even lists
"duplicate username checks" as pending). Root cause: upsert-by-username
used as account creation. Fix (owner-approved): reject signup for an
existing username **reusing the existing feedback string** `Invalid
username and/or passwords do not match.` (no new wording), plus a unique
index on `users.user` (test datastore: harness arrange-step; production:
M6 deploy-time — with a mandatory duplicate scan first, see GAP-9).
Also rejected: empty passwords (BUG-13), same string covers it. Gate:
G-AUTH.

**BUG-2 — Mood values unvalidated; `null` mood breaks rendering.**
Where: `api.py::Mood.post` (stores any JSON verbatim) × client
`mood.js`/`following.js`/`view_mood.html` (assume the 4 known values).
Verified consequences: a user who never set a mood has `mood: None` →
`show_mood("None")` renders an empty container on `/mood/<link>`;
`activate_mood(null)` breaks the highlight on `/mood` (cards render, none
highlighted); one followed user with a `null`/unknown mood aborts the
`following.js` loop — everyone after them is not rendered. Fix: server
whitelist (`super|ok|nok|down`) → 400 on other values; client guard
rendering a neutral "no mood set" state. **A\* strings (approved, Gate 2):
** API error `Invalid mood.`; client neutral state text `No mood set.`
(owner-approved with the Gate 2 "agree on all fronts" round as part of
the BUG-2 fix description). Gate: G-MOOD.

**BUG-3 — Latent `NameError` in the JSON encoder fallback.** Where:
`__init__.py::ObjectEncoder.default` — calls `json.JSONEncoder.default`
while only `from json import JSONEncoder` was imported. Latent (current
payloads never hit the fallback). Fix: `import json` /
`super().default(obj)`. Gate: G-API.

**BUG-4 — `assert` as authorization guard.** Where:
`user.py::change_password`: `if self._password: assert
self.validates(old_password)` — stripped under `python -O` (fail-open);
unreachable-in-practice via the UI (pre-checked in `ui.py`), which makes
it dead-code-plus-landmine. Fix: explicit check returning failure.
Gate: G-PW — **not expressible over HTTP** (the UI path pre-checks;
observable behaviour is identical before/after, pinned by T-P15):
verified at the code-review tier, not by a held HTTP test.

**BUG-5 — `/me` dispatch crash.** Where: `ui.py::show_my_page` POST:
`{…}[request.form.get("scope")]()` → `KeyError` → 500 on malformed POST.
Fix: explicit dispatch with a 400 fallback. Gate: G-ME.

**BUG-6 — API 500s on wrong-shaped bodies.** Where: `api.py` (missing
`mood`/`invited` keys; `add_follower(**request.get_json())` on non-dict
or extra keys; `Following.post` storing any JSON type). Precisely:
**invalid JSON** request bodies already return framework 400/415 today;
only **wrong-shaped** (valid JSON, wrong structure) returns 500.
Fix: shape validation → 400 JSON. **A\* messages (approved, Gate 2, as
part of the bulk approval):** per-endpoint validation messages in the
framework's existing shape `{"message": …}`: mood missing/not-a-string →
`Invalid mood.`; followers non-dict/unknown-keys → `Invalid follower
information`; invitations missing `invited` → `Missing invited.`;
following body not a valid username string → `Unknown user.`. Status
change 500→400 is observable only to direct API clients, not through the
shipped UI. Gate: G-API.

**BUG-7 — Dead `next` hidden inputs.** Where: `login.html`,
`signup.html` (`<input type="hidden" name="next" value="">`) vs
`ui.py` reading `request.args`. Removal (see deletions list in
`modernization.md` §11). Gate: G-FLOW.

**BUG-8 — `moods.length` undefined.** Where: `mood.js::show_mood_selectors`
(`row-cols-md-undefined mb-undefined` → single-column desktop layout).
Fix: `Object.keys(moods).length`. Client-side — verified via browser
tier, not HTTP. Gate: G-MOOD (server half) + manual sign-off.

**BUG-9 — Unknown mood link returns 200.** Where: `ui.py::show_mood_view_page`
renders `unknown_follower.html` without a status. Fix: `return …, 404`
(body unchanged). Gate: G-VIEW.

**BUG-10 — Side effects before `next` validation.** Where: `ui.py`
signup/login: `login_user` (and account creation + invitation revoke)
precede the `is_safe_url` check → a crafted bad `next` still consumes the
invitation / logs the user in while showing 400. Fix: validate `next`
first. Gate: G-FLOW.

**BUG-11 — Login crash on passwordless user document.** Where:
`user.py::validates`: `bcrypt.checkpw(password, None)` → `TypeError` →
500 (document without a `password` field; reachable via the mood-setter
upsert creating a bare document). Fix: `None` → return `False`. Gate:
G-AUTH.

**BUG-12 — `logger.warn` deprecated.** Where: `ui.py::show_mood_view_page`.
Fix: `logger.warning`. Gate: covered by suite-wide parity.

**BUG-13 — Empty-password accounts.** Where: signup accepts `""`
passwords (truthiness only checked on username). Folded into BUG-1's
fix (non-empty enforcement), same existing feedback string. Gate: G-AUTH.

**BUG-14 — Cleared/absent email bricks the account.** Where:
`ui.py::handle_profile_update` stores `{"email": request.form.get("email")}`
— a crafted POST without the field stores `email: null`;
`user.py::gravatar` catches only `KeyError`, so `None.lower()` raises
`AttributeError` **while rendering** → every authenticated page for that
user 500s permanently (no self-service recovery). (Found by the
edge-case sweep; surfaced again by critical-client review.) Fix: coerce
absent/None email to `""` at write time and guard `gravatar` against
non-string values (empty-string state stays as pinned by Q-8). Gate:
G-ME.

**BUG-15 — Bare `except:` masks all errors as 404.** Where:
`ui.py::show_about_page`: `try: render(f"about/{page}.html") except:
abort(404)` — genuine server faults are silently misreported as 404.
Fix (approved): catch `TemplateNotFound` only → 404; all other
exceptions propagate (→ 500). **This is a sanctioned observable delta
(A):** an about page failing for non-missing-template reasons changes
from 404 to 500; recorded in the sanctioned-fix table (G-ABOUT row) with
an expectation-change commit at M3. Path traversal is not possible
(route segments cannot contain `/`; suffix `.html` appended — verified).
Gate: G-ABOUT.

**BUG-16 — Missing password field on page POSTs → 500.** Where:
`ui.py::show_login_page`/`signup` — `request.form.get("password")`
returns `None`; `str.encode(None)` raises `TypeError` → 500. Fix: treat
missing fields as the existing validation-failure path (feedback string
unchanged). Folded into G-ME's explicit-dispatch work (same pattern as
BUG-5). Gate: G-ME.

### Security (SEC-)

**SEC-1 — Hardcoded fallback `SECRET_KEY`.** Where: `__init__.py`:
`os.environ.get("APP_SECRET_KEY", default="local")`. Owner fact: set in
production, not in development → forgeable-session risk is live in any
environment that boots without the variable (a forgeable
`{"_user_id": …}` cookie impersonates any account). Fix (approved): fail
fast at boot when `APP_SECRET_KEY` is unset — development environments
must set one too (any value). No user-visible wording. Gate: G-BOOT
(held test: app refuses to boot without the variable).

**SEC-2 — Over-exposed followed-user serialization.** Where:
`user.py::to_json` (single shape for self- and third-party contexts) via
`api.py::Following.get`; projection excludes only `password`. Any
authenticated user therefore receives, for every user they follow
(following is unilateral, no consent): the user's `profile` (email —
PII), their full `followers` list — i.e. **all their secret mood-page
links** — and their `following` graph. The shipped client uses only
`user`, `mood`, `gravatar`. Fix (approved): reduced serialization for
third-party context (`{user, mood, gravatar}`); `/api/mood` and self
pages keep full shape. Gate: G-FOLLOWING.

**SEC-3 — Stored XSS.** Where (verified sinks): `view_mood.html`
(`onclick='follow("{{ user.user }}");'`, `show_mood("{{ user.mood }}")`
inline in an attribute/script context); `following.js::show_followed`
(`${followed.user}` etc. into jQuery `.append()`); `followers.js` /
`me.js` (same pattern). Usernames, moods, follower names/links and
invitation targets are stored unvalidated (GAP-5) and rendered unescaped
into JS contexts. Exploitation: any visitor of a crafted `/mood/<link>`
page executes the page-owner's payload in *their* session. Fix
(approved): server-side input validation per GAP-10's concrete rules +
client-side rendering via `textContent`/`data-*` attributes instead of
string interpolation. **A\* strings (approved, Gate 2):** validation
rejections reuse the existing strings — follower: `Invalid follower
information`; username: existing signup feedback; mood: `Invalid mood.`
(BUG-2). No new wording. Gate: G-XSS (server-side rejection tests) +
manual browser sign-off (payload renders inert).

**SEC-4 — Follower-link integrity.** Where: `followers.js::generateUUID`
(timestamp + `Math.random()`, non-CSPRNG), editable link input,
`user.py::add_follower` (no uniqueness check), `followed_with_link`
(`find_one`, arbitrary first match). Consequences: duplicate links
resolve to an arbitrary user's page; one `break_link` `$pull` removes
every duplicate row; links never rotate. Fix (approved, Gate 2): links
generated server-side (`uuid.uuid4()` — the invitation path already does
exactly this); uniqueness enforced **globally** across all users (that
is what fixes Q-9's arbitrary resolution — per-owner uniqueness would
not). **Contract delta (part of the approved fix):** `POST
/api/followers` now returns the created `{"name": …, "link": …}` object
(the client renders the row from the response, so API and consumer land
together in M4); a client-supplied `link` value is ignored; an
existing-link collision (pre-existing data) is rejected with `Invalid
follower information`. Existing links keep working (capability lookups
unchanged). **A\* string (approved):** duplicate rejection reuses
`Invalid follower information`. Gate: G-LINK (M4, together with the
client half — moved out of M5 per critical-client review).

**SEC-5 — Invitation revoke lacks ownership filter.** Where:
`invitations.py::revoke`: `delete_one({"invitation": …})` — the GET list
is scoped `{"from": …}` but the delete is not; any authenticated user
holding another user's invitation UUID can revoke it. Fix: add
`"from": current_user.user` to the delete filter. Gate: G-INV.

**SEC-6 — Consumer-side error handling.** Where: `ajax.js` `post`/`dele`
error handlers: `JSON.parse(response.responseText).message` unguarded —
any non-JSON error body (HTML 500/404 from non-API routes or a proxy)
throws inside the handler → no notification at all; all four `$.get`
calls have no error callback → silent failures. Fix (approved): guarded
parse with fallback + error handlers on GETs. **A\* string (approved,
Gate 2):** fallback notification text `Whoops, someting went
wrong:\nUnknown error` — typo kept per Gate 2 #3. Client-side — browser
tier. Gate: manual sign-off row.

**SEC-7 — CSRF posture, logout method, cookie attributes.** Where: no
token generation/validation anywhere; `@app.get("/logout")`; no
`SESSION_COOKIE_SECURE`/`SAMESITE` set (HTTPONLY defaults True).
**Resolved (Gate 2):** set `SESSION_COOKIE_SECURE=True` and
`SameSite=Lax` explicitly during migration (A, gate G-COOKIE, M5);
**keep** the GET-only logout (C); full CSRF tokens are a post-migration
option (B) and otherwise out of scope. **Implementation note (from
critical-client review):** the flag must be environment-configurable
(env var, default `true` in production; the test harness sets `false`
for its plain-HTTP SUT) — otherwise every authenticated suite test goes
red the moment the M5 fix lands. G-COOKIE asserts the *production*
default via a config-reading test. Gate: G-COOKIE.

**SEC-8 — No login rate limiting.** Where: `ui.py::show_login_page`.
**Resolved (Gate 2):** keep as-is (C) — invitation-only user base,
bcrypt cost; may be revisited post-migration. No gate.

### Presentation / external assets (FE-)

**FE-1 — PWA manifest mis-served; icons missing.** Where:
`ui.py::manifest` renders `manifest.json` through the template engine →
`Content-Type: text/html` (declared-format miss, sweep S-1);
`pages/manifest.json` declares 8 icons at `/images/icons/icon-*.png` —
no such route or files exist (all 404; PWA install degraded).
**Resolved (Gate 2):** serve the manifest with
`application/manifest+json` (A) **and** ship a generated icon set (one
source image, 8 sizes) under the static tree, updating the manifest's
`src` paths. No on-screen wording changes. Gate: G-MANIFEST (content
type + each icon URL returns 200 image/png + updated manifest body).

### Gaps (GAP-)

**GAP-1 — DB-name parsing.** Where: `data.py`:
`DB_CONN.split("/")[-1].split("?")[0]` — `mongodb+srv://host/?params` →
empty name; pathless URI → `localhost:27017`. Failure surfaces at first
query, opaque. Fix: parse with `urllib.parse`, fail fast with a clear
error. Gate: G-BOOT (config variant test). **Timing note (from critical
review):** this fix lands with the data-layer port (M2), not the
skeleton (M1) — G-BOOT's milestone is M2 accordingly.

**GAP-2 — No DB timeout.** Where: `data.py` MongoClient without
`serverSelectionTimeoutMS` → ~30 s request hangs when MongoDB is down.
Fix: explicit `serverSelectionTimeoutMS` (5000 ms). Gate: G-DBFAIL
(split from G-API per critical review; M2).

**GAP-3 — Following bypasses revocation.** Where: `user.py::following`
serves moods directly from the followed user's document; `break_link`
cannot cut this channel; README states deleting links "remov[es] access
to certain users" — evidence conflict between documented intent and
behaviour. **Resolved (Gate 2):** keep behaviour during migration (C;
documented as a preserved wart in `modernization.md` §10); a
link-tracked redesign (TODO: "keep used link in following, to allow
followed to break") is post-migration feature work, out of this
engagement's scope. No gate during migration.

**GAP-4 — `LOG_LEVEL` boot crash.** Where: `setup.py` — invalid level
name → `ValueError` at import. Fix: validate against
`logging.getLevelNamesMapping()` with a warning + fallback to INFO.
Gate: G-BOOT (lands M2, with the boot/config code — see GAP-1 note).

**GAP-5 — No identity validation.** Where: signup accepts
whitespace-only usernames; `follow()` pushes arbitrary/duplicate/
nonexistent names (invisible via `$in`). Folded into SEC-3's validation
work (concrete rules: GAP-10). **A\* strings (approved, Gate 2):**
reuse existing feedback strings for signup/followers; following a
nonexistent user returns new `Unknown user.`. Gate: G-XSS /
G-FOLLOWING.

**GAP-6 — Invitation TOCTOU.** Where: `invitations.py::is_valid` +
later `revoke` — two concurrent signups can both pass. Fix: atomic
consume — `find_one_and_delete` as the first step of the **validated**
signup path (after form validation passes, before account creation;
consuming before validation would break T-P11's pinned behaviour).
Gate: G-INV. **Legacy-observable note (from critical review):** on the
single-worker legacy SUT the race may serialize (gate would XPASS);
T-E9 is therefore written as a deterministic post-fix verification
(*skip* on legacy, exempt from the xfail-strict rule), not an xfail
gate.

**GAP-7 — Unbounded growth.** Where: `$push` arrays on user documents,
invitation collection with no TTL. Info — no cap today; document-size
limit (16 MB) far away for realistic use. Keep (C, confirmed).

**GAP-8 — bcrypt 72-byte truncation.** Where: `user.py::validates`/
`change_password`. Info — document the limit; long-passphrase users
silently truncated. Keep (C, confirmed) — changing it would invalidate
existing passwords (data-touching; excluded by owner constraint).

**GAP-9 — Unique index vs. pre-existing duplicates (deploy risk).**
BUG-1 means duplicate usernames may exist in production today (upsert
never enforced uniqueness). `CREATE UNIQUE INDEX` fails outright on
duplicates — a mid-cutover deploy breaker. **Decision (part of Gate 2
approval):** M6 runs a **duplicate-scan pre-step** (`users.aggregate`
group-by on `user`, count > 1); if duplicates exist, deployment stops
and the owner decides resolution per case (owner-approved remediation —
data changes only with explicit per-case approval); only a clean scan
proceeds to index creation. Same logic applies to the test datastore
(harness creates the index as arrange; legacy-era test data is
generated, never imported from production).

**GAP-10 — Validation rules must be concrete (spec completeness).**
SEC-3/GAP-5 mandate charset/length validation; the rules are now
specified (owner-approved with the Gate 2 bulk approval):
- **username**: 1–32 chars, charset `[A-Za-z0-9_-]`, trimmed;
  whitespace-only rejected. Rejection string: existing signup feedback.
- **mood**: exact whitelist `super|ok|nok|down` (BUG-2).
- **follower name**: 1–64 chars, any printable characters except
  `<`, `>`, `"`, `'`, backslash, backtick, and control characters.
- **follower link**: server-generated UUID v4 (client-supplied values
  rejected — `Invalid follower information`).
- **email**: no format validation (non-goal §8); coerced to string,
  1–254 chars, `None`/absent → `""` (BUG-14).
Gate: G-XSS (rejection rows encode these rules).

### Runtime & dependency hygiene (RUN-)

**RUN-1 — eventlet (migration driver).** `__init__.py` monkey-patches at
import; `Makefile.local` serves with `gunicorn -k eventlet -w 1`. Gunicorn
deprecated (25.0) then **removed** (26.0, 2026-05) the eventlet worker;
eventlet upstream support ends 2027-04. Owner decision: migrate to
asyncio + uvicorn (Gate 1). Disposition: **migration step** (M2), not a
code fix.

**RUN-2 — Flask-RESTful (migration driver).** Unmaintained since 2023;
unverified against Flask/Quart 3.x. Owner decision: replace with plain
(Quart) views, preserving URL + JSON contract. Disposition: **migration
step** (M3).

**RUN-3 — Stale pin set.** `requirements.txt` pins (verified): Flask
3.0.3, Werkzeug 3.0.3, Jinja2 3.1.4, gunicorn 22.0.0, eventlet 0.36.1,
Flask-RESTful 0.3.10, Flask-Login 0.6.3, pymongo 4.8.0, bcrypt 4.1.3,
dnspython 2.6.1, python-dotenv 1.0.1 — the set predates current fix
releases. Disposition: **migration step** (M1 lockfile via uv; versions
per `modernization.md` §3).

**RUN-4 — Environment-coupled dependency (sweep S-class miss).**
`dnspython` is pinned in the freeze but absent from
`requirements.base.txt`; pymongo requires it only for `mongodb+srv://`
URIs. **Carryover decision (Gate 2): preserve** — keep it in the target
dependency set. `[verify]` whether the production `MONGODB_URI` actually
uses an srv URI.

**RUN-5 — No Python pin.** No `.python-version`, no runtime file in the
repo (the README-era `.python-version` is gone). Disposition: **migration
step** — target pins Python 3.13 (required by Quart 0.23.1; Gate 1 +
Gate 2 confirmed).

**eventlet-client interplay:** module-level `MongoClient` + import-time
monkey-patching are both dissolved by the asyncio migration (M2/M3);
recorded here for traceability with sweep findings.

### Documentation (DOC-)

**DOC-1 — Stale README.** Where: `README.md` — documents
`server.py`, a `Procfile`, `src/pages` layout, Heroku deployment and a
three-mood model; none match the tree (verified). No env-var
documentation (`APP_SECRET_KEY`, `MONGODB_URI`, `LOG_LEVEL`). Fix (A):
add a short current "Run & Deploy" section (module entrypoint, env vars,
target server command) atop the historical tutorial narrative; keep the
narrative (it is the project's purpose). No gate.

## 4. Cosmetic leftovers (for the record)

| Where | Item | Disposition |
|---|---|---|
| `api.py` | Identical comment `# resource to break a link to follower` above both `Link` and `Invitation`; `Invitations` carries the copy-pasted wrong comment `# resource to get followers or add a new one` | clean up in porting |
| `pages/index.html` | Stray duplicate `</main>`/`</div>` closing tags; class `fs-7` (does not exist in Bootstrap 5.1) | fix in M5 |
| `pages/about/whatsnew.html` | Announces the new mood as "Ok" while its value is `nok` (Q-7 — user-facing copy) | keep (C, confirmed) |
| `base.html` | `window.location.reload(true)` — deprecated argument | fix in M5 |
| `ajax.js` | Typo "someting" (Q-12 — verbatim behaviour) | **keep (C, Gate 2)** — typo kept verbatim, including in the new fallback string |
| `ui.py` | `render()`'s unused default parameters; local variable `next` shadows builtin | clean up in porting |

## 5. Recommended execution order

- **Step 0 (precursor, P):** build the characterization suite
  (`testing.md`) against the *current* app; no production data touched
  (local MongoDB only, isolation guard).
- **In-migration (A/A\*):** data-layer + boot fixes (SEC-1, GAP-1,
  GAP-4, GAP-2) land with M2 (where the Quart boot/data code exists);
  API fixes (BUG-1..6, SEC-2..6, GAP-5, GAP-6, GAP-9, GAP-10, BUG-14)
  land with their porting milestones (M3–M4); client-side halves
  (BUG-8, SEC-3 output side, SEC-6, SEC-4 client) land with the
  presentation workstream (M5).
- **Post-migration (B, optional):** CSRF tokens (SEC-7 remainder),
  rate limiting (SEC-8), link-tracked following (GAP-3) — all explicitly
  outside this engagement unless the owner reopens them.
- **Keep (C):** GAP-7, GAP-8, GET logout, Q-7/Q-8/Q-12 copy quirks,
  cosmetic leftovers except where folded into porting.

## 6. Decision record (Gate 2 — owner approved all items, 2026-09-02)

| # | Decision | Outcome |
|---|---|---|
| 1 | New API error strings `Invalid mood.` (BUG-2) and `Unknown user.` (GAP-5) | **Approved** |
| 2 | Client fallback error notification `Whoops, someting went wrong:\nUnknown error` | **Approved** |
| 3 | "someting" typo | **Keep verbatim** (incl. fallback string); no cosmetic fix |
| 4 | SEC-4 server-side link generation + global uniqueness; POST `/api/followers` returns the created object | **Approved** |
| 5 | FE-1 ship generated icon set + fix manifest content type | **Approved** |
| 6 | SEC-7: cookie `Secure`+`SameSite=Lax` now (A, env-configurable for plain-HTTP test harness); GET logout kept (C); CSRF deferred post-migration | **Approved** |
| 7 | SEC-8: no rate limiting (C) | **Approved** |
| 8 | GAP-3: keep during migration (C); redesign is post-migration feature work | **Approved** |
| 9 | Stack deviation: Motor → PyMongo `AsyncMongoClient` (Motor deprecated, EoL 2026-05; identical API names) | **Approved** |
| 10 | Stack deviation: Flask-Login → quart-auth; all users logged out once at cutover | **Approved** |
| 11 | Python 3.13 (Quart 0.23.1 floor) | **Approved** |
| 12 | Post-review additions folded under the bulk approval: BUG-14 (None-email bricking) fixed; BUG-15 (bare except → 404-only) narrowed; GAP-9 duplicate-scan gate before production index; GAP-10 concrete validation rules; BUG-2 client neutral text `No mood set.`; BUG-6 per-endpoint 400 messages as listed | **Approved** (inherited from "agree on all fronts") |

---

*Sources: three independent sweeps (security-engineer, code-reviewer,
edge-case pass) + source verification (verdicts C1–C37) + two
critical-client reviews (modernization team; rebuild team) + owner facts
and decisions from Gates 1–2. Cross-references: behaviours —
`functional.md` §9; gates — `testing.md` §6; migration mapping —
`modernization.md` §6.*