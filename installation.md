# Instalarea calculatorului de lucru (Windows)

Ce trebuie pe un PC nou ca să meargă skill-urile din acest repo, în ordinea în care se
instalează:

| # | Ce | De ce |
|---|---|---|
| 1 | **Claude Code** | rulează skill-urile |
| 2 | **Git for Windows** | `git` pentru repo + shell-ul Bash pentru Claude Code |
| 3 | **Python 3** | `proceseaza.py` — fără el, încasările nu merg deloc |
| 4 | **Google Drive for Desktop** (Mirror) | borderourile și facturile, ca fișiere reale pe disc |
| 5 | **Pluginurile din marketplace** | `alfin-consult` |
| 6 | **Notion** (conector) | board-ul `AI Agent overview`, unde se vede fiecare rulare |

Pașii 1–4 se fac o dată **per cont Windows** care are nevoie de acces. Contul Google
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

Skill-urile din acest repo rulează din **aplicația Claude Desktop, fila Code**, nu din
Cowork: Cowork execută comenzile într-o mașină virtuală Linux (Hyper-V) care pe Windows
are un bug cunoscut de pornire („Workspace unavailable… isolated Linux environment
failed to start"), nu citește `.claude/skills/` din folder, iar task-urile lui programate
nu pot fi legate de un folder local.

Fila Code rulează nativ și citește `CLAUDE.md` + `.claude/skills/` din folderul de lucru.

Rularea periodică: **Routines → New routine → Local**. La ALFIN Consult, routine-ul de
încasări e configurat astfel (05.09.2026):

| Câmp | Valoare |
|---|---|
| Folder | `C:\Users\Barna\My Drive\claude\incasari-saga` |
| Frecvență | lunar, pe **5 ale lunii** |
| Prompt | `Procesează borderourile noi de încasări și trimite raportul pe e-mail.` |

Folderul e cel din Drive, nu rădăcina repo-ului: acolo nu există niciun `CLAUDE.md` care
să încarce context de dezvoltare la fiecare rulare. **Nu folosi `incasari/`** — vezi
avertismentul de la pasul 4.

La prima rulare apasă **Run now** și alege **„always allow"** la promptul de Python,
altfel rulările următoare se blochează așteptând o aprobare pe care nu o vede nimeni.

Pentru raportul pe e-mail trebuie activat conectorul **Gmail** pentru chatul sau
routine-ul respectiv — butonul **+** din caseta de mesaj → Connectors. Se activează
**per sesiune**, nu global: cazul tipic de eșec e că Gmail merge în chatul unde s-a făcut
configurarea, dar routine-ul pornește o sesiune nouă fără el.

Activează pe același routine și conectorul **Notion**, ca rularea să-și scrie cardul în
board (pasul 5). Dacă lipsește, rularea merge oricum — doar că board-ul rămâne în urmă.

Laptopul trebuie să fie **logat**, nu doar pornit, la orele când rulează routine-ul.

> **Fereastra de recuperare: 5 → 12 ale lunii.** Routine-ul pleacă pe **5 ale lunii**. Dacă
> laptopul pe care e configurat nu are Claude pornit în acea zi, rularea se recuperează mai
> târziu — dar numai până în **12 ale lunii**. După 12, luna respectivă se pierde: routine-ul
> nu mai rulează deloc pentru ea, iar borderourile ei trebuie procesate manual, dintr-un chat.
> Deci: între 5 și 12 ale fiecărei luni, laptopul trebuie logat, cu Claude pornit, măcar o dată.

## Ce urmează

Configurarea căilor și a adreselor de raport se face conversațional („configurează
încasările"); detaliile sunt în
`plugins/incasari-saga/skills/incasari-cargus/references/configurare.md`.
