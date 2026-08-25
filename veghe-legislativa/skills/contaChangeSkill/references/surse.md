# Sursele monitorizate și cum se accesează

Fiecare sursă are o metodă de acces verificată. Unele site-uri blochează accesul direct al agenților (răspund cu 403, 404 sau conexiune resetată) — pentru acelea folosește căutarea web cu operatorul `site:`, care aduce articolele indexate fără a lovi blocajul. Ultima verificare a accesului: **24.08.2026**.

Sursele sunt grupate pe trei niveluri, după rolul lor în raport. Parcurge-le în ordinea A → B → C: nivelul A îți spune ce urmează, B ce s-a publicat oficial, C ce înseamnă pentru un contabil.

---

## Nivel A — Ce urmează (avertizare timpurie)

Aici actele sunt **adoptate sau propuse, dar încă nepublicate în Monitorul Oficial** — deci **nu au număr**. Nu le trata ca acte noi obișnuite: intră în `acte_in_asteptare` din starea skill-ului și se raportează într-o secțiune separată (vezi `SKILL.md`, pașii 3–4).

### A1. Ședințele de Guvern — actele adoptate

- **URL**: https://gov.ro/ro/guvernul/sedinte-guvern — listează ședințele pe săptămâni, cu link către informația de presă a fiecăreia.
- **Metodă**: acces direct (WebFetch), funcționează.
- **Pagina cu actele**, tipar de URL stabil:
  `https://gov.ro/ro/guvernul/sedinte-guvern/informatie-de-presa-privind-actele-normative-adoptate-in-edinta-guvernului-romaniei-din-<zi>-<luna>-<an>`
  (ex. `...din-5-februarie-2026`). Atenție la diacriticele din slug: se scrie `in-edinta`, nu `in-sedinta`. Dacă tiparul dă 404, ia linkul din pagina de listare sau caută `site:gov.ro acte normative adoptate <data>`.
- **Ce oferă**: titlurile complete ale OUG-urilor și HG-urilor adoptate, grupate pe secțiuni (proiecte de lege, ordonanțe, hotărâri, memorandumuri) — cu **1–5 zile înainte** să apară în Monitorul Oficial.
- **Ce cauți**: acte cu impact fiscal/contabil/salarizare. Ignoră restul (infrastructură, imobile, numiri).

### A2. SGG — proiecte de acte normative

- **URL**: https://sgg.gov.ro/1/category/proiecte-de-acte-normative-care-ar-putea-fi-incluse-in-sedinta-guvernului-romaniei/
- **Metodă**: acces direct (WebFetch), funcționează.
- **Ce oferă**: proiectele *înainte* de ședința de Guvern — avertizarea cea mai timpurie posibilă.
- **Atenție**: pagina `sgg.gov.ro/1/transparenta-decizionala/` este doar informativă (descrie procedura), nu conține lista proiectelor. Folosește URL-ul de categorie de mai sus.

---

## Nivel B — Ce s-a publicat oficial

### B1. Monitorul Oficial (sursa primară)

- **URL**: https://monitoruloficial.ro — **pagina principală**, care listează „Cele mai recente acte publicate în Monitorul Oficial, Partea I". (Atenție: `/e-monitor/` e doar o pagină informativă, fără lista actelor.)
- **Metodă**: acces direct (WebFetch).
- **Ce cauți**: acte din Partea I cu impact contabil/fiscal — legi, OUG, HG, ordine ale Ministerului Finanțelor (OMF) și ANAF (OPANAF).
- **Atenție**: aici actele apar doar cu titlul; conținutul și contextul le găsești pe site-urile de specialitate sau prin căutare web după numărul actului.

### B2. Portalul legislativ (legislatie.just.ro)

- **URL**: https://legislatie.just.ro
- **Metodă**: acces direct (WebFetch), funcționează.
- **Ce oferă**: **textul oficial consolidat** al actelor — adică forma în vigoare, cu modificările încorporate. Sursa de adevăr când trebuie să spui *ce se schimbă concret față de forma veche*.
- **Cum ajungi la un act**: pagina principală are „Ultimele acte publicate în Monitorul Oficial", dar lista e adesea în urmă cu câteva săptămâni — nu te baza pe ea pentru detectare. Folosește-o **după** ce știi numărul actului: caută `site:legislatie.just.ro <tip act> <număr>/<an>` și deschide pagina de detaliu.
- **Când o folosești**: pentru actele importante din raport, unde formularea exactă contează (praguri, cote, termene). Nu e nevoie s-o consulți pentru fiecare act.

---

## Nivel C — Ce înseamnă pentru contabil (semnalare + interpretări)

### C1. avocatnet.ro (analize + forum)

- **Blochează accesul direct (403).** Nu încerca WebFetch pe site.
- **Metodă**: căutare web, ex.: `site:avocatnet.ro sinteză legislativă <perioada>` sau `site:avocatnet.ro <numărul actului>`.
- **Truc valoros**: avocatnet.ro publică săptămânal o **„Sinteză legislativă — cele mai importante acte normative publicate în perioada X–Y"** — caut-o întâi, e practic munca de colectare gata făcută; extrage actele din rezumatul rezultatului căutării.
- **Ce oferă**: articole de analiză bine documentate + forum activ de practicieni — sursă excelentă și pentru pasul de interpretări.

### C2. ANAF – noutăți legislative

