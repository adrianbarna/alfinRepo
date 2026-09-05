# Încasări Saga — borderouri Cargus / Packeta → XML

Plugin pentru Claude Code (inclusiv fila **Code** din aplicația Claude Desktop) care transformă **borderourile de ramburs**
Cargus / Packeta (`.xlsx`) în fișiere **XML de import pentru Saga**
(Import documente → Încasări) și leagă fiecare încasare de **factura ei**.

## Ce face

La fiecare rulare:

1. Se uită în folderul cu borderouri și ia **doar fișierele noi** — ține minte ce a
   procesat deja, deci poate fi rulat oricând fără să dubleze nimic.
2. Pentru fiecare rând, caută factura în exporturile XML de facturi din Saga. Cheia e
   numărul de expediție (`RefExp1` = `inf_suplm`); **numele și totalul confirmă**
   potrivirea. Numărul facturii (`nr_iesire`) intră în `<FacturaNumar>`, iar suma
   încasată e luată **de pe factură**, ca factura să se stingă exact.
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
adrianbarna/alfinRepo
```

Apăsați **Sync**. Dacă aveți deja instalată *Monitorizarea legislativă*, sursa e
aceeași — nu trebuie adăugată din nou.

**Verificați că actualizările automate sunt pornite** — nu vin pornite din oficiu.
Lângă eticheta `alfinRepo`, în meniul **···**, trebuie să fie activ comutatorul
**Sync automatically**.

**Pasul 2 — Activați plugin-ul.** După sincronizare apare cardul **Încasări Saga**.
Deschideți-l cu rotița din colț și activați-l.

**Pasul 3 — Conectați Gmail** (Settings → Connectors), ca raportul să poată fi trimis.

**Pasul 4 — Prima rulare.** Scrieți în conversație:

> Procesează borderourile de încasări

La prima rulare vi se cer trei lucruri, o singură dată:

| Ce vă întreabă | De ce |
|---|---|
| Folderul cu borderourile `.xlsx`, per valută | de acolo citește fișierele noi |
| Folderul cu exportul XML de facturi din Saga | de acolo ia numerele de factură |
| Adresa (sau adresele) de email pentru raport | acolo ajung rândurile de verificat |

Răspunsurile se salvează în `~/.claude/incasari-saga/config.json` și nu mai sunt cerute.

Structura așteptată — **valuta e dată de folder**, sursa nu are folder (Cargus și eMAG
stau împreună, formatul se recunoaște după coloane):

```
borderouri/ron/   .xlsx  +  procesate/        facturi/   exporturile XML din Saga
```

RON merge pe contul 5125, orice altă valută pe 5126. Momentan e configurat doar RON;
o valută nouă se adaugă spunând asistentului unde stau borderourile ei.

<details>
<summary>Instalare din terminal, pentru administratori</summary>

```
/plugin marketplace add adrianbarna/alfinRepo
/plugin install incasari-saga@alfin-consult
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
| Verificarea sau refacerea configurării | „Configurează încasările" |

## Cum găsește factura

1. **Cheia: `RefExp1` din borderou = `inf_suplm` din factură.** Pe borderoul de
   referință se potrivește pe toate cele 219 rânduri.
2. **Totalul confirmă**, cu toleranță: diferențele de un ban sunt rotunjiri normale și
   trec tăcut, până la 10 bani trec cu avertisment, peste — factura nu e considerată
   confirmată. (Pe un borderou real, doar 129 din 216 totaluri coincid exact.)
   **Suma care intră în XML e cea de pe factură**, ca factura să se stingă exact.
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
- rânduri incomplete în borderou, numere de expediție duplicate sau de lungime atipică;
- **exporturi de facturi care se contrazic** — aceeași factură cu alt total în două
  exporturi; câștigă exportul cu perioada mai târzie, iar diferența e semnalată;
- **un export de facturi lipsă** — raportul spune ce perioadă acoperă exporturile
  existente, în loc să înșire sute de rânduri nepotrivite.

## Pentru administrator

- **Ce citește:** `.xlsx` fără dependențe externe (doar `python3` din stdlib) și export
  XML de facturi din Saga (`<VFPData><c_xml>`, Windows-1252).
- **Ce scrie:** `<folder>/procesate/<nume borderou, cu spațiile înlocuite de _>.xml`, jurnalul `.procesate.json`
  (cheie = numele fișierului `.xlsx`) și `ultimul-raport.txt` — textul trimis pe email.
- **Configurația** stă în `~/.claude/incasari-saga/config.json`, în afara plugin-ului,
  ca să supraviețuiască actualizărilor. Poate fi mutată cu variabila `INCASARI_CONFIG`.
  Plugin-ul vine fără căi setate; prima configurare (și orice schimbare ulterioară) o
  face skill-ul `config-incasari-cargus`, conversațional.
- **Windows:** are nevoie de Python 3 instalat (python.org, cu „Add python.exe to PATH"
  bifat); asistentul îl apelează cu `py -3` și nu instalează nimic. Se folosește fila
  **Code** din Claude Desktop, nu Cowork (Cowork rulează comenzile într-o mașină
  virtuală Linux care pe Windows pornește greu și nu are acces la folderele locale în
  task-urile programate). Rularea săptămânală se face din **Routines → New routine →
  Local**, cu folderul de lucru ales și „Run now" la prima rulare, ca să se aprobe
  o dată comenzile.
- **Emailul nu e trimis de script.** Scriptul compune raportul; plugin-ul îl trimite cu
  conectorul Gmail, după confirmarea de la prima trimitere.
- **Valute:** RON → 5125, orice altă valută → 5126. Exportul de facturi nu are câmp de
  valută, dar nu e nevoie: `total` e exprimat în valuta facturii, iar factura găsită
  prin numărul de expediție e în aceeași valută ca borderoul, deci comparația e directă.
  Azi e activ doar RON.
- **Exporturile de facturi se acumulează** și pot acoperi perioade oricât de lungi;
  perioada se deduce din conținut, nu din numele fișierului.
- Logica completă: [skills/incasari-cargus/SKILL.md](skills/incasari-cargus/SKILL.md).
