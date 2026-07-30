# Sursele monitorizate și cum se accesează

Fiecare sursă are o metodă de acces verificată. Unele site-uri blochează accesul direct al agenților (răspund cu 403 sau pagini goale) — pentru acelea folosește căutarea web cu operatorul `site:`, care aduce articolele indexate fără a lovi blocajul.

## 1. Monitorul Oficial (sursa primară)

- **URL**: https://monitoruloficial.ro — **pagina principală**, care listează „Cele mai recente acte publicate în Monitorul Oficial, Partea I". (Atenție: `/e-monitor/` e doar o pagină informativă, fără lista actelor.)
- **Metodă**: acces direct (WebFetch).
- **Ce cauți**: acte din Partea I cu impact contabil/fiscal — legi, OUG, HG, ordine ale Ministerului Finanțelor (OMF) și ANAF (OPANAF).
- **Atenție**: aici actele apar doar cu titlul; conținutul și contextul le găsești pe site-urile de specialitate sau prin căutare web după numărul actului.

## 2. avocatnet.ro (analize + forum)

- **Blochează accesul direct (403).** Nu încerca WebFetch pe site.
- **Metodă**: căutare web, ex.: `site:avocatnet.ro sinteză legislativă <perioada>` sau `site:avocatnet.ro <numărul actului>`.
- **Truc valoros**: avocatnet.ro publică săptămânal o **„Sinteză legislativă — cele mai importante acte normative publicate în perioada X–Y"** — caut-o întâi, e practic munca de colectare gata făcută; extrage actele din rezumatul rezultatului căutării.
- **Ce oferă**: articole de analiză bine documentate + forum activ de practicieni — sursă excelentă și pentru pasul de interpretări.

## 3. ANAF – noutăți legislative

- **Site JS-heavy / blochează agenții.** Nu te baza pe WebFetch pe anaf.ro sau static.anaf.ro.
- **Metodă**: căutare web, ex.: `site:anaf.ro noutăți legislative <luna> <anul>` sau `OPANAF <anul> ordin nou`.
- **Ce oferă**: ordine ANAF, proceduri, calendarul obligațiilor fiscale.

## 4. contzilla.ro

- **URL**: https://www.contzilla.ro — acces direct funcționează (WebFetch).
- **Ce oferă**: articole zilnice despre fiscalitate, TVA, salarizare, cu datele publicării vizibile pe prima pagină. Semnalează rapid actele noi cu impact practic.

## 5. contabilul.ro

- **URL**: http://contabilul.manager.ro/ — atenție, `www.contabilul.ro` redirecționează aici (301); folosește direct URL-ul final.
- **Metodă**: acces direct (WebFetch), gratuit.
- **Ce oferă**: articole practice (monografii, termene de declarații, spețe), publicate zilnic.

## Căutare de plasă de siguranță

Pe lângă sursele de mai sus, fă la final o căutare web generală de tip:
`modificări legislație contabilitate fiscalitate România <săptămâna/perioada>` —
prinde acte semnalate de alte publicații (profit.ro, economica.net, startupcafe.ro etc.) pe care sursele standard le-ar fi putut rata.

## Surse suplimentare ale clientului

Dacă `state.json` conține `surse_extra` (listă de URL-uri), consultă-le la fiecare rulare cu WebFetch, iar dacă dau eroare, încearcă `site:<domeniu>` prin căutare web. Sari peste sursele listate în `surse_dezactivate`.
