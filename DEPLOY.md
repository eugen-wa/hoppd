# Putting Hoppd online

## The simple way (2 minutes, no terminal, no tokens)

Your data is saved **in your browser** and survives every future update, so you
don't need any backend or tokens. Just host the file.

### 1. Put `index.html` on GitHub (in the browser)
1. Go to <https://github.com/new>.
2. Repository name: `type-in` → **Create repository**.
3. On the new page, click **“uploading an existing file.”**
4. Drag in **`index.html`** from your Drink-Tracker folder → **Commit changes.**

### 2. Host it on Render (in the browser)
1. <https://dashboard.render.com> → **New +** → **Static Site**.
2. Connect GitHub, pick the **`type-in`** repo.
3. Build command: *(leave empty)* · Publish directory: `.`
4. **Create Static Site** → open the URL. Done. ✅

That's it — two logins you already have, both in the browser. Free, no spin-down.

### Updating later
Edit `index.html` on GitHub (pencil icon) or re-upload it. Render redeploys
automatically and **your beers stay** — they live in your browser, not the files.

> Even faster with no accounts at all: drag the folder onto
> <https://app.netlify.com/drop> for an instant URL.

---

## Optional: cloud sync across devices (adds a backend)

Only do this if you want the same data on your phone *and* laptop, or to be safe
if you ever clear your browser. It stores data in a GitHub Gist via a small
Python server. Requires: a secret Gist, a token with the `gist` scope, and
deploying as a **Web Service** (`python serve.py`) instead of a Static Site,
with env vars `GITHUB_TOKEN`, `GIST_ID`, `GIST_FILE=hoppd-data.json`.
The files for this (`serve.py`, `render.yaml`, `requirements.txt`) are already in
this folder. Ask me and I'll walk you through it — but you don't need it to start.
