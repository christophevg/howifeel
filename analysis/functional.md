# How I Feel — Functional Specification

Analysis of the legacy codebase at commit `7aec49b` (master), 2026-09-02.
Prepared by the legacy-modernization analysis engagement
(`c4:legacy-modernization`). Every claim in this document was verified
against source; feedback strings are byte-verbatim (including known
typos — they are behaviour, see the quirks appendix).

**Audience:** a fresh team re-implementing the project *functionally
identically*. No technology and no implementation detail appears here —
only what the end-user gets and what the outside world can observe.

*Provenance notes (non-normative): the internal working note
`_orchestration.md` records engagement bookkeeping; sweep-step IDs
(S-1..S-4) referenced in `issues.md` are procedure-step labels, not
requirements.*

## 0. Archetype mapping (vocabulary driver)

| Aspect | Record |
|---|---|
| Archetype | Web app (server-rendered HTML) + JSON API + installable PWA shell |
| Contract surfaces | Page URLs + HTML; `/api/*` endpoints (methods, JSON payloads, status codes, response shapes); PWA manifest at `/manifest.json`; session cookie; static assets (CSS/JS/images); client-side behaviour defined by the shipped JS |
| Presentation layer | Server-rendered pages + client-side JS (DOM built at runtime) + CSS |
| State layer | Server-side datastore, two collections: `users`, `invitations`; session cookie identifies the user; no client-side persistence |
| Primary black-box interface | Real HTTP server + protocol: pages, JSON API, manifest, static assets |
| Coverage boundary | Browser-side rendering and behaviour (JS-built DOM, notifications, pull-to-refresh) are invisible to HTTP-level observation → routed to a manual sign-off tier (see `testing.md` §4) |

## 1. Product summary

How I Feel is a deliberately minimal social network: each user shares
exactly one thing — their current mood — chosen from four moods
(`super`, `ok`, `nok`, `down`). A user shares their mood with specific
people by handing them a secret URL; anyone with an account who visits
such a URL can additionally "follow" that user and see their mood on a
personal Following page. New accounts are created by invitation only:
existing users generate single-use invitation links.

Guiding principle, from the landing page: *"Putting the dot on the i of
micro social network. Share your mood with who you want and how you
want. And nothing more."*

## 2. Actors

| Actor | Capabilities |
|---|---|
| Anonymous visitor | Views landing page, about pages, login and signup forms; views any `/mood/<link>` page for which they hold the link; cannot use any authenticated feature |
| Invitation holder | A visitor holding a valid invitation link `/signup/<invitation>` may create an account (username + password + repeat). The invitation is consumed by a successful signup |
| Authenticated user | Sets their mood; manages followers and their secret links; creates and revokes invitations; follows/unfollows other users; updates profile (email) and password; logs out |
| Followed user | Passive actor: the person whose mood page and data are exposed to holders of their links and to their followers |

## 3. Core concepts

### 3.1 Mood
Exactly four values exist. The client maps each value to a colour, an
emoji, a two-line text, and a button label. Verbatim table (emoji given
as Unicode codepoints; `<br>` marks a line break):

| Value | Colour | Emoji | Body text | Button label |
|---|---|---|---|---|
| `super` | green (success) | U+1F60D 😍 | `I'm Super!<br>I'm feeling just fine.` | `Super!` |
| `ok` | yellow (warning) | U+1F600 😀 | `I'm Ok.<br>Everything is calm, normal.` | `Ok` |
| `nok` | yellow (warning) | U+1F610 😐 | `I'm Ok on the surface.<br>I hope things clear up a bit.` | `Ok` |
| `down` | red (danger) | U+1F612 😒 | `I'm Down.<br>I'm not feeling too good.` | `Down` |

- A user has at most one current mood; setting a mood replaces it.
- A user who never set a mood has **no mood** (observed as JSON `null`
  through the API). The no-mood states are specified in the quirks
  appendix: Q-4 (`/mood/<link>`: the mood container renders empty — no
  card at all; the rest of the page, including the follow button,
  renders normally), Q-5 (Following: rendering breaks), Q-16
  (`/mood` management page: all four cards render, none highlighted).
- The server stores whatever value it was given (Q-10); the four-value
  table above is client-side knowledge only.

