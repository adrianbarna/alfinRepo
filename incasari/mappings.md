# Mapare borderouri → XML import Saga „Încasări"

> **Șase surse, cinci formate** (decizia din 11.09.2026). Fiecare sursă e un agent
> separat, cu task-ul lui programat, jurnalul lui și raportul lui; codul e unul singur,
> `proceseaza.py`, cu câte un *profil* pe format. Formatul se recunoaște după coloane,
> nu după numele fișierului; valuta e dată de folder.
>
> | Sursă (`--sursa`) | Format | Folder | Stare |
> |---|---|---|---|
> | `cargus` — Cargus / Packeta | Cargus | `ron` | **implementat** |
> | `emag` — eMAG RO / BG / HU | eMAG | `ron` / `eur` / `huf` | mapat mai jos, neimplementat |
> | `sameday` — Sameday | Sameday | `ron` | mapat mai jos, neimplementat |
> | `trendyol` — Trendyol | „waybill" | `ron` | mapat mai jos, neimplementat |
> | `skroutz` — Skroutz | „waybill" (identic cu Trendyol) | `eur` | mapat mai jos, neimplementat |
> | `plationline` — PlatiOnline (card) | CSV PlatiOnline | `ron` | mapat mai jos, neimplementat |
>
> Exemplele reale pentru fiecare format stau în `exempluBorderouri/` (iulie 2026; doar
> local, în `.gitignore` — conțin date de clienți, iar repo-ul e public). Cifrele
> de potrivire cu facturile de mai jos sunt măsurate pe cele două exporturi din Saga:
> facturile în lei (`XML-2508-115350.XML`, 1.788 facturi, 01.05–31.07.2026) și cele în
> valută (`facturi-valuta.xlsx`, 11.09.2026, 317 facturi: 221 EUR, 96 HUF, aceeași
> perioadă) — vezi „Exportul de facturi în valută".

Formatul XML acceptat de Saga (Import documente → Încasări) este:

```xml
<Incasari>
  <Linie>
    <Data>…</Data>
    <Numar>…</Numar>
    <Suma>…</Suma>
    <Cont>…</Cont>              <!-- cont de trezorerie din clasa 5 -->
    <ContClient>…</ContClient>  <!-- opțional -->
    <Explicatie>…</Explicatie>
    <FacturaID>…</FacturaID>        <!-- opțional -->
    <FacturaNumar>…</FacturaNumar>  <!-- opțional -->
    <CodFiscal>…</CodFiscal>        <!-- opțional -->
    <Moneda>…</Moneda>              <!-- opțional -->
  </Linie>
  <Linie>…</Linie>
</Incasari>
```

