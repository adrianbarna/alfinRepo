# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ce este acest repo

Un **marketplace Claude Code cu două plugin-uri**, nu o aplicație:

| Plugin | Unde | Ce e „sursa" |
|---|---|---|
| `monitorizare-legislativa` | `veghe-legislativa/` | patru fișiere Markdown |
| `incasari-saga` | `incasari-saga/` | Markdown **plus** un script Python |

Pentru **monitorizare-legislativa** nu există cod executabil, build, dependențe sau teste: tot „sursa" sunt fișierele Markdown care descriu comportamentul unui agent de veghe legislativă. Consecința practică: **a edita acea parte înseamnă a edita comportamentul unui model**, nu a schimba logică deterministă. Nimic nu e impus de un runtime — o instrucțiune ambiguă produce un comportament greșit fără nicio eroare. Formularea contează la fel de mult ca structura.

Pentru **incasari-saga** e invers: conversia e făcută de `skills/incasari-cargus/scripts/proceseaza.py`, cod determinist, verificabil. Skill-ul doar îl rulează și rezumă raportul. **Nu genera XML de mână și nu citi borderourile cu alte unelte** — un borderou are sute de rânduri.

Textul e integral în română, inclusiv comentariile și mesajele de commit. Păstrează limba.

## Comenzi

```bash
claude plugin validate ./                 # marketplace.json + toate intrările
claude plugin validate ./veghe-legislativa
claude plugin validate ./incasari-saga
claude --plugin-dir .                     # încarcă plugin-ul local, fără instalare
```

Nu există build, lint sau teste. `claude plugin validate` verifică doar `.claude-plugin/*.json`, niciodată conținutul instrucțiunilor.

Pentru `incasari-saga` există totuși o verificare reală: o rulare de probă pe borderoul de referință, descrisă în secțiunea „Verificare".

## Cinci nume diferite pentru același lucru

Sursă frecventă de confuzie:

| Ce | Unde e definit | Valoare |
|---|---|---|
| Nume marketplace | `marketplace.json` | `lacramioara-conta` |
| Repo GitHub | remote `github` | `adrianbarna/contaLacramioara` |
| Nume plugin 1 | `veghe-legislativa/.claude-plugin/plugin.json` | `monitorizare-legislativa` |
| Nume skill 1 | folderul + frontmatter | `contaChangeSkill` |
| Instalare 1 | — | `monitorizare-legislativa@lacramioara-conta` |
| Invocare 1 | — | `/monitorizare-legislativa:contaChangeSkill` |
| Nume plugin 2 | `incasari-saga/.claude-plugin/plugin.json` | `incasari-saga` |
| Nume skill 2 | folderul + frontmatter | `incasari-cargus` |
| Instalare 2 | — | `incasari-saga@lacramioara-conta` |
| Invocare 2 | — | `/incasari-saga:incasari-cargus` |

## Protocol de release

**`version` stă într-un singur loc — `plugin.json`-ul fiecărui plugin — și se incrementează la fiecare release.** Cu `version` declarat, pluginul e *pinned*: un push fără bump **nu ajunge la client, în tăcere**. Bump-ul nu e opțional.

**Niciodată `version` în intrările din `marketplace.json`.** Documentația oficială interzice dublarea — „Avoid setting `version` in both `plugin.json` and the marketplace entry. Claude Code always uses the `plugin.json` value without warning" — iar când am avut-o, cele două valori au divergat în aceeași zi. `claude plugin validate ./` prinde nepotrivirea; rulează-l înainte de push.

Alternativa fără `version` (versiunea = SHA-ul commit-ului, push = release) e și ea validă oficial și a fost folosită temporar; dacă bump-ul devine o povară, e calea de simplificare.

Push pe remote-ul **`github`**, care e sursa de adevăr. `origin` e un GitLab vechi, rămas în urmă și care respinge push-ul; nu te baza pe el. Două sesiuni Claude lucrează uneori simultan pe acest repo — fă `git pull --rebase github main` înainte de push.

La client mai e nevoie și de `Sync automatically` pornit — nu vine pornit din oficiu, iar fără el plugin-ul rămâne blocat pe versiunea de la instalare, în tăcere.

## Constrângeri de distribuție, descoperite prin testare

Documentate pe larg în README, secțiunea „Cum funcționează în spate". Pe scurt, ca să nu fie reintroduse din greșeală:

