---
name: incasari-plationline
description: >
  Agentul de încasări pentru borderourile PlatiOnline: le transformă în XML de import pentru
  programul de contabilitate Saga (Import documente → Încasări), le trimite raportul pe
  e-mail și predă verificarea pe boardurile Notion. Folosește acest skill când apare
  „borderou PlatiOnline", „încasări PlatiOnline", „procesează PlatiOnline", „plăți cu cardul".
  Fluxul complet e în skill-ul `incasari-cargus`, pe care acest skill îl citește la
  fiecare rulare; aici stau doar particularitățile sursei PlatiOnline.
---

# Încasări PlatiOnline (plăți cu cardul)

Învelișul agentului PlatiOnline. **Fluxul nu se rescrie aici**: singura sursă de adevăr pentru
ce se întâmplă la o rulare — poarta de intrare, raportul pe e-mail, cardurile din Notion,
regula de aur — e `<skills-dir>/incasari-cargus/SKILL.md`. `<skills-dir>` e folderul care
ține skill-urile acestui plugin, adică părintele folderului de față.

## Ce ai de făcut

1. **Citește acum, integral, `<skills-dir>/incasari-cargus/SKILL.md`.** Fără el nu ai
   fluxul și nu ai voie să improvizezi unul.
2. Urmează-l pas cu pas, cu **sursa `plationline`**. Comanda de rulare:

   ```
   py -3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --sursa plationline
   ```

   Pe macOS/Linux, `python3` în loc de `py -3`.
3. Peste valorile implicite din flux (care sunt ale sursei `cargus`), pune-le pe acestea:

| Ce | Valoare pentru PlatiOnline |
|---|---|
| `--sursa` | `plationline` |
| Card poartă (borderou), pe Board Echipă — pasul „Poarta de intrare" | `"Task" LIKE 'Adaug% borderoul PlatiOnline%'` (reminderul scrie „Adauga", fără diacritice) și `Note` cu `borderouri/<LUNA>/` |
| Foldere de borderouri | `borderouri/<an>-<luna>/ron` |
| Jurnal | `borderouri/procesate/.procesate-plationline.json` — **comun tuturor lunilor**, dat cu `--jurnale` |
| Raport pentru e-mail | `<folder lunii>/procesate/ultimul-raport-plationline.txt` |
| `Agent`, pe AI Agent overview | `Agent Borderou PlatiOnline` |
| `ID rulare`, pe ambele boarduri | `INC-PLATIONLINE-<an>-<lună>` (ex. `INC-PLATIONLINE-2026-07`) |
| `Task`, pe Board Echipă | `<ID> · Verifică încasările PlatiOnline <luna> <anul> și importă-le în Saga` |

## Ce e specific sursei PlatiOnline

- Borderoul e **`.csv`**, cu `;` și fiecare valoare între `#`; scriptul îl citește ca atare, nu-l converti.
- **Cheia e `Order Number` = `inf_suplm`.** `StatementID` e lotul de decontare și nu intră în XML.
- **Data plății e în format american** (`M/D/YYYY`) și poate cădea cu una-trei zile *înaintea* facturii — de asta e de verificat la primul import.
- **Comenzile B2B** (seria `MCSCOD`) se facturează pe firmă, fără `Order Number` pe factură: se leagă după sumă + zi, cu avertisment. Raportează-le.
- `Settle/Credit` = `Credit` înseamnă bani întorși clientului: linie negativă, pe factura de storno.

Maparea completă a coloanelor, cu exemple și cifrele de potrivire cu facturile:
`<skills-dir>/incasari-cargus/references/mappings.md`, secțiunea PlatiOnline.
