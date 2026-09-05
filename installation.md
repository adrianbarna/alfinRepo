# Instalare Google Drive pe calculatorul de lucru

Ghid pentru a avea fișierele din Google Drive ca **fișiere reale pe disc** pe laptop,
folosite de skill-urile din acest repo, cu **un singur cont Google partajat**
(`alfin.consult.ai@gmail.com`).

## De ce Mirror, nu Stream

Google Drive for Desktop oferă două moduri de sincronizare:

- **Stream files** — fișierele stau doar în cloud, se descarcă „la cerere" când sunt
  deschise. Necesită conexiune bună în momentul accesului.
- **Mirror files** — ține o copie fizică locală, sincronizată. Fișierele sunt mereu
  prezente pe disc, indiferent de rețea.

Pentru **task-uri programate** (scheduled tasks / Routines), **Mirror** e alegerea
corectă: cu Stream, un task care rulează fără conexiune bună sau înainte ca fișierul să
fie hidratat poate eșua sau citi un placeholder gol. Cu Mirror, fișierul e mereu
disponibil local, instant.

## Instalare

```powershell
winget install --id Google.GoogleDrive --silent --accept-package-agreements --accept-source-agreements
```

Aplicația se instalează la nivel de mașină (`C:\Program Files\Google\Drive File
Stream`), deci **orice cont Windows de pe laptop o poate lansa fără reinstalare** — dar
fiecare cont trebuie să facă propriul sign-in (vezi mai jos).

## Configurare (per cont Windows)

Pași repetați o dată pentru **fiecare** cont Windows de pe laptop care are nevoie de
acces la fișiere:

1. Loghează-te pe acel cont Windows.
2. Deschide **Google Drive** din Start (pornește automat după prima configurare, la
   fiecare logare).
3. Sign-in cu contul Google partajat: **alfin.consult.ai@gmail.com**.
4. Click pe iconița **⚙️ (Settings)** din colțul dreapta-sus al ferestrei Drive →
   **Preferences** → **Google Drive** (în panoul din stânga, sub numele contului).
5. La **„My Drive syncing options"** alege **Mirror files**.
6. Verifică **folderul local** în care se face mirror-ul — e afișat în același ecran și
   poate fi schimbat. Implicit e `C:\Users\<utilizator>\My Drive`.

## Calea de folosit peste tot: folderul de mirror, nu litera de disc

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

## Atenție la spațiu pe disc

Cu Mirror, **fiecare cont Windows ține o copie fizică proprie** a fișierelor pe disc —
nu una singură partajată la nivel de mașină. Spațiul ocupat se înmulțește cu numărul de
conturi Windows care fac mirror pe același Google Drive.

## Sincronizarea nu e instantanee

Două consecințe practice, ambele au produs deja confuzie:

- **Un borderou pus acum în Drive nu e gata de procesat imediat.** Până se termină
  sincronizarea, fișierul poate exista pe disc incomplet și se citește ca `.xlsx`
  corupt. Verifică iconița Drive din bara de sistem înainte de a rula.
- **XML-ul generat nu apare instant în cloud.** Scriptul scrie în
  `borderouri\ron\procesate\`, iar sincronizarea îl urcă după aceea. Nu încărca nimic
  manual în Drive și nu folosi conectorul de Drive pentru asta — se dublează fișierele.

## Rulare pe un singur calculator

Jurnalul `.procesate.json` (evidența borderourilor deja procesate) stă într-un folder
sincronizat. **Procesează de pe un singur calculator.** Două mașini care rulează în
paralel produc un al doilea fișier de jurnal, de tip `.procesate (1).json`, iar evidența
se rupe fără niciun mesaj de eroare.

## Cum se rulează, pe Windows

Skill-urile din acest repo rulează din **aplicația Claude Desktop, fila Code**, nu din
Cowork: Cowork execută comenzile într-o mașină virtuală Linux (Hyper-V) care pe Windows
are un bug cunoscut de pornire („Workspace unavailable… isolated Linux environment
failed to start"), nu citește `.claude/skills/` din folder, iar task-urile lui programate
nu pot fi legate de un folder local.

Fila Code rulează nativ și citește `CLAUDE.md` + `.claude/skills/` din folderul de lucru.
Fără Git for Windows, shell-ul e **PowerShell**, care nu traduce comenzi bash — de aceea
instrucțiunile skill-urilor sunt neutre față de shell și scriptul se apelează cu `py -3`.

Rularea periodică: **Routines → New routine → Local**, folder = folderul de lucru,
frecvența dorită. La prima rulare apasă **Run now** și alege **„always allow"** la
promptul de Python, altfel rulările următoare se blochează așteptând o aprobare.

Laptopul trebuie să fie **logat**, nu doar pornit, la orele când rulează routine-ul.

## Ce urmează

Python 3 trebuie instalat separat (python.org, cu „Add python.exe to PATH" bifat) —
skill-urile nu instalează nimic. După aceea, configurarea căilor și a adreselor de
raport se face conversațional, cu skill-ul `incasari-cargus`; detaliile sunt în
`plugins/incasari-saga/skills/incasari-cargus/references/configurare.md`.
