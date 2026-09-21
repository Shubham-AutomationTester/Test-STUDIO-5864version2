# Robots Directive Lab - STUDIO-5864 v2

A new deployable revision of the original QA site. The original UI, static fixtures, case IDs and generator are retained. Read **START-HERE.md** for the deployment steps.

## What changed

| Request | Implementation |
|---|---|
| Missing real response headers | Default deployment is a Free Python Render Web Service. `tools/serve.py` reads `qa/http-headers.json` and calls `send_header` for every entry on GET and HEAD. This does not rely on a Static Site importing `_headers` or on HTML displaying header text. |
| Correct bot-specific meta name | `config.json` now uses `SearchStax Crawler`, mapping confirmed from the user's instruction. Generated matching tags, scope fixtures, test cases and documentation use it. Intentional uppercase/lookalike cases remain. |
| Header precedence and repeated fields | Added H15-H34: generic/specific conflict directions, reversed order, foreign-bot isolation, case and exact-name matching, repeated identical/conflicting/split directives, empty field, combined-field comparison, and cross-source conflicts. |
| Scenario URLs as crawl starts | Dashboard area cards open filtered scenarios instead of copying suite seeds. Each table row and case dialog offers **Copy Start URL**. Original suite files remain for backward compatibility only, not as execution seeds for this run. |
| No invented product results | Manual results remain Not run. Proposed header policies are explicitly labeled and separated from known expectations. |

## Repository layout

```text
render.yaml                   Default: ONE Free Python Web Service
config.json                   Bot name, phase and optional site prefix
START-HERE.md                 Exact Render fields and curl examples
docs/                         Retained static dashboard, assets and isolated cases
source/cases.py               Original definitions plus 20 new header cases
tools/build.py                Regenerates fixtures, manifests, headers and TestRail CSV
tools/serve.py                Serves static files with genuine repeated HTTP headers
tools/verify.py               Live GET/HEAD, markup, isolation and repeated-field audit
qa/http-headers.json          List-of-pairs mapping; duplicate keys are NOT collapsed
qa/testrail-cases.csv          Updated 92-case TestRail import
qa/HEADER-PRECEDENCE.md        New-case inputs, proposed outcomes and limitations
qa/TEST-PLAN.md                Execution and evidence requirements
qa/scenario-start-urls.csv    Individual start paths and unique parent markers
hosting/render-static.yaml   Optional old-style static deployment; limited raw-field coverage
```

The prebuilt site is included. A normal Render build uses only Python's standard library. No packages need installation. `render.yaml` remains a Web Service definition after rebuilding, including lifecycle or bot-name changes.

## Why a server for static pages?

The pages themselves are still static HTML. Actual HTTP headers must be supplied by the responding server or hosting configuration. The old package used static-host header rules, which are not automatically activated by every deployment flow. This release sends headers from the included server, eliminating that setup dependency.

A JSON object with repeated header names would overwrite earlier values. The rules are lists of `[name, value]` pairs instead. No scope is interpreted by the server and no fixture varies by User-Agent. Both GET and HEAD use the same authored fields. `/cases/h03/` and `/cases/h03/index.html` have the same rules; query strings do not disable them. The no-trailing-slash route redirects to the directory before returning the fixture.

A hosting proxy can normalize case, combine fields or affect transport. Check the public response as well as the origin. `--require-repeated` verifies count, order and normalized field values for EVERY repeated fixture on GET and HEAD. Semantic equivalence of a combined field does not establish physical repeated-field coverage.

`X-QA-Fixture-Version: 2.0.0` identifies responses from this server. `/healthz` is a small readiness endpoint. Unknown paths return 404, not a misleading dashboard rewrite. Configuration, source, logs and files outside `docs/` are not publicly served. Access logs go to stdout and identify the User-Agent and headers sent. They are fixture access records, not SearchStax pipeline outcomes.

## Identity and precedence

Default robots meta name: `SearchStax Crawler`. This is supplied by QA; capture the full actual crawler HTTP User-Agent separately, including any version suffix. A full HTTP User-Agent is not automatically interchangeable with a supported meta-name mapping.

For a deliberately different configured bot, quote names containing spaces:

```bash
python3 tools/build.py --bot-name "SearchStax Crawler" --confirm-bot-token
```

The same configured name is used in scoped-header fixtures, e.g. `X-Robots-Tag: SearchStax Crawler: noindex`. Such fixtures test support for that exact syntax; their presence does not prove the product accepts it.

For header generic/specific precedence, the proposed policy is matching-specific over generic when both dimensions are explicit, matching independent restrictions aggregated, and unrelated scopes ignored. These proposals extend the meta examples and must be agreed with engineering. Partial-dimension and cross-source rules remain open. Google documentation describes Google's behavior, not SearchStax acceptance criteria.

## Lifecycle tests retained

Run these as separate deploy-and-crawl phases, not back-to-back before a crawl:

```bash
python3 tools/build.py --phase baseline
# Deploy, force-crawl U01/U02/U03/U04 one at a time and capture V1 evidence.
python3 tools/build.py --phase restricted
# Deploy, verify headers, force-crawl SAME scenario URL and capture V2 evidence.
python3 tools/build.py --phase restored
# Deploy, verify headers, force-crawl SAME scenario URL and capture V3 evidence.
```

Keep the baseline index during this test. Under noindex, V2 must not add/update the document. Whether existing V1 content is retained or removed is recorded separately; this ticket does not supply a deletion requirement. The restricted U02 header is removed by changing it to `index,follow` in the restored phase.

## Optional static-only hosting

The former static-host outputs remain available in `hosting/render-static.yaml`, `docs/_headers`, `netlify.toml` and `qa/render-header-rules.csv`. They combine same-name header values for host configuration. **Do not use them to claim separate physical repeated-header coverage.** Render Static Site users must explicitly configure/import the generated header rules and verify exact deployed paths. Root `render.yaml` intentionally does NOT use that approach.

GitHub Pages can display the static fixtures but does not apply this server or Netlify `_headers` rules. For this task, use the default Render Web Service. `robots.txt` must be served at the host root. Subdirectory/project hosting needs correct host-root rules; the generator retains its optional `--base-path` support.

## Limitations

This is a public synthetic QA fixture, not a production application server. Python's standard HTTP server implements only basic security checks. Do not store secrets, private/customer data or credentials in this site. There is no administration API, upload route or request-controlled header value. Render Free can spin down, and its local filesystem is ephemeral; export browser notes and use Render's stdout logs rather than treating local files as durable evidence.

Both previously published sites remain unchanged until you deploy the new package. No live Render hostname or SearchStax crawler was tested as part of creating this ZIP. See the included verification reports for exactly what was tested locally.

## Sources

- User-provided STUDIO-5864 requirements and follow-up instructions: https://searchstax.atlassian.net/browse/STUDIO-5864
- Render Web Services and PORT binding: https://render.com/docs/web-services
- Render Free behavior and limits: https://render.com/docs/free
- Render Blueprint configuration: https://render.com/docs/blueprint-spec
- Static response-header configuration: https://render.com/docs/static-site-headers
- Python header emission and server limitations: https://docs.python.org/3/library/http.server.html
- Background on scoped/repeated robots headers (Google-specific): https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag

External hosting mechanics checked September 21, 2026. Product acceptance comes from the supplied ticket text and confirmed product decisions, not external crawler behavior.
