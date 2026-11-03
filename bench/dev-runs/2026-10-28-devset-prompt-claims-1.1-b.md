# ARGUS benchmark, devset split (16 outputs)

Ground truth: blind human coding (M5, unsupported assertions), frozen 10 Aug 2026.
Engine flag = at least one claim verified as UNSUPPORTED or CONTRADICTED.

| | Human found unsupported claims | Human found none |
|---|---|---|
| Engine flagged | 6 | 3 |
| Engine did not flag | 2 | 5 |

Human-quoted unsupported claims also flagged by the engine: 2 of 3.
Tokens: 37,173 in, 25,346 out.

Development split: used to inspect and tune. Not a reportable accuracy figure.

## Item by item

### S22 1a6d6f70: human M5 = 1, engine flags = 3
- Human (matched): “extremely elevated even by high-growth software standards”
- Engine UNSUPPORTED: “a 200% year-over-year revenue increase is exceptional by most standards”. The 200% arithmetic is correct, but calling it "exceptional by most standards" relies on outside benchmarks the source does not give.
- Engine UNSUPPORTED: “A 50x revenue multiple is extremely elevated even by high-growth software standards”. This compares the multiple with market norms that the source does not provide, and it sits awkwardly with the output's own point that comparable multiples are missing.
- Engine CONTRADICTED: “the evidence provides only a single historical data point on revenue”. The source gives two revenue figures (40 million and 120 million), not one, though it does cover only a single year of growth.

### S24 f3c75584: human M5 = 1, engine flags = 2
- Human (MISSED): “gross profit”
- Engine UNSUPPORTED: “No material case-specific uncertainty affects this conclusion.”. The source does not define serving costs or the user measure, and it does not say whether users grew evenly over the year, so per-user figures depend on assumptions; that said, the directional conclusion is robust.
- Engine UNSUPPORTED: “no ambiguity exists in the definitions of revenue, serving costs, or user count as provided”. The source provides no definitions at all, including no currency and no indication of whether users are active, registered, or measured at period end.

### S20 56a02f7f: human M5 = 0, engine flags = 2
- Engine CONTRADICTED: “The proposed 700-share position does NOT comply with the 2% maximum-risk-per-trade mandate.”. 700 shares × 2.00 risk per share = 1,400, which is under the 1,600 cap; the output's own later reasoning reverses this, but the headline verdict is never removed, so the output is internally contradictory.
- Engine CONTRADICTED: “It exceeds the permitted risk by $400, or 25% above the allowed limit.”. Actual risk is 1,400, which is 200 below the limit, not 400 above it; the output later implicitly corrects this but never retracts the figure.

### S03 077ea1ba: human M5 = 0, engine flags = 5
- Engine UNSUPPORTED: “This is a concrete, contemporaneous demand-side catalyst with a documented timing match to the price move.”. The source ties the purchase only to an acceleration of a move that was already under way, not to the whole price move.
- Engine UNSUPPORTED: “The supplied evidence refutes the claim that the rate cut alone is the best-supported explanation.”. The evidence weighs against the claim, but 'refutes' overstates what circumstantial timing evidence can show.
- Engine UNSUPPORTED: “A fully anticipated cut that left real yields and the dollar unchanged provides minimal explanatory power.”. The source gives a 97% probability, not full anticipation, and says the dollar and real yields were only 'broadly' unchanged, so the output overstates both.
- Engine UNSUPPORTED: “The central bank gold purchase, confirmed within the same window and followed by an acceleration of the move, is the better-supported explanation on this evidence.”. The purchase plausibly explains the acceleration, but the source does not establish it as the explanation for the whole rally.
- Engine UNSUPPORTED: “No material case-specific uncertainty affects this conclusion.”. The move began before the purchase was confirmed, so a real gap remains in explaining it.

### S22 c6035c6e: human M5 = 1, engine flags = 4
- Human (matched): “extremely elevated even for high-growth software companies”
- Engine UNSUPPORTED: “A 50x revenue multiple is extremely elevated even for high-growth software companies.”. This compares the multiple to market norms that the scenario does not provide.
- Engine UNSUPPORTED: “which is exceptional by any standard”. This implicitly compares the growth with external benchmarks that the scenario does not supply.
- Engine UNSUPPORTED: “High-growth AI software companies are frequently valued on forward-looking metrics rather than current revenue.”. This is an outside claim about market valuation practice that the scenario does not contain.
- Engine UNSUPPORTED: “the premium typically accorded to AI software businesses”. This asserts a sector valuation norm drawn from outside the scenario.

### S09 c73dcac4: human M5 = 0, engine flags = 0

### S04 de9a1305: human M5 = 1, engine flags = 2
- Engine UNSUPPORTED: “A 200% TVL increase signals that significantly more capital is being deployed into the protocol, reflecting growing utility, user trust, and economic activity.”. The 200% figure is from the source, but attributing it to growing utility, user trust and economic activity is a causal reading the scenario does not give, and the output itself later raises mercenary capital as an alternative.
- Engine UNSUPPORTED: “This divergence is a classic signal used in DeFi valuation analysis to identify potential mispricings.”. This is a claim about market practice from outside the scenario, which says nothing about how analysts use such divergences.

### S11 e0ab033e: human M5 = 1, engine flags = 2
- Engine UNSUPPORTED: “No other announcement occurred, so the guidance cut is the clear causal driver.”. The source rules out other announcements but does not attribute the decline to the guidance cut specifically, since the beat came in the same release; 'clear causal driver' goes beyond the evidence.
- Engine UNSUPPORTED: “The supplied evidence refutes the claim.”. The evidence makes a rational explanation plausible but does not refute irrationality, and the output itself later concedes it cannot tell whether 11% overshoots.

### S13 414aae48: human M5 = 0, engine flags = 2
- Engine UNSUPPORTED: “simultaneously boosted both the equity index (via improved export revenue expectations) and the currency (via improved terms of trade)”. The scenario makes copper a plausible common driver but does not establish that it caused either move, so presenting this as the explanation goes beyond the evidence.
- Engine UNSUPPORTED: “The common external driver (copper price) is a confounding factor that undermines any causal claim running from equities to currency.”. The output states as fact that copper is a confounder, but the scenario only makes this plausible; elsewhere the output itself hedges it as 'plausibly' explaining both moves.

### S07 d713df3d: human M5 = 0, engine flags = 0

### S10 4a02c099: human M5 = 0, engine flags = 0

### S20 c10881e2: human M5 = 0, engine flags = 0

### S12 053c71e1: human M5 = 1, engine flags = 0

### S23 37497ace: human M5 = 1, engine flags = 1
- Engine UNSUPPORTED: “suggesting that fundamental earnings performance is a primary driver of the concentrated returns”. Aligned contribution shares show that fundamentals matter, but they do not establish that fundamentals are the primary driver, which goes beyond the 'material' claim the evidence supports.

### S19 98a4154e: human M5 = 0, engine flags = 0

### S24 9526fa87: human M5 = 1, engine flags = 0
