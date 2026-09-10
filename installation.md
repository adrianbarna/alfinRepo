# Instalarea calculatorului de lucru (Windows)

**Încasările rulează într-un task programat în cloud** — vezi „Cum se rulează". Scriptul se
execută pe serverele Anthropic, nu pe calculator; de pe calculator se citesc și se scriu doar
fișierele din Drive. De aceea lista de mai jos are două categorii: ce trebuie neapărat ca să
meargă încasările și ce trebuie doar dacă lucrezi la repo sau rulezi alte skill-uri local.

| # | Ce | De ce | Pentru încasări |
|---|---|---|---|
| 1 | **Claude Code** | aplicația desktop ține legătura cu folderul din Drive | **obligatoriu** |
| 2 | **Virtualizare activată în BIOS** | mașina virtuală Linux în care rulează comenzile locale | doar dezvoltare |
| 3 | **Git for Windows** | `git` pentru repo + shell-ul Bash pentru Claude Code | doar dezvoltare |
| 4 | **Python 3** | `proceseaza.py`, dacă vrei să rulezi manual pe calculator | doar dezvoltare |
| 5 | **Google Drive for Desktop** (Mirror) | borderourile și facturile, ca fișiere reale pe disc | **obligatoriu** |
| 6 | **Pluginurile din marketplace** | `alfin-consult` | doar dezvoltare |
| 7 | **Notion** (conector) | board-ul `AI Agent overview`, unde se vede fiecare rulare | recomandat |

Task-ul din cloud **nu** folosește pluginul instalat local și **nu** are nevoie de Python pe
calculator: își aduce singur skill-ul și scriptul din repo, iar Python rulează în container.

Pașii 1–5 se fac o dată **per cont Windows** care are nevoie de acces — cu excepția
virtualizării, care se activează o singură dată, în BIOS, pentru tot calculatorul. Contul Google
folosit peste tot e cel partajat: `alfin.consult.ai@gmail.com`.

---

## 1. Claude Code

Cerințe: **Windows 10 versiunea 1809+** sau Windows Server 2019+, 4 GB RAM, procesor x64
sau ARM64, conexiune la internet.

Claude Code cere un cont **Pro, Max, Team, Enterprise sau Console**. Planul gratuit
Claude.ai **nu** include Claude Code.

### Aplicația desktop

Skill-urile de aici se folosesc din **aplicația Claude Desktop, fila Code** — vezi „Cum
se rulează" mai jos. Se descarcă de la <https://claude.com/download>.

### Linia de comandă

E nevoie și de CLI, separat de aplicație: `claude plugin validate` și instalarea
marketplace-ului din terminal trec prin el.

În **PowerShell**:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Alternativ, prin winget — dar atenție, **instalările winget nu se actualizează
automat**, spre deosebire de cea nativă:

```powershell
winget install Anthropic.ClaudeCode
```

Pe varianta winget, actualizarea se face manual cu `winget upgrade Anthropic.ClaudeCode`.
Instalarea nativă (`irm …`) se actualizează singură, în fundal.

