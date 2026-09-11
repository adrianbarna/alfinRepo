# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Încasări — import borderouri în Saga

## Scop

Transformăm borderourile de ramburs (Excel) în fișiere XML de import pentru programul
de contabilitate **Saga** (Import documente → Încasări), la cabinetul ALFIN Consult.

Nu e un proiect software clasic: nu există build, teste sau dependințe. E un folder de
lucru contabil + două skill-uri cu un script Python care face conversia. Din 05.09.2026
folderul **e versionat**, ca subfolder în repo-ul `alfinRepo` — vezi „Versionare și release".

Există **șase surse de borderouri, în cinci formate** (decizia din 11.09.2026; formatul
se recunoaște după coloane, nu după nume de fișier). Fiecare sursă e un **agent
separat**: are task-ul ei programat, cardul ei de reminder, jurnalul ei și raportul ei;
codul e unul singur, `proceseaza.py`, cu câte un profil pe format.

| Sursă (`--sursa`) | Coloane-cheie | Folder | Stare |
|--------|---------------|--------|-------|
| **`cargus`** — Cargus / Packeta | `Awb`, `Destinatar`, `Data OP`, `RefExp1` | `ron` | **automatizat** (task programat) |
| **`emag`** — eMAG RO / BG / HU | `Order ID`, `Fraction type`, `Client name` | `ron` / `eur` / `huf` | profil implementat (11.09.2026), fără task încă |
| **`sameday`** | `AWB`, `Nume destinatar`, `Suma ramburs` | `ron` | idem |
| **`trendyol`** | `Waybill`, `Recipient`, `Amount` (Waybill = număr) | `ron` | idem |
| **`skroutz`** | aceleași coloane ca Trendyol (Waybill = `aallzz-nnnnnnn`) | `eur` | idem |
| **`plationline`** — plăți cu cardul, `.csv` | `StatementID`, `Order Number`, `Amount` | `ron` | idem |

Exemplele reale, câte unul pe format (iulie 2026), stau în `../exempluBorderouri/` — **doar
local, în `.gitignore`**: conțin nume, adrese și sume ale clienților, iar repo-ul e public.
La fel orice `.xlsx` / `.xls` / `.csv` / `.XML` din repo.

**Codul și datele stau în foldere separate** (decizie din 25.08.2026), ca să
poată fi versionat doar ce nu conține date de client:

```
alfinRepo/incasari/   ← AICI. În git, fără date de client.
  .claude/skills/incasari-cargus/          skill-ul de procesare
    references/configurare.md              fluxul de configurare (citit la nevoie)
  CLAUDE.md   mappings.md

~/.claude/incasari-saga/config.json        ← Configul. Per mașină, nu se livrează.

clienti/test-incasari/                     ← Datele. Niciodată în git.
  borderouri/ron/  .xlsx / .csv, toate sursele în lei   +  procesate/
  borderouri/eur/  eMAG BG, Skroutz                      +  procesate/
  borderouri/huf/  eMAG HU                               +  procesate/
  facturi/         exporturile XML din Saga (nume păstrat ca atare)
```

La ALFIN, datele stau în Google Drive (Mirror):
`C:\Users\Barna\My Drive\claude\incasari-saga\{borderouri,facturi}`.

Structura datelor — **valuta e dată de folder, sursa nu are folder**. Calea către ele
e absolută în `config.json`; se schimbă cu `--set-folder` / `--set-facturi`, niciodată
editând configul de mână. **Skill-ul se livrează fără căi setate** (decizie din
26.08.2026): pe o mașină nouă, prima configurare urmează
`references/configurare.md`, care propune căile și le salvează prin script.

**Azi e configurat doar RON** (decizie din 25.08.2026). EUR și HUF se adaugă cu câte o
comandă când intră în lucru eMAG BG/HU și Skroutz — `--set-folder borderouri/eur` și
`--set-folder borderouri/huf` (valuta vine din numele folderului, contul 5126 îl pune
scriptul). Până atunci, HUF nu are niciun borderou procesabil.

## Versionare și release

