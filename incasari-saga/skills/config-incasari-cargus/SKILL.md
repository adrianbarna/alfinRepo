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

Plugin-ul se livrează **fără nicio cale setată** — căile diferă de la o mașină la
alta, așa că se stabilesc aici, la prima rulare pe fiecare mașină. Configul stă la
`~/.claude/incasari-saga/config.json`, **în afara plugin-ului** — folderul
plugin-ului e rescris la fiecare actualizare.

Totul trece prin scriptul skill-ului frate `incasari-cargus`, din același plugin:
`<plugin-dir>/skills/incasari-cargus/scripts/proceseaza.py`. Folosește-i **calea
absolută** — utilizatorul rulează din folderul lui de lucru, nu din folderul
plugin-ului:

```bash
python3 <plugin-dir>/skills/incasari-cargus/scripts/proceseaza.py --arata-config
```

## Regula de aur

**Nu edita `config.json` de mână și nu ghici nicio cale.** Fiecare cale vine de la
utilizator; scriptul o validează (refuză căile inexistente) și o salvează singur.
Nu crea foldere în locul utilizatorului.

## Flux

### 1. Arată starea curentă

Rulează `--arata-config`. Afișează unde e configul, folderele de borderouri (cu
valută și cont), folderul de facturi și adresele de e-mail — și marchează ce
lipsește sau ce cale nu mai există pe disc.

### 2. Prima configurare (nimic setat)

Întreabă utilizatorul, pe rând — **nu ghici, nu propune căi**:

1. **Unde ține borderourile în lei?** (folderul cu fișierele .xlsx)

   ```bash
   python3 <plugin-dir>/skills/incasari-cargus/scripts/proceseaza.py --set-folder "<cale>" --moneda RON
   ```

2. **Unde ține exporturile XML de facturi din Saga?**

   ```bash
   python3 <plugin-dir>/skills/incasari-cargus/scripts/proceseaza.py --set-facturi "<cale>"
   ```

3. **Cui se trimite raportul pe e-mail?** (pot fi mai multe adrese)

   ```bash
   python3 <plugin-dir>/skills/incasari-cargus/scripts/proceseaza.py --set-email "adresa1@exemplu.ro,adresa2@exemplu.ro"
   ```

Dacă scriptul răspunde „Calea nu exista sau nu e un folder", spune-i utilizatorului
și cere calea corectă — nu o corecta din proprie inițiativă.

### 3. Verifică și încheie

Rulează din nou `--arata-config` și arată utilizatorului configurarea rezultată.
Apoi propune o probă fără efecte:

```bash
python3 <plugin-dir>/skills/incasari-cargus/scripts/proceseaza.py --dry-run
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

- Instalat ca plugin, căile se salvează absolut. (Copiat într-un proiect la
  `<proiect>/.claude/skills/`, căile din interiorul proiectului se salvează relativ.)
- Mutarea unui folder de valută nu pierde evidența: jurnalul `.procesate.json`
  călătorește cu folderul. După mutare trebuie doar refăcut `--set-folder`.
- Variabila de mediu `INCASARI_CONFIG` poate indica alt fișier de config (util la
  teste); un `config.json` rămas lângă skill din instalări vechi are prioritate.