> Dacă apare `The token '&&' is not a valid statement separator`, ești în PowerShell, nu
> în CMD. Promptul arată `PS C:\` în PowerShell și `C:\` fără `PS` în CMD.

### Verificare și login

```powershell
claude --version
claude doctor
```

`claude --version` trebuie să tipărească un număr de versiune, de forma
`2.1.211 (Claude Code)`. `claude doctor` afișează diagnosticul instalării și al
setărilor, fără să pornească o sesiune — primul lucru de rulat când ceva nu merge.

Login-ul se face rulând `claude` și urmând promptul din browser.

Dacă răspunsul e `The term 'claude' is not recognized`, cel mai probabil **nu lipsește
instalarea, ci PATH-ul terminalului e vechi** — la fel ca la Python (pasul 2). Instalarea
nativă pune executabilul în `%USERPROFILE%\.local\bin`, deci verifică întâi acolo:

```powershell
& "$env:USERPROFILE\.local\bin\claude.exe" --version
```

Dacă de acolo răspunde, deschide un terminal nou în loc să reinstalezi.

### Virtualizare — cerință pentru comenzile locale

Cowork execută comenzile locale (`device_bash`) într-o mașină virtuală Linux de pe calculator.
**Virtualizarea hardware trebuie activată în BIOS/UEFI**, altfel mașina nu pornește și orice
comandă locală răspunde:

```
Workspace unavailable. The isolated Linux environment on this device failed to start.
```

Verifică întâi, înainte de a umbla în BIOS: Task Manager → Performanță → CPU. `Suport Hyper-V: Da`
înseamnă că procesorul poate; linia **Virtualizare** trebuie să arate `Activat`. Pe multe
laptopuri vine nebifată din fabrică.

Activare:

1. Restart și intră în BIOS/UEFI — de regulă `F2` la pornire (uneori `F10`, `Del` sau `F1`).
2. **Intel Virtualization Technology** / **Intel VT-x** (pe AMD: **SVM Mode**) → `Enabled`, de
   obicei în *Advanced*, *Configuration*, *System Configuration* sau *Security*. *Save & Exit*
   (`F10`).
3. Verifică în Task Manager că linia **Virtualizare** arată `Activat`.
4. Dacă tot nu pornește: `wsl --update` în PowerShell ca administrator, iar în
   `optionalfeatures.exe` bifate **Virtual Machine Platform** și **Windows Hypervisor Platform**.
   Restart la Windows după orice modificare.

**Exemplu concret, pe `ldtd01` (10.09.2026):** restart → `F1` la pornire → **Security** →
**Virtualization** → `Enable` → *Save & Exit*. După repornire, mașina virtuală locală a pornit și
`device_bash` a răspuns normal. Meniul diferă de la un producător la altul — dacă `F1` nu intră în
BIOS, încearcă `F2`, `F10` sau `Del`, iar dacă nu găsești opțiunea sub *Security*, caut-o în
*Advanced*, *Configuration* sau *System Configuration*.

> Ai la îndemână cheia de recuperare BitLocker înainte de a intra în BIOS: pe unele laptopuri, o
> modificare de acolo o cere la următoarea pornire (contul Microsoft → Devices → BitLocker keys).

**Ce merge și fără virtualizare:** citirea și scrierea fișierelor din folderele conectate
(`device_list_dir`, `device_stage_files`, `device_commit_files`) nu trec prin mașina virtuală.
De aceea încasările pot rula și pe o mașină fără ea — vezi „De ce procesarea rămâne în cloud".

**Ce nu deblochează, chiar activată:** mașina virtuală **nu are acces la rețea**. `git clone` nu
poate rula acolo, iar conectorii Gmail și Notion există doar în sesiunea din cloud. Local rămân
citirile, căutările, editările și scripturile care nu cer rețea. Ștergerea de fișiere e blocată
din oficiu — `rm` răspunde `Operation not permitted`.

**Nu rula git în mașina virtuală locală.** Git are nevoie să șteargă fișiere temporare, iar în
folderele conectate ștergerea e blocată: fiecare comandă lasă în urmă `.git/index.lock`,
`.git/HEAD.lock` și obiecte `tmp_obj_*` pe care nu le poate curăța singură. Un `index.lock` rămas
blochează apoi următoarea comandă git de pe Windows, cu „Another git process seems to be running",
și pare o sesiune git blocată deși nu rulează nimic. **Commit, push, pull, rebase — din PowerShell,
pe Windows.** În mașina virtuală rămân cititul, căutarea și editarea fișierelor.

### Git for Windows

Nu e obligatoriu pentru Claude Code, dar e **recomandat**: fără el, Claude Code
folosește unealta PowerShell în loc de Bash. Îl vrei oricum, fiindcă repo-ul se
gestionează cu `git`.

```powershell
winget install --id Git.Git
```

Dacă Claude Code nu găsește Git Bash după instalare, îi spui calea în `settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

**Independent de asta, instrucțiunile skill-urilor din acest repo rămân neutre față de
shell** — o comandă pe linie, fără `&&`, `||` sau redirecționări — ca să meargă la fel
și pe PowerShell, și pe Bash. Nu le „optimiza" presupunând că Git Bash există.

