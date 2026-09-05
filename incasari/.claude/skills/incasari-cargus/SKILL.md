---
name: incasari-cargus
description: >
  Transformă borderourile de ramburs Cargus / Packeta (.xlsx) în fișiere XML de
  import pentru programul de contabilitate Saga (Import documente → Încasări).
  Procesează doar borderourile noi și ține minte ce a procesat deja. Folosește
  acest skill când apare „borderou", „borderouri", „încasări", „ramburs",
  „Cargus", „Packeta", „xml pentru Saga", „procesează borderourile", „mai sunt
  borderouri noi", „generează încasările". Tot el acoperă și configurarea —
  „configurează încasările", „config încasări", „schimbă folderul de borderouri",
  „setează folderul de facturi", „schimbă adresele de raport", „adaugă EUR",
  „mută borderourile" — al cărei flux stă în references/configurare.md.
---

# Borderouri Cargus / Packeta → XML Saga

Toată conversia trece prin `scripts/proceseaza.py`, care vine împreună cu acest
SKILL.md (vezi „Cum rulezi scriptul").

Fiecare rând de borderou e legat de **factura lui** din folderul de facturi (exportul
XML din Saga). `<FacturaNumar>` primește `nr_iesire` de pe factură, iar `<Suma>` ia
valoarea **de pe factură**, ca factura să se stingă exact. Un rând care nu poate fi
legat sigur de o factură **nu intră în XML** — ajunge în raportul trimis pe e-mail,
ca să fie verificat manual.

Structura de lucru: **valuta e dată de folder, sursa nu are folder**. Cargus și eMAG
stau împreună; formatul se recunoaște după coloane.

```
borderouri/ron/  .xlsx  +  procesate/      facturi/  exporturile XML din Saga
```

**Azi e configurat doar RON.** O altă valută se adaugă cu o singură comandă
(`--set-folder borderouri/eur --moneda EUR`, cont 5126) — nu e nevoie de cod nou.

## Unde stau fișierele

La ALFIN Consult, borderourile și facturile stau în **Google Drive, sincronizat în
modul Mirror** pe calculatorul cu Saga — deci sunt fișiere reale pe disc, nu
referințe către cloud:

```
C:\Users\Barna\My Drive\claude\incasari-saga\borderouri\ron
C:\Users\Barna\My Drive\claude\incasari-saga\facturi
```

Trei consecințe practice:

- **Nu folosi litera `G:`** în căi, chiar dacă există pe mașină. E un drive virtual
  montat doar în sesiunea interactivă a utilizatorului logat, deci un task programat
  nu-l vede. Calea de sub `C:\Users\<utilizator>\My Drive` e o cale reală și merge
  în ambele situații.
- **XML-ul generat urcă singur în Drive.** Scriptul scrie în `borderouri\ron\procesate\`,
  iar sincronizarea îl duce în cloud. Nu încărca nimic manual și nu folosi conectorul
  de Drive pentru asta.
- **Rulează de pe un singur calculator.** Jurnalul `.procesate.json` stă într-un folder
  sincronizat; două mașini care procesează în paralel produc un al doilea fișier de
  jurnal, iar evidența se rupe în tăcere.

Dacă tocmai s-a pus un borderou nou în Drive, verifică întâi că sincronizarea s-a
terminat (iconița Drive din bara de sistem). Un fișier pe jumătate sincronizat se
citește ca `.xlsx` corupt.

## Cum rulezi scriptul (Windows / macOS)

Scriptul e `scripts/proceseaza.py`, lângă acest SKILL.md. Folosește-i **calea absolută**
— utilizatorul rulează din folderul lui de lucru, nu din folderul skill-ului. Mai jos,
`<skill-dir>` e folderul acestui SKILL.md (calea afișată la încărcarea skill-ului):
instalat ca plugin, `<plugin-dir>/skills/incasari-cargus`; copiat într-un proiect,
`<proiect>/.claude/skills/incasari-cargus`. Are nevoie doar de Python 3, fără pachete.

**Mașina de lucru e Windows**, deci interpretorul e `py -3` (sau `python`, dacă `py`
lipsește); pe macOS/Linux e `python3`. Verifică **o singură dată** pe sesiune, cu
`--version`; pe Windows încearcă în ordine `py -3`, `python`, `python3`. Dacă răspunsul
e „Python was not found; run without arguments to install from the Microsoft Store", ăla
e stub-ul Windows, nu Python — treci la următorul nume. Dacă niciunul nu merge, spune
utilizatorului să instaleze Python 3 de pe python.org (cu „Add python.exe to PATH"
bifat). **Nu instala tu nimic.**

Comenzile de mai jos sunt scrise cu `py -3`; pe macOS pui `python3` în loc, restul
rămâne identic:

```
py -3 <skill-dir>/scripts/proceseaza.py --dry-run       # Windows
python3 <skill-dir>/scripts/proceseaza.py --dry-run     # macOS / Linux
```

Comenzile merg la fel **în PowerShell și în bash**: o singură comandă pe linie, fără
`&&`, `||`, `2>/dev/null`, variabile `$X`, backticks sau `cd`. Căile primite de la
utilizator se pun între ghilimele duble; pe Windows merg și cu `\`, și cu `/`.

**Nu crea fișiere de lansare (`.bat`, `.ps1`, `.sh`).** Scriptul se apelează direct, iar
un task programat îl apelează exact la fel.

Configul stă la `~/.claude/incasari-saga/config.json` — pe Windows
`C:\Users\<utilizator>\.claude\incasari-saga\config.json`.

## Regula de aur

**Nu genera XML de mână și nu citi borderourile cu alte unelte.** Un borderou are
sute de rânduri; scriptul e determinist, XML-ul scris de model nu e. La fel, **nu
edita `.procesate.json`** direct — îl gestionează scriptul.

Rolul tău: rulezi scriptul, rezumi raportul în chat (în română), îl trimiți pe email și
ții la zi cardul rulării în board-ul Notion (pasul 3).

## Flux

### 1. Rulare normală (cazul obișnuit)

```
py -3 <skill-dir>/scripts/proceseaza.py
```

Se uită în folder, sare peste borderourile deja procesate și scrie pentru fiecare
fișier nou un XML în `<folder>/procesate/`, cu **numele borderoului, dar fără
spații** (`Cargus Packeta Iulie 2026.xlsx` → `Cargus_Packeta_Iulie_2026.xml`).

Rezumă în chat: ce fișiere s-au procesat, câte linii, totalul, unde s-a scris
XML-ul. **Raportează întotdeauna avertismentele și rândurile sărite** — sunt
lucruri pe care utilizatorul trebuie să le verifice înainte de importul în Saga.
Dacă nu e nimic nou, spune-o într-o propoziție, fără ceremonie.

### 2. Trimite raportul pe e-mail

Când s-a procesat ceva nou, scriptul compune raportul și îl scrie în
`<folder>/procesate/ultimul-raport.txt`. Cu `--json` îl ai gata de trimis în
`email.subiect` și `email.corp`, iar destinatarii în `email.catre`.

Trimite-l cu unealta de Gmail către adresele din `email.catre`, apoi spune în chat cui
ai trimis. **Nu cere confirmare înainte de trimitere, niciodată** — nici la prima
rulare. Adresele au fost stabilite la configurare, iar asta *este* autorizarea. O rulare
programată care așteaptă un „da" la 8 dimineața e o rulare ratată.

Singura excepție: utilizatorul e prezent și tocmai a schimbat adresele — atunci confirmi
o dată lista nouă, ca să nu trimiți la o adresă tastată greșit.

Raportul se trimite **și când niciun rând nu a putut fi legat de o factură** — atunci nu
se scrie niciun XML, dar lista rândurilor sărite e exact ce trebuie verificat.

Dacă `email.neconfigurat` e `true`, sau uneltele Gmail lipsesc din sesiune, vezi
`references/configurare.md`.

### 3. Ține la zi cardul din board-ul Notion

Fiecare rulare are un card în board-ul **AI Agent overview** din Notion. Acolo se vede că
rularea a avut loc și ce a mai rămas de făcut — mai ales când rularea e programată și nu
o urmărește nimeni în direct.

```
Board:       https://app.notion.com/p/6ab8018a469d4f18abda5e239cf4932f
Data source: aa9a26d8-67fc-47d2-acf0-0460d8bc9abf
```

**Dacă uneltele Notion lipsesc din sesiune, nu te opri și nu cere activarea conectorului.**
Procesarea, XML-ul și emailul sunt independente de board. Spui la final, într-o
propoziție, în ce fază ar fi trebuit să ajungă cardul, și mergi mai departe.

**La început**, imediat ce știi că ai borderouri noi de procesat, creează cardul:

| Proprietate | Valoare |
|---|---|
| `Rulare` | `Încasări — <luna> <anul>` (ex. `Încasări — septembrie 2026`) |
| `Agent` | `Încasări Cargus/Packeta` |
| `Fază` | `În lucru` |
| `Perioadă` | luna acoperită de borderouri |
| `Declanșat` | data și ora de acum |
| `Declanșare` | `Automat (programat)` dintr-un routine, altfel `Manual` |

Caută întâi în data source după `Perioadă`: dacă există deja un card pentru aceeași lună,
refolosește-l în loc să faci al doilea.

**La final**, după ce raportul pe email a plecat, mută cardul într-una din trei faze:

| Ce s-a întâmplat | `Fază` | `Pas manual rămas` |
|---|---|---|
| S-a scris XML, cu sau fără avertismente | `De verificat` | `Verifică totalurile și rândurile sărite, apoi importă XML-ul în Saga` |
| Toate rândurile sărite, niciun XML | `Blocat / Necesită input` | ce lipsește concret (un export de facturi, un borderou corectat…) |
| Cod de ieșire 1 sau 2 | `Blocat / Necesită input` | ce trebuie reparat sau configurat |

`Rezultat` primește un rezumat de o linie: `219 linii, 26.570,21 RON, 0 rânduri sărite,
15 avertismente`.

**Nu muta niciodată cardul în `De aplicat` sau `Done`.** Cele două faze înseamnă „omul a
verificat" și „omul a importat"; le mută utilizatorul. Un agent care își închide singur
cardul face board-ul inutil.

**În corpul cardului scrie jurnalul rulării, în română**, ca peste o lună să se înțeleagă
ce s-a întâmplat fără să caute nimeni raportul de email:

```markdown
## Ce a rulat
Rulat 05.09.2026 08:03, din routine-ul lunar „Încasări".
Comandă: py -3 <skill-dir>/scripts/proceseaza.py

## Fișiere procesate
- Cargus Packeta August 2026.xlsx → Cargus_Packeta_August_2026.xml
  219 linii, 26.570,21 RON

## Ce a ieșit
Total pe zile: 7.178,35 / 6.334,85 / 6.951,57 / 6.105,44 RON.
87 de linii au luat suma de pe factură (+0,95 RON față de borderou).

## De verificat
- 15 avertismente: 8 de nume, 3 de storno, 2 de sumă, 2 de lungime RefExp1
- rânduri sărite: niciunul

## Raport
Trimis la 08:04 către alfin.consult.ai@gmail.com.
```

Scrie doar ce s-a întâmplat efectiv: fără secțiuni goale, fără cifre inventate. Dacă
rularea s-a oprit, jurnalul spune unde și de ce — asta e tot rostul lui.

**Când nu e nimic nou de procesat, nu crea niciun card.** O lună fără borderouri noi nu
e o rulare.

### 4. Configurare lipsă sau de schimbat

Scriptul iese cu **codul 2** când nu știe unde sunt borderourile sau facturile. Tot
acolo ajungi când utilizatorul cere schimbarea unei căi, a valutei sau a adreselor de
raport.

În oricare din cazuri: **citește `references/configurare.md` și urmează-l.** Nu improviza
comenzi `--set-*` de aici și nu ghici nicio cale — fluxul complet, cu valorile implicite
propuse, e acolo.

### 5. Alte comenzi

| Comandă | Când |
|---|---|
| `--dry-run` | arată ce s-ar întâmpla, nu scrie nimic |
| `--reproceseaza "<nume.xlsx>"` | borderoul a fost corectat și trebuie regenerat |
| `--folder <cale>` | o rulare punctuală pe alt folder, fără să atingi configul |
| `--facturi <cale>` | alt folder de facturi, doar pentru rularea asta |
| `--fara-facturi` | nu lega facturile: `FacturaNumar` rămâne gol și nimic nu se sare |
| `--arata-config` | arată configurarea curentă |
| `--json` | raport structurat, dacă ai nevoie să-l prelucrezi |

Cod de ieșire: `0` = a mers, `2` = configurare lipsă (vezi pasul 4), `1` = eroare.

## Ce produce

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Incasari>
  <Linie>
    <Data>30.07.2026</Data>
    <Numar>47312</Numar>
    <Suma>268.89</Suma>
    <Cont>5125</Cont>
    <ContClient>4111</ContClient>
    <Explicatie>Incasare ramburs client - Narcis Fieraru</Explicatie>
    <FacturaID>47312</FacturaID>
    <FacturaNumar>MCS36634</FacturaNumar>
    <CodFiscal></CodFiscal>
    <Moneda>RON</Moneda>
  </Linie>
</Incasari>
```

Maparea (borderoul are header pe două rânduri, datele încep de la rândul 3):

| Tag | Sursă | Transformare |
|---|---|---|
| `Data` | `Data OP` | `dd.mm.yyyy` |
| `Numar`, `FacturaID` | `RefExp1` | ca atare |
| `Suma` | `Suma` | virgulă → punct, 2 zecimale |
| `Cont` | valuta folderului | `5125` RON / `5126` valută |
| `ContClient` | fix | `4111` |
| `Explicatie` | `Destinatar` | `Incasare ramburs client - <Destinatar>` |
| `FacturaNumar` | `nr_iesire` de pe factura legată | vezi mai jos |
| `CodFiscal` | — | gol |
| `Moneda` | valuta folderului | `RON` |

Coloanele `Awb`, `Data tur`, `Livrata`, `Numar`, `Numar OP`, `Beneficiar plata`,
`RefExp2`, `RefFact` nu intră în XML.

## Cum se găsește factura

Folderul de facturi conține exportul XML din Saga (`<VFPData><c_xml>`, de obicei
Windows-1252). Câmpurile folosite: `nr_iesire`, `denumire`, `total`, `inf_suplm`.

1. **Cheia e `RefExp1` = `inf_suplm`.** Pe borderoul de referință se potrivește 219/219.
2. **Totalul confirmă.** Diferențele până la 0,01 lei sunt rotunjiri normale și trec
   tăcut; între 0,02 și 0,10 trec, dar cu avertisment; peste 0,10 factura **nu** e
   considerată confirmată. Totalul departajează și când același `RefExp1` are mai
   multe facturi (tipic: factura inițială plus stornarea ei).

   `total` de pe factură e **în valuta facturii**, deci comparația e directă oricare ar
   fi valuta folderului — exportul nu are nevoie de un câmp de valută.
3. **Numele e al doilea control**, comparat fără diacritice, fără majuscule și fără
   să conteze ordinea sau forma juridică (SRL, PFA…). Dacă diferă, rândul **intră**
   în XML cu un avertisment — e normal ca pe colet să fie persoana și pe factură firma
   („Robert Dorin" → `DONARINI TRUST SRL`).
4. **Rezervă:** dacă `RefExp1` nu duce la o factură confirmată de total, se caută după
   nume + total. Reușita e semnalată ca avertisment, ca să fie verificată.

Un rând ajunge **sărit** (nu intră în XML, apare în raport) când: nu există nicio
factură nici pe `RefExp1`, nici pe nume; totalul nu confirmă niciuna; sau rămân mai
multe facturi la fel de plauzibile.

## Ce e suportat și ce nu

Suportat: borderouri **Cargus / Packeta în RON**, recunoscute după coloanele `Awb`
și `Destinatar`.

Nesuportat, raportat explicit și **fără** a fi marcat ca procesat (deci se reia
automat după ce adaugi maparea):

- **borderouri eMAG** — alt format cu totul (`Order ID`, `Fraction value`,
  `Client name`); maparea lor e în `mappings.md`, dar nu e implementată aici;
- orice fișier fără header recunoscut.

**Alte valute:** azi e configurat doar RON. Se adaugă cu `--set-folder <cale>
--moneda EUR` (cont `5126`) și nu au nevoie de cod nou: `total` de pe factură e deja
în valuta facturii. **HUF e ignorat deocamdată** — factorul de 100 din `mappings.md`
e documentat doar pentru eMAG, nu pentru Cargus.

## Anomalii pe care le semnalează scriptul

- `RefExp1` cu altă lungime decât tiparul dominant (posibil greșeală de tastare);
- `RefExp1` duplicat între rânduri;
- sumă ≤ 0;
- rânduri **sărite** — lipsește `Data OP`, `Suma`, `Destinatar` sau `RefExp1`, suma nu
  se poate interpreta, ori nu s-a găsit o factură sigură. Raportul spune numărul
  rândului din Excel și cât lipsește din total, ca nimic să nu se piardă în tăcere;
- **exporturi de facturi care se contrazic** — aceeași factură cu alt total în două
  exporturi. Câștigă exportul cu perioada mai târzie, dar diferența e semnalată;
- **un export de facturi lipsă** — când multe rânduri nu găsesc nicio factură, raportul
  spune ce perioadă acoperă exporturile și că probabil lipsește unul. Atunci: aduci
  exportul și rulezi `--reproceseaza` pe borderoul respectiv;
- factura găsită doar după nume, nume diferit față de factură, sumă diferită de total
  cu mai mult de 0,01, `RefExp1` care are și factură de storno.

Avertismentele nu opresc generarea: XML-ul se scrie oricum, cu rândurile bune.

## Neconfirmate la import — spune-i utilizatorului dacă apare problema

1. **Numele fișierului fără prefix `I_`** — `mappings.md` susține că prefixul e
   obligatoriu ca Saga să trateze fișierul ca import de încasări. S-a ales numele
   borderoului. **Dacă importul în Saga e refuzat, asta e prima cauză de verificat.**
2. **`Data` = `Data OP`** (data virării banilor). Rândul 1 din borderou, pus de
   contabil, indica `Livrata` (data livrării). De confirmat ce dată vrea în contabilitate.
3. **`FacturaID` = `RefExp1`** — util doar dacă facturile sunt importate cu același ID.
4. **Diacriticele** din nume — de verificat cum le afișează Saga după import.
