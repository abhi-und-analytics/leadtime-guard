# Evaluation - extractor: `gemini`

- Emails: 23, items: 25
- Risky items in the answer key (amber/red): 14
- **Missed risks (risky item rated green): 0 -> missed-risk rate 0.0%** (target: at most 1 in about 20)
- Red recall: 100.0% | false-alarm rate on green items: 9.1%
- Items with exactly the right colour: 96%

## Extraction accuracy

| field          |   accuracy_% |
|:---------------|-------------:|
| po_number      |          100 |
| date           |          100 |
| date_basis     |           87 |
| no_date_alert  |          100 |
| evidence_found |          100 |

## Confusion matrix (rows = expected)

| true   |   green |   amber |   red |
|:-------|--------:|--------:|------:|
| green  |      10 |       1 |     0 |
| amber  |       0 |      10 |     0 |
| red    |       0 |       0 |     4 |

## Items where the colour differs

| item_id   | expected   | predicted   | result           | expected_why                            |
|:----------|:-----------|:------------|:-----------------|:----------------------------------------|
| EQ-BAT-01 | GREEN      | AMBER       | different colour | float 20 working days, no warning signs |

## Emails where the date was read wrongly

None.
