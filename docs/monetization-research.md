# Monetisation research

Researched 2026-09-19 against providers' own programme pages and terms. This is an
internal working document, not published to the site. The site's public,
reader-facing version of this information is `/about/disclosure/`.

Every figure below came from an official source. Anything that could not be confirmed
from a primary source is marked **UNVERIFIED** and should not be relied on.

---

## 1. The ranking that actually matters

The owner's stated preference order is cash first, credit near-last. That single
constraint reorders the entire field, because most compute-provider programmes pay
credit, and credit is only spendable with the company that issued it — which also makes
it the payout most likely to bias a recommendation.

| Rank | Programme | Payout | Recurring | Gate | Why it ranks here |
| --- | --- | --- | --- | --- | --- |
| 1 | **Vast.ai referral** | Cash (75% of value) or credit (100%) | Yes, life of the referred account, 3% of spend | Accrues immediately; **cash-out** requires earnings to exceed that account's own lifetime instance spend | Only on-topic programme paying real cash, and its terms explicitly permit disclosed comparison content. Use a dedicated account (see below) |
| 2 | **DigitalOcean affiliate** (Awin) | Cash | Yes, 10%/month for 12 months | Awin approval, ~30 days | Real recurring cash, on-topic via GPU Droplets |
| 3 | **RunPod affiliate** (tier 2) | Cash via PartnerStack, or credit | Yes, 10% for 6 months | **25 paying referrals first** | Best rate found, but it is a destination, not a starting point |
| 4 | **Namecheap** (Impact/CJ) | Cash | No, one-time | Network signup | 20–35%, easy, but off-topic for this site's subject matter |
| 5 | **RunPod referral** (tier 1) | **Credit only**, 90-day expiry | Partly, 6 months | Referee spends $10 | Only worth activating as the on-ramp to tier 2 |

### Credit-only, therefore deprioritised

RunPod tier 1, DigitalOcean's in-app referral ($25 credit), Hetzner Cloud (€10, and
gated behind the referrer already having three paid invoices), Genesis Cloud.

### Confirmed to have no programme

Checked directly or via an official staff statement, not inferred from silence:
OpenRouter, Together AI, Modal, Replicate, Fal, Cloudflare (no consumer programme;
Registrar sells domains at cost so there is structurally no margin), Fly.io, Render,
Porkbun (discontinued), Lambda (private B2B negotiation only).

Third-party "affiliate directory" sites list plausible-looking terms for several of
these. Those listings appear to be fabricated. Do not trust them.

### Needs a human to check

- **Vultr** — official pages returned 403 to automated fetch and third-party sources conflict wildly. Requires signing in at `my.vultr.com` to confirm. **UNVERIFIED.**
- **Backblaze B2** — a programme probably exists, but rate, cookie window and whether B2 (as opposed to Computer Backup) qualifies could only be found on third-party trackers. **UNVERIFIED.**

---

## 2. Programme terms worth knowing before writing anything

- **Vast.ai** explicitly permits disclosed comparison and review content on a website. It forbids paid search or display advertising on Vast.ai brand terms. This site does no paid advertising, so there is no conflict.
- **DigitalOcean** forbids bidding on its branded keywords. Same conclusion.
- **Hetzner** forbids using the referral link in paid advertising.
- **RunPod** is silent on this point in its published terms. **UNVERIFIED** — assume the same rules apply.

Nothing in any of these terms restricts writing an honest comparison that concludes
against the provider, which is worth confirming before publishing one.

---

## 3. What the SERP research changed

Competitive analysis of eight candidate topics produced three findings that reshaped
the content plan more than the referral research did.

**Three ideas killed outright:**

- *Cheapest GPU aggregator page.* Several funded aggregators run continuous scraping across dozens of providers. A zero-authority static page cannot compete and would need a permanently maintained scraper to draw level.
- *Monero mining profitability.* RandomX is CPU-oriented and GPU-resistant, so the framing that would connect it to this site is technically wrong. Entrenched live-difficulty calculators do it better, and it is a volatile-asset profitability claim.
- *AI crawler robots.txt guide.* `github.com/ai-robots-txt/ai.robots.txt` owns this space and is actively maintained.

**The reframing that mattered.** The gap in GPU-pricing content is not the prices — it
is the reasoning that turns prices into a decision. Every existing calculator is
published by a vendor selling one of the two answers, and none disclose the throughput
and utilisation assumptions that actually decide the result. That became
`/compute/gpu-rental-vs-inference-api/`.

**The honest strategic conclusion.** This site will not outrank funded aggregators on
commercial queries. Its realistic distribution is citation by AI answer systems for
narrow, dated, methodology-transparent pages — which is what the research says those
systems favour, and what none of the eight SERPs currently contain.

---

## 4. Revenue expectations, stated plainly

Setting an honest baseline so that later results can be judged against something.

| Channel | Realistic near-term | Notes |
| --- | --- | --- |
| Crypto donations | ~$0 | Donation addresses convert at negligible rates even at high traffic |
| Referral commissions | $0 until there is traffic | Needs qualified clicks, which need visitors |
| Paid data or API | $0 | Nobody has asked to buy anything; building it first would be a liability |
| Sponsorship | $0 | Requires an audience a sponsor wants |

The bottleneck is not the payment mechanism. It is traffic and trust. It is far more
tempting to spend a weekend integrating a payment protocol than producing something
worth paying for, because the first has a visible finish line.

**Therefore: no payment infrastructure until someone asks to pay for something.**

---

## 5. Crypto payment rails

Full public write-up at `/crypto/agent-payments/`. The operative conclusion:

**Every agent payment protocol — x402, L402, AP2, ACP — requires a server.** Something
must return the 402, verify payment, and gate the response. Static hosting does none of
these. The minimum viable version is a Cloudflare Worker in front of static content,
which is a real backend with real obligations.

If this is ever built, x402 is the one to reach for: lowest integration cost, least
infrastructure, and actually carrying production traffic.

---

## 6. What to do next, in order

1. **Publish.** Nothing is measurable until the site is live and indexed.
2. **Activate Vast.ai.** Free, cash-paying, on-topic, and its terms bless the use case. Highest value per minute of owner time by a wide margin.
3. **Apply to DigitalOcean via Awin.** Free, recurring cash, ~30-day approval, so start the clock early.
4. **Wait for data.** Do not add referral programmes to pages that have no traffic. Measure which pages get qualified clicks first.
5. **Spend on the measured GPU benchmark** only once a page is drawing traffic. It costs real money and is the most defensible page available, so it should be funded by evidence rather than optimism.

Explicitly **not** recommended: creating accounts for credit-only programmes, buying
tools, paying for backlinks, or registering additional domains.
