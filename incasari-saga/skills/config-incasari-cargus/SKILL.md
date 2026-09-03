---
name: config-incasari-cargus
description: >
  Configurează skill-ul incasari-cargus pe mașina curentă: unde stau borderourile,
  folderul cu exporturile XML de facturi din Saga și adresele de e-mail pentru
  raport. Folosește acest skill la prima instalare pe o mașină nouă, când scriptul
  de procesare iese cu cod 2 (configurare lipsă), sau când apare „configurează
  încasările", „config încasări", „schimbă folderul de borderouri", „unde se uită
  scriptul", „setează folderul de facturi", „schimbă adresele de raport",
  „adaugă EUR", „mută borderourile".
---

# Configurarea skill-ului incasari-cargus

Skill-ul `incasari-cargus` se livrează **fără nicio cale setată** — căile diferă de
la o mașină la alta, așa că se stabilesc aici, la prima rulare pe fiecare mașină.
Configul stă la `~/.claude/incasari-saga/config.json` (în afara skill-ului, ca să
supraviețuiască actualizărilor și să nu plece cu skill-ul spre altă mașină).

Totul trece prin scriptul skill-ului frate `incasari-cargus`. Mai jos, `<skills-dir>` e
folderul care conține ambele skill-uri (calea afișată la încărcarea skill-ului, fără
ultimul segment): instalat ca plugin, `<plugin-dir>/skills`; copiat într-un proiect,
`<proiect>/.claude/skills`. Folosește **calea absolută** — utilizatorul rulează din
folderul lui de lucru:

```
python3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --arata-config
```

**Interpretorul depinde de sistem:** `python3` pe macOS/Linux, `py -3` (sau `python`)
pe Windows — verifică o dată cu `--version`. Comenzile de mai jos sunt scrise cu
`python3`, pe Windows pui `py -3` în loc; merg la fel în bash și în PowerShell (o comandă
pe linie, fără `&&`, `||`, redirecționări sau `cd`). Ordinea de încercare pe Windows și
ce înseamnă mesajul „Python was not found": secțiunea „Cum rulezi scriptul" din skill-ul
`incasari-cargus`. Pe Windows configul ajunge la
`C:\Users\<utilizator>\.claude\incasari-saga\config.json`. Căile primite de la
utilizator se pun între ghilimele duble; pe Windows merg și cu `\`, și cu `/`.

## Regula de aur

**Nu edita `config.json` de mână și nu ghici nicio cale.** Fiecare cale vine de la
utilizator; scriptul o validează (refuză căile inexistente) și o salvează singur.
Nu crea foldere în locul utilizatorului. **Nu crea fișiere de lansare (`.bat`, `.ps1`,
`.sh`) și nu instala Python** — dacă lipsește, spune-i utilizatorului să-l instaleze de
pe python.org.

## Flux

### 1. Arată starea curentă

Rulează `--arata-config`. Afișează unde e configul, folderele de borderouri (cu
valută și cont), folderul de facturi și adresele de e-mail — și marchează ce
lipsește sau ce cale nu mai există pe disc.

### 2. Prima configurare (nimic setat)

Întreabă utilizatorul, pe rând — **nu ghici, nu propune căi**:

1. **Unde ține borderourile în lei?** (folderul cu fișierele .xlsx)

   ```
   python3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --set-folder "<cale>" --moneda RON
   ```

2. **Unde ține exporturile XML de facturi din Saga?**

   ```
   python3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --set-facturi "<cale>"
   ```

3. **Cui se trimite raportul pe e-mail?** (pot fi mai multe adrese)

   ```
   python3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --set-email "adresa1@exemplu.ro,adresa2@exemplu.ro"
   ```

Dacă scriptul răspunde „Calea nu exista sau nu e un folder", spune-i utilizatorului
și cere calea corectă — nu o corecta din proprie inițiativă.

### 3. Verifică și încheie

Rulează din nou `--arata-config` și arată utilizatorului configurarea rezultată.
Apoi propune o probă fără efecte:

```
python3 <skills-dir>/incasari-cargus/scripts/proceseaza.py --dry-run
```

Dacă proba arată borderouri de procesat, procesarea propriu-zisă e treaba
skill-ului `incasari-cargus`, nu a acestui skill.

### 4. Modificări ulterioare

Schimbă **doar ce cere utilizatorul**, cu aceleași comenzi `--set-*`:

| Ce se schimbă | Comanda |
|---|---|
| folderul de borderouri RON | `--set-folder "<cale>" --moneda RON` |
| valută nouă (ex. EUR, cont 5126) | `--set-folder "<cale>" --moneda EUR` |
| folderul de facturi | `--set-facturi "<cale>"` |
| adresele de raport | `--set-email "a@b.ro,c@d.ro"` (înlocuiește lista întreagă) |

`--set-folder` **înlocuiește** intrarea valutei respective, nu adaugă un al doilea
folder pe aceeași valută. RON merge pe contul 5125, orice altă valută pe 5126 —
conturile le pune scriptul, nu se cer utilizatorului. **HUF e ignorat deocamdată.**

## De știut

- Instalat ca plugin, căile se salvează absolut. Copiat într-un proiect la
  `<proiect>/.claude/skills/`, căile din interiorul proiectului se salvează relativ
  (merge pe alt PC fără reconfigurare), cele din afara lui absolut.
- Mutarea unui folder de valută nu pierde evidența: jurnalul `.procesate.json`
  călătorește cu folderul. După mutare trebuie doar refăcut `--set-folder`.
- Variabila de mediu `INCASARI_CONFIG` poate indica alt fișier de config (util la
  teste); un `config.json` rămas lângă skill din instalări vechi are prioritate.
