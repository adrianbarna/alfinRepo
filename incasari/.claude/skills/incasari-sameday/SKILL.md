---
name: incasari-sameday
description: >
  Agentul de încasări pentru borderourile Sameday: le transformă în XML de import pentru
  programul de contabilitate Saga (Import documente → Încasări), le trimite raportul pe
  e-mail și predă verificarea pe boardurile Notion. Folosește acest skill când apare
  „borderou Sameday", „încasări Sameday", „procesează Sameday", „AWB Sameday".
  Fluxul complet e în skill-ul `incasari-cargus`, pe care acest skill îl citește la
  fiecare rulare; aici stau doar particularitățile sursei Sameday.
---

# Încasări Sameday

Învelișul agentului Sameday. **Fluxul nu se rescrie aici**: singura sursă de adevăr pentru
ce se întâmplă la o rulare — poarta de intrare, raportul pe e-mail, cardurile din Notion,
regula de aur — e `<skills-dir>/incasari-cargus/SKILL.md`. `<skills-dir>` e folderul care
ține skill-urile acestui plugin, adică părintele folderului de față.

## Ce ai de făcut

1. **Citește acum, integral, `<skills-dir>/incasari-cargus/SKILL.md`.** Fără el nu ai
   fluxul și nu ai voie să improvizezi unul.
2. Urmează-l pas cu pas, cu **sursa `sameday`**. Comanda de rulare:

   ```
   py -3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --sursa sameday
   ```

   Pe macOS/Linux, `python3` în loc de `py -3`.
3. Peste valorile implicite din flux (care sunt ale sursei `cargus`), pune-le pe acestea:

| Ce | Valoare pentru Sameday |
|---|---|
| `--sursa` | `sameday` |
| Foldere de borderouri | `borderouri/<an>-<luna>/ron` |
| Jurnal | `borderouri/procesate/.procesate-sameday.json` — **comun tuturor lunilor**, dat cu `--jurnale` |
| Raport pentru e-mail | `<folder lunii>/procesate/ultimul-raport-sameday.txt` |
| `Agent`, pe AI Agent overview | `Agent Borderou Sameday` |
| `ID rulare`, pe ambele boarduri | `INC-SAMEDAY-<an>-<lună>` (ex. `INC-SAMEDAY-2026-07`) |
| `Task`, pe Board Echipă | `<ID> · Verifică încasările Sameday <luna> <anul> și importă-le în Saga` |

## Ce e specific sursei Sameday

- **Borderoul nu are numărul comenzii** — coloana `Referinta client` e goală („Nicio referinta”), deci factura se caută după **nume + sumă + dată** (ziua AWB-ului, care e și ziua facturii).
- `Numar` și `FacturaID` din XML vin din `inf_suplm` al facturii găsite, nu din AWB.
- Un client fără nicio factură pe nume sau cu două facturi la fel de plauzibile e **sărit** și raportat — asta e cazul obișnuit de verificat manual aici.
- Dacă magazinul începe să pună numărul comenzii în `Referinta client`, spune-i utilizatorului: legarea ar deveni pe cheie, ca la Cargus.

Maparea completă a coloanelor, cu exemple și cifrele de potrivire cu facturile:
`<skills-dir>/incasari-cargus/references/mappings.md`, secțiunea Sameday.