- **Fiecare plugin stă în propriul subfolder** (`"source": "./veghe-legislativa"`, `"source": "./incasari-saga"`), iar rădăcina ține doar `marketplace.json`. Pluginul de monitorizare a stat inițial în rădăcină (`"source": "./"`) și a fost mutat: serverul Directory părea să lege artefactul cache-uit și de calea sursei, iar redenumirea singură nu l-a făcut să apară în catalog. Nu mai pune niciun plugin în rădăcină.
- **Sursele din `marketplace.json` trebuie să fie căi relative.** Tipul `archive` (zip peste HTTPS) e recunoscut de Claude Code CLI, dar validatorul server-side de la claude.ai îl respinge: găsește repo-ul, apoi sincronizarea eșuează fără explicație.
- **GitLab nu funcționează** pentru instalarea din claude.ai. Validatorul rezolvă adresa ca repo GitHub și respinge orice formă GitLab — repo, `.git` sau raw.
- Compromisul acceptat: cu cale relativă, instalarea din terminal clonează repo-ul, deci acolo e nevoie de git local. Instalarea din Settings nu are nevoie — clonarea se face pe serverele Anthropic.
- **Cache-ul Directory: nu refolosi sursa `./` și nu muta niciun plugin în rădăcină.** Înregistrarea inițială (nume `monitorizare-legislativa`, sursă `./`) a rămas înghețată pe o versiune depășită, imună la sync, la dezinstalare și la reinstalare; abia o intrare cu **nume și cale noi** a apărut curată. Numele a fost apoi restaurat pe calea nouă `./veghe-legislativa` și cardul a apărut curat, cu versiunea corectă — deci **cheia otrăvită era calea `./`, nu numele**. Folderul rămâne `veghe-legislativa/` indiferent de numele pluginului: redenumirea lui ar schimba iar calea sursei. Fișierul de stare (`monitorizare-legislativa-state.json`, `~/.claude/monitorizare-legislativa/`) nu se redenumește niciodată.

## Arhitectura celor trei documente

`veghe-legislativa/skills/contaChangeSkill/SKILL.md` e bucla de rulare, în șapte pași. Citește celelalte două la momente precise:

- **pasul 3** → `references/surse.md`, catalogul surselor, grupat pe trei niveluri: *ce urmează* (ședințe de Guvern, SGG), *ce s-a publicat* (Monitorul Oficial, portalul legislativ), *ce înseamnă pentru contabil* (presa de specialitate). Fișierul conține și o listă de domenii testate ca inaccesibile, cu data verificării — acolo, nu în SKILL.md.
- **pasul 6** → `references/email-template.md`, contractul de ieșire: structura raportului și regulile de redactare.

Când modifici un comportament, verifică dacă e descris în mai multe locuri. Regulile despre ce intră în email există și în SKILL.md, și în email-template.md — o contradicție între ele s-a manifestat deja în producție.

## `incasari-saga`: unde stau lucrurile

- `incasari-saga/skills/incasari-cargus/SKILL.md` — fluxul conversațional.
- `incasari-saga/skills/incasari-cargus/scripts/proceseaza.py` — toată logica. Fără dependințe externe: `.xlsx` e citit direct cu `zipfile` + `ElementTree`, ca să meargă pe orice PC cu `python3`.
- **Configurația nu stă în plugin.** Se scrie în `~/.claude/incasari-saga/config.json`, pentru că folderul plugin-ului e rescris la fiecare actualizare. Poate fi mutată cu variabila de mediu `INCASARI_CONFIG`.
- Scriptul merge în două așezări: instalat ca plugin (rădăcină de proiect inexistentă, căi absolute în config) și copiat într-un proiect la `<proiect>/.claude/skills/incasari-cargus/` (căi relative la proiect, config lângă skill). `_radacina_proiect()` face distincția după numele folderelor părinte — **dacă muți skill-ul, se rup căile relative.**
- **Sursa de adevăr e plugin-ul.** Copia din proiectul de lucru al clientului (`incasari/.claude/skills/incasari-cargus/`) trebuie ținută identică; altfel cele două diverg în tăcere.

## Invariante care nu trebuie stricate

Fiecare vine dintr-un eșec real. Nu le slăbi fără motiv explicit.

