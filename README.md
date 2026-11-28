# Luna Unia

![Docker required](https://img.shields.io/badge/Docker-required-2496ED?logo=docker&logoColor=white)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Luna Sentia required](https://img.shields.io/badge/Luna_Sentia-required-6C5CE7?logo=docker&logoColor=white)
![Status: v2.0.1](https://img.shields.io/badge/Status-v2.0.1-2EA043)

**One home for every Luna app.** Unia shows a card for each Luna app, says which ones are running, and opens them
with the shared sign-in, so you never sign in twice.

<p align="center">
  <a href="docs/luna-unia-showcase.mp4"><img src="docs/luna-unia-showcase.webp" alt="From Google sign-in to the Luna Unia home, then into the apps" width="900"></a>
</p>

## What it does

- **Live status:** each app is **running**, **not running** (dimmed), or running with a service not answering. It
  checks every 15 seconds, or at once with **Check again**.
- **One click in:** a running app's card opens it, already signed in.
- **Only what you can use:** apps the owner hid are left out, and only the owner sees Sentia and Luna Socia.
- **Nothing stored:** a UI only, with no database, no MCP server and no model calls. It never reads the apps' data,
  only whether they answer.

<p align="center">
  <img src="docs/showcase.png" alt="Luna Unia showing all seven Luna stacks running, each card linking to its app" width="900">
</p>

## Quickstart

Clone Unia and the apps you want beside [Luna Sentia](https://github.com/pranjallk1995/Luna_Sentia), then start
everything. On one machine you need no `.env`:

```sh
git clone https://github.com/pranjallk1995/Luna_Sentia.git
git clone https://github.com/pranjallk1995/Luna_Unia.git
git clone https://github.com/pranjallk1995/Luna_Visia.git        # and any other Luna_<App> you want
./Luna_Sentia/luna.sh start
```

Open <http://localhost:42069> and sign in as Sentia's owner. Who else may use Unia, and a public address, are in
[Getting started](https://github.com/pranjallk1995/Luna_Unia/wiki/Getting-Started).

## Documentation

The [wiki](https://github.com/pranjallk1995/Luna_Unia/wiki) has the full reference:

| Page | What's in it |
| --- | --- |
| [Home](https://github.com/pranjallk1995/Luna_Unia/wiki) | What Unia is |
| [Getting started](https://github.com/pranjallk1995/Luna_Unia/wiki/Getting-Started) | Setup, `.env`, sign-in |
| [Architecture](https://github.com/pranjallk1995/Luna_Unia/wiki/Architecture) | How detection works, who sees what, adding an app |
| [Development](https://github.com/pranjallk1995/Luna_Unia/wiki/Development) | Development workflow and tests |

The UI follows [UI_STYLE_GUIDE.md](UI_STYLE_GUIDE.md).

## Releases and development

Releases are on the [Releases page](https://github.com/pranjallk1995/Luna_Unia/releases). To update: `git pull`, then
`./Luna_Sentia/luna.sh start`. To run your local code and reload it as you edit:
`./Luna_Sentia/luna.sh start --build --watch unia`.
