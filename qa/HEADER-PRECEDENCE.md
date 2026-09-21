# HTTP header precedence and repeated-field tests - v2

Use each individual scenario Start URL. Prepend your deployed hostname. Never use the dashboard or a suite as the Start URL.

The default matching identity is `SearchStax Crawler`. All header strings below are actual server output, not HTML meta substitutes. The origin sends multiple fields separately, in the listed order. Confirm public delivery with `tools/verify.py BASE_URL --require-repeated` before grading physical repeated-header cases.

## Acceptance versus proposal

Ready cases have authored expectations. For Confirm cases, the expected result is a product decision, and any candidate result below is explicitly PROPOSED. The ticket describes specific-over-generic precedence for HTML meta; it does not fully define header scope/source aggregation. Confirm those rules in Jira before assigning pass/fail. This suite never computes a fake crawler result.

Proposed general policy: matching-specific over generic when both dimensions are explicit; ignore unrelated scopes; aggregate independent same-scope restrictions; resolve same-scope conflicts consistently. H29 leaves the child outcome open because whole-scope replacement and per-dimension override differ. H33/H34 leave cross-source outcomes open.

H08 is a text extraction control pair: its parent has no header; the allowed text may index, but the restricted text must not index. Establish text parser support before grading.

## Cases

| Case / Start path | Actual header field(s), top to bottom | Meta input | Parent index / child eligible | Readiness |
|---|---|---|---|---|
| H01 `/cases/h01/` | `X-Robots-Tag: noindex` | None | No / Yes | Ready |
| H02 `/cases/h02/` | `X-Robots-Tag: nofollow` | None | Yes / No | Ready |
| H03 `/cases/h03/` | `X-Robots-Tag: noindex, nofollow` | None | No / No | Ready |
| H04 `/cases/h04/` | `X-Robots-Tag: NOINDEX, NOFOLLOW` | None | No / No | Ready |
| H05 `/cases/h05/` | `X-Robots-Tag: noindex nofollow` | None | No / No | Ready |
| H06 `/cases/h06/` | `x-RoBoTs-TaG: noindex` | None | No / Yes | Ready |
| H07 `/cases/h07/` | `X-Robots-Tag: noindex`<br>`X-Robots-Tag: nofollow` | None | PROPOSED: No / No | Confirm |
| H08 `/cases/h08/` | None on parent; see target fixtures | None | Yes / Yes | Conditional |
| H09 `/cases/h09/` | `X-Robots-Tag: noindex` | &lt;meta name="robots" content="nofollow"&gt; | Decision / lifecycle check / Decision / lifecycle check | Confirm |
| H10 `/cases/h10/` | `X-Robots-Tag: noindex,nofollow` | &lt;meta name="robots" content="index,follow"&gt; | Decision / lifecycle check / Decision / lifecycle check | Confirm |
| H11 `/cases/h11/` | `X-Robots-Tag: index,follow` | &lt;meta name="robots" content="noindex,nofollow"&gt; | Decision / lifecycle check / Decision / lifecycle check | Confirm |
| H12 `/cases/h12/` | `X-Robots-Tag: googlebot: noindex,nofollow` | None | PROPOSED: Yes / Yes | Confirm |
| H13 `/cases/h13/` | `X-Robots-Tag: SearchStax Crawler: noindex,nofollow` | None | PROPOSED: No / No | Confirm |
| H14 `/cases/h14/` | `X-Robots-Tags: noindex,nofollow` | None | Yes / Yes | Ready |
| H15 `/cases/h15/` | `X-Robots-Tag: noindex,nofollow`<br>`X-Robots-Tag: SearchStax Crawler: index,follow` | None | PROPOSED: Yes / Yes | Confirm |
| H16 `/cases/h16/` | `X-Robots-Tag: SearchStax Crawler: index,follow`<br>`X-Robots-Tag: noindex,nofollow` | None | PROPOSED: Yes / Yes | Confirm |
| H17 `/cases/h17/` | `X-Robots-Tag: index,follow`<br>`X-Robots-Tag: SearchStax Crawler: noindex,nofollow` | None | PROPOSED: No / No | Confirm |
| H18 `/cases/h18/` | `X-Robots-Tag: SearchStax Crawler: noindex,nofollow`<br>`X-Robots-Tag: index,follow` | None | PROPOSED: No / No | Confirm |
| H19 `/cases/h19/` | `X-Robots-Tag: noindex`<br>`X-Robots-Tag: googlebot: index,follow` | None | PROPOSED: No / Yes | Confirm |
| H20 `/cases/h20/` | `X-Robots-Tag: index,follow`<br>`X-Robots-Tag: googlebot: noindex,nofollow` | None | PROPOSED: Yes / Yes | Confirm |
| H21 `/cases/h21/` | `X-Robots-Tag: SEARCHSTAX CRAWLER: NoInDeX, NoFoLlOw` | None | PROPOSED: No / No | Confirm |
| H22 `/cases/h22/` | `X-Robots-Tag: SearchStax Crawler-lookalike: noindex,nofollow` | None | PROPOSED: Yes / Yes | Confirm |
| H23 `/cases/h23/` | `X-Robots-Tag: nofollow`<br>`X-Robots-Tag: noindex` | None | PROPOSED: No / No | Confirm |
| H24 `/cases/h24/` | `X-Robots-Tag: noindex`<br>`X-Robots-Tag: noindex` | None | No / Yes | Ready |
| H25 `/cases/h25/` | `X-Robots-Tag: index,follow`<br>`X-Robots-Tag: noindex,nofollow` | None | PROPOSED: No / No | Confirm |
| H26 `/cases/h26/` | `X-Robots-Tag: noindex,nofollow`<br>`X-Robots-Tag: index,follow` | None | PROPOSED: No / No | Confirm |
| H27 `/cases/h27/` | `X-Robots-Tag: index,follow`<br>`X-Robots-Tag: SearchStax Crawler: noindex`<br>`X-Robots-Tag: SearchStax Crawler: nofollow` | None | PROPOSED: No / No | Confirm |
| H28 `/cases/h28/` | `X-Robots-Tag: SearchStax Crawler: nofollow`<br>`X-Robots-Tag: SearchStax Crawler: noindex`<br>`X-Robots-Tag: index,follow` | None | PROPOSED: No / No | Confirm |
| H29 `/cases/h29/` | `X-Robots-Tag: noindex,nofollow`<br>`X-Robots-Tag: SearchStax Crawler: index` | None | PROPOSED: Yes / Decision / lifecycle check | Confirm |
| H30 `/cases/h30/` | `X-Robots-Tag: noindex,nofollow, SearchStax Crawler: index,follow` | None | PROPOSED: Yes / Yes | Confirm |
| H31 `/cases/h31/` | `X-Robots-Tag: noindex,nofollow`<br>`X-Robots-Tag: SearchStax Crawler: index,follow`<br>`X-Robots-Tag: googlebot: noindex,nofollow` | None | PROPOSED: Yes / Yes | Confirm |
| H32 `/cases/h32/` | `X-Robots-Tag: (empty value)`<br>`X-Robots-Tag: noindex` | None | No / Yes | Ready |
| H33 `/cases/h33/` | `X-Robots-Tag: SearchStax Crawler: index,follow` | &lt;meta name="robots" content="noindex,nofollow"&gt; | PROPOSED: Decision / lifecycle check / Decision / lifecycle check | Confirm |
| H34 `/cases/h34/` | `X-Robots-Tag: noindex,nofollow` | &lt;meta name="SearchStax Crawler" content="index,follow"&gt; | PROPOSED: Decision / lifecycle check / Decision / lifecycle check | Confirm |

