# Local validation summary - v2.0.0

- 212 generated baseline fixture URLs plus the host-root robots check: 213 fixture checks, zero failures. Headers were inspected on GET and HEAD.
- 142 additional method/path checks cover configured header aliases and query strings; expected repeated-field values and order were preserved.
- All 72 original IDs were retained. Meta, link and robots behavioral inputs/graphs and host-root robots rules were compared with v1 and were unchanged.
- New bot meta tags use SearchStax Crawler; the legacy exact name="searchstax" is absent from generated HTML.
- 20 new header cases produce a 92-case TestRail export and 92 individual Start URLs; all actual product results are Not run.
- Rebuilds tested baseline, restricted, restored and quoted bot names; the default Render Blueprint remains a Free Python Web Service. Project-prefix graph/root-robots generation was also checked.
- Dashboard controls, header-check presentation, scenario dialogs, case filters, initial result state and mobile overflow checks passed in an offline Chromium rendering environment. Direct browser localhost navigation was blocked by environment policy, so browser requests were fulfilled using locally measured HTTP responses. Independent direct HTTP checks were not mocked.
- Public Render hosts tested: 0. SearchStax crawls executed: 0. This report validates the package, not deployment or product acceptance.

See fixture-verification.json, v2-verification.json, rebuild-verification.json, browser-verification.json and LOCAL-HTTP-HEADERS.txt for the evidence.
