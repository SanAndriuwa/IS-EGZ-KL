# Eksperimento rezultatai

Automatiškai sukurta paleidus `python -m src.experiment`.

AP yra pagrindinė PR kreivės suvestinė; trapecinis PR-AUC pateiktas atskirai. Mažesnis Brier yra geriau.

| Modelis | Scenarijus | AP | PR-AUC | Precision | Recall | Brier | Slenkstis |
|---|---|---:|---:|---:|---:|---:|---:|
| purchase_rate | clean | 0.2066 | 0.6033 | 0.2066 | 1.0000 | 0.1731 | 0.01 |
| logistic | clean | 0.3336 | 0.3326 | 0.2438 | 0.9693 | 0.1582 | 0.04 |
| random_forest | clean | 0.3411 | 0.3400 | 0.2414 | 0.9795 | 0.1555 | 0.03 |
| gradient_boosting | clean | 0.3392 | 0.3385 | 0.2311 | 0.9877 | 0.1572 | 0.01 |
| random_forest_with_page_values | clean | 0.6715 | 0.6713 | 0.6280 | 0.6332 | 0.1158 | 0.20 |
| purchase_rate | missing_numeric_10pct | 0.2066 | 0.6033 | 0.2066 | 1.0000 | 0.1731 | 0.01 |
| logistic | missing_numeric_10pct | 0.3298 | 0.3288 | 0.2385 | 0.9703 | 0.1594 | 0.04 |
| random_forest | missing_numeric_10pct | 0.3386 | 0.3378 | 0.2363 | 0.9816 | 0.1558 | 0.03 |
| gradient_boosting | missing_numeric_10pct | 0.3360 | 0.3352 | 0.2273 | 0.9877 | 0.1576 | 0.01 |

RF ir logistinės regresijos AP skirtumas: **0.0076**. Sąlyginis 95 % porinio bootstrap intervalas: **[-0.0113; 0.0284]**.

Hipotezė AP skirtumas ≥ 0,02: **nepasitvirtino šiame teste**.

Formulės ir bibliotekos prognozių didžiausias skirtumas: `0`.

![PR ir kalibracija](evaluation.svg)

Interpretacija, ribos ir klaidų analizė: [ataskaita](../docs/ATASKAITA.md).
