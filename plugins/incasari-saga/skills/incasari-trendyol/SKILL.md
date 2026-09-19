---
name: incasari-trendyol
description: >
  Agentul de încasări pentru borderourile Trendyol: le transformă în XML de import pentru
  programul de contabilitate Saga (Import documente → Încasări), le trimite raportul pe
  e-mail și predă verificarea pe boardurile Notion. Folosește acest skill când apare
  „borderou Trendyol", „încasări Trendyol", „procesează Trendyol".
  Fluxul complet e în skill-ul `incasari-cargus`, pe care acest skill îl citește la
  fiecare rulare; aici stau doar particularitățile sursei Trendyol.
---

# Încasări Trendyol

Învelișul agentului Trendyol. **Fluxul nu se rescrie aici**: singura sursă de adevăr pentru
ce se întâmplă la o rulare — poarta de intrare, raportul pe e-mail, cardurile din Notion,
regula de aur — e `<skills-dir>/incasari-cargus/SKILL.md`. `<skills-dir>` e folderul care
ține skill-urile acestui plugin, adică părintele folderului de față.

## Ce ai de făcut

1. **Citește acum, integral, `<skills-dir>/incasari-cargus/SKILL.md`.** Fără el nu ai
   fluxul și nu ai voie să improvizezi unul.
2. Urmează-l pas cu pas, cu **sursa `trendyol`**. Comanda de rulare:

   ```
   py -3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --sursa trendyol
   ```

   Pe macOS/Linux, `python3` în loc de `py -3`.
3. Peste valorile implicite din flux (care sunt ale sursei `cargus`), pune-le pe acestea:

| Ce | Valoare pentru Trendyol |
|---|---|
| `--sursa` | `trendyol` |
| Foldere de borderouri | `borderouri/<an>-<luna>/ron` |
| Jurnal | `borderouri/procesate/.procesate-trendyol.json` — **comun tuturor lunilor**, dat cu `--jurnale` |
| Raport pentru e-mail | `<folder lunii>/procesate/ultimul-raport-trendyol.txt` |
| `Agent`, pe AI Agent overview | `Agent Borderou Trendyol` |
| `ID rulare`, pe ambele boarduri | `INC-TRENDYOL-<an>-<lună>` (ex. `INC-TRENDYOL-2026-07`) |
| `Task`, pe Board Echipă | `<ID> · Verifică încasările Trendyol <luna> <anul> și importă-le în Saga` |

## Ce e specific sursei Trendyol

- **Waybill-ul nu apare pe factură**, deci legarea e după **nume + sumă + dată**.
- **Coletele aceleiași comenzi se adună**: rândurile aceluiași client, din aceeași zi, cu același semn, sunt o singură linie.
- **Clienții greci sunt facturați în EUR, dar plătiți în lei.** Linia intră în RON (cont 5125), la valoarea în lei a facturii, cu avertisment. Menționează-le în rezumat: sunt de verificat la import, pentru diferența de curs.
- Numele grecești se transliterează automat; avertismentele de nume ar trebui să lipsească.

Maparea completă a coloanelor, cu exemple și cifrele de potrivire cu facturile:
`<skills-dir>/incasari-cargus/references/mappings.md`, secțiunea Trendyol.
