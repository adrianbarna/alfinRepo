# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Încasări — import borderouri în Saga

## Scop

Transformăm borderourile de ramburs (Excel) în fișiere XML de import pentru programul
de contabilitate **Saga** (Import documente → Încasări), la cabinetul ALFIN Consult.

Nu e un proiect software clasic: nu există build, teste sau dependințe. E un folder de
lucru contabil + două skill-uri cu un script Python care face conversia. Din 05.09.2026
folderul **e versionat**, ca subfolder în repo-ul `alfinRepo` — vezi „Versionare și release".

Există **două formate-sursă**, fără nicio coloană comună (formatul se recunoaște
după coloane, nu după nume de fișier):

| Format | Coloane-cheie | Stare |
|--------|---------------|-------|
| **Cargus / Packeta** | `Awb`, `Destinatar`, `Data OP`, `RefExp1` | **automatizat** — skill-ul `incasari-cargus` |
| **eMAG** | `Order ID`, `Fraction value`, `Client name` | mapat în `mappings.md`, **neimplementat** |

**Codul și datele stau în foldere separate** (decizie din 25.08.2026), ca să
poată fi versionat doar ce nu conține date de client:

```
alfinRepo/incasari/   ← AICI. În git, fără date de client.
  .claude/skills/incasari-cargus/          skill-ul de procesare
  .claude/skills/config-incasari-cargus/   skill-ul de configurare (prima rulare)
  CLAUDE.md   mappings.md

~/.claude/incasari-saga/config.json        ← Configul. Per mașină, nu se livrează.

clienti/test-incasari/                     ← Datele. Niciodată în git.
  borderouri/ron/  .xlsx (Cargus/Packeta sau eMAG)  +  procesate/
  facturi/         exporturile XML din Saga (nume păstrat ca atare)
```

Structura datelor — **valuta e dată de folder, sursa nu are folder**. Calea către ele
e absolută în `config.json`; se schimbă cu `--set-folder` / `--set-facturi`, niciodată
editând configul de mână. **Skill-ul se livrează fără căi setate** (decizie din
26.08.2026): pe o mașină nouă, prima configurare o face skill-ul
`config-incasari-cargus`, care întreabă utilizatorul căile și le salvează prin script.

**Azi skill-ul e doar pe RON** (decizie din 25.08.2026). EUR se adaugă cu o
singură comandă când apare primul borderou — `--set-folder borderouri/eur --moneda EUR`
creează intrarea cu contul 5126. **HUF e ignorat deocamdată.**

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
  (2.0.0 din 05.09.2026). Fără bump, push-ul nu ajunge la instalare, în tăcere.
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
python3 .claude/skills/incasari-cargus/scripts/proceseaza.py --folder <cale> --moneda EUR   # rulare punctuală, nu atinge configul
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
Avertismente: 15 — 8 de nume (persoană pe colet vs. firmă pe factură), 3 de storno,
2 de sumă peste 0,01 (rândurile 12 și 123) și 2 de lungime `RefExp1` (rândurile 35 și 49).

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

Un singur skill, `incasari-cargus`, cu un script care tratează **câte un folder per valută**.
Valuta se determină din **folderul** în care se află borderoul, nu din conținut:

| Folder | Valută | Cont | Stare |
|--------|--------|------|-------|
| `borderouri/ron` | RON | 5125 | **singurul activ azi** |
| `borderouri/eur` | EUR | 5126 | de adăugat când apare primul borderou |
| — | HUF | 5126 | ignorat deocamdată

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
- **Evidența** e per folder, în `<folder>/procesate/.procesate.json`, **cheie = numele
  fișierului xlsx**. Redenumirea unui borderou îl face „nou" și se reprocesează.
  Mutarea unui folder de valută nu strică nimic: jurnalul călătorește cu el.
- **Ieșirea**: `<folder>/procesate/<numele borderoului, cu spațiile înlocuite de _>.xml`
  (cerință din 31.08.2026), un singur XML per borderou, chiar dacă borderoul
  conține mai multe date de plată.
- **Formate nesuportate** (eMAG, header nerecunoscut) sunt raportate explicit și **nu**
  se marchează ca procesate — se reiau automat când se adaugă maparea.
- Fișierele temporare Excel (`~$*.xlsx`) sunt ignorate.
- **Raportul de e-mail** e scris în `<folder>/procesate/ultimul-raport.txt` (suprascris
  la fiecare rulare) și livrat în `--json` ca `email.subiect` / `email.corp` /
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

Sursa de adevăr e **`mappings.md`**, care acoperă ambele formate în detaliu, cu exemple.
Rezumat pentru orientare:

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

