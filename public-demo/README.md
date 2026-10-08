# Safe static production showcase

This is the **only directory** intended to be deployed publicly on Vercel.
Select **Framework Preset: Other** and **Root Directory: `public-demo`** with
no build command or production environment variables. It contains only local
HTML, CSS and JavaScript. The calculation happens in the visitor's browser
with hard-coded synthetic coordinates; there is **no network API** and no
persistent storage, real GPS ingestion, admin route, Redis, PostgreSQL or worker.

The Python FastAPI/PostGIS/Celery implementation remains in the repository as
a developer-run, unaudited business prototype. Do not expose that implementation
to public customers. Do not describe this deployed static UI as a live PostGIS
or FastAPI API. Its Haversine output illustrates the geofence concept.

Vercel must be configured for the `public-demo` root, not the repository root.
Review its response headers, test mobile and keyboard usage, and verify Vercel
project-to-GitHub main synchronization before promoting a preview. Restrict
hostnames to HTTPS. Enable platform spend limits/usage alerts and observability.

Rollback to the previous verified static deployment. The UI has no database
migrations and does not handle or retain personal data.

See ../docs/production-demo.md for backend security-release gates.

## Release-only deployment on Vercel

This repository deliberately disables automatic Git deployments with
`git.deploymentEnabled: false` in `public-demo/vercel.json`.

The `.github/workflows/release.yml` workflow deploys **only when a
non-prerelease GitHub Release with a version tag is published**, and checks
out that exact tag, verifies it came from main, confirms successful CI
for its commit and reruns static isolation tests. It then builds and
uploads only `public-demo/` with the pinned Vercel CLI.

### One-time bootstrap

1. Create/import the Vercel project with Root Directory `public-demo`
   and Framework Preset **Other**. An initial manual deployment through
   the Vercel UI is acceptable for project creation.
2. Configure the GitHub repo Variables `VERCEL_ORG_ID` and
   `VERCEL_PROJECT_ID` with your own Vercel account/project IDs.
3. Configure `VERCEL_TOKEN` as a masked GitHub Actions repository or
   production-environment **secret** (never commit or paste it into chat).
4. Protect the GitHub `production` environment with required reviewers,
   and restrict deployments to approved refs when your plan supports it.
5. Merge the release-only configuration after the initial project is
   created. Future commits to `main` will not deploy to Vercel.
6. Publish a **new GitHub release** (e.g. `v0.2.1`) pointing to the
   reviewed green `main` commit. The release event triggers deployment.
   An already-published `v0.2.0` does not trigger again retroactively.

Vercel Deploy Hooks are **not used**: their branch-oriented behavior
could deploy a newer commit than the selected release. The workflow
deploys the immutable release tag via the CLI instead.


### GitHub Actions CLI working directory

The Vercel project has **Root Directory = `public-demo`** configured in Vercel.
The GitHub Actions workflow must call `vercel pull`, `vercel build --prod`,
and `vercel deploy --prebuilt --prod` from the **repository root**, not from
`public-demo/`. Running from `public-demo/` applies the root directory twice
and fails with `.../public-demo/public-demo does not exist`.

Before uploading, CI checks that `.vercel/output/static/` contains the HTML,
CSS, and JS assets and that no serverless functions or services were built.
If the static-only guard fails, do not remove it just to ship: inspect Vercel's
framework and root-directory settings and repair the output configuration.

### Retrying an already-published release after a CI/CD configuration fix

GitHub Actions → **Deploy Published Release to Vercel** → **Run workflow**
(select branch `main`) → set `release_tag` to the existing published stable
release (for example `v0.2.1`). This manual replay deploys the exact
published release commit, not whatever code currently sits at `main`.

The replay checks that the tag is a stable published GitHub release, is
contained in `main` history, has green CI at that exact SHA, passes static
artifact tests, and produces a static-only Vercel build. It cannot deploy
unreleased commits. Routine pushes still do not deploy to Vercel.