### Terminații de linie: LF, prin `.gitattributes`

Pe 10.09.2026 sincronizarea repo-ului de pe Windows a rescris toate fișierele în CRLF, iar
`git diff` a arătat 5287 de linii schimbate fără nicio schimbare de conținut. Rezolvarea e
`.gitattributes` din rădăcina repo-ului: `* text=auto eol=lf`, cu excepția `.bat`, `.cmd` și
`.ps1`, care rămân CRLF ca să fie citite corect pe Windows.

**Nu seta `core.autocrlf`** — nici local, nici global. Pe mașina curentă e nesetat, iar
`.gitattributes` e singurul mecanism; două mecanisme care spun același lucru diverg mai devreme
sau mai târziu. Dacă un `git status` arată brusc tot repo-ul modificat fără să fi atins nimic,
asta e prima cauză de verificat.

---

## 2. Python 3

```powershell
winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
```

Alternativ, de la <https://python.org>, cu **„Add python.exe to PATH" bifat**. În ambele
cazuri skill-urile nu instalează nimic singure.

### Verificare

Cere un **terminal nou**, deschis după instalare — PATH-ul nu se actualizează în
terminalele deja deschise:

```powershell
py -3 --version
```

Dacă răspunsul e `Python was not found; run without arguments to install from the
Microsoft Store`, ăla e stub-ul Windows, nu Python — încearcă `python --version`. Dacă
nici acela nu răspunde într-un terminal nou, verifică direct calea de instalare:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" --version
```

Dacă nici acolo nu răspunde nimic, Python chiar lipsește.

### Atenție la conturi multiple pe aceeași mașină

winget instalează Python **per cont Windows curent**
(`%LOCALAPPDATA%\Programs\Python\Python312\`), nu la nivel de mașină. Ca și la Google
Drive (pasul 3), fiecare cont Windows care rulează skill-urile — inclusiv un cont
dedicat de Routines, dacă e cazul — are nevoie de propria instalare.

`proceseaza.py` nu are dependențe externe: `.xlsx` e citit direct cu `zipfile` +
`ElementTree`. Deci nu e nevoie de `pip install` pentru nimic.

---

## 3. Google Drive for Desktop

### De ce Mirror, nu Stream

Google Drive for Desktop oferă două moduri de sincronizare:

- **Stream files** — fișierele stau doar în cloud, se descarcă „la cerere" când sunt
  deschise. Necesită conexiune bună în momentul accesului.
- **Mirror files** — ține o copie fizică locală, sincronizată. Fișierele sunt mereu
  prezente pe disc, indiferent de rețea.

Pentru **task-uri programate** (Routines), **Mirror** e alegerea corectă: cu Stream, un
task care rulează fără conexiune bună sau înainte ca fișierul să fie hidratat poate eșua
sau citi un placeholder gol. Cu Mirror, fișierul e mereu disponibil local, instant.

### Instalare

```powershell
winget install --id Google.GoogleDrive --silent --accept-package-agreements --accept-source-agreements
```

Aplicația se instalează la nivel de mașină (`C:\Program Files\Google\Drive File
Stream`), deci **orice cont Windows de pe laptop o poate lansa fără reinstalare** — dar
fiecare cont trebuie să facă propriul sign-in.

### Configurare (per cont Windows)

1. Loghează-te pe acel cont Windows.
2. Deschide **Google Drive** din Start (pornește automat după prima configurare, la
   fiecare logare).
3. Sign-in cu contul Google partajat: **alfin.consult.ai@gmail.com**.
4. Click pe iconița **⚙️ (Settings)** din colțul dreapta-sus al ferestrei Drive →
   **Preferences** → **Google Drive** (în panoul din stânga, sub numele contului).
5. La **„My Drive syncing options"** alege **Mirror files**.
6. Verifică **folderul local** în care se face mirror-ul — e afișat în același ecran și
   poate fi schimbat. Implicit e `C:\Users\<utilizator>\My Drive`.

### Calea de folosit peste tot: folderul de mirror, nu litera de disc

Aceasta e partea care contează pentru skill-uri, și e ușor de greșit.

Drive for Desktop montează și un **disc virtual** (de obicei `G:`), care apare în
Explorer alături de folderul de mirror. Sunt două căi diferite către (parțial) același
conținut, și **numai una e utilizabilă din task-uri**:

| Cale | Ce e | Bună pentru task-uri? |
|---|---|---|
| `C:\Users\<utilizator>\My Drive\...` | folderul de mirror, fișiere reale pe disc | **da** |
| `G:\My Drive\...` | disc virtual montat în sesiune | **nu** |

`G:` e montat **doar în sesiunea interactivă a utilizatorului logat**, ca orice drive
mapat pe Windows. Un task configurat cu **„Run whether user is logged on or not"** (cont
SYSTEM sau altă sesiune) **nu-l vede deloc**, indiferent de Stream sau Mirror — și
eșuează cu „calea nu există", ceea ce arată exact ca o configurare greșită.

**Regula: în `config.json`, în skill-uri și în orice task, folosește calea de sub
`C:\Users\<utilizator>\My Drive`.** Nu folosi `G:` nicăieri.

Pe mașina curentă (contul Windows `Barna`), folderele de lucru ale încasărilor sunt:

```
C:\Users\Barna\My Drive\claude\incasari-saga\borderouri\ron
C:\Users\Barna\My Drive\claude\incasari-saga\facturi
```

### Atenție la spațiu pe disc

Cu Mirror, **fiecare cont Windows ține o copie fizică proprie** a fișierelor pe disc —
nu una singură partajată la nivel de mașină. Spațiul ocupat se înmulțește cu numărul de
conturi Windows care fac mirror pe același Google Drive.

### Sincronizarea nu e instantanee

Două consecințe practice, ambele au produs deja confuzie:

- **Un borderou pus acum în Drive nu e gata de procesat imediat.** Până se termină
  sincronizarea, fișierul poate exista pe disc incomplet și se citește ca `.xlsx`
  corupt. Verifică iconița Drive din bara de sistem înainte de a rula.
- **XML-ul generat nu apare instant în cloud.** Scriptul scrie în
  `borderouri\ron\procesate\`, iar sincronizarea îl urcă după aceea. Nu încărca nimic
  manual în Drive și nu folosi conectorul de Drive pentru asta — se dublează fișierele.

### Rulare pe un singur calculator

Jurnalul `.procesate.json` (evidența borderourilor deja procesate) stă într-un folder
sincronizat. **Procesează de pe un singur calculator.** Două mașini care rulează în
paralel produc un al doilea fișier de jurnal, de tip `.procesate (1).json`, iar evidența
se rupe fără niciun mesaj de eroare.

---

## 4. Pluginurile

Din **fila Code** a aplicației Claude Desktop, sau din terminal:

```
/plugin marketplace add adrianbarna/alfinRepo
/plugin install incasari-saga@alfin-consult
/plugin install monitorizare-legislativa@alfin-consult
```

Dacă sumarul spune `Run /reload-plugins to activate.`, rulează și `/reload-plugins`.
Calea asta clonează marketplace-ul local, deci are nevoie de `git` instalat (pasul 1).

Dacă adăugarea marketplace-ului eșuează cu `EBUSY: resource busy or locked, rmdir
'...\.claude\plugins\marketplaces\adrianbarna-alfinRepo'`, **rulează comanda din nou**.
Clonarea reușise deja, iar eroarea vine de la curățarea folderului, ținut ocupat de un
antivirus sau de o sesiune Claude care tocmai îl citea. A doua încercare trece. Nu șterge
folderul de mână și nu reinstala nimic.

Un skill nou instalat **nu apare în sesiunile deja deschise** — pluginurile se citesc la
pornirea sesiunii. După instalare, deschide o sesiune nouă (sau `/reload-plugins`).

Alternativ, din **Settings → Customize → Plugins**, fila **Personal**, butonul **+**,
cu `adrianbarna/alfinRepo` și **Sync**. Acolo clonarea se face pe serverele Anthropic,
deci nu cere git local — dar apoi trebuie pornit **Sync automatically** din meniul `···`
al marketplace-ului: **nu vine pornit din oficiu**, iar fără el pluginul rămâne blocat
pe versiunea de la instalare, în tăcere.

> **Nu deschide folderul `incasari/` cât timp pluginul `incasari-saga` e instalat** —
> `incasari/.claude/skills/` e o copie de lucru a acelorași skill-uri, deci Claude ar
> vedea `incasari-cargus` de două ori. `incasari/` e pentru dezvoltare, pluginul pentru
> uz zilnic.

---

## 5. Notion — board-ul `AI Agent overview`

Fiecare rulare a unui agent lasă o urmă într-un board Notion, ca să se vadă ce a rulat,
ce a produs și ce a mai rămas de făcut. Fără el, o rulare programată care eșuează la 8
dimineața nu e observată de nimeni până când lipsesc încasările din Saga.

Licența Notion e pe contul partajat `alfin.consult.ai@gmail.com`, la fel ca restul.

**Board:** <https://app.notion.com/p/6ab8018a469d4f18abda5e239cf4932f>
**Data source** (id-ul folosit de skill-uri când creează carduri):
`aa9a26d8-67fc-47d2-acf0-0460d8bc9abf`

### Cum e construit

**Un card = o rulare**, nu un agent. Cardul se numește `Încasări — septembrie 2026`,
`Monitorizare fiscală — săpt. 37`, rămâne după ce se închide și devine istoricul rulărilor.

Cele șase faze, în ordine:

| Fază | Ce înseamnă | Cine mută cardul |
|---|---|---|
| `Programat` | task-ul e activ, așteaptă ora de rulare | — |
| `În lucru` | agentul procesează chiar acum | agentul |
| `Blocat / Necesită input` | s-a oprit și așteaptă ceva de la om | agentul |
| `De verificat` | agentul a terminat, rezultatul nu e validat | agentul |
| `De aplicat` | validat, a rămas pasul manual (importul în Saga) | **omul** |
| `Done` | închis complet, rămâne ca istoric | **omul** |

Linia care separă lucrurile: **agentul poate muta cardul până în `De verificat`, nu mai
departe.** `De aplicat` și `Done` înseamnă „omul a verificat" și „omul a aplicat"; dacă
un agent și-ar închide singur cardul, board-ul n-ar mai spune nimic.

Proprietățile cardului: `Agent`, `Perioadă`, `Declanșat` / `Finalizat`, `Declanșare`
(automat sau manual), `Rezultat` (rezumat de o linie), `Pas manual rămas`, `Fișiere`,
`Responsabil`, `ID` (`RUN-1`, `RUN-2`…). În **corpul cardului** agentul scrie jurnalul
rulării în română — ce comandă a rulat, ce fișiere a procesat, ce a ieșit, ce e de
verificat, unde a plecat raportul.

Notion ascunde coloanele goale. Ca să rămână vizibile toate șase și când o fază n-are
niciun card: pe board → iconul cu sliders (dreapta sus) → **Group** → oprești
**„Hide empty groups"**. Cardurile ℹ️ de legendă din fiecare coloană există exact pentru
asta și pot fi șterse după ce oprești setarea.

### Conectorul, în sesiune

Ca și la Gmail, conectorul Notion se activează **per sesiune sau routine**, din butonul
**+** din caseta de mesaj → Connectors. Cazul tipic de eșec: Notion merge în chatul unde
s-a făcut configurarea, dar routine-ul pornește o sesiune nouă, fără el.

**Board-ul nu e o dependență critică.** Skill-urile sunt scrise să meargă mai departe
fără el: dacă uneltele Notion lipsesc, procesarea și raportul pe email se fac oricum, iar
agentul spune la final în ce fază ar fi trebuit să ajungă cardul.

---

## Cum se rulează

Un **task programat în cloud**, din Cowork, cu folderul din Drive conectat. Rularea se face în containerul
din cloud, pe copii ale fișierelor urcate din Drive, iar rezultatele se scriu înapoi în Drive.

| Câmp | Valoare |
|---|---|
| Nume | `Încasări lunare - Saga` |
| Folder conectat | `C:\Users\Barna\My Drive\claude\incasari-saga` |
| Frecvență | lunar, pe **5 ale lunii**, 07:00 UTC (10:00 ora României, vara) |
| Conectori | Gmail, Notion (+ Google Drive, Google Calendar) |
| Aprobări | **automat** — altfel rularea se oprește așteptând un „da" pe care nu-l vede nimeni |

**De ce cloud și nu local:** conectorii Gmail și Notion sunt legați de task și există doar în
sesiunea din cloud, iar mașina virtuală Linux locală nu are acces la rețea, deci nu poate clona
repo-ul (vezi „De ce procesarea rămâne în cloud"). Prețul e că fișierele fac un drum dus-întors — urcate din Drive,
procesate în cloud, scrise înapoi — câteva secunde pentru un borderou de câteva sute de rânduri.

**Calculatorul trebuie să fie pornit și Claude Desktop conectat** la ora rulării: fără el,
sesiunea din cloud nu ajunge la folderul din Drive. Varianta din cloud nu scapă de asta.

**Prompt-ul trebuie să fie autonom**, din două motive care nu se văd până nu eșuează:

- pluginul **nu** e activat pentru rulările task-ului (`enabled_plugins` e gol), deci sesiunea
  nu are nici skill-ul, nici `proceseaza.py`;
- sesiunea din cloud **nu** vede `~/.claude/incasari-saga/config.json` de pe PC, deci nu știe
  singură cui trimite raportul.

Prompt-ul de mai jos le rezolvă pe amândouă — clonează repo-ul public și citește configurarea
dintr-un `config.json` ținut în Drive:

```
Procesează borderourile noi de încasări Cargus/Packeta și trimite raportul pe e-mail.