Sursă: manualul Saga („Import date") + exemple funcționale de pe forumul Saga.
Valuta se determină din **folderul** în care se află borderoul (`borderouri/ron` /
`borderouri/eur` / `borderouri/huf`), nu din conținut.

## Reguli generale de fișier

| Regulă | Valoare |
|--------|---------|
| Nume fișier | **numele borderoului, cu spațiile înlocuite de `_`**, pentru toate sursele (ex. `Cargus_Packeta_Iulie_2026.xml`) — decizie internă din 31.08.2026. Notele vechi susțin că prefixul `I_` (ex. `I_30.03.2026.xml`) e obligatoriu ca Saga să trateze fișierul ca import de încasări. **Dacă importul e refuzat, asta e prima cauză de verificat.** |
| Encoding | UTF-8, cu declarația `<?xml version="1.0" encoding="UTF-8"?>` |
| Format dată | `dd.mm.yyyy` (ex. `30.03.2026`) |
| Separator zecimal | punct (`.`), 2 zecimale (ex. `60.90`) |
| Rădăcină | `<Incasari>` … `</Incasari>` |
| Câte fișiere | un XML per borderou, chiar dacă borderoul are mai multe date de plată |

## Decizii comune tuturor surselor (11.09.2026)

Pentru RON, regulile skill-ului Cargus au prioritate față de notițele vechi de mapare.

| Ce | Regula |
|---|---|
| `Data` | **data virării, unde borderoul o are** (Cargus `Data OP`, eMAG `Payout date`) — se potrivește cu extrasul de cont. Unde nu există, data indicată de client în rândul 1 al borderoului. |
| `Numar` / `FacturaID` | **numărul comenzii**, ca la Cargus (la Skroutz, `Waybill` e chiar codul comenzii). Unde borderoul nu-l are (Sameday, Trendyol), se ia din `inf_suplm` al facturii găsite. AWB-ul și `StatementID` nu intră în XML. |
| `Suma` | valoarea **de pe factură**, ca factura să se stingă exact (ca la Cargus). |
| `Cont` / `Moneda` | valuta folderului: `5125` / `RON`; `5126` / `EUR` sau `HUF`. |
| `ContClient` | `4111`, fix. |
| `Explicatie` | `Incasare ramburs client - <nume>`. Numele în alfabet grecesc sau chirilic se **transliterează în latină**: exporturile Saga sunt Windows-1252, iar pe facturi numele grecești apar deja transliterate („greeklish": Μιχάλης → MIXALIS). Aceeași transliterare servește și la comparația cu factura. |
| `CodFiscal` | gol. |
| Sume negative (refund, retur) | **linie negativă, legată de factura de storno** (factura cu `total` negativ). De validat la primul import în Saga. |
| Sume zero | nu intră în XML; apar în raport. |
| O factură, două borderouri | o factură se stinge **o singură dată**: jurnalul fiecărei surse ține `nr_iesire`-urile stinse, iar fiecare rulare le citește pe ale tuturor surselor. Un rând care ar stinge a doua oară aceeași factură e sărit și raportat. |
| Rânduri fără factură sigură | nu intră în XML; apar în raport, cu motiv (ca la Cargus). |

Cum se caută factura, pe sursă:

| Sursă | Cheie | Control | Potrivire, iulie 2026 |
|---|---|---|---|
| Cargus | `RefExp1` = `inf_suplm` | total, apoi nume | 219/219 |
| eMAG | `Order ID` = `inf_suplm`, pe **comandă** (fracțiunile adunate) | total, apoi nume | RO 44/44, BG 11/12, HU 15/17 — restul sunt plăți parțiale; comenzile cu sumă netă 0 nu se numără |
| Skroutz | `Waybill` = `inf_suplm` (codul comenzii Skroutz) | total, apoi nume | 46/48 |
| PlatiOnline | `Order Number` = `inf_suplm` | total, apoi nume; comenzile B2B (31xx) după sumă + zi pe seria `MCSCOD` | 46/49 pe cheie |
| Sameday | nu există cheie comună cu factura | **nume + sumă + dată** | 72/76 |
| Trendyol | nu există cheie comună cu factura | **nume + sumă + dată**; la clienții greci suma în lei a facturii în EUR | 12/21 pe nume românesc; grecii — vezi secțiunea Trendyol |

---

## Cargus / Packeta (folder `borderouri/ron` → cont 5125)

**Format-sursă activ**, procesat automat de skill-ul `incasari-cargus`
(`scripts/proceseaza.py`, sursa `cargus`).

Borderoul are **header pe două rânduri**; datele încep de la rândul 3.
Rândul 1 e o hartă parțială pusă de client, cu numele câmpurilor din schema veche
(`Den_partener`, `Nr_doc`); rândul 2 are numele reale ale coloanelor:

```
col C        col D          col G     col H       col K
Livrata      Destinatar     Suma      Data OP     RefExp1
```

| Tag XML         | Coloană xlsx     | Transformare                                                    | Exemplu (rândul 3 din `Cargus Packeta Iulie 2026.xlsx`) |
|-----------------|------------------|-----------------------------------------------------------------|------------------------------------------------------------|
| `Data`          | `Data OP` (H)    | deja `dd.mm.yyyy`; dacă celula e dată Excel → `dd.mm.yyyy`        | `30.07.2026`                                               |
| `Numar`         | `RefExp1` (K)    | ca atare, trim                                                   | `47312`                                                    |
| `Suma`          | `Suma` (G)       | **text cu virgulă românească** → punct, 2 zecimale; apoi suma de pe factură | `268,89` → `268.89`                              |
| `Cont`          | — (fix)          | `5125`                                                           | `5125`                                                     |
| `ContClient`    | — (fix)          | `4111`                                                           | `4111`                                                     |
| `Explicatie`    | `Destinatar` (D) | `Incasare ramburs client - <Destinatar>`                         | `Incasare ramburs client - Narcis Fieraru`                 |
| `FacturaID`     | `RefExp1` (K)    | ca atare (același ca `Numar`)                                    | `47312`                                                    |
| `FacturaNumar`  | factura legată   | `nr_iesire`                                                      | `MCS36634`                                                 |
| `CodFiscal`     | —                | gol                                                              | *(gol)*                                                    |
| `Moneda`        | — (fix)          | `RON`                                                            | `RON`                                                      |

Coloanele `Awb` (A), `Data tur` (B), `Livrata` (C), `Numar` (F), `Numar OP` (I),
`Beneficiar plata` (J), `RefExp2` (L), `RefFact` (M) **nu intră în XML**. Ultimele cinci
sunt goale pe toate rândurile borderoului din iulie 2026.

Scriptul raportează subtotalul pe fiecare `Data OP`, pentru reconciliere cu extrasul de
cont (borderoul din iulie 2026 are 4: 10/16/23/30.07).

Rezultat pentru borderoul din iulie 2026: `borderouri/ron/procesate/Cargus_Packeta_Iulie_2026.xml`
— 219 linii, total **26.570,21 RON** (26.569,26 în borderou; 87 de linii iau suma de pe
factură).

**`RefExp1` de lungime atipică nu sunt greșeli.** `9822` (4 cifre) și `26540717`
(8 cifre), semnalate luni la rând ca probabile greșeli de tastare, sunt `inf_suplm` reale
(facturile MCS36218 și MCS36251). 98xx e a doua serie de comenzi a magazinului și apare
și la PlatiOnline (9823, 9824, 9825). De la 11.09.2026 avertismentul de lungime apare
doar la rulările `--fara-facturi`: când facturile sunt legate, factura confirmă cheia.

---

## eMAG (sursa `emag`; RO → `ron`, BG → `eur`, HU → `huf`)

Același format în toate trei țările. Header pe două rânduri (rândul 1 = harta
clientului: `Nr_doc` peste `Order ID`, `Nume client/Den_partener` peste `Client name`,
`Data` peste `Order finalization date`, `Suma` peste `Fraction value`). Borderoul BG are
coloana `Fraction value [EUR]`, deci merge în folderul `eur`; harta de pe HU scrie
`Suma (/100)`.

Coloane: `Payout date`, `Reference period start/end`, `DP ID`, `Seller`, `Seller ID`,
`Supplier ID`, `Unique Identification Code`, `Order ID`, `OFID`, `Fraction type`,
`Client name`, `Order date`, `Order finalization date`, `Order eligibility date`,
`Payment method`, `Fraction value`, `Reference` (AWB-ul, la COD), `Courier`.

### O linie pe comandă (decizia din 11.09.2026)

eMAG plătește o comandă în mai multe **fracțiuni**, fiecare pe rândul ei:

| `Fraction type` | `Payment method` | Semn | Ce e |
|---|---|---|---|
| `CO Cashing` | `Online CARD` | + | plata cu cardul pe eMAG |
| `COD Cashing` | `Cash on delivery` | + | ramburs |
| `Refund CO` | `Online CARD` | − | banii întorși clientului |
| `Voucher` | `Voucher` | + / − | partea din preț acoperită de un voucher eMAG |

Fracțiunile se **adună pe `Order ID`** (atenție: eMAG dă `Order ID` când număr, când
text — la voucher e text) și comanda devine **o singură linie**. Exemplu: comanda
492052184 = COD 304,63 + voucher 24,27 = factura MCS35961 de 328,90 — luate separat,
niciuna nu confirmă factura. Consecințe:

- comanda plătită și returnată în același borderou dă 0 → nu intră în XML, apare în
  raport (7 comenzi în iulie 2026, RO);
- un refund pe o comandă plătită într-o lună anterioară dă o linie negativă, legată de
  factura de storno (ex. 491822092: −29,90 → MCS35999 de −29,90);
- un `Fraction type` necunoscut nu se adună: rândul e sărit și raportat.

### Maparea

| Tag XML | Sursă | Transformare |
|---|---|---|
| `Data` | `Payout date` | `yyyy-mm-dd` → `dd.mm.yyyy`. **Decizie 11.09.2026:** data virării, ca `Data OP` la Cargus (notițele vechi și harta clientului spuneau `Order finalization date`, care e ziua facturii) |
| `Numar`, `FacturaID` | `Order ID` | ca atare |
| `Suma` | suma fracțiunilor comenzii | punct zecimal, 2 zecimale; **HUF: împărțit la 100**; apoi suma de pe factură |
| `Cont` / `Moneda` | folderul | `5125`/`RON` (RO), `5126`/`EUR` (BG), `5126`/`HUF` (HU) |
| `ContClient` | fix | `4111` |
| `Explicatie` | `Client name` | `Incasare ramburs client - <Client name>`; chirilicul BG transliterat |
| `FacturaNumar` | factura legată | `nr_iesire` (cheia `Order ID` = `inf_suplm`) |
| `CodFiscal` | — | gol |

Traducerea mapării vechi (`<rand>`, care nu a mers la import): `NR_DOC` → `Numar` +
`FacturaID`; `SUMA` → `Suma`; `CONT` / `CONT_CORESP` → `Cont` / `ContClient`;
`DEN_PARTENER` intră în `Explicatie`; `VALUTA` → `Moneda`; `CURS` și `SUMA_VALUTA` nu au
tag — Saga aplică singură cursul pe contul 5126 (confirmat de client, 25.08.2026);
`DATA` era `Order finalization date`, acum `Payout date`.

### Potrivirea cu facturile (iulie 2026)

- **RO:** 51/51 de comenzi au factură cu `inf_suplm` = `Order ID` (seria de 9 cifre din
  exportul în lei). Pe comandă: 44 legate, 7 cu sumă netă 0. Pe fracțiune ar fi picat
  exact comenzile cu voucher.
- **BG:** 11/12, pe facturile `MCSBGN` în EUR. **HU:** 15/17 (plus 2 cu sumă netă 0), pe
  facturile `MCSHUF`.
- **Plăți parțiale.** Cele trei comenzi nelegate au doar o parte din bani în borderoul
  ăsta, restul vine în altă virare: BG 1026468629 — doar voucherul de 4,60 din factura
  de 45,98; HU 1136145436 — COD 86,36 din 103,87; HU 1136237414 — două vouchere (20,00)
  din 55,98. Cheia e sigură (`Order ID`, o singură factură), doar suma nu acoperă
  factura. **Propunere, de confirmat:** linia intră cu suma din borderou, legată de
  factură, cu avertisment „plată parțială: X din Y"; a doua virare stinge restul.

### HUF: împărțirea la 100 — confirmată pe facturi

`Fraction value` de pe HU e în forinți întregi (13.484 HUF ≈ 35 EUR, comparabil cu
prețurile RO și BG). Saga ține însă sumele în HUF **la sută de forinți**, ca în cursul
BNR (publicat pentru 100 HUF): pe `MCSHUF2828`, `val_val` 89,98 × `curs` 1,4088 = 126,76
lei = `baza_tva`. Deci `Fraction value` / 100 se compară direct cu totalul facturii —
15/17 comenzi o confirmă.

---

## Sameday (sursa `sameday`; folder `ron`)

Foaia cu date e prima (`New folder`; a doua, `Sheet1`, e goală). Header pe două rânduri
(rândul 1 = harta: `Nr_doc` peste `AWB`, `Nume client/Den_partener` peste
`Nume destinatar`, `Suma` peste `Suma ramburs`, `Data` peste `Data`).

Coloane: `AWB`, `Nume destinatar`, `Judet destinatar`, `Oras destinatar`,
`Adresa destinatar`, `Adresa ridicare`, `Referinta client`, `Suma ramburs`, `Data`,
`Data colectare ramburs`, `Numar colete livrate`.

| Tag XML | Sursă | Transformare |
|---|---|---|
| `Data` | `Data` (col I) | `yyyy-mm-dd` → `dd.mm.yyyy`. Borderoul nu are dată de virare; `Data` e ziua AWB-ului și coincide cu data facturii (72/72) |
| `Numar`, `FacturaID` | `inf_suplm` al facturii găsite | numărul comenzii (seria de 5 cifre, ca la Cargus) |
| `Suma` | `Suma ramburs` | deja număr; apoi suma de pe factură |
| `Explicatie` | `Nume destinatar` | `Incasare ramburs client - <Nume destinatar>` |
| restul | ca la regulile comune | `5125` / `RON` / `4111` |

**Nu există număr de comandă:** `Referinta client` = „Nicio referinta" pe toate cele 76
de rânduri. Factura se caută după **nume + sumă + dată**: în iulie 2026, 72/76 după nume
și sumă; unul ambiguu (85,88 — același client are două facturi de 85,89, pe 17.07 și 20.07)
e rezolvat de dată (AWB din 17.07), trei nu au factură pe nume.

Recomandare pentru magazin: numărul comenzii în „Referinta client" la emiterea AWB-ului
Sameday — atunci legarea devine pe cheie, ca la Cargus.

---

## Trendyol și Skroutz — formatul „waybill" (surse `trendyol` → `ron`, `skroutz` → `eur`)

Aceleași coloane la amândouă: `Line`, `Waybill`, `Pickup date`, `Delivery date`,
`Sender`, `Recipient`, `Note(Client)`, `Reference 1`, `Reference 2`, `OrderID`, `Amount`,
`Currency`, `Amount (w/ card)`, `DATA`. Harta din rândul 1: `Nr_doc` peste `Waybill`,
`Data` peste `Pickup date`, `Nume client/Den_partener` peste `Recipient`, `Suma` peste
`Amount`. `Note(Client)` repetă `Waybill`; `OrderID`, `Currency` și restul sunt goale.

**Cine e cine:** la Skroutz, `Waybill` e codul comenzii Skroutz (`aallzz-nnnnnnn`, ex.
`260518-9008682`); la Trendyol, un număr de 8 cifre. Scriptul desparte sursele după
acest tipar.

| Tag XML | Sursă | Transformare |
|---|---|---|
| `Data` | `Pickup date` | deja `dd.mm.yyyy` |
| `Numar`, `FacturaID` | Skroutz: `Waybill`; Trendyol: `inf_suplm` al facturii găsite | la Trendyol, nr. comandă Trendyol (ex. `11372867760-3965293854`) |
| `Suma` | `Amount` | 0 → rândul nu intră; negativ → linie pe storno; apoi suma de pe factură |
| `Explicatie` | `Recipient` | transliterat din grecește unde e cazul |
| `Cont` / `Moneda` | folderul | Trendyol `5125`/`RON`, Skroutz `5126`/`EUR` |

### Skroutz — pe cheie

**`Waybill` = `inf_suplm`**: facturile Skroutz (EUR, seria `MCS`) poartă codul comenzii.
Iulie 2026: **46/48 legate pe cheie**, plus 6 rânduri cu sumă 0 (două dublează un
waybill care are și sumă: 260616-3064879, 260618-4122179). Cele două nelegate sunt
cazuri de verificat de om, nu de cod:

- 260629-9269001, o firmă cu cod de TVA grecesc: borderoul are 80,48,
  factura MCS36224 are 99,80 — adică exact 80,48 plus 24% TVA. Skroutz a încasat fără
  TVA, factura s-a emis cu TVA.
- 260705-3032888 (9,66 EUR): facturat **în lei**, MCS36350, 50,59 lei cu
  `curs_ref` 5,2374 (singura factură din exportul în lei cu curs), fără `inf_suplm`.

Mai sunt facturi cu `inf_suplm` cu sufix (`260624-0224606-2`, `260728-7965967-2`) — a
doua factură pe aceeași comandă. Cheia se compară și fără sufix.

**`Pickup date` e 01.07.2026 pe toate rândurile**, inclusiv la comenzi din 10.07 (codul
începe cu `260710`). De aflat ce înseamnă coloana la Skroutz, altfel încasarea iese
datată înaintea comenzii.

### Trendyol — pe nume + sumă + dată

**Waybill-ul nu apare pe factură**; pe factură, `inf_suplm` e numărul comenzii
Trendyol. Legarea se face după nume + sumă + dată.

- **Clienții români** (facturi în lei): 12/21 legate după nume, inclusiv o pereche
  +347,30 / −347,30 (factura MCS36107 și stornarea ei MCS36213). **O comandă poate avea
  mai multe colete**: 64,40 + 58,65 pe același client = factura MCS36506 de 123,05 — rândurile
  se grupează pe nume + dată înainte de căutarea facturii, ca la eMAG pe comandă.
- **Clienții greci sunt facturați în EUR, dar plătiți în lei** în borderoul „Trendyol
  RON": 90,13 lei pentru MCS35815 de 17,19 EUR. Suma din borderou e **valoarea în lei a
  facturii** (`baza_tva` + `tva` din exportul în valută): 90,13 ↔ 90,12; 38,59 ↔ 38,59;
  77,10 ↔ 77,10 (două colete de 38,55); 70,13 ↔ 70,06. Numele sunt transliterate în
  Saga după convenția „greeklish": Μιχάλης → MIXALIS, Χρήστος → XRISTOS, Θανάσης →
  THANASIS, Λουκάς → LOYKAS (χ → X, θ → TH, η → I, ου → OY). Transliterarea din
  script trebuie să urmeze aceeași convenție. **De decis contabil:** încasare în lei pe
  factură în EUR (diferența de curs).

---

## PlatiOnline — plăți cu cardul (sursa `plationline`; folder `ron`)

Exemplul: `C Solution Iulie 2026.csv`. **CSV, nu xlsx**: separator `;`, fiecare valoare
între `#` (`#131.70#`), trei rânduri de preambul (`Factura PlatiOnline`, `PO`, harta
clientului), headerul pe rândul 4:

```
Nr.crt. | StatementID | Client | Trx ID | Order Number | Settle/Credit | Amount | Currency | Date
```

Harta clientului pune `Nr_doc` peste `StatementID`, `Nume client/Den_partener` peste
`Client`, `Suma` peste `Amount`, `Data` peste `Date`. `StatementID` e lotul de decontare
(4 în iulie 2026), nu comanda.

| Tag XML | Sursă | Transformare |
|---|---|---|
| `Data` | `Date` | **format american** `M/D/YYYY h:mm:ss AM/PM` → `dd.mm.yyyy`. Fișierul nu are data virării. Plata cu cardul vine cu 0–3 zile **înaintea** facturii (24 din 46) — de verificat la import |
| `Numar`, `FacturaID` | `Order Number` | ca atare |
| `Suma` | `Amount` | punct zecimal; `Credit` → negativ (de confirmat pe un exemplu real); apoi suma de pe factură |
| `Explicatie` | `Client` | `Incasare ramburs client - <Client>` |
| control | `Currency` | trebuie să fie valuta folderului, altfel avertisment |

Potrivirea, iulie 2026: **46/49 după `Order Number` = `inf_suplm`**. Comenzile 31xx sunt
**B2B**: facturile lor sunt pe seria `MCSCOD`, pe firmă și **fără `inf_suplm`**, dar se
potrivesc pe sumă + zi — 3163 (246,45, 06.07) → MCSCOD0553; 3164 (184,84, 07.07) →
MCSCOD0554: plătite cu cardul de o persoană, facturate pe firmă. 3166 → MCSCOD0557, pe
nume. Recomandare pentru magazin: `inf_suplm` completat și pe facturile `MCSCOD`.

---

## Exportul de facturi în valută

Facturile în EUR și HUF **nu sunt** în exportul XML în lei (niciun `nr_iesire` comun):
Saga le exportă separat, cu alte coloane. Exportul din 11.09.2026 a ieșit din Saga ca
`.xls` (foaia `xls-1109-144651`, același tipar de nume ca `XML-2508-115350`) și a fost
salvat din Excel ca `facturi-valuta.xlsx`:

```
tip  nr_iesire  cod  denumire  tvai  data  scadent  cod_valuta  curs  val_val  baza_tva
tva_val  tva  neachitat  data_doc  inf_suplm  den_agent  adaos  id_solicit
```

- **Nu există `total`.** Totalul în valuta facturii e **`val_val` + `tva_val`** (baza și
  TVA-ul în valută); `baza_tva` + `tva` sunt aceleași sume în lei.
- `cod_valuta` = `EUR` (221) sau `HUF` (96); la HUF sumele sunt la sută de forinți.
- Serii: `MCS` (Skroutz și Trendyol GR, EUR), `MCSBGN` (eMAG BG, EUR), `MCSHUF` (eMAG HU),
  `V-MKTP-HU-*` (eMAG Ungaria, fără `inf_suplm`).
- `inf_suplm`: cod Skroutz (134), `Order ID` eMAG BG (72) și HU (93), nr. comandă Trendyol
  (9).

**Scriptul citește exporturile `.xml` și `.xlsx`** din folderul de facturi, cu totalul
din `total` sau, unde lipsește, din `val_val` + `tva_val`; `cod_valuta` lipsă înseamnă
RON. **Un `.xls` nu se poate citi** (format binar vechi; scriptul folosește doar biblioteca
standard Python): e raportat ca „fișier de facturi necitit", cu excepția cazului în care
lângă el stă același export salvat ca `.xlsx` sau `.xml`.

**Fiecare borderou se leagă doar de facturile în valuta folderului lui** (`facturi_in()`):
RON cu RON, EUR cu EUR, HUF cu HUF. Un client facturat în EUR nu poate fi luat drept
omonimul lui dintr-un ramburs în lei. Excepția de rezolvat e Trendyol GR (încasare în lei
pe factură în EUR).

---

## De confirmat la primul import

1. **Numele fișierului fără prefixul `I_`** — vezi „Reguli generale de fișier".
2. **Liniile negative** (refund eMAG, retururi Trendyol/Skroutz, `Credit` PlatiOnline)
   legate de factura de storno — Saga le acceptă?
3. **Valută: `Suma` în valută, fără curs** — Saga, primind `Moneda` = EUR/HUF și cont
   5126, tratează `Suma` ca sumă în valută și aplică cursul singur (confirmat de client
   pentru EUR, 25.08.2026). De validat pe un import real EUR și HUF (la HUF, suma la sută
   de forinți, ca pe facturi).
4. **Plăți parțiale eMAG** — linie cu suma din borderou pe factură mai mare (propunerea
   din secțiunea eMAG).
5. **Trendyol GR** — încasare în lei pe factură în EUR.
6. **`Data`**: la Cargus și eMAG data virării; la PlatiOnline data plății, care poate fi
   înaintea facturii — Saga acceptă o încasare datată înaintea facturii pe care o stinge?
7. **Diacritice și transliterare** în nume — de verificat cum le afișează Saga.
8. **`FacturaID`** — conform manualului Saga, leagă încasarea de o factură importată tot
   din XML cu același ID; dacă facturile nu sunt importate cu ID = numărul comenzii,
   câmpul e probabil ignorat (nu ar trebui să blocheze importul).
9. **`Data` la Cargus = `Data OP` sau `Livrata`?** Harta pusă de client în rândul 1
   indica `Livrata`; s-a ales `Data OP`, iar decizia din 11.09.2026 („data virării unde
   există") o confirmă pentru toate sursele.