## Notes for H15-H34

**H15** - Proposed: a matching scoped header overrides generic directives when both dimensions are explicit. Parent and child index. Confirm that the ticket-specific meta precedence also applies to HTTP headers.

**H16** - Same policy and outcome as H15, with physical field order reversed. Detects last-header-wins or scope leakage. Confirm header precedence first.

**H17** - Proposed: the matching scoped noindex/nofollow wins; process the parent, do not add/update it, and do not enqueue its child. Confirm header precedence first.

**H18** - Reverse of H17. A later generic allow must not overwrite the matching scoped restriction under the proposed policy.

**H19** - Proposed with scoped-header support: ignore googlebot for SearchStax; keep generic noindex. Parent does not index, ordinary child remains eligible.

**H20** - Proposed with scoped-header support: the googlebot restriction must not leak into SearchStax decisions. Both parent and child remain eligible.

**H21** - Proposed: match the configured SearchStax Crawler name and directive tokens case-insensitively. Confirm the bot-scoped header parser contract.

**H22** - Proposed: do not match SearchStax Crawler-lookalike to SearchStax Crawler by substring. No generic restrictions are present.

**H23** - Reverse of H07. Proposed: combine independent restrictions from both generic field instances. Both noindex and nofollow apply regardless of field order.

**H24** - Identical repeated noindex must not be dropped or cause a failure. Parent can process but cannot add/update; its ordinary child remains eligible. Verify two physical fields.

**H25** - Proposed same-scope conflict rule: restrictive directives win. Confirm rather than assuming first/last-field precedence; compare H26.

**H26** - Reverse of H25. Proposed restrictive-wins result is unchanged. A different agreed policy must be documented for both cases.

**H27** - Proposed: collect BOTH matching scoped fields before applying precedence. Do not let one specific field overwrite the other. Three physical fields are required.

**H28** - Reverse ordering of H27. Tests aggregation and scope precedence together. Three physical fields must reach the client.

**H29** - Parent index is allowed under either proposed specific-precedence interpretation. Child depends on the unresolved policy: per-dimension override keeps generic nofollow; whole-scope replacement permits follow. Record the agreed choice.

**H30** - Combined-field counterpart of H15. Proposed: parse scope boundaries correctly and apply matching-specific precedence. Confirm comma-separated multi-scope syntax; this is NOT a physical repeated-header test.

**H31** - Proposed: matching allow overrides generic block; the trailing googlebot block is irrelevant. Detects scope leakage across three repeated fields.

**H32** - Robustness: the empty field contributes no directive and must not hide the valid noindex. Parent does not add/update; its child remains eligible. Verify both physical fields, including the empty one.

**H33** - Cross-source AND cross-scope conflict. The ticket does not settle whether specific scope outranks the other source or whether header/meta restrictions are merged. Record the exact product policy; no outcome is invented.

**H34** - Reverse source placement of H33. Confirm source-versus-scope precedence; do not infer it from Google behavior or the meta-only examples.

## Execution steps

1. Inspect the final GET response and confirm the exact field values/count/order. Keep verifier/browser requests outside the crawler evidence time window.
2. Start a fresh dedicated crawl from only the scenario URL, with its child path in scope. Capture the actual HTTP User-Agent.
3. Verify parent processing and index add/update separately; noindex must not be misread as a crawl prohibition.
4. Inspect the child queue provenance and unique document marker. Missing search results alone do not prove nofollow.
5. Compare order-reversal pairs in separate clean runs; repeat selected cases with Ignore robots.txt OFF and ON. Page-level outcomes must not change when robots.txt does not block the page.
6. Keep all actual results Not run until executed. Confirm cases require an agreed product rule and evidence.

Source: https://searchstax.atlassian.net/browse/STUDIO-5864 and the user-provided v2 change request. No current Jira comment contents were assumed.
