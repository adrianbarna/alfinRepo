---
name: incasari-skroutz
description: >
  Agentul de încasări pentru borderourile Skroutz: le transformă în XML de import pentru
  programul de contabilitate Saga (Import documente → Încasări), le trimite raportul pe
  e-mail și predă verificarea pe boardurile Notion. Folosește acest skill când apare
  „borderou Skroutz", „încasări Skroutz", „procesează Skroutz".
  Fluxul complet e în skill-ul `incasari-cargus`, pe care acest skill îl citește la
  fiecare rulare; aici stau doar particularitățile sursei Skroutz.
---

# Încasări Skroutz

Învelișul agentului Skroutz. **Fluxul nu se rescrie aici**: singura sursă de adevăr pentru
ce se întâmplă la o rulare — poarta de intrare, raportul pe e-mail, cardurile din Notion,
regula de aur — e `<skills-dir>/incasari-cargus/SKILL.md`. `<skills-dir>` e folderul care
ține skill-urile acestui plugin, adică părintele folderului de față.

## Ce ai de făcut

1. **Citește acum, integral, `<skills-dir>/incasari-cargus/SKILL.md`.** Fără el nu ai
   fluxul și nu ai voie să improvizezi unul.
2. Urmează-l pas cu pas, cu **sursa `skroutz`**. Comanda de rulare:

   ```
   py -3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --sursa skroutz
   ```

   Pe macOS/Linux, `python3` în loc de `py -3`.
3. Peste valorile implicite din flux (care sunt ale sursei `cargus`), pune-le pe acestea:

| Ce | Valoare pentru Skroutz |
|---|---|
| `--sursa` | `skroutz` |
| Foldere de borderouri | `borderouri/eur` |
| Jurnal | `procesate/.procesate-skroutz.json` |
| Raport pentru e-mail | `procesate/ultimul-raport-skroutz.txt` |
| `Agent`, pe AI Agent overview | `Agent Borderou Skroutz` |
| `ID rulare`, pe ambele boarduri | `INC-SKROUTZ-<an>-<lună>` (ex. `INC-SKROUTZ-2026-07`) |
| `Task`, pe Board Echipă | `<ID> · Verifică încasările Skroutz <luna> <anul> și importă-le în Saga` |

## Ce e specific sursei Skroutz

- **Cheia e `Waybill` = `inf_suplm`** — codul comenzii Skroutz e trecut pe factură, inclusiv cu sufix (`…-2`, a doua factură pe aceeași comandă).
- **Rândurile cu suma 0 nu intră** în XML (livrări repetate); apar în raport.
- Facturile sunt în EUR, deci contul e `5126` și `Moneda` `EUR` — vin din folderul `eur`.
- Cazuri de verificat manual, văzute deja: o firmă cu cod de TVA grecesc, unde borderoul are suma fără TVA și factura cu TVA; și o comandă facturată în lei, care nu apare în facturile în valută.

Maparea completă a coloanelor, cu exemple și cifrele de potrivire cu facturile:
`<skills-dir>/incasari-cargus/references/mappings.md`, secțiunea Skroutz.
