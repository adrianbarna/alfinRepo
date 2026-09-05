# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ce este acest repo

`alfinRepo` ține la un loc **două lucruri fără legătură directă între ele**, sub același
remote GitHub (`adrianbarna/alfinRepo`, singurul remote, branch `main`):

```
.claude-plugin/marketplace.json      marketplace-ul Claude Code `alfin-consult`
plugins/                             cele două plugin-uri livrate prin marketplace
  monitorizare-legislativa/          veghe legislativă săptămânală, raport pe email
  incasari-saga/                     borderouri Cargus/Packeta → XML de import în Saga
incasari/                            folderul de lucru al încasărilor (copie a
                                      skill-urilor din incasari-saga + mapările de coloane)
```

`incasari/` **nu e cod separat** — e o copie de lucru a skill-urilor din
`plugins/incasari-saga/skills/`, ținută identică cu sursa (`diff -r`) și folosită pentru
verificare pe date reale. Fiecare din cele trei foldere are propriul `CLAUDE.md`, mult mai
detaliat decât acesta — **citește-l pe cel relevant înainte de a lucra acolo**:

- [`plugins/CLAUDE.md`](plugins/CLAUDE.md) — arhitectura marketplace-ului, protocolul de
  release, capcanele de distribuție descoperite prin testare, invariantele celor două
  plugin-uri.
- [`incasari/CLAUDE.md`](incasari/CLAUDE.md) — logica de mapare Excel → XML, legarea
  facturilor, contractul XML cu Saga, rezultatul de referință pentru verificare.

Nu există build, lint sau suită de teste la nivel de repo. Singura verificare automată e
`claude plugin validate ./`, care validează doar `.claude-plugin/*.json` — niciodată
conținutul instrucțiunilor sau al scriptului Python.

Textul e integral în română, inclusiv comentariile și mesajele de commit. Păstrează limba.

## Comenzi de bază (din rădăcina repo-ului)

```bash
claude plugin validate ./                                 # marketplace.json + ambele plugin-uri
claude plugin validate ./plugins/monitorizare-legislativa
claude plugin validate ./plugins/incasari-saga
claude --plugin-dir ./plugins/monitorizare-legislativa     # rulare locală, fără instalare
```

Verificarea reală pentru `incasari-saga` (script determinist, singurul cu logică
verificabilă) e detaliată în `incasari/CLAUDE.md`, secțiunea „Verificare" — o rulare
`--dry-run --reproceseaza` pe borderoul de referință, cu un rezultat exact de comparat.

## Ce trebuie știut înainte de orice modificare

- **Fiecare plugin stă în propriul subfolder sub `plugins/`; niciodată în rădăcină**
  (`"source": "./"` a rămas otrăvit definitiv în cache-ul Directory al claude.ai — vezi
  `plugins/CLAUDE.md`).
- **`version` din `plugin.json` e singurul loc unde se declară versiunea** — niciodată și
  în `marketplace.json`. Fără bump la fiecare release, actualizarea nu ajunge la
  instalare, în tăcere.
- **Redenumirea unui folder de plugin schimbă `source` din `marketplace.json` și cere
  bump de versiune** — exact ce s-a întâmplat la trecerea `monitorizare-legislativa-plugin/`
  → `plugins/` (05.09.2026, bump la 2.0.0 pe ambele plugin-uri).
- **`incasari/` și `plugins/incasari-saga/skills/` trebuie ținute identice.** Sursa de
  adevăr pentru release e `plugins/`; `incasari/` e copia de lucru, testată pe date reale.
  Protocolul complet de sincronizare + push e în `plugins/CLAUDE.md`, secțiunea „Protocol
  de release".
- **Orice pas de instalare sau configurare la nivel de mașină (instalare de software,
  setări de sistem, configurare de cont Windows etc.) trebuie adăugat în
  [`installation.md`](installation.md)**, ori de câte ori consideri că e necesar pentru
  reproducerea configurării pe altă mașină — nu doar rulat și uitat. Ține fișierul la zi
  ca ghid complet de instalare pe o mașină nouă.
