# Monitorizare Legislație Contabilă

> Repo-ul găzduiește **două plugin-uri**, ambele din aceeași sursă
> `adrianbarna/alfinRepo`: **Monitorizare legislativă** (mai jos) și
> **[Încasări Saga](incasari-saga/README.md)** — borderourile de ramburs Cargus /
> Packeta transformate în XML de import pentru Saga. Sursa se adaugă o singură dată;
> plugin-urile se activează separat.

Plugin pentru Claude (Cowork / Claude Code) care monitorizează **săptămânal** legislația contabilă și fiscală din România și trimite un **raport detaliat pe email** cu noutățile apărute și interpretările specialiștilor.

## Ce face

O dată pe săptămână, automat:

1. Verifică sursele de specialitate, pe trei niveluri:
   - *ce urmează* — **ședințele de Guvern** (gov.ro) și proiectele **SGG**, care anunță actele cu câteva zile înainte de publicare;
   - *ce s-a publicat* — **Monitorul Oficial** și **portalul legislativ** (legislatie.just.ro, text consolidat);
   - *ce înseamnă pentru contabil* — **avocatnet.ro**, **ANAF**, **contzilla.ro**, **legestart.ro**, **CECCAR Business Magazine**, **ceccar.ro**, **contabilul.ro**.
2. Identifică actele normative noi cu impact contabil/fiscal (legi, OUG, HG, ordine MF/ANAF).
3. Pentru fiecare act nou, caută pe internet analizele și părerile contabililor (articole, forumuri).
4. Trimite un email cu raportul: ce prevede fiecare act, de când se aplică, pe cine afectează, ce spun specialiștii — totul cu linkuri către surse.

Dacă într-o săptămână nu apare nimic nou, nu primiți email.

## Instalare (o singură dată)

Nu aveți nevoie de git și nu aveți nevoie de terminal. Totul se face din aplicația Claude sau de pe claude.ai.

**Pasul 1 — Adăugați sursa plugin-ului.** Deschideți **Settings → Customize → Plugins** (sau, în aplicație, meniul **Directory → Plugins**). Alegeți fila **Personal** și apăsați **+** din dreapta. În câmpul URL scrieți exact:

```
adrianbarna/alfinRepo
```

Apăsați **Sync**.

**Verificați apoi că actualizările automate sunt pornite** — nu vin pornite întotdeauna. Lângă eticheta `alfinRepo` apăsați meniul **···**: acolo trebuie să fie activ comutatorul **Sync automatically**. Tot de acolo, **Check for updates** aduce imediat o versiune nouă, fără să așteptați. Meniul arată și `Synced commit`, adică exact ce versiune aveți.

> Fără comutatorul ăsta pornit, plugin-ul rămâne pe versiunea de la instalare la nesfârșit, fără niciun avertisment.

**Pasul 2 — Activați plugin-ul.** După sincronizare apare cardul **Monitorizare legislativa**. Deschideți-l cu rotița din colț și activați-l.

**Pasul 3 — Conectați Gmail.** În **Settings → Connectors**, alegeți **Gmail** și autorizați accesul. Fără Gmail raportul nu poate fi trimis — asistentul vă spune dacă lipsește și se oprește elegant.

