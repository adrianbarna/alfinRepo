# Configurarea skill-ului `incasari-cargus`

Citește acest fișier **doar** în două situații:

- scriptul a ieșit cu **codul 2** — nu știe unde sunt borderourile sau facturile;
- utilizatorul cere o schimbare: altă cale, altă valută, alte adrese de raport.

În rest, nu-l încărca: rularea normală n-are nevoie de nimic de aici.

Configul stă la `~/.claude/incasari-saga/config.json` — pe Windows
`C:\Users\<utilizator>\.claude\incasari-saga\config.json`. Stă **în afara skill-ului**
pentru că folderul plugin-ului e rescris la fiecare actualizare.

Mai jos, `<skill-dir>` e folderul skill-ului `incasari-cargus` (calea afișată la
încărcarea lui). Comenzile sunt scrise cu `py -3`, interpretorul mașinii de lucru; pe
macOS/Linux pui `python3`. Restul e identic și merge la fel în PowerShell și în bash.

## Regula de aur

**Nu edita `config.json` de mână și nu inventa nicio cale.** Fiecare cale vine de la
utilizator sau din lista de mai jos, iar scriptul o validează — refuză căile
inexistente — și o salvează singur. Nu crea foldere în locul utilizatorului. **Nu crea
fișiere de lansare (`.bat`, `.ps1`, `.sh`) și nu instala Python**; dacă lipsește,
spune-i să-l instaleze de pe python.org.

## Valorile ALFIN Consult

Astea sunt valorile de propus, nu de scris tăcut. Le arăți, utilizatorul confirmă
(„da", „lasă așa") sau dă altele, și abia atunci le salvezi.

| Ce | Valoarea propusă |
|---|---|
| Borderouri RON | `C:\Users\Barna\My Drive\claude\incasari-saga\borderouri\ron` |
| Facturi (export XML Saga) | `C:\Users\Barna\My Drive\claude\incasari-saga\facturi` |
| Adresa de raport | `alfin.consult.ai@gmail.com` |

Căile sunt în **Google Drive sincronizat în modul Mirror**, deci fișiere reale pe disc.
**Nu propune niciodată litera `G:`**, chiar dacă apare pe mașină: e un drive virtual
vizibil doar în sesiunea interactivă a utilizatorului logat, iar un task programat nu-l
vede. Pe alt calculator sau alt cont Windows, `Barna` din cale se schimbă — atunci
întrebi, nu presupui.

## Flux

### 1. Arată starea curentă

```
py -3 <skill-dir>/scripts/proceseaza.py --arata-config
```

Afișează unde e configul, folderele de borderouri (cu valută și cont), folderul de
facturi și adresele de e-mail — și marchează ce lipsește sau ce cale nu mai există pe
disc. Prima linie arată versiunea de Python și sistemul, util pentru depanare de la
distanță.

### 2. Prima configurare (nimic setat)

Pe rând, cu valoarea propusă din tabelul de mai sus:

1. **Folderul cu borderourile în lei.**

   ```
   py -3 <skill-dir>/scripts/proceseaza.py --set-folder "C:\Users\Barna\My Drive\claude\incasari-saga\borderouri\ron" --moneda RON
   ```

2. **Folderul cu exporturile XML de facturi din Saga.**

   ```
   py -3 <skill-dir>/scripts/proceseaza.py --set-facturi "C:\Users\Barna\My Drive\claude\incasari-saga\facturi"
   ```

3. **Adresele pentru raport.** Cu mai multe, separate prin virgulă, fără spații.

   ```
   py -3 <skill-dir>/scripts/proceseaza.py --set-email "alfin.consult.ai@gmail.com"
   ```

Dacă scriptul răspunde „Calea nu exista sau nu e un folder", spune-i utilizatorului și
cere calea corectă — nu o corecta din proprie inițiativă. Pe o mașină cu Drive
proaspăt instalat, cauza obișnuită e că sincronizarea Mirror n-a terminat de creat
folderele.

### 3. Verifică și încheie

Rulează din nou `--arata-config` și arată configurarea rezultată. Apoi o probă fără
efecte:

```
py -3 <skill-dir>/scripts/proceseaza.py --dry-run
```

Dacă proba arată borderouri de procesat, procesarea propriu-zisă e treaba fluxului din
`SKILL.md`, nu a acestui fișier.

### 4. Modificări ulterioare

Schimbă **doar ce cere utilizatorul**:

| Ce se schimbă | Comanda |
|---|---|
| folderul de borderouri RON | `--set-folder "<cale>" --moneda RON` |
| valută nouă (ex. EUR, cont 5126) | `--set-folder "<cale>" --moneda EUR` |
| folderul de facturi | `--set-facturi "<cale>"` |
| adresele de raport | `--set-email "a@b.ro,c@d.ro"` (înlocuiește lista întreagă) |

`--set-folder` **înlocuiește** intrarea valutei respective, nu adaugă un al doilea
folder pe aceeași valută. RON merge pe contul 5125, orice altă valută pe 5126 —
conturile le pune scriptul, nu se cer utilizatorului. **HUF e ignorat deocamdată.**

## Gmail lipsă

Dacă uneltele Gmail nu sunt în sesiune, raportul nu poate pleca. Conectorul are **două
niveluri** și ambele trebuie pornite: autorizat la nivel de cont (Settings → Connectors)
și **activat în sesiunea curentă** — în chat, respectiv în task-ul programat. Cazul
tipic de eșec e al doilea: Gmail merge în chatul unde s-a făcut configurarea, dar
rularea programată pornește o sesiune nouă în care conectorul nu e activat.

Spune-i utilizatorului să-l activeze din butonul **+** al casetei de mesaj (sau panoul
**Context**) → Connectors → **Gmail**, pentru chatul sau task-ul respectiv. Nu există
unealtă prin care să faci asta în locul lui. XML-ul e deja scris pe disc, deci nu se
pierde nimic — doar raportul întârzie.

## De știut

- Instalat ca plugin, căile se salvează absolut. Copiat într-un proiect la
  `<proiect>/.claude/skills/`, căile din interiorul proiectului se salvează relativ
  (merge pe alt PC fără reconfigurare), cele din afara lui absolut. Căile din Drive
  sunt în afara proiectului, deci absolute.
- Mutarea unui folder de valută nu pierde evidența: jurnalul `.procesate.json`
  călătorește cu folderul. După mutare trebuie doar refăcut `--set-folder`.
- Variabila de mediu `INCASARI_CONFIG` poate indica alt fișier de config (util la
  teste); un `config.json` rămas lângă skill din instalări vechi are prioritate.
- `_radacina_proiect()` deduce rădăcina din numele folderelor părinte
  (`.claude/skills/<skill>/`) — **dacă muți skill-ul, se rup căile relative.**
