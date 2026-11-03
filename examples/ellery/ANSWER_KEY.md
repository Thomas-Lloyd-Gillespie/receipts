# Ellery answer key

The Ellery file is made up. `report.txt` is a draft suitability report that was written with errors on purpose, so the check has something known to find. Each line below sets a sentence in the report against the line of `factfind.txt` it conflicts with.

## Eight statements the fact-find contradicts

| # | The report says | The fact-find says |
|---|---|---|
| 1 | You are both in good health. | David: Type 2 diabetes, on medication. Minor stroke in 2023. Uses a walking stick. |
| 2 | You need £85,000 in total. | Total required: £82,000. |
| 3 | You have discussed your plans with your children, who are supportive. | Clients have not yet discussed these plans with their children. |
| 4 | Leaving an inheritance is not a priority for you. | "We want to leave something for Clare and Robert." Interested in protecting part of the property value for inheritance. |
| 5 | You have confirmed that no grants are available for the adaptations. | Council grants for the adaptations: clients have not looked into this yet. |
| 6 | Your monthly budget shows a comfortable surplus of around £450 a month | Surplus about £120 a month. |
| 7 | You do not wish to make any payments towards the interest. | Clients would like to pay some interest each month if they can, but do not want to commit to it. |
| 8 | You have up-to-date wills and lasting powers of attorney in place. | Wills in place (2019). No lasting powers of attorney. |

## One objective left out

The fact-find lists three objectives. The report covers the mortgage and the adaptations but not the third: "c) Gift of £5,000 to granddaughter Ellie for university costs."

## The sample receipt

`sample-receipt/` holds one run of the engine on this file (engine 0.1.0, prompt claims-1.1, claude-opus-5-5, 28 Oct 2026). Its input hashes match `report.txt` and `factfind.txt`, so it can be checked against them. It marks all eight statements above as CONTRADICTED, lists the £5,000 gift among the facts left out, and has no quote failures. Open `receipt.html` in a browser for the printable version.