**Pasul 4 — Conectați un folder de pe calculator.** Configurația și istoricul monitorizării stau într-un fișier pe calculatorul dumneavoastră, într-un folder conectat în aplicația Claude („Add folder" / butonul de folder din panoul Context). Alegeți un folder stabil, de exemplu cel de lucru al cabinetului.

**Pasul 5 — Configurarea.** Scrieți în conversație:

> Configurează monitorizarea știrilor contabile

Asistentul vă întreabă, într-un singur mesaj, cinci lucruri — fiecare cu o variantă propusă, ca să puteți răspunde „lăsați așa":

| Ce vă întreabă | Ce propune |
|---|---|
| În ce folder conectat ține fișierul de configurare | folderul conectat la pasul 4 |
| Adresa de email pentru rapoarte | — |
| Cât în urmă să se uite la primul raport | ultimele 7 zile |
| Cât de des rulează | săptămânal |
| Ziua și ora | luni, 08:00 |

Nu vă întreabă ce domenii vă interesează: raportul acoperă tot ce are impact asupra activității unui contabil.

**Pasul 6 — Creați task-ul programat.** Asistentul **nu** creează programarea în locul dumneavoastră: la finalul configurării primiți o **fișă cu toate valorile** de completat în **Scheduled tasks → New task** — nume, instrucțiuni (gata de copiat), folderul, frecvența, permisiunile („Skip all approvals") și comutatorul **Require this computer** (pornit — el dă rulărilor acces la folderul cu fișierul de configurare). După salvare mai e un singur pas: deschideți task-ul și activați **Gmail** pentru el (butonul **+** → Connectors), apoi testați cu „Run now".

Primul raport vi-l poate genera pe loc, în aceeași conversație: „Rulează monitorizarea".

<details>
<summary>Instalare din terminal, pentru administratori</summary>

```
/plugin marketplace add adrianbarna/alfinRepo
/plugin install monitorizare-legislativa@lacramioara-conta
```

Dacă sumarul spune `Run /reload-plugins to activate.`, rulați și `/reload-plugins`.

Pe această cale marketplace-ul se **clonează local**, deci mașina are nevoie de git instalat. Calea din Settings nu are nevoie: clonarea se face pe serverele Anthropic.

</details>

Din acel moment totul e automat: raportul sosește săptămânal pe email.

## Comenzi utile după instalare

| Ce vreți | Ce scrieți |
|---|---|
| Raport imediat, în afara programării | „Rulează acum monitorizarea legislativă" |
| Schimbarea adresei de email | „Schimbă adresa de email pentru rapoartele legislative în ..." |
| Adăugarea unei surse de monitorizat | „Adaugă sursa <URL> la monitorizarea legislativă" |
| Schimbarea zilei/orei de rulare | „Mută monitorizarea legislativă <ziua> la <ora>" |

## Cum funcționează în spate (pentru administrator)

- Monitorizarea are **două skill-uri**: `initial-config-monitorizare-stiri-conta` (configurarea, o singură dată) și `monitorizare-stiri-conta` (rularea). Configurația și istoricul stau într-un fișier numit `monitorizare-legislativa-state.json` (adresa destinatar, ritmul, data ultimei rulări, lista actelor deja raportate — pentru a nu trimite același act de două ori), salvat **pe calculatorul utilizatorului, într-un folder conectat** — sesiunile cloud nu păstrează fișiere între rulări. Numele fișierului e fix, ca să poată fi regăsit prin căutare oriunde ar fi salvat.
- **Distribuție**: repo public pe GitHub, `adrianbarna/alfinRepo`. Marketplace-ul se adaugă cu scurtătura `owner/repo`, iar fiecare plugin stă în subfolderul lui și e livrat prin cale relativă: `"source": "./monitorizare-legislativa-plugin/monitorizare-legislativa"`, respectiv `"source": "./monitorizare-legislativa-plugin/incasari-saga"`.
- **De ce cale relativă și nu arhivă zip**: validatorul din Settings → Plugins nu acceptă tipul de sursă `archive` — recunoaște repo-ul, dar sincronizarea eșuează. Cu marketplace-ul clonat, calea relativă se rezolvă corect. Compromisul: instalarea din terminal cere git local.
- **GitLab nu funcționează pentru această cale.** Dialogul de adăugare validează adresa server-side ca repo GitHub și respinge orice adresă GitLab, indiferent de formă — repo, `.git` sau raw.
- **Actualizări**: `version` stă **doar** în `plugin.json`-ul fiecărui plugin (niciodată în `marketplace.json` — documentația interzice dublarea) și se incrementează la fiecare release; fără bump, push-ul nu ajunge la client. La client mai trebuie o singură condiție: `Sync automatically` pornit, în meniul `···` al marketplace-ului — **nu vine pornit din oficiu**, iar fără el plugin-ul rămâne pe versiunea de la instalare la nesfârșit, fără avertisment. Meniul afișează `Synced commit`, util pentru diagnostic: comparați-l cu ultimul commit de pe GitHub.
- Sursele și metoda de acces a fiecăreia: [monitorizare-legislativa/skills/monitorizare-stiri-conta/references/surse.md](monitorizare-legislativa/skills/monitorizare-stiri-conta/references/surse.md).
- Formatul raportului: [monitorizare-legislativa/skills/monitorizare-stiri-conta/references/email-template.md](monitorizare-legislativa/skills/monitorizare-stiri-conta/references/email-template.md).
- Logica completă de rulare: [monitorizare-legislativa/skills/monitorizare-stiri-conta/SKILL.md](monitorizare-legislativa/skills/monitorizare-stiri-conta/SKILL.md).
