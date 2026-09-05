# Instalare Google Drive ca drive local (G:)

Ghid pentru montarea Google Drive ca un drive normal **G:** pe laptop, folosit de toate
conturile Windows de pe mașină, cu **un singur cont Google partajat**
(`alfin.consult.ai@gmail.com`).

## De ce Mirror, nu Stream

Google Drive for Desktop oferă două moduri de sincronizare:

- **Stream files** — fișierele stau doar în cloud, se descarcă „la cerere" când sunt
  deschise. Necesită conexiune bună în momentul accesului.
- **Mirror files** — ține o copie fizică locală, sincronizată. Fișierele sunt mereu
  prezente pe disc, indiferent de rețea.

Pentru **task-uri programate** (scheduled tasks / cron), **Mirror** e alegerea corectă:
cu Stream, un task care rulează fără conexiune bună sau înainte ca fișierul să fie
hidratat poate eșua sau citi un placeholder gol. Cu Mirror, fișierul e mereu disponibil
local, instant.

## Instalare

```powershell
winget install --id Google.GoogleDrive --silent --accept-package-agreements --accept-source-agreements
```

Aplicația se instalează la nivel de mașină (`C:\Program Files\Google\Drive File
Stream`), deci **orice cont Windows de pe laptop o poate lansa fără reinstalare** — dar
fiecare cont trebuie să facă propriul sign-in (vezi mai jos).

## Configurare (per cont Windows)

Pași repetați o dată pentru **fiecare** cont Windows de pe laptop care are nevoie de
acces la G:\:

1. Loghează-te pe acel cont Windows.
2. Deschide **Google Drive** din Start (pornește automat după prima configurare, la
   fiecare logare).
3. Sign-in cu contul Google partajat: **alfin.consult.ai@gmail.com**.
4. Click pe iconița **⚙️ (Settings)** din colțul dreapta-sus al ferestrei Drive →
   **Preferences** → **Google Drive** (în panoul din stânga, sub numele contului).
5. La **„My Drive syncing options"** alege **Mirror files**.
6. Setează litera driverului la **G** (opțiunea de „Drive letter" e în același ecran de
   Preferences, lângă setările de sincronizare, sau sub rotița ⚙️ de lângă „My Drive").

După acest setup, **G:** apare ca un drive normal în Explorer, cu conținutul Drive-ului
partajat, de fiecare dată când acel cont Windows e logat.

## Atenție la spațiu pe disc

Cu Mirror, **fiecare cont Windows ține o copie fizică proprie** a fișierelor pe disc —
nu una singură partajată la nivel de mașină. Spațiul ocupat se înmulțește cu numărul de
conturi Windows care fac mirror pe același Google Drive.

## Task-uri programate (scheduled tasks)

G: e un drive virtual montat **doar în sesiunea interactivă a utilizatorului logat** —
la fel ca orice network/mapped drive pe Windows. Dacă un task din Task Scheduler e
configurat cu opțiunea **„Run whether user is logged on or not"** (cont SYSTEM sau altă
sesiune), **nu va vedea deloc G:**, indiferent de Stream sau Mirror.

Pentru ca un task programat să acceseze G:\:

- Rulează-l sub contul Windows care are Drive montat și logat.
- Folosește opțiunea **„Run only when user is logged on"** în Task Scheduler.
- Ține laptopul logat (nu doar pornit) la orele când rulează task-ul.
