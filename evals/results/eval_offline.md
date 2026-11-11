# Evaluation - extractor: `offline`

- Emails: 23, items: 25
- Risky items in the answer key (amber/red): 14
- **Missed risks (risky item rated green): 2 -> missed-risk rate 14.3%** (target: at most 1 in about 20)
- Red recall: 100.0% | false-alarm rate on green items: 9.1%
- Items with exactly the right colour: 88%

## Extraction accuracy

| field          |   accuracy_% |
|:---------------|-------------:|
| po_number      |        100   |
| date           |         82.6 |
| date_basis     |         91.3 |
| no_date_alert  |        100   |
| evidence_found |        100   |

## Confusion matrix (rows = expected)

| true   |   green |   amber |   red |
|:-------|--------:|--------:|------:|
| green  |      10 |       1 |     0 |
| amber  |       2 |       8 |     0 |
| red    |       0 |       0 |     4 |

## Items where the colour differs

| item_id    | expected   | predicted   | result           | expected_why                            |
|:-----------|:-----------|:------------|:-----------------|:----------------------------------------|
| EQ-CRAH-02 | AMBER      | GREEN       | MISSED RISK      | float only 5 working days               |
| EQ-TX-01   | AMBER      | GREEN       | MISSED RISK      | float only 15 working days              |
| EQ-BMS-01  | GREEN      | AMBER       | different colour | float 30 working days, no warning signs |

## Emails where the date was read wrongly

| email_id   | expected_date_text   | extracted_date_text   |
|:-----------|:---------------------|:----------------------|
| E01        | 25 January 2027      | 11 January 2027       |
| E16        | 18 March 2027        | 4 March 2027          |
| E19        | 10 June 2027         | 26 May 2027           |
| E23        | 23 August 2027       | 12 July 2027          |