- **Site JS-heavy / blochează agenții.** Nu te baza pe WebFetch pe anaf.ro sau static.anaf.ro.
- **Metodă**: căutare web, ex.: `site:anaf.ro noutăți legislative <luna> <anul>` sau `OPANAF <anul> ordin nou`.
- **Ce oferă**: ordine ANAF, proceduri, calendarul obligațiilor fiscale.
- **Alternativă mai bună**: proiectele ANAF puse în transparență decizională apar de regulă pe legestart.ro (C4) și ceccar.ro (C6), care sunt accesibile direct.

### C3. contzilla.ro

- **URL**: https://www.contzilla.ro/feed/ — **folosește feed-ul RSS**, nu pagina principală. Feed valid, cu articole din aceeași zi și `pubDate` curat pentru fiecare intrare, deci filtrarea pe perioadă e exactă.
- **Metodă**: acces direct (WebFetch) pe feed. Homepage-ul funcționează și el, dar datele sunt mai greu de extras.
- **Ce oferă**: articole zilnice despre fiscalitate, TVA, salarizare, pensii. Semnalează rapid actele noi cu impact practic.

### C4. legestart.ro (Indaco)

- **URL**: https://legestart.ro
- **Metodă**: acces direct (WebFetch), funcționează. **Nu are RSS** (`/feed` și `/rss` dau 404) — citește pagina principală.
- **Ce oferă**: știri legislative gratuite, pe categorii (Legislație, Muncă, Financiar și Bancar). Prinde bine **proiectele în transparență decizională** (ANAF, MF) — deci semnalează modificări înainte de publicare.
- **Atenție**: o parte din conținut e premium (module Indaco); știrile de pe prima pagină sunt gratuite.

### C5. CECCAR Business Magazine

- **URL**: https://www.ceccarbusinessmagazine.ro
- **Metodă**: acces direct (WebFetch), funcționează. **Nu are RSS** (`/rss` dă 404).
- **Ce oferă**: revista corpului profesional al contabililor, apare bilunar. Semnalează exact tipul de act care ne interesează — ordine ANAF, formulare modificate, proceduri MF — explicate pentru contabili. Titlurile sunt de regulă auto-explicative („ANAF a modificat formularul 216...").

### C6. ceccar.ro

- **URL**: https://ceccar.ro/ro/
- **Metodă**: acces direct (WebFetch), funcționează.
- **Ce oferă**: secțiunea „Știri" cu comunicate zilnice despre acte MF/ANAF (inclusiv proiecte în consultare) și arhivă cu filtrare pe luni. Perspectiva oficială a profesiei — util și pentru obligațiile profesionale ale contabilului (termene CECCAR, cotizații, formare).

### C7. contabilul.ro

- **URL**: http://contabilul.manager.ro/ — atenție, `www.contabilul.ro` redirecționează aici (301); folosește direct URL-ul final.
- **Metodă**: acces direct (WebFetch), gratuit.
- **Ce oferă**: articole practice (monografii, termene de declarații, spețe), publicate zilnic.

---

## Căutare de plasă de siguranță

Pe lângă sursele de mai sus, fă la final o căutare web generală de tip:
`modificări legislație contabilitate fiscalitate România <săptămâna/perioada>` —
prinde acte semnalate de alte publicații (profit.ro, economica.net, startupcafe.ro etc.) pe care sursele standard le-ar fi putut rata.

## Surse suplimentare ale clientului

Dacă `state.json` conține `surse_extra` (listă de URL-uri), consultă-le la fiecare rulare cu WebFetch, iar dacă dau eroare, încearcă `site:<domeniu>` prin căutare web. Sari peste sursele listate în `surse_dezactivate`.

---

## Surse verificate ca inaccesibile — nu le reîncerca

Testate la 24.08.2026. Nu irosi apeluri pe ele la fiecare rulare; dacă ai nevoie de conținutul lor, treci direct la căutare web cu `site:<domeniu>`.

| Sursă | URL testat | Rezultat |
|---|---|---|
| Ministerul Finanțelor | `mfinante.gov.ro` (rădăcină și `/transparenta-decizionala`) | conexiune resetată (ECONNRESET) |
| ANAF – noutăți legislative | `static.anaf.ro/static/10/Anaf/legislatie/Noutati_legislative.htm` | 404 |
| PwC România – tax alerts | `pwc.ro/en/tax-legal-alerts.html` | 403 |
| Portal Contabilitate (Rentrop & Straton) | `portalcontabilitate.ro` | 403 |
| Ministerul Muncii | `mmuncii.ro` → `old.mmuncii.gov.ro` | 301, apoi 403 |
| Camera Deputaților – proiecte | `cdep.ro/pls/proiecte/upl_pck.home` și `upl_pck2015.home` | 404 |
| SGG – transparență decizională | `sgg.gov.ro/1/transparenta-decizionala/` | răspunde, dar e pagină informativă fără listă de proiecte — folosește URL-ul de categorie de la A2 |
| Curierul Fiscal | `curierulfiscal.ro` | răspunde, dar ultimul conținut relevant e din dec. 2025 — abandonat, fără valoare |

**Feed-uri RSS inexistente** (nu le mai căuta): `legestart.ro/feed`, `legestart.ro/rss`, `ceccarbusinessmagazine.ro/rss` — toate 404. Singurul RSS funcțional dintre sursele noastre este `contzilla.ro/feed/`.
