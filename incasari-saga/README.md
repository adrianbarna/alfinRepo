# Încasări Saga — borderouri Cargus / Packeta → XML

Plugin pentru Claude (Cowork / Claude Code) care transformă **borderourile de ramburs**
Cargus / Packeta (`.xlsx`) în fișiere **XML de import pentru Saga**
(Import documente → Încasări) și leagă fiecare încasare de **factura ei**.

## Ce face

La fiecare rulare:

1. Se uită în folderul cu borderouri și ia **doar fișierele noi** — ține minte ce a
   procesat deja, deci poate fi rulat oricând fără să dubleze nimic.
2. Pentru fiecare rând, caută factura în exportul XML de facturi din Saga. Cheia e
   numărul de expediție (`RefExp1` = `inf_suplm`); **numele și totalul confirmă**
   potrivirea. Numărul facturii (`nr_iesire`) intră în `<FacturaNumar>`.
3. Scrie un XML per borderou, gata de importat.
4. Rândurile care **nu** pot fi legate sigur de o factură nu intră în XML — ajung
   într-un raport trimis pe email, cu motiv, sumă și numărul rândului din Excel.

Nimic nu se pierde în tăcere: raportul spune și cât însumează rândurile rămase pe
dinafară, ca totalul să poată fi verificat față de borderou.

## Instalare (o singură dată)

Nu aveți nevoie de git și nu aveți nevoie de terminal.

**Pasul 1 — Adăugați sursa plugin-ului.** În **Settings → Customize → Plugins**, fila
**Personal**, apăsați **+** și scrieți exact:

```
adrianbarna/contaLacramioara
```

Apăsați **Sync**. Dacă aveți deja instalată *Monitorizarea legislativă*, sursa e
aceeași — nu trebuie adăugată din nou.

**Verificați că actualizările automate sunt pornite** — nu vin pornite din oficiu.
Lângă eticheta `contaLacramioara`, în meniul **···**, trebuie să fie activ comutatorul
**Sync automatically**.

**Pasul 2 — Activați plugin-ul.** După sincronizare apare cardul **Încasări Saga**.
Deschideți-l cu rotița din colț și activați-l.

**Pasul 3 — Conectați Gmail** (Settings → Connectors), ca raportul să poată fi trimis.

**Pasul 4 — Prima rulare.** Scrieți în conversație:

> Procesează borderourile de încasări

La prima rulare vi se cer trei lucruri, o singură dată:

| Ce vă întreabă | De ce |
|---|---|
| Folderul cu borderourile `.xlsx` | de acolo citește fișierele noi |
| Folderul cu exportul XML de facturi din Saga | de acolo ia numerele de factură |
| Adresa (sau adresele) de email pentru raport | acolo ajung rândurile de verificat |

Răspunsurile se salvează în `~/.claude/incasari-saga/config.json` și nu mai sunt cerute.

<details>
<summary>Instalare din terminal, pentru administratori</summary>

```
/plugin marketplace add adrianbarna/contaLacramioara
/plugin install incasari-saga@lacramioara-conta
```

Dacă sumarul spune `Run /reload-plugins to activate.`, rulați și `/reload-plugins`.

</details>

## Comenzi utile după instalare

| Ce vreți | Ce scrieți |
|---|---|
| Procesarea borderourilor noi | „Procesează borderourile" |
| O verificare fără să scrie nimic | „Arată-mi ce ar face, fără să scrii fișierele" |
| Refacerea unui borderou corectat | „Reprocesează borderoul <nume>" |
| Schimbarea adresei de raport | „Trimite raportul de încasări pe <adresa>" |
| Alt folder de borderouri sau de facturi | „Borderourile sunt acum în <cale>" |

## Cum găsește factura

1. **Cheia: `RefExp1` din borderou = `inf_suplm` din factură.** Pe borderoul de
   referință se potrivește pe toate cele 219 rânduri.
2. **Totalul confirmă**, cu toleranță: diferențele de un ban sunt rotunjiri normale și
   trec tăcut, până la 10 bani trec cu avertisment, peste — factura nu e considerată
   confirmată. (Pe un borderou real, doar 129 din 216 totaluri coincid exact.)
3. **Numele e al doilea control**, fără diacritice, fără majuscule, fără să conteze
   ordinea sau forma juridică. Dacă diferă, rândul **intră** în XML cu un avertisment —
   e normal ca pe colet să fie persoana și pe factură firma.
4. **Rezervă:** dacă numărul de expediție nu duce la o factură confirmată de total, se
   caută după nume + total, iar rezultatul e semnalat ca de verificat.

Un rând e **sărit** când nu există nicio factură, când totalul nu confirmă niciuna, sau
când rămân mai multe la fel de plauzibile.

## Ce semnalează în raport

- rânduri fără factură sigură, cu motivul exact și cu totalul lor;
- factură găsită doar după nume;
- nume diferit față de factură;
- sumă diferită de totalul facturii cu mai mult de un ban;
- număr de expediție care are și **factură de storno** — banii au intrat, dar factura e
  anulată;
- rânduri incomplete în borderou, numere de expediție duplicate sau de lungime atipică.

## Pentru administrator

- **Ce citește:** `.xlsx` fără dependențe externe (doar `python3` din stdlib) și export
  XML de facturi din Saga (`<VFPData><c_xml>`, Windows-1252).
- **Ce scrie:** `<folder>/procesate/<nume borderou>.xml`, jurnalul `.procesate.json`
  (cheie = numele fișierului `.xlsx`) și `ultimul-raport.txt` — textul trimis pe email.
- **Configurația** stă în `~/.claude/incasari-saga/config.json`, în afara plugin-ului,
  ca să supraviețuiască actualizărilor. Poate fi mutată cu variabila `INCASARI_CONFIG`.
- **Emailul nu e trimis de script.** Scriptul compune raportul; plugin-ul îl trimite cu
  conectorul Gmail, după confirmarea de la prima trimitere.
- **Valute:** RON → cont 5125. Structura acceptă și alte valute (cont 5126), dar
  maparea nu a fost verificată pe un borderou real în valută.
- Logica completă: [skills/incasari-cargus/SKILL.md](skills/incasari-cargus/SKILL.md).