Codul de aici (**ambele skill-uri + scriptul**) e versionat **în alt folder**, ca plugin
Claude Code în marketplace-ul `alfin-consult`:

- **Repo local:** `alfinRepo/`, adică **părintele acestui
  folder** (`..`), branch `main`. Folderul de față e versionat în același repo.
- **GitHub:** `adrianbarna/alfinRepo`, remote **`origin`** — de acolo se instalează pluginul
  (Settings → Plugins, cu *Sync automatically* pornit). Din 05.09.2026 e singurul remote:
  vechiul GitHub și GitLab-ul au fost scoase.
- **Pluginul:** `../plugins/incasari-saga/`; skill-urile stau în
  `incasari-saga/skills/`.
  **Versiunea stă într-un singur loc:** `incasari-saga/.claude-plugin/plugin.json`
  (2.5.0 din 11.09.2026). Fără bump, push-ul nu ajunge la instalare, în tăcere.
- **Protocolul de release** (detaliat în CLAUDE.md-ul repo-ului): copiezi skill-urile de
  aici peste `../plugins/incasari-saga/skills/` → bump în
  `plugin.json` → `claude plugin validate ./` **din rădăcina repo-ului**
  → `git pull --rebase origin main` → commit → `git push origin main`. La client, în
  meniul `···` al marketplace-ului, *Check for updates* aduce versiunea imediat.
- **Cele două copii trebuie să rămână identice** (`diff -r`): sursa de adevăr e
  plugin-ul, aici e copia de lucru, testată pe borderoul de referință. De aceea
  SKILL.md-urile folosesc în comenzi `<skill-dir>` / `<skills-dir>` (folderul skill-ului,
  cale absolută): merg și din cache-ul pluginului, și de aici.

## Comenzi

Totul trece prin `.claude/skills/incasari-cargus/scripts/proceseaza.py` (python3,
fără dependințe externe — `.xlsx` e citit direct cu `zipfile` + `ElementTree`).
**Interpretorul:** `python3` pe macOS/Linux, `py -3` (sau `python`) pe Windows; în rest
comenzile sunt identice și **neutre față de shell** (merg la fel în bash și PowerShell,
o comandă pe linie, fără `&&`/`||`/redirecționări). Fără fișiere de lansare `.bat`/`.sh`.

```
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py             # procesează doar borderourile noi
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --dry-run   # arată ce ar face, nu scrie nimic
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --reproceseaza "Cargus Packeta Iulie 2026.xlsx"  # după ce sosește un export de facturi lipsă
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --sursa emag  # alt agent: cargus (implicit), emag, sameday, trendyol, skroutz, plationline
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --folder <cale> --moneda EUR   # rulare punctuală, nu atinge configul
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --folder <.../ron> --folder <.../eur>   # mai multe foldere; valuta din numele folderului
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --set-folder <cale> [--moneda RON]  # scrie config.json și iese
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --set-facturi <cale>   # folderul cu facturi
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --set-email a@b.ro,c@d.ro  # cui se trimite raportul
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --arata-config  # configurarea curentă (folosit de config-incasari-cargus)
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --fara-facturi  # nu lega facturile (FacturaNumar gol)
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --json      # raport structurat
```

Coduri de ieșire: `0` = a mers (posibil cu avertismente), `2` = **configurare lipsă**
(întreabă utilizatorul unde ține borderourile **sau facturile**, **nu ghici calea**,
apoi `--set-folder` / `--set-facturi`), `1` = eroare.

Nu există suită de teste. Verificarea unei modificări în script se face cu
`--dry-run --reproceseaza <borderou>` pe `Cargus Packeta Iulie 2026.xlsx`, al cărui
rezultat de referință e **219 linii, total 26570.21 RON**, defalcat pe 4 date de plată
(10/16/23/30.07.2026 = 7178.35 / 6334.85 / 6951.57 / 6105.44), **fiecare linie cu
`FacturaNumar` completat (219 `nr_iesire` distincte), niciun rând sărit**, și
**87 de linii cu suma preluată de pe factură (diferență totală +0,95 RON)**.
Avertismente: 13 — 8 de nume (persoană pe colet vs. firmă pe factură), 3 de storno și
2 de sumă peste 0,01 (rândurile 12 și 123). Cele 2 de lungime `RefExp1` (rândurile 35 și
49) apar din 11.09.2026 doar cu `--fara-facturi` — vezi „Stare curentă".

