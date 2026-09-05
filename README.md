# alfinRepo

Repo-ul de lucru pentru cabinetul de contabilitate Lăcrămioara (PFA). Ține la un loc
**marketplace-ul de plugin-uri Claude Code** și **folderul de lucru pentru încasări**,
care până acum stăteau separat.

```
.claude-plugin/marketplace.json      marketplace-ul `lacramioara-conta`
monitorizare-legislativa-plugin/     cele două plugin-uri livrate clientei
  monitorizare-legislativa/          veghe legislativă săptămânală, raport pe email
  incasari-saga/                     borderouri Cargus/Packeta → XML de import în Saga
incasari/                            folderul de lucru al încasărilor (copia de lucru
                                     a skill-urilor + mapările de coloane)
```

## Instalare la client

În Claude Code:

```
/plugin marketplace add adrianbarna/alfinRepo
/plugin install monitorizare-legislativa@lacramioara-conta
/plugin install incasari-saga@lacramioara-conta
```

Din aplicație: **Settings → Plugins**, adaugă marketplace-ul `adrianbarna/alfinRepo`,
apoi în meniul `···` al marketplace-ului pornește **Sync automatically** — nu vine
pornit din oficiu, iar fără el plugin-ul rămâne pe versiunea de la instalare.

Instrucțiunile pentru utilizator sunt în
[`monitorizare-legislativa-plugin/README.md`](monitorizare-legislativa-plugin/README.md)
și [`monitorizare-legislativa-plugin/incasari-saga/README.md`](monitorizare-legislativa-plugin/incasari-saga/README.md).
Protocolul de release și capcanele descoperite prin testare stau în CLAUDE.md-urile
din cele două subfoldere.

## Date de client

**Nu intră niciodată în acest repo.** Borderourile, exporturile de facturi și
`config.json`-ul (per mașină, în `~/.claude/incasari-saga/`) stau în afara git-ului.