Anomalii semnalate automat: `RefExp1` cu lungime diferită de tiparul dominant, `RefExp1`
duplicat, sumă ≤ 0, și rânduri **sărite** (lipsă `Data OP` / `Suma` / `Destinatar` /
`RefExp1`) — cu numărul rândului din Excel și cât lipsește din total.

### eMAG — documentat, neimplementat

Tabele complete în `mappings.md`. Pe scurt: `Data` ← `Order finalization date`,
`Numar`/`FacturaID` ← `Order ID`, `Suma` ← `Fraction value`, `Explicatie` ←
`Incasare ramburs client - <Client name>`. Singura logică per valută e `Cont`, `Moneda`
și **factorul HUF: `Suma` = `Fraction value` / 100** (împărțit, nu înmulțit — confirmat
de utilizator pe 15.08.2026, înlocuiește notele contradictorii anterioare).

Câmpurile vechi `DEN_PARTENER`, `CURS`, `SUMA_VALUTA` nu au tag în formatul nou: numele
cumpărătorului intră în `Explicatie`, iar cursul/suma în valută sunt acoperite de `Suma`
(în valuta folderului) + `Moneda`.

## Stare curentă / next steps

1. **Cargus / Packeta — automatizat**, cu `FacturaNumar` completat din `facturi/`:
   `borderouri/ron/procesate/Cargus_Packeta_Iulie_2026.xml` — 219 linii, 26.570,21 RON,
   toate legate de factură. **De testat importul în Saga.**
2. **eMAG — neimplementat.** `I_30.03.2026.xml` (o linie, formatul corect `<Linie>`)
   rămâne exemplul de testat la import.
3. **De confirmat la primul import** (detaliat în `mappings.md`, secțiunea
   „De confirmat la primul import", și în `SKILL.md`):
   - numele fișierului fără prefixul `I_` — **prima cauză de verificat dacă importul e refuzat**;
   - `Data` = `Data OP` (ales, se potrivește cu extrasul) vs `Livrata` (indicat de harta
     din rândul 1 al borderoului);
   - `FacturaID` = `RefExp1` — util doar dacă facturile sunt importate cu același ID;
   - diacriticele în Saga după import UTF-8;
   - **totalul XML e cu 0,95 RON mai mare decât borderoul** (suma vine de pe factură);
     de confirmat că reconcilierea cu extrasul de cont nu se supără;
   - două valori `RefExp1` atipice în borderoul din iulie (`9822`, `26540717`) — probabil
     greșeli de tastare, de corectat la sursă;
   - ce se întâmplă cu refund-urile / sumele negative (nu apar încă la Cargus);
   - **cele 3 `RefExp1` cu factură de storno** (47356, 47364, 47170): banii au fost
     încasați, dar factura e stornată — se importă încasarea pe factura inițială?
   - **diferențele de 0,08 și 0,02** (rândurile 12 și 123) — restul sunt de 0,01.
4. **EUR** — skill-ul e azi doar pe RON, la cerere. Când apare primul
   borderou EUR: `--set-folder borderouri/eur --moneda EUR` și atât — maparea nu are
   nevoie de cod nou, fiindcă `total` e deja în valuta facturii. **HUF: ignorat
   deocamdată** (factorul de 100 rămâne documentat doar pentru eMAG, în `mappings.md`).
5. **Facturile eMAG nu au `inf_suplm`** — 58 din 1788 (`V-MKTP-*`, `H-MKTP-*` de la
   DANTE INTERNATIONAL SA, plus 38 `MCSCOD*` de B2B). Când se implementează eMAG, cheia
   va trebui să fie alta decât `RefExp1`; de stabilit ce leagă `Order ID` de `nr_iesire`.
6. **Windows (03.09.2026) — de testat pe PC-ul de lucru**, din fila Code:
   `py -3 … --arata-config` (prima linie arată versiunea de Python și sistemul),
   configurarea prin `config-incasari-cargus`, `--dry-run`, o rulare reală (XML UTF-8 cu
   LF), apoi task-ul local săptămânal cu **Run now**. De rezolvat **trimiterea e-mailului
   în rulare neasistată**: `SKILL.md` cere confirmare la prima trimitere, iar conectorul
   Gmail trebuie configurat și aprobat („always allow") în task, altfel rularea se
   blochează la prompt. Dacă numele cu diacritice apar stricate în chat pe PowerShell 5.1,
   e doar afișarea — XML-ul e corect.

## Fișiere de referință

- `.claude/skills/incasari-cargus/` — skill-ul de procesare: `SKILL.md` (fluxul
  conversațional) + `scripts/proceseaza.py`
- `.claude/skills/config-incasari-cargus/` — skill-ul de configurare: prima rulare pe
  o mașină nouă și orice schimbare de căi/adrese ulterioară
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