**Întreabă despre *când*, niciodată despre *ce*.** La configurare se stabilesc ritmul și destinația: adresa de email, perioada primului raport, frecvența, ziua și ora, unde stă fișierul de stare. Aria acoperită e fixă — tot ce afectează activitatea unui contabil — și nu se cere utilizatorului s-o restrângă.

**Emailul e client-facing.** Îl citește un contabil. Zero mențiuni despre surse blocate, metode de acces, fișier de stare, task-uri programate, permisiuni sau limitări ale mediului. Notele de funcționare se spun în conversație, o singură dată, la prima rulare.

**Starea se regăsește prin căutare după nume**, nu printr-o cale memorată. Numele e fix: `monitorizare-legislativa-state.json`. În Claude Desktop, Cowork și sesiunile cloud sistemul de fișiere se resetează între rulări, deci o cale memorată se pierde odată cu fișierul pe care îl indică. Ordinea de căutare e în SKILL.md, secțiunea „Fișierul de stare".

**`acte_in_asteptare` există dintr-un motiv precis.** Cheia de deduplicare e tip + număr + an („OUG 71/2026"), dar actele adoptate în ședință de Guvern **nu au încă număr**. Sunt urmărite separat și reconciliate prin titlu + tip + dată apropiată când apar în Monitorul Oficial, ca să fie raportate integral o singură dată.

**Rulările programate nu cer niciodată confirmare** — nici pentru accesarea site-urilor, nici pentru trimiterea emailului. Adresa dată la configurare *este* autorizarea. O rulare care așteaptă un „da" la 8 dimineața e o rulare ratată.

**O sursă căzută nu oprește rularea.** 403 și 404 sunt normale și așteptate — gov.ro, ceccar.ro și avocatnet.ro blochează frecvent accesul direct. Se trece la căutare web cu `site:<domeniu>` și se merge mai departe, fără să se raporteze nicăieri.

**Starea se salvează abia după ce emailul a plecat.** Dacă trimiterea eșuează, starea rămâne neatinsă și rularea următoare reia aceleași acte.

**La încasări, toleranța la sumă nu se strânge la egalitate strictă.** Borderoul și factura diferă frecvent cu un ban: pe un borderou real, doar 129 din 216 totaluri coincid exact, 85 diferă cu 0,01. Cu egalitate strictă s-ar sări ~40% din rânduri.

**Numele e control secundar, nu cheie.** Cheia e `RefExp1` = `inf_suplm`. Căutarea după nume e strict rezervă: folosită în paralel cu cheia, un omonim cu aceeași sumă face ambiguă o potrivire deja sigură. Un nume care diferă dă doar avertisment — pe colet e persoana, pe factură firma.

**Un rând sărit e raportat, nu înghițit.** Inclusiv când *toate* rândurile sunt sărite: atunci nu se scrie niciun XML, dar raportul trebuie totuși compus și trimis — e cazul în care utilizatorul are cel mai mult de verificat.

## Verificare

### `incasari-saga`

Rulare de probă pe borderoul de referință din proiectul clientului:

```bash
python3 incasari-saga/skills/incasari-cargus/scripts/proceseaza.py \
  --dry-run --reproceseaza "Cargus Packeta Iulie 2026.xlsx"
```

Rezultat așteptat: **219 linii, total 26569.26 RON**, defalcat pe 10/16/23/30.07.2026 = 7178.10 / 6334.61 / 6951.29 / 6105.26, **fiecare linie cu `FacturaNumar` completat, niciun rând sărit**, și 15 avertismente: 8 de nume, 3 de storno, 2 de sumă (0,08 și 0,02) și 2 de lungime `RefExp1`.

### `monitorizare-legislativa`

Nu există teste automate; singura verificare reală e o rulare live cu Gmail conectat.

Testul care contează cel mai mult e **deduplicarea pe două rulări**, fiindcă e singura logică cu stare: rulează, apoi pune manual `ultima_rulare` cu șapte zile în urmă în fișierul de stare și rulează din nou. Actele deja raportate nu trebuie să reapară, iar un act din `acte_in_asteptare` publicat între timp trebuie să apară o singură dată, în raportul principal.

Această logică nu a fost niciodată executată cu succes cap-coadă. Mediile unde a rulat până acum resetează sistemul de fișiere între sesiuni, deci starea nu a supraviețuit — de aici și mecanismul de căutare a fișierului în stocarea conectată.
