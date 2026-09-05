# Mapare borderouri (xlsx) → XML import Saga „Încasări"

> **Două formate-sursă distincte.** Documentul acoperă:
> - **Cargus / Packeta** (folder `borderouri/ron`) — implementat în skill-ul `incasari-cargus`,
>   vezi secțiunea de mai jos. Acesta e formatul care se procesează automat azi.
> - **eMAG** — restul documentului (secțiunile „Traducerea mapării vechi", RON, EUR, HUF).
>   Mapare documentată, **neimplementată** în skill.
>
> Cele două nu au nicio coloană comună: `Order ID` / `Fraction value` / `Client name` /
> `Order finalization date` nu există în borderoul Cargus, iar `Awb` / `Destinatar` /
> `RefExp1` / `Data OP` nu există în cel eMAG. Formatul se recunoaște după coloane.

Formatul XML acceptat de Saga (Import documente → Încasări) este:

```xml
<Incasari>
  <Linie>
    <Data>…</Data>
    <Numar>…</Numar>
    <Suma>…</Suma>
    <Cont>…</Cont>              <!-- cont de trezorerie din clasa 5 -->
    <ContClient>…</ContClient>  <!-- opțional -->
    <Explicatie>…</Explicatie>
    <FacturaID>…</FacturaID>        <!-- opțional -->
    <FacturaNumar>…</FacturaNumar>  <!-- opțional -->
    <CodFiscal>…</CodFiscal>        <!-- opțional -->
    <Moneda>…</Moneda>              <!-- opțional -->
  </Linie>
  <Linie>…</Linie>
</Incasari>
```

Sursă: manualul Saga („Import date") + exemple funcționale de pe forumul Saga.
Câte un `<Linie>` per rând din borderou. Valuta se determină din **folderul** în care se
află borderoul (`borderouri/ron` / `borderouri/eur` / `borderouri/huf`), nu din conținut.

## Reguli generale de fișier

| Regulă | Valoare |
|--------|---------|
| Nume fișier (eMAG) | **`I_<data>.xml`** — ex. `I_30.03.2026.xml`. Prefixul `I_` e obligatoriu, altfel Saga nu-l tratează ca import de încasări. |
| Data din numele fișierului | Propunere pentru automatizare: **`Payout date`** (unic per borderou, ex. `2026-04-17` → `I_17.04.2026.xml`), un fișier per borderou. |
| Encoding | UTF-8, cu declarația `<?xml version="1.0" encoding="UTF-8"?>` |
| Format dată | `dd.mm.yyyy` (ex. `30.03.2026`) |
| Separator zecimal | punct (`.`), 2 zecimale (ex. `60.90`) |
| Rădăcină | `<Incasari>` … `</Incasari>` |
| Nume fișier (Cargus) | **numele borderoului**, ex. `Cargus Packeta Iulie 2026.xml` — decizie internă, deși nota de mai sus susține că prefixul `I_` ar fi obligatoriu. Dacă importul e refuzat, asta e prima cauză de verificat. |

---

## Cargus / Packeta (folder `borderouri/ron` → cont 5125)

**Format-sursă activ**, procesat automat de skill-ul `incasari-cargus`
(`.claude/skills/incasari-cargus/scripts/proceseaza.py`).

Borderoul are **header pe două rânduri**; datele încep de la rândul 3.
Rândul 1 e o hartă parțială pusă de client, cu numele câmpurilor din schema veche
(`Den_partener`, `Nr_doc`); rândul 2 are numele reale ale coloanelor:

```
col C        col D          col G     col H       col K
Livrata      Destinatar     Suma      Data OP     RefExp1
```

| Tag XML         | Coloană xlsx     | Transformare                                                    | Exemplu (rândul 3 din `Cargus Packeta Iulie 2026.xlsx`) |
|-----------------|------------------|-----------------------------------------------------------------|------------------------------------------------------------|
| `Data`          | `Data OP` (H)    | deja `dd.mm.yyyy`; dacă celula e dată Excel → `dd.mm.yyyy`        | `30.07.2026`                                               |
| `Numar`         | `RefExp1` (K)    | ca atare, trim                                                   | `47312`                                                    |
| `Suma`          | `Suma` (G)       | **text cu virgulă românească** → punct, 2 zecimale; fără separator de mii | `268,89` → `268.89`                              |
| `Cont`          | — (fix)          | `5125`                                                           | `5125`                                                     |
| `ContClient`    | — (fix)          | `4111`                                                           | `4111`                                                     |
| `Explicatie`    | `Destinatar` (D) | `Incasare ramburs client - <Destinatar>`                         | `Incasare ramburs client - Narcis Fieraru`                 |
| `FacturaID`     | `RefExp1` (K)    | ca atare (același ca `Numar`)                                    | `47312`                                                    |
| `FacturaNumar`  | —                | gol                                                              | *(gol)*                                                    |
| `CodFiscal`     | —                | gol                                                              | *(gol)*                                                    |
| `Moneda`        | — (fix)          | `RON`                                                            | `RON`                                                      |

Coloanele `Awb` (A), `Data tur` (B), `Livrata` (C), `Numar` (F), `Numar OP` (I),
`Beneficiar plata` (J), `RefExp2` (L), `RefFact` (M) **nu intră în XML**. Ultimele cinci
sunt goale pe toate rândurile borderoului din iulie 2026.

**Un singur XML per borderou**, chiar dacă borderoul conține mai multe date de plată
(cel din iulie 2026 are 4: 10/16/23/30.07). Scriptul raportează subtotalul pe fiecare
`Data OP`, pentru reconciliere cu extrasul de cont.

Rezultat pentru borderoul din iulie 2026: `borderouri/ron/procesate/Cargus Packeta Iulie 2026.xml`
— 219 linii, total **26.569,26 RON**.

**EUR / HUF pentru acest format:** folderele există și sunt configurate
(cont `5126`, `Moneda` corespunzătoare), dar maparea nu a fost verificată pe un borderou
real în valută. Factorul de 100 de la HUF e documentat doar pentru eMAG.

---

## eMAG — traducerea mapării vechi (`<rand>`) în formatul nou (`<Linie>`)

Maparea a fost definită inițial pentru o structură `<rand>` care nu a mers la import.
Așa o refolosim în formatul corect:

| Câmp vechi (`<rand>`) | Sursă xlsx / valoare                     | Tag nou (`<Linie>`)        | Observație |
|-----------------------|------------------------------------------|----------------------------|------------|
| `DATA`                | `Order finalization date`                | `Data`                     | `yyyy-mm-dd hh:mm:ss` → `dd.mm.yyyy` |
| `NR_DOC`              | `Order ID`                               | `Numar` **și** `FacturaID` | același Order ID în ambele |
| `SUMA`                | `Fraction value`                         | `Suma`                     | punct zecimal, 2 zecimale; **HUF: împărțit la 100** |
| `CONT`                | 5125 RON / 5126 valută (după folder)     | `Cont`                     | neschimbat |
| `CONT_CORESP`         | 4111 fix                                 | `ContClient`               | neschimbat |
| `EXPLICATIE`          | „Incasare ramburs client"                | `Explicatie`               | + sufix ` - <Client name>` |
| `DEN_PARTENER`        | `Client name`                            | *(nu există tag)*          | absorbit în `Explicatie` |
| `COD_FISCAL`          | gol                                      | `CodFiscal`                | gol |
| `VALUTA`              | RON / EUR / HUF după folder              | `Moneda`                   | hardcodat per folder (și pentru RON) |
| `CURS`                | gol                                      | *(nu există tag)*          | dispare natural — Saga își ia cursul singur |
| `SUMA_VALUTA`         | = SUMA dacă valută, 0 dacă RON           | *(nu există tag)*          | absorbit în `Suma` + `Moneda`: `Suma` e mereu suma din borderou, în valuta folderului; `Moneda` spune ce valută e |
| —                     | —                                        | `FacturaNumar`             | gol (tag nou, fără corespondent) |

Concluzie: 8 câmpuri au corespondent 1:1, `DEN_PARTENER` intră în `Explicatie`, iar
`CURS` / `SUMA_VALUTA` nu mai au nevoie de reprezentare. **Singura logică per valută**
rămâne `Cont`, `Moneda` și factorul de 100 la HUF:

| Tag      | RON            | EUR            | HUF                        |
|----------|----------------|----------------|----------------------------|
| `Cont`   | `5125`         | `5126`         | `5126`                     |
| `Moneda` | `RON`          | `EUR`          | `HUF`                      |
| `Suma`   | Fraction value | Fraction value | Fraction value **/ 100**   |
| restul   | identic        | identic        | identic                    |

---

## eMAG — RON (folder RON → cont 5125)

| Tag XML         | Coloană xlsx               | Transformare                                             | Exemplu (rând 4 din `emag RO2 Aprilie 2026.xlsx`) |
|-----------------|----------------------------|----------------------------------------------------------|---------------------------------------------------|
| `Data`          | `Order finalization date`  | `yyyy-mm-dd hh:mm:ss` → `dd.mm.yyyy` (se ignoră ora)      | `2026-03-30 08:59:49` → `30.03.2026`              |
| `Numar`         | `Order ID`                 | ca atare                                                 | `482792410`                                       |
| `Suma`          | `Fraction value`           | număr cu punct zecimal, 2 zecimale                        | `60.9` → `60.90`                                  |
| `Cont`          | — (fix)                    | `5125`                                                   | `5125`                                            |
| `ContClient`    | — (fix)                    | `4111`                                                   | `4111`                                            |
| `Explicatie`    | `Client name`              | `Incasare ramburs client - <Client name>`                | `Incasare ramburs client - Madaras Melinda`       |
| `FacturaID`     | `Order ID`                 | ca atare (același ca `Numar`)                            | `482792410`                                       |
| `FacturaNumar`  | —                          | gol                                                      | *(gol)*                                           |
| `CodFiscal`     | —                          | gol (clienți persoane fizice)                            | *(gol)*                                           |
| `Moneda`        | — (fix)                    | `RON`                                                    | `RON`                                             |

Rezultat pentru rândul de mai sus: vezi `I_30.03.2026.xml`.

---

## eMAG — EUR (folder EUR → cont 5126)

Identic cu RON, cu excepția `Cont` și `Moneda`. `Suma` este suma din borderou (în EUR);
nu se convertește în lei — nu există tag de curs, Saga aplică cursul singur.

| Tag XML         | Coloană xlsx               | Transformare                                             | Exemplu (ipotetic)                                |
|-----------------|----------------------------|----------------------------------------------------------|---------------------------------------------------|
| `Data`          | `Order finalization date`  | `yyyy-mm-dd hh:mm:ss` → `dd.mm.yyyy`                      | `2026-03-30 08:59:49` → `30.03.2026`              |
| `Numar`         | `Order ID`                 | ca atare                                                 | `482792410`                                       |
| `Suma`          | `Fraction value`           | număr cu punct zecimal, 2 zecimale (în EUR)               | `12.5` → `12.50`                                  |
| `Cont`          | — (fix)                    | `5126`                                                   | `5126`                                            |
| `ContClient`    | — (fix)                    | `4111`                                                   | `4111`                                            |
| `Explicatie`    | `Client name`              | `Incasare ramburs client - <Client name>`                | `Incasare ramburs client - Nume Client`           |
| `FacturaID`     | `Order ID`                 | ca atare (același ca `Numar`)                            | `482792410`                                       |
| `FacturaNumar`  | —                          | gol                                                      | *(gol)*                                           |
| `CodFiscal`     | —                          | gol                                                      | *(gol)*                                           |
| `Moneda`        | — (fix)                    | `EUR`                                                    | `EUR`                                             |

XML de test EUR: se generează când primim un borderou EUR real.

---

## eMAG — HUF (folder HUF → cont 5126)

Identic cu RON, cu excepția `Cont`, `Moneda` și a sumei: **`Suma` = `Fraction value` / 100**
(confirmat; borderoul HUF are suma cu factor 100).

| Tag XML         | Coloană xlsx               | Transformare                                             | Exemplu (ipotetic)                                |
|-----------------|----------------------------|----------------------------------------------------------|---------------------------------------------------|
| `Data`          | `Order finalization date`  | `yyyy-mm-dd hh:mm:ss` → `dd.mm.yyyy`                      | `2026-03-30 08:59:49` → `30.03.2026`              |
| `Numar`         | `Order ID`                 | ca atare                                                 | `482792410`                                       |
| `Suma`          | `Fraction value`           | **împărțit la 100**, punct zecimal, 2 zecimale (în HUF)   | `1234500` → `12345.00`                            |
| `Cont`          | — (fix)                    | `5126`                                                   | `5126`                                            |
| `ContClient`    | — (fix)                    | `4111`                                                   | `4111`                                            |
| `Explicatie`    | `Client name`              | `Incasare ramburs client - <Client name>`                | `Incasare ramburs client - Nume Client`           |
| `FacturaID`     | `Order ID`                 | ca atare (același ca `Numar`)                            | `482792410`                                       |
| `FacturaNumar`  | —                          | gol                                                      | *(gol)*                                           |
| `CodFiscal`     | —                          | gol                                                      | *(gol)*                                           |
| `Moneda`        | — (fix)                    | `HUF`                                                    | `HUF`                                             |

XML de test HUF: se generează când primim un borderou HUF real.

---

## De confirmat la primul import

1. **Ce rânduri intră în XML** — borderoul RON conține și `Fraction type` = `Refund CO` /
   `Refund COD` (sume negative) și `Voucher`. Deocamdată maparea e definită pentru
   încasările propriu-zise (`CO Cashing`, `COD Cashing`); refund-urile și voucherele
   trebuie stabilite (încasare negativă? plată `P_<data>.xml`? se ignoră?).
2. **`Data`** — folosim `Order finalization date` (validat anterior). Alternativa ar fi
   `Payout date` (data în care eMAG a virat banii).
3. **Diacritice** în nume (ex. `Șușnea Adrian`) — de verificat că importul UTF-8 le
   afișează corect în Saga.
4. **`FacturaID`** — conform manualului Saga, leagă încasarea de o factură importată tot din
   XML cu același ID; dacă facturile nu sunt importate cu ID = Order ID, câmpul e probabil
   ignorat (nu ar trebui să blocheze importul).
5. **Valută: `Suma` în valută, fără curs** — presupunem că Saga, primind `Moneda` = EUR/HUF
   și cont 5126, tratează `Suma` ca sumă în valută și aplică cursul singur. De validat la
   primul import EUR/HUF.

### Specific Cargus / Packeta

6. **`Data` = `Data OP` sau `Livrata`?** Am ales `Data OP` (data virării banilor, se
   potrivește cu extrasul de cont). Harta pusă de client în rândul 1 al borderoului
   indica însă `Livrata` (data livrării coletului). De confirmat.
7. **Numele fișierului fără prefixul `I_`** — vezi nota din „Reguli generale de fișier".
8. **Două valori `RefExp1` atipice** în borderoul din iulie 2026: `9822` (4 cifre, AWB
   `COPK7442480`) și `26540717` (8 cifre, AWB `COPK7448616`), față de restul care sunt
   numere de 5 cifre în seria ~46900–47400. Probabil greșeli de introducere; de corectat
   la sursă. Scriptul le include în XML, dar le semnalează la fiecare rulare.
9. **Refund-uri / retururi** — borderoul din iulie 2026 nu are nicio sumă negativă, deci
   punctul 1 de mai sus nu se aplică deocamdată acestui format. De stabilit ce se
   întâmplă dacă apare unul.