### 3.2 Follower link
A pair `{name, link}` on the owner. The `link` is a secret capability:
anyone holding `/mood/<link>` can view the owner's mood page — no login
required, viewer not identified, view not attributed. Deleting the
follower entry revokes the capability. Link uniqueness across users is
**not** enforced (Q-9: first matching user wins). The link is generated
client-side as a pseudo-UUID and the field is user-editable.

### 3.3 Following
A one-way list of usernames on the follower's document. No consent step;
no notification. The Following page resolves each username to the user's
current mood, emoji and gravatar. Nonexistent usernames silently never
appear (the lookup is a set-membership query). The Followed user cannot
remove a follower; only the follower can unfollow (Q-6 documents the
privacy consequence; disposition in `issues.md` GAP-3).
**Render order:** the Following page and its API render in datastore
query-result order, which is **not** the stored list order and can
differ from it after unfollow/refollow. (Followers and invitations
tables, by contrast, follow insertion order.)

### 3.4 Invitation
`{invitation: UUID, invited: name, from: username}`. Created by an
authenticated user for a named person; consumed by exactly one successful
signup; listed by its creator only. **Revocation model:** today *any*
authenticated user holding the UUID can revoke an invitation
(ownership is enforced on listing only — this is issue SEC-5; the fix
restores creator-only revocation, matching this section's model).
No expiry. Invitations live in their own collection, not on the user.

### 3.5 Session
Cookie-based login session identifying the username. Established by
login or signup; ended by logout. No "remember me"; no password reset;
no email verification.

### 3.6 Gravatar
If the user's profile has an `email`, the app derives an
MD5-of-lowercased-email avatar id and renders
`https://www.gravatar.com/avatar/<id>?d=mp` (external service). Email
edge states (all pinned behaviour):
- **key absent** (no email ever set) → avatar id is empty (`…/avatar/?d=mp`);
- **email set then cleared** (stored as empty string) → the id is the
  MD5 of the empty string — a non-empty id rendering a real (wrong)
  avatar (Q-8, kept);
- **email stored as `null`** (only reachable via a crafted POST without
  the field) → page rendering crashes — BUG-14, to be fixed.

## 4. Feature specifications

Feedback strings are byte-verbatim and part of the contract.

### 4.1 Landing page — `GET /`
Hero text: *"No really, how are you feeling?"* plus the product
principle quoted above. For anonymous visitors: a `Login` button
(→ `/login`) and the note *"No login yet? We're currently in
invitation-mode. Active users can create invitations to get you on
board."* For logged-in users the login block is absent. An `About`
section links to `/about/whatisthis` ("What is this?") and
`/about/whatsnew` ("What's new?"), plus a muted, non-clickable "FAQ"
placeholder. The header's own Login button is suppressed on this page.

### 4.2 Login — `GET/POST /login`
- GET: centered sign-in form with its own in-form brand block ("How I
  Feel", linking to `/`) and the visible heading *"Please sign in"*
  (Username, Password, `Sign in` button); the site header is suppressed.
- POST with valid credentials → session established → redirect to the
  `next` query parameter when it is a same-host URL; **absent** `next`
  → `/mood`; **present but foreign** `next` → 400.
- POST with invalid credentials → form re-rendered with notification
  `Incorrect username and/or password.` (error style).
- POST with a missing password field → server error today (BUG-16,
  fixed to 400 in migration).
- Passwords are stored salted and hashed; the server never stores or
  logs the plaintext.

### 4.3 Signup — `GET/POST /signup[/<invitation>]`
- Reached only through an invitation link. Without a valid invitation
  (missing or unknown UUID), both GET and POST redirect to `/`.
- GET (valid invitation): in-form brand block (as login) and heading
  *"Choose your Username and Password"* (Username, Password, Repeat
  Password, `Sign up` button); site header suppressed.
- POST (valid invitation) with a username and two matching passwords →
  account created with that username, invitation consumed, user logged
  in, redirect per the `next` rules of §4.2.
- POST otherwise (missing username, mismatched or missing passwords) →
  form re-rendered with notification `Invalid username and/or passwords
  do not match.` (error style).
- **No check exists that the username is free**: signing up with an
  existing username overwrites that account's password (BUG-1, High).

### 4.4 Logout — `GET /logout`
Authenticated only. Ends the session, redirects to `/`. (GET — see Q-11.)

### 4.5 My settings — `GET/POST /me` (authenticated)
One page, three sections:
1. **About Me**: an email field (pre-filled from profile) and an
   `Update` button → POST with form scope `profile` → re-render with
   notification `Profile successfully updated.` (success style).
2. **Change Password**: Old Password, New Password, Repeat New Password,
   `Change` button → POST with scope `password`:
   - old password correct and new passwords equal and non-empty →
     notification `Password successfully changed.` (success style);
   - otherwise → notification `Old or new passwords do not match.`
     (error style).
3. **Invitations**: a `Who` input with an `invite` button; a table of the
   user's invitations (Who / Link / remove — the row's delete button is
   a literal ASCII `x`). The UUID is rendered as a link to
   `/signup/<invitation>`, opening in a new tab. (There is no
   copy-to-clipboard affordance.)

### 4.6 Mood management — `GET /mood` (authenticated)
Four mood cards (client-rendered from the mood table in §3.1): emoji
header, colour-coded button with the mood's label. The currently-set
mood's card is highlighted and its button disabled; clicking another
card's button sets that mood immediately (POST `/api/mood`) and moves the
highlight. Initial state comes from `GET /api/mood` (no-mood state: Q-16).

### 4.7 Followers management — `GET /followers` (authenticated)
1. **Add Follower**: Name field; Link field with a `generate` button that
   fills in a client-generated pseudo-UUID; `add follower` button →
   POST `/api/followers`.
2. **Followers table**: one row per follower (Name, the `link` rendered
   as a link to `/mood/<link>` opening in a new tab, delete button — a
   literal ASCII `x` → DELETE `/api/link/<link>`).

### 4.8 Following page — `GET /following` (authenticated)
One card per followed user (client-rendered from `GET /api/me/following`),
in query-result order (§3.3): their gravatar, username, and current mood
rendered as the mood's emoji plus two-line body on the mood's colour. A
✕ (times glyph) button unfollows (DELETE `/api/me/following/<username>`).
If any followed user's stored mood is not one of the four known values,
the page's rendering loop breaks at that user and subsequent users are
not shown (Q-5).

### 4.9 Public mood view — `GET /mood/<link>`
For the owner of `<link>`: their gravatar (only if an email is set), and
their mood card (emoji + body). If the viewer is authenticated, is not
the page's owner, and does not yet follow them: a button
`follow <username>` that follows them and redirects to `/following`.
Visiting one's own page correctly shows no follow button.
Unknown link → the *"I'm sorry :-("* page (see Q-3 for its HTTP status).

### 4.10 About pages — `GET /about/<page>`
`whatisthis` — project origin story; `whatsnew` — feature announcements
(mentions the fourth mood as "Ok", referring to what is actually the
`nok` value — Q-7). Any other (or failing) page renders the 404 page.
**The about-page bodies are contract content**: a re-implementation
copies them byte-for-byte from the legacy tree
(`pages/about/whatisthis.html`, `pages/about/whatsnew.html`) — the
deliverable set intentionally does not inline multi-paragraph prose.

### 4.11 PWA manifest — `GET /manifest.json`
Web-app manifest declaring: name `How I Feel`, short_name `HowIFeel`,
`start_url` `/`, display `standalone`, background/theme colours
`#f5f5f5`, orientation `portrait-primary`, and eight icon entries
(`/images/icons/icon-72x72.png`, `-96x96`, `-128x128`, `-144x144`,
`-152x152`, `-192x192`, `-384x384`, `-512x512`, all `image/png`; the
full literal JSON is pinned in `testing.md` §5.3). None of the icon
files are actually served (Q-2), and the manifest is served with an
HTML content type (Q-1). The manifest is linked from every page
(`<link rel="manifest" href="/manifest.json">`).

### 4.12 Error pages
- Unknown URL → 404 page: *"I'm sorry :-( I can't seem to find the page
  you are looking for. It's often just a glitch. Try again later."*
- Unknown mood link → *"I'm sorry :-( I can't seem to find the person
  you try to follow. It's often just a glitch. Try again later."* (served
  with status 200 — Q-3).