Refactorizarea pe surse (11.09.2026) a fost verificată pe acest borderou: XML-ul iese
**identic la byte** cu cel produs de versiunea anterioară, iar raportul și JSON-ul la fel
(în JSON apar în plus doar cheile `sursa` și `alte_surse`).

## Reguli de lucru

- **Nu genera XML de mână și nu citi borderourile cu alte unelte.** Un borderou are sute
  de rânduri; scriptul e determinist, XML-ul scris de model nu e.
- **Nu edita `<date>/borderouri/<valuta>/procesate/.procesate.json`** direct — e
  jurnalul scriptului.
- **Nu căuta facturile de mână.** Legarea rând ↔ factură o face scriptul; folderul
  `facturi/` are mii de înregistrări.
- **Nu crea fișiere de lansare (`.bat`, `.ps1`, `.sh`) și nu instala Python.** Scriptul
  se apelează direct, pe Windows cu `py -3`; dacă Python lipsește, i se spune
  utilizatorului să-l instaleze de pe python.org.
- **Raportează întotdeauna avertismentele și rândurile sărite** în rezumatul din chat,
  în română. Sunt lucruri de verificat înainte de importul în Saga.

## Arhitectură

Un singur skill, `incasari-cargus`, cu un script care tratează **câte un folder per valută**
și **câte o sursă per rulare** (`--sursa`, implicit `cargus`). Valuta se determină din
**folderul** în care se află borderoul, nu din conținut:

| Folder | Valută | Cont | Surse | Stare |
|--------|--------|------|-------|-------|
| `borderouri/ron` | RON | 5125 | Cargus, eMAG RO, Sameday, Trendyol, PlatiOnline | **activ** (doar Cargus implementat) |
| `borderouri/eur` | EUR | 5126 | eMAG BG, Skroutz | de adăugat odată cu sursele lui |
| `borderouri/huf` | HUF | 5126 | eMAG HU | de adăugat odată cu eMAG |

**Surse, profiluri, agenți (11.09.2026).** În script, `SURSE` ține cele șase surse, iar
`FORMATE` coloanele după care se recunoaște fiecare format; `PROFILURI` ține funcția care
procesează o sursă: `proceseaza_cargus`, `_emag`, `_plationline`, `_skroutz`, `_sameday`,
`_trendyol`. Legarea pe cheie trece prin `alege_factura()` (cu eticheta cheii în mesaje),
cea după nume prin `alege_factura_nume()`, plățile parțiale eMAG prin
`alege_factura_emag()`. O rulare procesează **doar** fișierele
sursei ei; fișierele celorlalte surse sunt recunoscute și lăsate neatinse (apar în JSON
ca `alte_surse` și în rezumatul din chat, nu pe e-mail). Un `--sursa` fără profil
implementat iese cu codul 1. Fișierele pe care nu le recunoaște niciun format (sau care
nu se pot citi) le raportează doar sursa colectoare, `cargus`, ca să nu apară de șase
ori pe lună.

Detalii greu de dedus din citirea unui singur fișier:

- **`config.json`** stă la **`~/.claude/incasari-saga/config.json`** — per mașină,
  **nu** în folderul skill-ului (decizie din 26.08.2026), ca skill-ul să se
  poată copia la client fără căile lui Adrian. Un `config.json` rămas lângă skill din
  instalări vechi are încă prioritate; `INCASARI_CONFIG` poate indica alt fișier.
  Ține lista de foldere, calea către `facturi` și lista de adrese de e-mail (`email`);
  `--set-folder` salvează calea **relativ la rădăcina proiectului** dacă e înăuntru,
  altfel absolut. Datele fiind acum în afara proiectului, căile sunt absolute.
  Rădăcina se deduce din structura folderelor părinte (`.claude/skills/<skill>/`) —
  deci **skill-ul trebuie să rămână la `.claude/skills/incasari-cargus/`**, altfel se
  rupe detecția.
