# ARGUS benchmark, devset split (16 outputs)

Ground truth: blind human coding (M5, unsupported assertions), frozen 10 Aug 2026.
Engine flag = at least one claim verified as UNSUPPORTED or CONTRADICTED.

| | Human found unsupported claims | Human found none |
|---|---|---|
| Engine flagged | 6 | 3 |
| Engine did not flag | 2 | 5 |

Human-quoted unsupported claims also flagged by the engine: 2 of 3.
Tokens: 37,173 in, 25,761 out.

Development split: used to inspect and tune. Not a reportable accuracy figure.

## Item by item

### S22 1a6d6f70: human M5 = 1, engine flags = 2
- Human (matched): “extremely elevated even by high-growth software standards”
- Engine UNSUPPORTED: “is exceptional by most standards”. This compares the growth with outside norms that the scenario does not provide.
- Engine UNSUPPORTED: “A 50x revenue multiple is extremely elevated even by high-growth software standards”. The scenario gives no market or peer multiples, so this comparison rests on outside information.

### S24 f3c75584: human M5 = 1, engine flags = 2
- Human (MISSED): “gross profit”
- Engine UNSUPPORTED: “No material case-specific uncertainty affects this conclusion.”. The output overstates certainty: the source does not define how users are counted relative to the annual revenue, although the direction of the conclusion likely holds either way.
- Engine UNSUPPORTED: “no ambiguity exists in the definitions of revenue, serving costs, or user count as provided”. The source gives no definitions at all, so the claim that there is no ambiguity is not established.

### S20 56a02f7f: human M5 = 0, engine flags = 2
- Engine CONTRADICTED: “The proposed 700-share position does NOT comply with the 2% maximum-risk-per-trade mandate.”. The final verdict reverses the output's own correct reasoning: 700 shares risk 1,400, which is under the 1,600 cap, so the position complies.
- Engine CONTRADICTED: “It exceeds the permitted risk by $400, or 25% above the allowed limit.”. The source figures give 1,400 of risk, which is 200 below the cap, not 400 above it; the $400 and 25% figures have no basis in the case.

### S03 077ea1ba: human M5 = 0, engine flags = 1
- Engine UNSUPPORTED: “No material case-specific uncertainty affects this conclusion.”. The source leaves real gaps, including the split of the move before and after the purchase and the 'immediately after' limit on the yield and dollar data, so claiming no uncertainty goes too far.

### S22 c6035c6e: human M5 = 1, engine flags = 4
- Human (matched): “extremely elevated even for high-growth software companies”
- Engine UNSUPPORTED: “which is exceptional by any standard”. This is a comparative judgement against outside norms that the scenario does not provide.
- Engine UNSUPPORTED: “High-growth AI software companies are frequently valued on forward-looking metrics rather than current revenue.”. This is a claim about market practice from outside the case, and the source says nothing about how such firms are valued.
- Engine UNSUPPORTED: “the premium typically accorded to AI software businesses”. The source gives no market comparison, so this assumed sector premium comes from outside the evidence.
- Engine UNSUPPORTED: “A 50x revenue multiple is extremely elevated even for high-growth software companies.”. The scenario contains no benchmark multiples, so this comparison relies on outside market norms.

### S09 c73dcac4: human M5 = 0, engine flags = 0

### S04 de9a1305: human M5 = 1, engine flags = 3
- Engine UNSUPPORTED: “signals that significantly more capital is being deployed into the protocol, reflecting growing utility, user trust, and economic activity”. The scenario gives only the TVL change and never says what drove it, so attributing it to utility, trust and activity goes beyond the evidence (the output's own opposing case concedes as much).
- Engine UNSUPPORTED: “implies the ratio has compressed sharply”. P/TVL is normally based on market capitalisation, and a flat price establishes a flat market cap only if supply was unchanged, which the scenario does not state.
- Engine UNSUPPORTED: “This divergence is a classic signal used in DeFi valuation analysis to identify potential mispricings.”. This describes outside market practice that the scenario does not address.

### S11 e0ab033e: human M5 = 1, engine flags = 3
- Engine UNSUPPORTED: “For a growth-oriented software company, forward revenue growth is a primary valuation driver.”. The scenario only says the company is a software company and does not describe it as growth-oriented or say what drives its valuation.
- Engine UNSUPPORTED: “The 11% decline is consistent with a rational repricing of discounted future cash flows under lower growth assumptions.”. The 11% fall is given, but nothing in the scenario allows the decline to be checked against a cash-flow repricing, which the output itself admits in its uncertainty section.
- Engine UNSUPPORTED: “The supplied evidence refutes the claim.”. The evidence shows the direction of the reaction is explicable, but saying it 'refutes' the irrationality claim goes further than the scenario allows, and it conflicts with the output's own admission that the magnitude cannot be assessed.

### S13 414aae48: human M5 = 0, engine flags = 1
- Engine UNSUPPORTED: “The common external driver (copper price) is a confounding factor that undermines any causal claim running from equities to currency.”. The output asserts as fact that copper drove both series, but the scenario only reports co-occurring moves, so copper is a plausible rather than established common driver.

### S07 d713df3d: human M5 = 0, engine flags = 0

### S10 4a02c099: human M5 = 0, engine flags = 0

### S20 c10881e2: human M5 = 0, engine flags = 0

### S12 053c71e1: human M5 = 1, engine flags = 0

### S23 37497ace: human M5 = 1, engine flags = 3
- Engine UNSUPPORTED: “suggesting that fundamental earnings performance is a primary driver of the concentrated returns”. Matching shares support a material fundamentals component, but calling earnings the 'primary' driver goes beyond what share comparisons alone can establish.
- Engine UNSUPPORTED: “The 45% year-on-year earnings growth further reinforces that these companies delivered substantial real earnings improvement, not merely re-rating.”. The 45% earnings growth is sourced, but 'real' (inflation-adjusted) improvement is not established, and the scenario gives no price or multiple data to rule re-rating in or out.
- Engine UNSUPPORTED: “is substantially underpinned by actual earnings performance”. 'Substantially' is a stronger claim than the 'material' component the evidence supports, because the scenario gives no direct return decomposition.

### S19 98a4154e: human M5 = 0, engine flags = 0

### S24 9526fa87: human M5 = 1, engine flags = 0
