# STUDIO-5864 Robots QA site v2 - start here

## Deploy the new site on Render Free

This release reuses the original static HTML/CSS/JavaScript site and Python fixture generator. A small Python HTTP server now supplies the actual response headers, including repeated X-Robots-Tag fields. It needs no third-party packages, database, Docker, or paid instance.

**Choose Web Service, not Static Site, for the complete v2 tests.**

1. Extract the ZIP. Upload the CONTENTS of `studio-5864-robots-qa-v2/` into a new GitHub repository. At the repository root you should see `render.yaml`, `config.json`, `tools/`, `source/`, and `docs/`.
2. In Render choose **New > Web Service** and connect that repository.
3. Set these values:

| Setting | Value |
|---|---|
| Name | Any available name, e.g. `studio5864-robots-v2` |
| Language | Python 3 |
| Branch | Your uploaded branch, normally `main` |
| Root Directory | Leave empty when the files above are at the repository root |
| Build Command | `python3 tools/build.py` |
| Start Command | `python3 tools/serve.py --bind 0.0.0.0` |
| Instance Type | **Free** |
| Health Check Path | `/healthz` |

There is no Publish Directory setting for this Web Service. The server reads Render's `PORT` environment variable and serves the committed `docs/` folder. Do not run `python -m http.server`; it would not apply the fixture headers.

4. Deploy and open the new hostname. On the dashboard select **Check this deployment**. Both checks must say MATCH before header testing.
5. Open **Test catalog**, choose one case, and click **Copy Start URL**. Paste that exact URL into the SearchStax crawler.

Alternative: **New > Blueprint**, connect the new repository, and deploy its root `render.yaml`. It defines one Free Python Web Service. Use a new service rather than attempting to change the existing Static Site's type. When hosting two test sites, deploy this package to each new service and verify each hostname independently.

## The important execution rule

**One scenario URL per crawl. Never use the dashboard, a suite page, or a target page as the Start URL.**

Examples (prepend the deployed site origin):

| Scenario | Start path | Purpose |
|---|---|---|
| B05 | `/cases/b05/` | `<meta name="SearchStax Crawler" content="noindex">` |
| H03 | `/cases/h03/` | Real `X-Robots-Tag: noindex, nofollow` |
| H07 | `/cases/h07/` | Two physical generic header fields |
| H15 | `/cases/h15/` | Generic block plus matching-specific allow |
| H17 | `/cases/h17/` | Generic allow plus matching-specific block |
| H24 | `/cases/h24/` | Repeated identical `noindex` |
| H27 | `/cases/h27/` | Three fields: generic allow and split specific restrictions |
| R06 | `/cases/r06/` | Allowed entry -> robots-blocked parent with header restrictions |

Use a dedicated QA index and clean crawl queue; disable sitemap/import discovery and additional Start URLs. Keep the complete scenario path in scope, including its unique children. Suggested depth is at least 5 and item budget at least 500. For independent comparisons, reset through supported product controls; do not clear unrelated data. Repeat selected cases with Ignore robots.txt OFF and ON in separate clean runs.

## Verify genuine response headers

Replace only the sample hostname below:

```bash
curl --http1.1 -sS -L -D - -o /dev/null "https://YOUR-SITE.onrender.com/cases/h03/"
```

The final response should be HTTP 200 and contain:

```http
X-QA-Fixture-Version: 2.0.0
X-Robots-Tag: noindex, nofollow
```

For H15:

```bash
curl --http1.1 -sS -L -D - -o /dev/null "https://YOUR-SITE.onrender.com/cases/h15/"
```

At the origin, the response has TWO distinct fields:

```http
X-Robots-Tag: noindex,nofollow
X-Robots-Tag: SearchStax Crawler: index,follow
```

A proxy can combine fields. Browser Fetch also presents combined values. Use the strict verifier against the final public hostname; it fails the raw-field check when instances are combined, reordered or lost. That is a fixture/transport prerequisite failure, not automatically a SearchStax defect.

```bash
python3 tools/verify.py "https://YOUR-SITE.onrender.com" --require-repeated --timeout 60
```

A free Render Web Service can sleep after idle time. Open the homepage and wait until the actual QA page/health check responds before starting the crawl. Do not classify a cold-start timeout or platform loading page as a robots bug.

## Local preview

```bash
python3 tools/serve.py --port 8000
```

Open `http://localhost:8000/`. From another terminal:

```bash
python3 tools/verify.py http://localhost:8000 --require-repeated
```

Localhost is not reachable by a hosted SearchStax crawler. Deploy for crawler execution.

## Scope and expectations

There are **92 scenarios**: all 72 original cases plus 20 new header cases H15-H34. The default meta name is now **SearchStax Crawler**. The header server is not a mock crawler: it sends identical configured fixtures to all User-Agents and never computes SearchStax pass/fail outcomes.

Meta-specific precedence is covered by the original requirements. Header-specific precedence, repeated-field conflict resolution and header/meta conflicts without a specified contract are labeled **Confirm**, with proposed outcomes where useful. Approve the policy in Jira before using those outcomes as release-blocking assertions.

All actual crawler results are **Not run** until you execute SearchStax. Local fixture-verification reports do not verify deployed Render hosts or product behavior.

More detail: `README.md`, `qa/HEADER-PRECEDENCE.md`, `qa/TEST-PLAN.md`, and `qa/testrail-cases.csv`.