- **Evidența** e per folder **și per sursă**, în `<folder>/procesate/`, **cheie = numele
  fișierului**: `.procesate.json` pentru Cargus (numele vechi, ca task-ul existent să
  meargă neschimbat), `.procesate-<sursa>.json` pentru celelalte. Un jurnal comun ar fi
  scris de șase task-uri, iar al doilea care scrie șterge intrările primului — luna
  următoare primul reprocesează tot și iese XML dublu. Redenumirea unui borderou îl face
  „nou"; mutarea unui folder de valută nu strică nimic, jurnalele călătoresc cu el.
- **O factură se stinge o singură dată.** Din 11.09.2026 fiecare intrare de jurnal ține
  și `facturi` — `nr_iesire`-urile stinse de borderoul acela. La fiecare rulare,
  `incarca_folosite()` citește jurnalele **tuturor** surselor din folderele procesate
  (fiecare task scrie doar jurnalul lui, dar le citește pe toate); un rând care ar
  stinge a doua oară o factură e sărit, cu motivul „factura X e deja stinsă prin Y".
  Borderourile date la `--reproceseaza` nu se numără. Protecția acoperă borderourile
  procesate de acum încolo: intrările vechi de jurnal nu au `facturi`. Consecință utilă:
  un borderou corectat și pus sub **alt nume** nu mai dublează încasările — se folosește
  `--reproceseaza` pe numele vechi.
- **Ieșirea**: `<folder>/procesate/<numele borderoului, cu spațiile înlocuite de _>.xml`
  (cerință din 31.08.2026), un singur XML per borderou, chiar dacă borderoul
  conține mai multe date de plată.
- **Fișiere nerecunoscute** sunt raportate explicit (doar de `cargus`) și **nu** se
  marchează ca procesate — se reiau automat. Un fișier al unei surse încă neimplementate
  așteaptă, nemarcat, până îi vine agentul.
- Se citesc `.xlsx` și `.csv` (PlatiOnline); fișierele temporare Excel (`~$*`) sunt ignorate.
- **Raportul de e-mail** e scris în `<folder>/procesate/ultimul-raport.txt` pentru Cargus și
  `ultimul-raport-<sursa>.txt` pentru celelalte (suprascris la fiecare rulare) și livrat
  în `--json` ca `email.subiect` / `email.corp` /
  `email.catre`. **Scriptul nu trimite e-mail** — îl trimite skill-ul cu unealta de
  Gmail. Se compune și când niciun rând nu a putut fi legat de o factură: atunci nu
  există XML, dar lista rândurilor sărite e tot ce contează.
