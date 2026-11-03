# ARGUS benchmark, dev split (16 outputs)

Ground truth: blind human coding (M5, unsupported assertions), frozen 10 Aug 2026.
Engine flag = at least one claim verified as UNSUPPORTED or CONTRADICTED.

| | Human found unsupported claims | Human found none |
|---|---|---|
| Engine flagged | 3 | 1 |
| Engine did not flag | 5 | 7 |

Human-quoted unsupported claims also flagged by the engine: 0 of 3.
Tokens: 33,941 in, 18,354 out.

Development split: used to inspect and tune. Not a reportable accuracy figure.

## Item by item

### S24 f3c75584: human M5 = 1, engine flags = 1
- Human (MISSED): “gross profit”
- Engine UNSUPPORTED: “no ambiguity exists in the definitions of revenue, serving costs, or user count as provided”. The source gives bare figures with no definitions, so it cannot establish that no definitional ambiguity exists.

### S22 c6035c6e: human M5 = 1, engine flags = 0
- Human (MISSED): “extremely elevated even for high-growth software companies”

### S11 e0ab033e: human M5 = 1, engine flags = 0

### S12 053c71e1: human M5 = 1, engine flags = 0

### S23 37497ace: human M5 = 1, engine flags = 1
- Engine UNSUPPORTED: “The 45% year-on-year earnings growth further reinforces that these companies delivered substantial real earnings improvement, not merely re-rating.”. The 45% earnings growth is in the source, but the conclusion that returns were not merely re-rating goes beyond it, since no price change or multiple data is given.

### S04 de9a1305: human M5 = 1, engine flags = 1
- Engine UNSUPPORTED: “reflecting growing utility, user trust, and economic activity”. The source gives only the TVL change and says nothing about utility, trust, or activity, so this is the output's interpretation stated as fact.

### S24 9526fa87: human M5 = 1, engine flags = 0

### S22 1a6d6f70: human M5 = 1, engine flags = 0
- Human (MISSED): “extremely elevated even by high-growth software standards”

### S20 56a02f7f: human M5 = 0, engine flags = 2
- Engine CONTRADICTED: “The proposed 700-share position does NOT comply with the 2% maximum-risk-per-trade mandate.”. The scenario figures give a risk of 1,400, which is under 1,600, so the position complies; the final verdict is wrong and contradicts the output's own reasoning.
- Engine CONTRADICTED: “It exceeds the permitted risk by $400, or 25% above the allowed limit.”. The actual risk is 1,400, which is 200 below the limit rather than 400 above it; the 25% figure would only apply to a 1,000-share position.

### S03 077ea1ba: human M5 = 0, engine flags = 0

### S19 98a4154e: human M5 = 0, engine flags = 0

### S10 4a02c099: human M5 = 0, engine flags = 0

### S09 c73dcac4: human M5 = 0, engine flags = 0

### S13 414aae48: human M5 = 0, engine flags = 0

### S20 c10881e2: human M5 = 0, engine flags = 0

### S07 d713df3d: human M5 = 0, engine flags = 0
