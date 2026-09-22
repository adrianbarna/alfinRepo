---
name: incasari-emag
description: >
  Agentul de încasări pentru borderourile eMAG: le transformă în XML de import pentru
  programul de contabilitate Saga (Import documente → Încasări), le trimite raportul pe
  e-mail și predă verificarea pe boardurile Notion. Folosește acest skill când apare
  „borderou eMAG", „încasări eMAG", „procesează eMAG", „eMAG RO", „eMAG BG", „eMAG HU".
  Fluxul complet e în skill-ul `incasari-cargus`, pe care acest skill îl citește la
  fiecare rulare; aici stau doar particularitățile sursei eMAG.
---

# Încasări eMAG (RO, BG, HU)

Învelișul agentului eMAG. **Fluxul nu se rescrie aici**: singura sursă de adevăr pentru
ce se întâmplă la o rulare — poarta de intrare, raportul pe e-mail, cardurile din Notion,
regula de aur — e `<skills-dir>/incasari-cargus/SKILL.md`. `<skills-dir>` e folderul care
ține skill-urile acestui plugin, adică părintele folderului de față.

## Ce ai de făcut

1. **Citește acum, integral, `<skills-dir>/incasari-cargus/SKILL.md`.** Fără el nu ai
   fluxul și nu ai voie să improvizezi unul.
2. Urmează-l pas cu pas, cu **sursa `emag`**. Comanda de rulare:

   ```
   py -3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --sursa emag
   ```

   Pe macOS/Linux, `python3` în loc de `py -3`.
3. Peste valorile implicite din flux (care sunt ale sursei `cargus`), pune-le pe acestea:

| Ce | Valoare pentru eMAG |
|---|---|
| `--sursa` | `emag` |
| Card poartă (borderou), pe Board Echipă — pasul „Poarta de intrare" | `Task` începe cu `Adaugă borderoul eMAG` |
| Foldere de borderouri | `borderouri/<an>-<luna>/ron` (RO), `borderouri/<an>-<luna>/eur` (BG), `borderouri/<an>-<luna>/huf` (HU) |
| Jurnal | `borderouri/procesate/.procesate-emag.json` — **comun tuturor lunilor**, dat cu `--jurnale` |
| Raport pentru e-mail | `<folder lunii>/procesate/ultimul-raport-emag.txt` |
| `Agent`, pe AI Agent overview | `Agent Borderou eMAG` |
| `ID rulare`, pe ambele boarduri | `INC-EMAG-<an>-<lună>` (ex. `INC-EMAG-2026-07`) |
| `Task`, pe Board Echipă | `<ID> · Verifică încasările eMAG <luna> <anul> și importă-le în Saga` |

## Ce e specific sursei eMAG

- **O linie pe comandă, nu pe rând.** eMAG plată o comandă în fracțiuni — card, ramburs, refund, voucher — iar scriptul le adună pe `Order ID`. O comandă plătită și returnată în același borderou iese pe 0 și nu intră în XML; apare în raport.
- **`Data` e `Payout date`**, data virării, nu data comenzii.
- **HUF se împarte la 100**: Saga ține forinții la sută, ca în cursul BNR.
- **Plățile parțiale intră** cu suma din borderou, cu avertisment „plată parțială”; virarea care aduce restul stinge factura. Raportează-le explicit.
- Cheia către factură e `Order ID` = `inf_suplm`.

Maparea completă a coloanelor, cu exemple și cifrele de potrivire cu facturile:
`<skills-dir>/incasari-cargus/references/mappings.md`, secțiunea eMAG.