- **Windows / Claude Desktop (decizia din 03.09.2026).** La client skill-ul rulează din
  **aplicația Claude Desktop, fila Code** (Claude Code Desktop), **nu din Cowork**: Cowork
  rulează bash într-o mașină virtuală Linux (Hyper-V) care pe Windows are un bug cunoscut
  de pornire („Workspace unavailable… isolated Linux environment failed to start") — de
  aici „comenzile bash nu au mers deloc" la prima încercare —, nu citește
  `.claude/skills/` din folder, iar task-urile lui programate nu pot fi legate de un
  folder local. Fila Code rulează nativ, citește `CLAUDE.md` + `.claude/skills/` din
  folderul de lucru, iar fără Git for Windows shell-ul e **PowerShell** (5.1 sau 7), care
  **nu traduce** comenzi bash — de aceea instrucțiunile skill-urilor sunt neutre față de
  shell și scriptul se apelează cu `py -3`. Rularea săptămânală: **Routines → New routine
  → Local**, folder = folderul proiectului (`incasari/`), *Weekly*; prima dată **Run now**
  și „always allow" la promptul de Python, ca rulările următoare să nu se blocheze.
  Scriptul forțează UTF-8 pe consolă
  (`errors=replace`, ca un nume cu diacritice să nu oprească raportul) și LF în fișiere,
  ca XML-ul să fie identic pe orice sistem. Fără Python instalat nu merge nimic; nu se
  instalează automat.

## Legarea facturilor (`facturi/`)

Folderul `facturi/` conține exporturile XML de facturi din Saga: `<VFPData><c_xml>`,
encoding **Windows-1252** — expat nu-l știe, așa că scriptul decodează singur și scoate
declarația înainte de parsare. Câmpuri folosite: `nr_iesire`, `denumire`, `total`,
`inf_suplm`, `curs_ref`.

- **Exporturile se acumulează și se suprapun.** Unul poate acoperi mai multe luni (cel
  din 25.08.2026 acoperă mai–iulie), deci **perioada se deduce din conținut**
  (`min`/`max` pe `<data>`), niciodată din numele fișierului. Se citesc recursiv toate
  XML-urile din folder.
- **La `nr_iesire` duplicat între exporturi câștigă exportul a cărui perioadă se termină
  mai târziu** (departajare pe nume). Dacă versiunile diferă ca `total` sau `denumire`,
  se avertizează: o factură corectată în tăcere ar schimba încasarea fără urmă.
- **Când multe rânduri nu găsesc nicio factură**, raportul numește perioada acoperită și
  spune că probabil lipsește un export — nu înșiră sute de rânduri nepotrivite.

### Exportul nu are câmp de valută — și nu contează

Exportul nu spune în ce valută e o factură (singurul indiciu ar fi `curs_ref`, `0` la
1787 din 1788). **Nu contează, fiindcă `total` e exprimat în valuta facturii**
(confirmat pe 25.08.2026), iar factura găsită prin `RefExp1` e implicit în
aceeași valută ca borderoul. Deci comparația e directă, în orice valută.

A existat aici o încercare de a converti prin `curs_ref` — **greșită**, ștearsă. Dacă
reapare tentația: `total` **nu** e în lei pentru o factură în valută.

Verificat pe 11.09.2026: exportul XML de mai sus conține **doar facturile în lei**.
Facturile în EUR și HUF vin într-un export separat, cu `cod_valuta` și totalul în
valută ca `val_val` + `tva_val` (HUF la sută de forinți) — vezi `mappings.md`,
„Exportul de facturi în valută". Singura excepție din exportul în lei e MCS36350
(`curs_ref` 5,2374): o comandă Skroutz de 9,66 EUR facturată în lei.

Scriptul citește toate exporturile `.xml` și `.xlsx` din folder (un `.xls` e raportat ca
necitit, dacă nu are lângă el aceeași formă citibilă), le indexează o dată pe toate și o
dată pe valută, iar un borderou se leagă **doar de facturile în valuta folderului lui**
(`facturi_in()`). Verificat: cu exportul în valută adăugat în folder, XML-ul Cargus din
iulie iese identic; raportul primește doar rândul „pe valute: EUR 221, HUF 96, RON 1788".

- **Cheia: `RefExp1` = `inf_suplm`** — 219/219 pe borderoul de referință. `nr_iesire`
  e unic (1788/1788), `inf_suplm` **nu** e (153 duplicate, tipic factură + storno).
- **Totalul confirmă**, cu toleranță: `TOL_TACITA` = 0,01 (rotunjire normală, tace),
  până la `TOL_MAX` = 0,10 trece cu avertisment, peste — factura nu e confirmată.
  Pe borderoul din iulie: 129 identice, 85 la 0,01, una la 0,02, una la 0,08.
  **Nu strânge toleranța la egalitate strictă** — ar sări ~40% din rânduri.
- **Numele e al doilea control**, nu cheie: fără diacritice, fără majuscule, ordinea
  și forma juridică ignorate, potrivire prin incluziune de cuvinte. Nepotrivirea dă
  doar avertisment — pe colet e persoana, pe factură firma („Robert Dorin" →
  `DONARINI TRUST SRL`), 8 cazuri legitime în iulie.
- **Căutarea după nume e strict rezervă**, doar când `RefExp1` nu duce la o factură
  confirmată de total. Dacă e folosită în paralel cu `RefExp1`, un omonim cu aceeași
  sumă face ambiguă o potrivire deja sigură (3 rânduri pierdute în iulie).
- **Rândurile fără factură sigură nu intră în XML** (decizie din 25.08.2026) și
  ajung în raportul de e-mail, cu motiv, sumă și numărul rândului.
- **`<Suma>` ia valoarea de pe factură, nu din borderou** (decizie din
  25.08.2026), ca factura să se stingă exact, fără sold rămas pe 4111. Compromisul
  asumat: încasarea nu mai e identică cu ce a virat curierul — pe borderoul din iulie,
  87 de linii diferă, în total **+0,95 RON** (26569,26 în borderou → 26570,21 în XML).
  Diferențele peste 0,01 sunt raportate individual; restul, agregat.
- **Saga acceptă `<Moneda>` cu cont 5126 și aplică singură cursul** (confirmat de
  client, 25.08.2026): 5125 pentru RON, 5126 pentru valută.

## Contractul XML cu Saga

Structura corectă (manualul Saga, confirmată de client) e `<Incasari><Linie>…`,
**nu** `<Incasari><rand>…` cum era în prima încercare (care nu a mers la import):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Incasari>
  <Linie>
    <Data>30.07.2026</Data>          <!-- dd.mm.yyyy -->
    <Numar>47312</Numar>
    <Suma>268.89</Suma>              <!-- punct zecimal, 2 zecimale -->
    <Cont>5125</Cont>                <!-- cont trezorerie clasa 5 -->
    <ContClient>4111</ContClient>
    <Explicatie>Incasare ramburs client - Narcis Fieraru</Explicatie>
    <FacturaID>47312</FacturaID>
    <FacturaNumar>MCS36634</FacturaNumar>   <!-- nr_iesire de pe factura legata -->
    <CodFiscal></CodFiscal>
    <Moneda>RON</Moneda>
  </Linie>
</Incasari>
```

**Numele fișierului:** notele vechi susțin că prefixul `I_` e obligatoriu ca Saga să
trateze fișierul ca import de încasări (ex. `I_30.03.2026.xml`). Pentru Cargus s-a ales
totuși numele borderoului (din 31.08.2026 cu spațiile înlocuite de `_`), la cerere — **dacă importul e refuzat, ăsta e primul lucru de verificat.**

## Maparea Excel → XML

Sursa de adevăr e **`mappings.md`**, care acoperă toate cele șase surse în detaliu, cu
exemple, cifrele de potrivire cu facturile și deciziile comune din 11.09.2026. Rezumat
pentru orientare:

### Cargus / Packeta (folderul `borderouri/ron`) — cel folosit azi

Header pe **două rânduri** (rândul 1 e o hartă parțială pusă de client cu numele din
schema veche, rândul 2 are numele reale); datele încep de la rândul 3.

| Tag XML | Sursă | Transformare |
|---------|-------|--------------|
| `Data` | `Data OP` (col H) | → `dd.mm.yyyy` |
| `Numar`, `FacturaID` | `RefExp1` (col K) | ca atare |
| `Suma` | `Suma` (col G) | virgulă → punct, 2 zecimale |
| `Cont` / `Moneda` | valuta folderului | `5125` / `RON` |
| `ContClient` | fix | `4111` |
| `Explicatie` | `Destinatar` (col D) | `Incasare ramburs client - <Destinatar>` |
| `FacturaNumar` | `nr_iesire` din `facturi/` | vezi „Legarea facturilor" |
| `CodFiscal` | — | gol |

`Awb`, `Data tur`, `Livrata`, `Numar`, `Numar OP`, `Beneficiar plata`, `RefExp2`,
`RefFact` nu intră în XML.

Anomalii semnalate automat: `RefExp1` duplicat, sumă ≤ 0, factură stinsă deja prin alt
borderou, și rânduri **sărite** (lipsă `Data OP` / `Suma` / `Destinatar` / `RefExp1`) —
cu numărul rândului din Excel și cât lipsește din total. `RefExp1` cu lungime diferită de
tiparul dominant se semnalează doar la `--fara-facturi`.

### Celelalte cinci surse — mapate, neimplementate

Tabele complete în `mappings.md`. Deciziile comune (11.09.2026): `Data` = data virării
unde există (eMAG `Payout date`), altfel data din rândul 1; `Numar`/`FacturaID` =
numărul comenzii; `Suma` de pe factură; linie negativă pe factura de storno; eMAG o
linie pe comandă (fracțiunile adunate); nume grecești/chirilice transliterate.
**Factorul HUF: `Suma` = `Fraction value` / 100** (confirmat de utilizator pe
15.08.2026 și, pe 11.09.2026, pe facturile HUF: Saga ține HUF la sută de forinți).

Câmpurile vechi `DEN_PARTENER`, `CURS`, `SUMA_VALUTA` nu au tag în formatul nou: numele
cumpărătorului intră în `Explicatie`, iar cursul/suma în valută sunt acoperite de `Suma`
(în valuta folderului) + `Moneda`.

Facturile în valută vin într-un **export separat**, cu alte coloane (`cod_valuta`,
`val_val`, `tva_val`, fără `total`) — vezi `mappings.md`, „Exportul de facturi în
valută". Scriptul îl citește ca `.xlsx` (sau XML); un `.xls` e raportat ca necitit.

## Stare curentă / next steps

1. **Cargus / Packeta — automatizat**, cu `FacturaNumar` completat din `facturi/`:
   `borderouri/ron/procesate/Cargus_Packeta_Iulie_2026.xml` — 219 linii, 26.570,21 RON,
   toate legate de factură. **De testat importul în Saga.**
2. **Refactorizare pe surse (11.09.2026) — gata**, verificată pe borderoul de referință
   (XML identic la byte). Scriptul recunoaște toate cele șase surse, citește `.csv`,
   ține jurnal și raport pe sursă, nu stinge o factură de două ori și ia valuta din
   numele folderului.
3. **Toate cele șase profiluri sunt implementate (11.09.2026)** și verificate pe
   exemplele din `../exempluBorderouri/`, cu ambele exporturi de facturi — rezultatul de
   comparat la orice modificare:

   | Sursă | Borderou | Linii | Total | Sărite | Ignorate |
   |---|---|---|---|---|---|
   | `emag` | RO1 / BG1 / HU1 | 44 / 12 / 17 | 4.196,68 RON / 178,55 EUR / 3.126,31 HUF | 0 | 7 / 0 / 2 |
   | `plationline` | C Solution | 49 | 4.954,45 RON | 0 | 0 |
   | `skroutz` | Skroutz EUR | 46 | 931,11 EUR | 2 | 6 |
   | `sameday` | Sameday | 73 | 7.054,78 RON | 3 | 0 |
   | `trendyol` | Trendyol RON | 19 (din 21 de rânduri) | 966,26 RON | 0 | 0 |

   Rulate pe rând, toate șase pe aceleași foldere: nicio factură stinsă de două surse; a
   doua rulare nu mai găsește nimic nou. O plată parțială eMAG completată într-o virare
   ulterioară stinge factura („completează factura …"), iar o plată întreagă repetată e
   sărită.
   Rămân de făcut: task-urile programate (câte unul pe sursă), cardurile de reminder,
   `installation.md` și `ai-architecture.html`.
4. **Un agent pe sursă (11.09.2026):** câte un task programat pentru fiecare sursă, după
   modelul „Procesare borderou cargus", la 30 de minute unul de altul pe 5 ale lunii;
   task-ul de reminder de pe 1 ale lunii creează, pe lângă cardul de facturi, câte un
   card „Adauga borderoul <sursă> in Drive" pentru Paula. Fiecare task pornește doar cu
   cardul de facturi **și** cardul lui în `Done`; altfel trimite reminder doar despre
   borderoul lui. Cardurile și task-urile se adaugă odată cu fiecare profil. Pentru
   verificarea dublei stingeri, task-urile trebuie să stage-uiască **toate**
   `procesate/.procesate*.json`, nu doar jurnalul lor.
5. **De confirmat la primul import** (detaliat în `mappings.md`, secțiunea
   „De confirmat la primul import", și în `SKILL.md`):
   - numele fișierului fără prefixul `I_` — **prima cauză de verificat dacă importul e refuzat**;
   - `FacturaID` = `RefExp1` — util doar dacă facturile sunt importate cu același ID;
   - diacriticele în Saga după import UTF-8;
   - **totalul XML e cu 0,95 RON mai mare decât borderoul** (suma vine de pe factură);
     de confirmat că reconcilierea cu extrasul de cont nu se supără;
   - liniile negative, pe factura de storno (eMAG, Trendyol, Skroutz, PlatiOnline);
   - **cele 3 `RefExp1` cu factură de storno** (47356, 47364, 47170): banii au fost
     încasați, dar factura e stornată — se importă încasarea pe factura inițială?
   - **diferențele de 0,08 și 0,02** (rândurile 12 și 123) — restul sunt de 0,01.
   - rezolvat pe 11.09.2026: `RefExp1` `9822` și `26540717` **nu** sunt greșeli de
     tastare — sunt `inf_suplm` reale (MCS36218, MCS36251); 98xx e a doua serie de comenzi.
6. **Cheile facturilor, verificate pe 11.09.2026.** Din cele 58 de facturi fără
   `inf_suplm` din exportul în lei, niciuna nu e de eMAG client: 8 sunt `V-MKTP-*` /
   `H-MKTP-*` către DANTE INTERNATIONAL SA (eMAG ca partener), 38 `MCSCOD*` (B2B,
   plătite prin PlatiOnline) și 12 `MCS`. Comenzile eMAG RO **au** `inf_suplm` = `Order ID`
   (seria de 9 cifre, 51/51); eMAG BG/HU și Skroutz au cheia pe facturile în valută.
6. **Windows (03.09.2026) — de testat pe PC-ul de lucru**, din fila Code:
   `py -3 … --arata-config` (prima linie arată versiunea de Python și sistemul),
   configurarea prin `references/configurare.md`, `--dry-run`, o rulare reală (XML UTF-8 cu
   LF), apoi task-ul local săptămânal cu **Run now**. De rezolvat **trimiterea e-mailului
   în rulare neasistată**: `SKILL.md` cere confirmare la prima trimitere, iar conectorul
   Gmail trebuie configurat și aprobat („always allow") în task, altfel rularea se
   blochează la prompt. Dacă numele cu diacritice apar stricate în chat pe PowerShell 5.1,
   e doar afișarea — XML-ul e corect.

## Fișiere de referință

- `.claude/skills/incasari-cargus/` — skill-ul de procesare: `SKILL.md` (fluxul
  conversațional) + `scripts/proceseaza.py`
- `.claude/skills/incasari-cargus/references/configurare.md` — fluxul de configurare:
  prima rulare pe o mașină nouă și orice schimbare de căi/adrese ulterioară
- `~/.claude/incasari-saga/config.json` — configul mașinii curente (foldere, facturi,
  e-mail); se creează la prima configurare, nu se livrează cu skill-ul
- `<date>/facturi/` — exporturile XML de facturi din Saga, sursa pentru `FacturaNumar`
- `<date>/borderouri/<valuta>/procesate/ultimul-raport.txt` — raportul ultimei rulări,
  textul trimis pe e-mail
- `mappings.md` — maparea xlsx → XML pentru ambele formate (**sursa de adevăr**)
- `<date>/borderouri/ron/Cargus Packeta Iulie 2026.xlsx` — borderoul de referință
- `<date>/borderouri/<valuta>/procesate/` — XML-urile generate + `.procesate.json`

`<date>` = folderul de date din `config.json`, azi `clienti/test-incasari/`.
Referite în notele vechi, dar **inexistente pe disc** — șterse din proiect pe
25.08.2026; ce descriau a rămas în documentație:

- `emag RO2 Aprilie 2026.xlsx` — borderoul eMAG, sursa coloanelor pentru maparea din
  `mappings.md`. Maparea rămâne, exemplul nu.
- `I_30.03.2026.xml` — exemplu XML eMAG în formatul corect `<Linie>`. Formatul e mai
  sus, în „Contractul XML cu Saga".
- `exemplu_incasare.xml` (prima încercare, cu structura greșită `<rand>`),
  `xml versio1.docx`, `Import_documente.PNG`.
