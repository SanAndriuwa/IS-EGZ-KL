# Užduoties reikalavimų atitiktis

Šaltinis – pateiktas `DISfm-26_Andrej_Kondratjev.docx`. Dokumento originalas nekeistas. Toliau nurodyti darbo įrodymai, o ne pažadėtas įvertinimas.

| Reikalavimas | Įgyvendinimas ir įrodymas |
|---|---|
| Problema, praktinė vertė, klaidų kaina | Kolokviumo planas ir ataskaita |
| Etapai, įvestis ir išvestis | Plano modulių lentelė; `src/data.py`, `src/predict.py` |
| 2–4 intelektualieji metodai ir baseline | RF ir gradientinis stiprinimas; pirkimų dažnis ir logistinė regresija |
| Pirminiai šaltiniai, DOI ar stabilios nuorodos | Plano metodų lentelė; AI žurnale patikrų ribos |
| Pagrindinis metodas ir hipotezė | `PROTOKOLAS.md`, RF AP persvara ≥0,02 |
| Formulės ir ryšys su kodu | Plano RF formulė, `forest_probability_by_formula`, skirtumas 0 |
| Skaidymas, preprocessing, metrikos ir biudžetas | Protokolas, `config.json`, `split_summary.csv` |
| AI planas ir žurnalas | Planas ir `AI_ZURNALAS.md`, bent dvi klaidos / prielaidos |
| Veikianti duomenų grandinė ir du intelektualieji modeliai | `python -m src.experiment`, `results/manifest.json` |
| Tas pats skaidymas ir jokio testo parinkimui | `src/experiment.py`, `split_membership.csv`, `model_selection.csv` |
| Abliacija arba požymių jautrumas | RF su PageValues ir be jo, vienodas kandidatų biudžetas |
| Atsparumo bandymas | Vienoda 10 % skaitinių langelių praradimo kaukė |
| Rezultatų lentelė, grafikas, klaidos | `RESULTS.md`, `evaluation.svg`, `error_examples.csv` |
| Laimėjimo ar nelaimėjimo paaiškinimas | `ATASKAITA.md`, neigiama hipotezės išvada ir bootstrap |
| Priklausomybės, sėkla, viena komanda | README, `requirements.txt`, sėkla 42 |
| Nematytas testas ir mažas pakeitimas | Programa ir `GYNIMAS.md` paruošti; gyvai dar neatlikta |
