# GitHub Pages

## What runs in the browser

The static site (`web/index.html`) provides:

- Product overview
- **Client-side SPDX demo** (`web/demo.js`) — pattern match only
- Links to GitHub and desktop build instructions

## What does NOT run on Pages

- Python / sklearn TF-IDF scanning  
- SWI-Prolog MQI  
- Full project folder analysis  

Those require the **desktop application**.

## Deploy

Workflow: `.github/workflows/deploy-pages.yml`  
Publishes the `web/` directory on push to `main`.

Enable Pages in repo settings: **Source → GitHub Actions**.

## Local preview

Open `web/index.html` in a browser or use any static server.