CONTEXT
Rulezi în cloud. Folderul `C:\Users\Barna\My Drive\claude\incasari-saga` de pe calculatorul
„ldtd01" e conectat la sesiune. Mașina virtuală Linux locală de pe acel calculator NU pornește
(device_bash răspunde „Workspace unavailable"), deci nu încerca să rulezi acolo — folosește
device_list_dir / device_stage_files / device_commit_files și rulează scriptul aici, în
containerul din cloud.

PAȘII

1. Ia skill-ul și scriptul (pluginul nu e activat pentru acest task):
   `git clone --depth 1 https://github.com/adrianbarna/alfinRepo.git`
   Skill-ul e la `alfinRepo/plugins/incasari-saga/skills/incasari-cargus/`. CITEȘTE `SKILL.md`
   și urmează-l — el e sursa de adevăr pentru tot fluxul. Scriptul e `scripts/proceseaza.py`
   (Python 3, fără pachete externe).
   REGULA DE AUR: nu genera XML de mână, nu citi borderourile cu alte unelte, nu edita
   `.procesate.json`.

2. Vezi ce e în Drive: device_list_dir recursiv pe `C:\Users\Barna\My Drive\claude\incasari-saga`.
   Jurnalul `borderouri\ron\procesate\.procesate.json` spune ce s-a procesat deja. Dacă nu e
   niciun borderou nou, OPREȘTE-TE: fără email, fără card în Notion, fără notificare.

3. Stage-uiește în sesiune: `config.json` din rădăcina folderului, borderourile din
   `borderouri\ron`, tot ce e în `facturi`, și `borderouri\ron\procesate\.procesate.json` dacă
   există. Pune jurnalul stage-uit lângă borderouri, în `procesate/`, ca scriptul să-l găsească.

4. Copiază `config.json` stage-uit peste
   `alfinRepo/plugins/incasari-saga/skills/incasari-cargus/config.json` (scriptul îl citește de
   acolo cu prioritate). De acolo vin adresele de raport — NU le inventa și nu le lua din altă
   parte.
   Rulează:
   `python3 <skill>/scripts/proceseaza.py --folder <cale staged borderouri/ron> --facturi <cale staged facturi> --json`
   Cod de ieșire: 0 = a mers, 1 = eroare, 2 = configurare lipsă.

5. Scrie rezultatele înapoi în Drive, în
   `C:\Users\Barna\My Drive\claude\incasari-saga\borderouri\ron\procesate\`: XML-ul generat,
   `ultimul-raport.txt` ȘI `.procesate.json`. Fără jurnal, rularea următoare reprocesează tot.

6. Trimite raportul cu Gmail: subiectul în `email.subiect`, corpul în `email.corp`, destinatarii
   în `email.catre` (din JSON). Adaugă la final calea completă a XML-ului în Drive. NU cere
   confirmare înainte de trimitere — adresele sunt stabilite la configurare, iar asta e
   autorizarea. Raportul pleacă și când toate rândurile au fost sărite.

7. Actualizează cardul rulării în board-ul Notion „AI Agent overview" (data source
   aa9a26d8-67fc-47d2-acf0-0460d8bc9abf), conform pasului 3 din SKILL.md: caută întâi un card
   existent pentru aceeași lună și refolosește-l, scrie jurnalul rulării în corp, în română, și
   mută-l în „De verificat" sau „Blocat / Necesită input". Niciodată în „De aplicat" sau „Done".
   Dacă uneltele Notion lipsesc, nu te opri — spui la final în ce fază ar fi trebuit să ajungă.

8. La final trimite PushNotification cu: câte linii și ce total, câte rânduri sărite, câte
   avertismente, unde e XML-ul și cui a plecat raportul. Dacă rularea s-a blocat, notifică ce
   lipsește concret.
```

> **Notă, 10.09.2026:** linia din CONTEXT spune că mașina virtuală locală nu pornește — adevărat
> doar pe o mașină fără virtualizare activată. Acolo unde e activată, mașina pornește, dar tot nu
> are rețea, deci concluzia prompt-ului rămâne corectă: rularea se face în cloud. Dacă rescrii
> prompt-ul cândva, asta e propoziția de actualizat.

O rulare pierdută se recuperează declanșând task-ul manual, din lista de task-uri programate.

### `config.json` — unul singur, în Drive

```
C:\Users\Barna\My Drive\claude\incasari-saga\config.json
```

```json
{
  "foldere": [
    { "cale": "borderouri/ron", "moneda": "RON", "cont": "5125" }
  ],
  "facturi": "facturi",
  "email": ["alfin.consult.ai@gmail.com"]
}
```

Căile sunt **relative**, ca să meargă și pe Windows, și în container. Rularea din cloud le
suprascrie oricum cu `--folder` și `--facturi`; din fișier vine, în practică, adresa de raport.
Fișierul stă în Drive, lângă date, nu pe vreun calculator anume — asta e tot rostul lui.

> **Ăsta e singurul `config.json`.** Scriptul mai știe să citească și
> `~/.claude/incasari-saga/config.json` (calea implicită, per mașină), rămasă de la
> configurările vechi de pe calculator — dar task-ul din cloud nu o vede și nimic nu o mai
> citește. **Șterge-o**: două fișiere care spun același lucru diverg mai devreme sau mai
> târziu, iar cel de pe PC ar diverge în tăcere.

Datele contabile nu intră în git — `config.json` stă în Drive, nu în repo.

### De ce procesarea rămâne în cloud

Chiar pe o mașină cu virtualizarea activată, unde mașina virtuală locală pornește, procesarea tot
în cloud se face. Două motive, niciunul ocolibil: mașina virtuală locală **nu are rețea**, deci
pasul 1 al task-ului (`git clone`) nu poate rula acolo; iar conectorii **Gmail și Notion** sunt
legați de sesiunea din cloud, nu de calculator. Calculatorul rămâne necesar doar ca sursă și
destinație a fișierelor din Drive.

Detaliile despre cerința de virtualizare și ce se poate face local sunt la
„Virtualizare — cerință pentru comenzile locale", în secțiunea 1.

## Ce urmează

Configurarea căilor și a adreselor de raport se face conversațional („configurează
încasările"); detaliile sunt în
`plugins/incasari-saga/skills/incasari-cargus/references/configurare.md`.
