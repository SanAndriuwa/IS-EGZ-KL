# Dėstytojo kriterijų patikra (2026-09-30)

Ši lentelė nurodo patikrinamus artefaktus, o ne žada maksimalų įvertinimą. Nauji bandymai yra **post-test exploratory**: tas pats lapkričio–gruodžio testas jau žinomas tyrėjui.

## Kolokviumas

| Kriterijus | Kur įgyvendinta | Patikrinamas rezultatas | Kas liko |
|---|---|---|---|
| Problema, apribojimai ir klaidų kaina | `KOLIOKVIUMO_PLANAS.md`, 1–2 sk.; `ATASKAITA.md` | Apibrėžta pirkimo sesijos klasifikacija ir false negative / false positive kompromisas. | Reali piniginė klaidų kaina nenustatyta. |
| Alternatyvos, baseline ir literatūra | `KOLIOKVIUMO_PLANAS.md`, 3 ir 3.6 sk.; `NAUJA_LITERATURA.md` | Palyginti RF, LR, GB ir šiuolaikiniai task-specific variantai; pasirinktas ribotas XGBoost bandymas. | Straipsnių rezultatai nėra tiesiogiai palyginami su mūsų temporal AP. |
| Įvestis, išvestis, formulės ir kodo struktūra | `KOLIOKVIUMO_PLANAS.md`, 4–5 sk.; `src/` | X, y, RF taisyklė ir moduliai aprašyti; kodas veikia. | Studentas turi gebėti paaiškinti gyvai. |
| Skaidymas, metrikos, eksperimentai ir rizikos | `PROTOKOLAS.md`; `KOLIOKVIUMO_PLANAS.md`, 6–7 sk. | Temporal split, AP/F2, abliacija ir naujas tyrimo planas dokumentuoti. | Naujai nepriklausomai patikrai reikia būsimo laikotarpio. |
| AI naudojimas ir tikrinimas | `KOLIOKVIUMO_PLANAS.md`, 8 sk.; `AI_ZURNALAS.md` | Užrašyti pasiūlymai, atmestos alternatyvos, faktinės patikros. | Gyvą savarankiškumą turi parodyti studentas. |

## Egzaminas

| Kriterijus | Kur įgyvendinta | Patikrinamas rezultatas | Kas liko |
|---|---|---|---|
| Baseline, duomenų grandinė ir atkuriamumas | `src/data.py`, `src/experiment.py`, `results/metrics.csv`, `results/test_log.txt` | Baseline test AP 0.2066; pagrindinis paleidimas ir 14 testų dokumentuoti. | Originalaus `manifest.json` kontrolinės sumos yra istorinio paleidimo, ne dabartinio papildyto kodo. |
| Bent du intelektualieji metodai | `src/models.py`, `src/improvement.py` | Įgyvendinti LR, RF, GB; atskirai XGBoost. | Nėra. |
| Korektiškas eksperimentas ir vienodos sąlygos | `PROTOKOLAS.md`, `src/training.py`, `src/improvement.py` | Vienodas temporal split; fit tik train; AP pasirinkimas ir F2 slenkstis validation. | Nauji test rezultatai tik tiriamieji, nes testas jau žinomas. |
| Rezultatai, abliacija, atsparumas, klaidos | `EGZAMINO_ATASKAITA.md`, `results/pagevalues_ablation.csv`, `results/improvement_experiments.csv`, `results/tuning/SUMMARY.md` | Parodyti ir neigiami bandymai, 722 konfigūracijų tyrimas, PageValues jautrumas, 10 % missing-values bandymas ir klaidų analizė. | Realaus laiko požymių momentinės reikšmės nepateiktos. |
| Ribos, rizikos ir tinkamumas | `ATASKAITA.md`, `EGZAMINO_ATASKAITA.md`, `GYNIMAS.md` | Nurodyti temporal leakage, distribution shift, calibration ir pakartotinio testo ribotumai. | Production real-time tinkamumas nepatvirtintas. |
| AI auditas | `AI_ZURNALAS.md`, `NAUJA_LITERATURA.md` | Matyti literatūros patikra, pasirinkimo motyvai, skaičiavimo patikra. | Studentas turi patvirtinti, kad supranta sprendimus. |
| Gyvas gynimas, nematytas testas, nedidelis pakeitimas | `GYNIMAS.md` | Yra pasiruošimo atmintinė. | **Neuždaryta:** gyvą demonstraciją, dėstytojo nematytą testą ir pakeitimą turi atlikti studentas. |
