# alfinRepo

Repo-ul de lucru al cabinetului **ALFIN Consult**. Ține la un loc **marketplace-ul de
plugin-uri Claude** și **folderul de lucru pentru încasări**.

```
.claude-plugin/marketplace.json      marketplace-ul `alfin-consult`
plugins/                             cele două plugin-uri
  monitorizare-legislativa/          veghe legislativă săptămânală, raport pe email
  incasari-saga/                     borderouri Cargus/Packeta → XML de import în Saga
incasari/                            folderul de lucru al încasărilor (copia de lucru
                                     a skill-urilor + mapările de coloane)
```

## Instalare

Din aplicație: **Settings → Customize → Plugins**, fila **Personal**, **+**, apoi
`adrianbarna/alfinRepo` și **Sync**. În meniul `···` al marketplace-ului pornește
**Sync automatically** — nu vine pornit din oficiu, iar fără el plugin-ul rămâne pe
versiunea de la instalare, în tăcere.

Din terminal (Claude Code):

```
/plugin marketplace add adrianbarna/alfinRepo
/plugin install monitorizare-legislativa@alfin-consult
/plugin install incasari-saga@alfin-consult
```

Instrucțiunile de utilizare sunt în [`plugins/README.md`](plugins/README.md) și
[`plugins/incasari-saga/README.md`](plugins/incasari-saga/README.md). Protocolul de
release și capcanele descoperite prin testare stau în CLAUDE.md-uri.

## Configurare implicită

Ambele plugin-uri propun la configurare **alfin.consult.ai@gmail.com** ca adresă de
raport. Adresa se confirmă o dată, la configurare, și rămâne schimbabilă oricând —
niciun plugin nu trimite la o adresă neconfirmată.

Căile de foldere rămân întrebate la prima rulare pe fiecare mașină: diferă de la un
calculator la altul și nu se pot presupune.

## Date contabile

**Nu intră niciodată în acest repo.** Borderourile, exporturile de facturi și
`config.json`-ul (per mașină, în `~/.claude/incasari-saga/`) stau în afara git-ului.