- Non-page error surfaces (framework defaults, not the styled pages):
  a foreign `next` on login/signup returns a bare framework 400 body;
  POST to a GET-only page route (e.g. `/logout`, `/mood`) returns a bare
  framework 405; unhandled server faults return a bare framework 500.
  These are pinned byte-level by the suite (`testing.md` §5.4).

### 4.13 JSON API (consumed by the shipped client)
All endpoints require an authenticated session; anonymous calls get an
authorization failure (401; API-shape JSON body — shape pinned in the
error table below). The page contract and the API are consumed by the
bundled client JS; the shapes below are the de-facto contract.
**Success-body convention:** every operation returning no payload
returns the JSON body `null` (observed on `GET /api/mood` unset; the
suite pins the exact bytes per endpoint at M0).

| Endpoint | Method | Request | Success | Failure |
|---|---|---|---|---|
| `/api/mood` | GET | — | `200`, body = the user's stored mood value verbatim (string, or `null` when never set) | `401` |
| `/api/mood` | POST | JSON `{"mood": <value>}` — stored verbatim, no validation | `200`, body `null` | `401`; missing `mood` key → server error (Q-10); **non-JSON request body → framework 400/415** (not 500) |
| `/api/followers` | GET | — | `200`, `[{"name": …, "link": …}, …]` | `401` |
| `/api/followers` | POST | JSON `{"name": …, "link": …}` | `200`, body `null` | `401`; falsy name/link → `400` JSON `{"message": "Invalid follower information"}`; wrong-shaped JSON (non-dict / extra keys) → server error (Q-10) |
| `/api/link/<link>` | DELETE | — | `200`, body `null`; follower entry removed | `401` |
| /api/invitations` | GET | — | `200`, `[{"invitation": …, "invited": …, "from": …}, …]` | `401` |
| `/api/invitations` | POST | JSON `{"invited": …}` | `200`, `{"invitation": <uuid>, "invited": …, "from": <username>}` | `401` |
| `/api/invitation/<invitation>` | DELETE | — | `200`, body `null`; invitation removed (any invitation, regardless of owner — SEC-5) | `401` |
| `/api/me/following` | GET | — | `200`, array of followed users, each serialized as `{"user", "profile", "mood", "gravatar", "following", "followers"}` (over-exposure — SEC-2) | `401` |
| `/api/me/following[/<followed>]` | POST | JSON body = username (raw JSON value, type unchecked; path segment ignored) | `200`, body `null`; username pushed onto following | `401` |
| `/api/me/following/<followed>` | DELETE | — | `200`, body `null`; username removed from following | `401` |

**Error-body table** (shapes the client JS depends on — it parses
`.message`):

| Surface | Status | Body |
|---|---|---|
| API authorization failure | 401 | JSON `{"message": "<framework wording>"}` — exact wording pinned at M0 `[verify M0]` |
| API validation failure (follower) | 400 | JSON `{"message": "Invalid follower information"}` |
| API malformed JSON request | 400/415 | framework JSON error |
| API wrong-shaped JSON / unhandled fault | 500 | framework error body (JSON on API routes, HTML on page routes) — pinned at M0 |
| Page routes: foreign `next` | 400 | bare framework HTML (not the styled 404 page) |
| Page routes: wrong method | 405 | bare framework HTML |
| Unknown URL | 404 | styled 404 page (§4.12) |

Client error handling: failed POST/DELETE requests surface a top-center
error notification `Whoops, someting went wrong:\n<message>` (typo
"someting" is verbatim, Q-1/Q-12); the message is extracted from the
response body's `message` field — a non-JSON error body crashes the
handler silently (SEC-6). Failed GET requests are silent (no error
handler).

## 5. Global conventions

- **Header**: logo text "How I Feel" (→ `/`), and on the right: for
  authenticated users a dropdown menu anchored on their gravatar avatar
  with entries Mood (`/mood`), Following (`/following`), Followers
  (`/followers`), Settings (`/me`), divider, Logout (`/logout`); for
  anonymous users a `Login` button (→ `/login`), suppressed on `/` and on
  the auth pages; on login/signup the entire header is suppressed (the
  in-form brand block of §4.2/§4.3 remains).
- **Notifications**: transient, top-center popups; `success` styling for
  green confirmations, otherwise error styling. Triggered by server-side
  feedback strings and by client-side API errors (§4.13).
- **Pages are rendered from a common layout**: viewport meta, manifest
  link, title "How I Feel", third-party styles/scripts from a public CDN
  (Bootstrap 5.1.3 with integrity hashes, jQuery 3.6.0 with integrity
  hash), one vendored notification library, one custom stylesheet per
  page group.
- **Pull-to-refresh**: on touch devices, dragging down ≥100px shows a
  circular progress indicator (canvas, top-center) and reloads the page
  on release; <50px cancels.
- **PWA behaviour**: manifest display mode `standalone` (app-like when
  installed).

## 6. Data entities (functional view)

**User** (identified by username):
- `user` — username, unique in practice but *not* enforced (BUG-1).
- `password` — salted hash; set at signup, changeable in Settings with
  old-password confirmation.
- `profile.email` — optional; used only for the gravatar id (edge
  states in §3.6).
- `mood` — at most one current mood value; initially unset.
- `followers` — list of `{name, link}` pairs owned by this user;
  rendered in insertion order.
- `following` — list of usernames this user follows (may contain
  duplicates and nonexistent names; both are invisible side effects);
  rendered in query-result order, not list order (§3.3).

**Invitation** (standalone record): `{invitation, invited, from}`;
created, listed (own only), revoked; consumed by signup.

Lifecycle rules: creating an account consumes an invitation; deleting a
follower entry revokes that link; unfollowing removes the username from
the follower's list only; nothing expires.

## 7. Complete surface & operation inventory

### 7.1 Page surfaces

| Surface | Methods | Access | Renders / effect |
|---|---|---|---|
| `/` | GET | public | landing page |
| `/login` | GET, POST | public | login form / authenticate |
| `/signup` | GET, POST | public | redirect to `/` (no invitation) |
| `/signup/<invitation>` | GET, POST | public (valid invitation) | signup form / create account |
| `/logout` | GET | authenticated | end session → `/` |
| `/me` | GET, POST | authenticated | settings page / profile or password change |
| `/mood` | GET | authenticated | mood management page |
| `/followers` | GET | authenticated | followers management page |
| `/following` | GET | authenticated | following page |
| `/mood/<link>` | GET | public (capability) | public mood view |
| `/about/<page>` | GET | public | about pages; unknown → 404 page |
| `/manifest.json` | GET | public | PWA manifest (declared fields in §4.11) |
| `/static/<path>` | GET | public | stylesheets, client JS, notification JS, images |
| any other URL | GET | public | 404 page (status 404) |

Anonymous access to an authenticated **page** redirects to
`/login?next=<requested path>`; after login the user is returned to that
path (same-host only; an **absent** `next` falls back to `/mood`; a
**foreign** `next` is rejected with a 400).

### 7.2 API operations

See the table in §4.13 — it is the complete API surface (7 endpoints, 11
operations including the duplicated-POST variant of following).
Authorization failure on the API is a 401 with a JSON error body; it
does **not** redirect.

### 7.3 Declared artifacts

- **PWA manifest** (`/manifest.json`): declared fields verbatim in §4.11.
  Declared format: web-app manifest; *served* format: HTML (Q-1).
- **Icons**: 8 PNG icons declared; none served (Q-2).
- **HTML pages**: all 14 templates listed in §4; served as HTML.
- **API payloads**: JSON (`application/json`).
- **Cookies**: one `session` cookie (framework-signed, HTTP-only)
  carrying both the framework session and the login identity.
- **Security-relevant response headers**: none beyond framework defaults
  (no CSP, no explicit cache policy); the session cookie carries no
  `Secure`/`SameSite` attributes (HTTP-only by framework default).

### 7.4 Static assets & page→asset mapping (part of the contract)

CSS: `howifeel.css` (all pages), `login.css` (login, signup), `me.css`
(settings), `about.css` (about pages). JS: `ajax.js` (POST/DELETE
helpers, always loaded), `mood.js` (mood table §3.1 + rendering),
`followers.js`, `following.js`, `me.js`; vendored `notify.js` (always).
Images: `github-logo.png`, `gravatar.png`, `ok-and-ok.png`,
`your-menu.png` (about/whatsnew illustrations). Third-party CDN:
Bootstrap 5.1.3 (CSS+bundle JS), jQuery 3.6.0 — referenced with
integrity hashes. **Page → asset mapping (order matters — the mood map
must exist before dependent scripts run):**

| Page | Extra CSS | Extra JS (in load order) |
|---|---|---|
| login, signup | `login.css` | — |
| `/` | — | — |
| `/me` | `me.css` | `me.js` |
| `/mood` | — | `mood.js`, then inline `show_mood_selectors()` |
| `/followers` | — | `followers.js` |
| `/following` | — | `mood.js` → `following.js`, then inline `show_followed()` |
| `/mood/<link>` | — | `following.js` → `mood.js`, then inline `show_mood(...)` |
| about pages | `about.css` | — |

## 8. Explicit non-goals

The application does **not** do the following, and a re-implementation
must not silently add them:

- No password reset or recovery flow; no email verification.
- No mood history or timestamps; one current mood per user.
- No notifications, likes, comments, or any other content than the mood.
- No user search or directory; discovery only via shared links or the
  follow button on a visited mood page.
- No account deletion; no profile fields beyond email.
- No admin interface or operator UI.
- No i18n; all copy is English (with its typos).
- No "FAQ" content (placeholder text only).
- No avatar upload (gravatar only); no image storage.
- No email validation (the email field accepts any string; only the
  gravatar hash derives from it).
- No API authentication beyond the session cookie; no API versioning; no
  API documentation surface.
- No CSRF tokens; logout is a GET link; no rate limiting.
- Links and invitations never expire; no rotation mechanism.
- The followed user has no way to see or remove their followers.
- No copy-to-clipboard affordances.

## 9. Appendix: known quirks (observable oddities)

Each quirk is behaviour today; a re-implementation must consciously keep
or fix it. Dispositions live in `issues.md`.

| ID | Quirk | Keep/fix |
|---|---|---|
| Q-1 | `/manifest.json` served with an HTML content type instead of a manifest type | fix (FE-1) |
| Q-2 | All 8 manifest icons reference URLs that return 404 (PWA install degraded) | fix (FE-1) |
| Q-3 | Unknown `/mood/<link>` renders the "person not found" page with status 200, not 404 | fix (BUG-9) |
| Q-4 | A user who never set a mood: the mood container on `/mood/<link>` renders **empty** (no card at all); the rest of the page, including the follow button, is unaffected | fix (BUG-2) |
| Q-5 | One followed user with an unknown/null mood aborts rendering of the whole Following page | fix (BUG-2) |
| Q-6 | Following bypasses link revocation: `break_link` does not remove followers; only they can unfollow (README states deleting links "remov[es] access") | keep during migration (GAP-3, C) |
| Q-7 | "What's new?" announces the new mood as "Ok" while its actual value is `nok` (two buttons labelled "Ok") | keep (cosmetic copy) |
| Q-8 | Email states: key absent → empty gravatar id; email cleared to `""` → MD5-of-empty-string id (renders a real, wrong avatar) | keep |
| Q-9 | Duplicate follower links resolve to an arbitrary user's page; `find_one` order decides | fix (SEC-4) |
| Q-10 | Mood values, usernames, follower names/links are stored verbatim without validation (free-text moods, whitespace usernames, non-string moods) | fix (SEC-3, BUG-2, GAP-5) |
| Q-11 | Logout is a GET link (can be triggered by any cross-site link/image) | keep (SEC-7, C) |
| Q-12 | API error notification reads `Whoops, someting went wrong:` (typo, verbatim) and crashes silently on non-JSON error bodies | fix robustness (SEC-6); typo kept (Gate 2 #3) |
| Q-13 | Login/signup forms carry a dead hidden `next` field; the actual `next` flows through the query string | fix (BUG-7) |
| Q-14 | `/api/me/following/<followed>` POST ignores the path segment and uses the request body | keep |
| Q-15 | Mood management grid computes its column count from `moods.length` (undefined) → single-column layout on wide screens | fix (BUG-8) |
| Q-16 | `/mood` page for a user with no mood: all four cards render, none highlighted (the highlight call fails on `null` after the cards are built) | fix (BUG-2 client guard) |
| Q-17 | Invitations/followers delete buttons are literal ASCII `x`; the Following page's unfollow button is the `✕` (times) glyph | keep |

---

*Cross-references: issues — `issues.md`; verification of every behaviour —
`testing.md`; migration treatment — `modernization.md`.*