# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ce este acest repo

Un **plugin Claude Code**, nu o aplicație. Nu există cod executabil, build, dependențe sau teste: tot „sursa" sunt patru fișiere Markdown care descriu comportamentul unui agent de veghe legislativă pentru un cabinet de contabilitate din România.

Consecința practică: **a edita acest repo înseamnă a edita comportamentul unui model**, nu a schimba logică deterministă. Nimic nu e impus de un runtime — o instrucțiune ambiguă produce un comportament greșit fără nicio eroare. Formularea contează la fel de mult ca structura.

Textul e integral în română, inclusiv comentariile și mesajele de commit. Păstrează limba.

## Comenzi

```bash
claude plugin validate ./     # singura verificare automată: manifestele
claude --plugin-dir .         # încarcă plugin-ul local, fără instalare
```

Nu există build, lint sau teste. `claude plugin validate` verifică doar `.claude-plugin/*.json`, niciodată conținutul instrucțiunilor.

## Cinci nume diferite pentru același lucru

Sursă frecventă de confuzie:

| Ce | Unde e definit | Valoare |
|---|---|---|
| Nume plugin | `plugin.json` | `monitorizare-legislativa` |
| Nume marketplace | `marketplace.json` | `lacramioara-conta` |
| Nume skill | folderul + frontmatter | `contaChangeSkill` |
| Repo GitHub | remote `github` | `adrianbarna/contaLacramioara` |
| Instalare | — | `monitorizare-legislativa@lacramioara-conta` |
| Invocare | — | `/monitorizare-legislativa:contaChangeSkill` |

## Protocol de release

**Incrementează `version` în `.claude-plugin/plugin.json` la fiecare modificare.** Fără asta, push-ul nu ajunge niciodată la client — sistemul nu-l vede ca schimbare. Nu e opțional și nu dă niciun avertisment când e omis.

Push pe remote-ul **`github`**, care e sursa de adevăr. `origin` e un GitLab vechi, rămas în urmă și care respinge push-ul; nu te baza pe el.

La client mai e nevoie și de `Sync automatically` pornit — nu vine pornit din oficiu, iar fără el plugin-ul rămâne blocat pe versiunea de la instalare, în tăcere.

## Constrângeri de distribuție, descoperite prin testare

Documentate pe larg în README, secțiunea „Cum funcționează în spate". Pe scurt, ca să nu fie reintroduse din greșeală:

- **`"source": "./"` în `marketplace.json` e obligatoriu.** Tipul `archive` (zip peste HTTPS) e recunoscut de Claude Code CLI, dar validatorul server-side de la claude.ai îl respinge: găsește repo-ul, apoi sincronizarea eșuează fără explicație.
- **GitLab nu funcționează** pentru instalarea din claude.ai. Validatorul rezolvă adresa ca repo GitHub și respinge orice formă GitLab — repo, `.git` sau raw.
- Compromisul acceptat: cu cale relativă, instalarea din terminal clonează repo-ul, deci acolo e nevoie de git local. Instalarea din Settings nu are nevoie — clonarea se face pe serverele Anthropic.

## Arhitectura celor trei documente

`skills/contaChangeSkill/SKILL.md` e bucla de rulare, în șapte pași. Citește celelalte două la momente precise:

- **pasul 3** → `references/surse.md`, catalogul surselor, grupat pe trei niveluri: *ce urmează* (ședințe de Guvern, SGG), *ce s-a publicat* (Monitorul Oficial, portalul legislativ), *ce înseamnă pentru contabil* (presa de specialitate). Fișierul conține și o listă de domenii testate ca inaccesibile, cu data verificării — acolo, nu în SKILL.md.
- **pasul 6** → `references/email-template.md`, contractul de ieșire: structura raportului și regulile de redactare.

Când modifici un comportament, verifică dacă e descris în mai multe locuri. Regulile despre ce intră în email există și în SKILL.md, și în email-template.md — o contradicție între ele s-a manifestat deja în producție.

## Invariante care nu trebuie stricate

Fiecare vine dintr-un eșec real. Nu le slăbi fără motiv explicit.

**Întreabă despre *când*, niciodată despre *ce*.** La configurare se stabilesc ritmul și destinația: adresa de email, perioada primului raport, frecvența, ziua și ora, unde stă fișierul de stare. Aria acoperită e fixă — tot ce afectează activitatea unui contabil — și nu se cere utilizatorului s-o restrângă.

**Emailul e client-facing.** Îl citește un contabil. Zero mențiuni despre surse blocate, metode de acces, fișier de stare, task-uri programate, permisiuni sau limitări ale mediului. Notele de funcționare se spun în conversație, o singură dată, la prima rulare.

**Starea se regăsește prin căutare după nume**, nu printr-o cale memorată. Numele e fix: `monitorizare-legislativa-state.json`. În Claude Desktop, Cowork și sesiunile cloud sistemul de fișiere se resetează între rulări, deci o cale memorată se pierde odată cu fișierul pe care îl indică. Ordinea de căutare e în SKILL.md, secțiunea „Fișierul de stare".

**`acte_in_asteptare` există dintr-un motiv precis.** Cheia de deduplicare e tip + număr + an („OUG 71/2026"), dar actele adoptate în ședință de Guvern **nu au încă număr**. Sunt urmărite separat și reconciliate prin titlu + tip + dată apropiată când apar în Monitorul Oficial, ca să fie raportate integral o singură dată.

**Rulările programate nu cer niciodată confirmare** — nici pentru accesarea site-urilor, nici pentru trimiterea emailului. Adresa dată la configurare *este* autorizarea. O rulare care așteaptă un „da" la 8 dimineața e o rulare ratată.

**O sursă căzută nu oprește rularea.** 403 și 404 sunt normale și așteptate — gov.ro, ceccar.ro și avocatnet.ro blochează frecvent accesul direct. Se trece la căutare web cu `site:<domeniu>` și se merge mai departe, fără să se raporteze nicăieri.

**Starea se salvează abia după ce emailul a plecat.** Dacă trimiterea eșuează, starea rămâne neatinsă și rularea următoare reia aceleași acte.

## Verificare

Nu există teste automate; singura verificare reală e o rulare live cu Gmail conectat.

Testul care contează cel mai mult e **deduplicarea pe două rulări**, fiindcă e singura logică cu stare: rulează, apoi pune manual `ultima_rulare` cu șapte zile în urmă în fișierul de stare și rulează din nou. Actele deja raportate nu trebuie să reapară, iar un act din `acte_in_asteptare` publicat între timp trebuie să apară o singură dată, în raportul principal.

Această logică nu a fost niciodată executată cu succes cap-coadă. Mediile unde a rulat până acum resetează sistemul de fișiere între sesiuni, deci starea nu a supraviețuit — de aici și mecanismul de căutare a fișierului în stocarea conectată.
