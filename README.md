# Luna Unia

![Docker required](https://img.shields.io/badge/Docker-required-2496ED?logo=docker&logoColor=white)
![Docker Compose v2](https://img.shields.io/badge/Docker_Compose-v2-2496ED?logo=docker&logoColor=white)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Luna Sentia required](https://img.shields.io/badge/Luna_Sentia-required-111111?logo=ollama&logoColor=white)
![Status: v1.1](https://img.shields.io/badge/Status-v1.1-2EA043)

<p align="center">
  <a href="docs/luna-unia-showcase.mp4"><img src="docs/luna-unia-showcase.webp" alt="From Google sign-in to the Luna Unia home, then into the apps" width="900"></a>
</p>

<p align="center"><em>From Google sign-in to the Luna Unia home, then into the apps. Select it for the sharper video.</em></p>

## One home for every Luna app

Luna Unia is the front door to the Luna apps. It checks which Luna stacks are running
and shows each one as a card with its icon, name, and description. Pick a running
app to go to it; the shared sign-in means it opens without signing in again.

It has a UI only: no MCP service, no database, and no model calls. It reads nothing
from the apps except whether they answer.

<p align="center">
  <img src="docs/showcase.png" alt="Luna Unia showing all seven Luna stacks running, each card linking to its app">
</p>

## Who sees what

Unia shows each person only the apps they can use. Apps the owner has hidden at Luna Sentia's `/admin` do not appear, within about a minute, and only the owner sees Sentia's services. Set `LUNAUNIA_ALLOWED_EMAILS` to `*` for everyone with a Luna account, or to a comma-separated list. Unia keeps no data of its own; see [Users and separate storage](https://github.com/pranjallk1995/Luna_Sentia#users-and-separate-storage).

## Architecture

### Luna ecosystem

![Luna ecosystem architecture](docs/luna-ecosystem.svg)

Every Luna app is a React UI plus a FastMCP service on Luna Sentia's
`luna_sentia_network`: its data lives in Sentia's PostgreSQL, people sign in
through Sentia's `auth`, and model calls go to Sentia's Ollama. Visia's SigLIP 2 image
embeddings and Vibia's CLAP music embeddings run inside those apps instead. Orange lines are
Visia image URLs that other apps use: food images for Vita, room images for
Lumia, and cover art for Vibia. Grey dashed lines are planned: links into Fiora
(tax details from Lexia, transaction image and icon URLs from Visia). Luna Unia
is the one home for all of them, on port 42069: it checks which Luna stacks are
running and opens each one with the shared sign-in. The purple line is the mood and
beats of the track Vibia plays, which Lumia's lights follow.

| Component | Technology | Purpose |
| --- | --- | --- |
| UI (`luna-unia-ui`, `:42069`) | React + TypeScript (Vite), served by a Starlette gateway | App cards with live status; each running app's card opens it |
| Sign-in | Luna Sentia's `auth` | The shared `luna_sso` session, plus Unia's own allowlist |

## How detection works

Unia joins `luna_sentia_network` and asks every stack's services, all at once, whether
they answer (2 seconds at most each):

| Stack | Checks | Card opens |
| --- | --- | --- |
| Visia, Vita, Lumia, Fiora, Lexia, Vibia | `http://luna-<app>-ui:8501/_stcore/health` (kept by the React apps as an alias of `/health`), then `http://luna-<app>-mcp:8000/health` | The app's UI |
| Sentia | Adminer (`luna-sentia-adminer:8080`), sign-on (`luna-sentia-auth:8000/health`), and models (`luna-sentia-ollama:11434/api/version`) | Its user settings, with a second link to Adminer |

- **Running:** every check answers. The card opens the app.
- **`MCP not responding`** (or another service): the UI answers but a service behind it
  does not. The card still opens the app, which may show errors until that service is up.
- **Not running:** the UI does not answer. The card is dimmed and does not open.

The grid checks again every 15 seconds while the page is open; **Check again** checks
at once. Unia finds stacks by these network aliases, so it needs no Docker socket and
sees nothing else on the host. The list of stacks, their descriptions, and their
localhost ports is `LUNA_APPS` in `ui/config.py`; add a new app there.

## Start

Start [Luna Sentia](https://github.com/pranjallk1995/Luna_Sentia) first and wait until
its `auth` service is healthy; Unia needs no database. `../luna.sh start` starts Sentia,
every app, and Unia last.

Create a private `.env` from `.env.example`:

```dotenv
LUNAUNIA_ALLOWED_EMAILS=*
LUNAUNIA_URL_TEMPLATE=https://{app}.example.com
LUNA_SSO_URL=https://auth.example.com
LUNA_SSO_INTERNAL_URL=http://luna-sentia-auth:8000
```

- `LUNAUNIA_URL_TEMPLATE` is where the cards send the browser: `{app}` becomes `visia`,
  `vita`, `lumia`, `fiora`, `lexia`, or `vibia`. Leave it blank to open each app at its
  localhost port (18501 to 18506). `LUNA<APP>_URL`, such as `LUNAVIBIA_URL`, sets one
  app's address when it does not follow the pattern.
- Luna Sentia's card opens its user settings, `/admin` at `LUNA_SSO_URL`, and only the
  owner sees it. Its second link opens Adminer at `LUNASENTIA_URL` (default
  `http://localhost:19080`). Adminer listens only on localhost, so that link works only
  on the machine running Luna, and it goes while Adminer is down.
- Sign-in goes through Luna Sentia's single sign-on, as in every Luna app; see
  [Single sign-on](https://github.com/pranjallk1995/Luna_Sentia#single-sign-on). With
  `SENTIA_AUTH_COOKIE_DOMAIN` set, Unia must be reached under that domain, like every
  app: route a public hostname such as `unia.example.com` to `127.0.0.1:42069` in your
  tunnel.

```sh
docker compose up -d
```

- UI: <http://127.0.0.1:42069>

## Development workflow

```sh
docker compose up -d --build
docker compose exec ui python -m unittest discover -s tests -t .
```

Tests use a fake network (`httpx.MockTransport`), so they need no running stacks. The
UI follows the shared [UI style guide](UI_STYLE_GUIDE.md); it has no navbar, which the
guide lists under "Known deviations".
