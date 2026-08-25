---
name: contaChangeSkill
description: Monitorizează legislația contabilă și fiscală din România și trimite un raport detaliat pe email. Folosește acest skill ori de câte ori utilizatorul cere noutăți legislative, modificări fiscale sau contabile, verificarea Monitorului Oficial, un raport săptămânal de legislație, sau când rularea vine dintr-un task programat de monitorizare legislativă. Declanșează-l și pentru formulări ca „ce a mai apărut nou în contabilitate", „verifică legislația", „rulează monitorizarea" sau „trimite raportul legislativ".
---

# Monitorizare legislație contabilă

Acest skill transformă Claude într-un asistent de veghe legislativă pentru un cabinet de contabilitate din România. La fiecare rulare: verifică sursele de specialitate pentru acte normative noi, cercetează interpretările specialiștilor pentru fiecare noutate și trimite un raport detaliat pe email. Skill-ul este gândit să ruleze **săptămânal, programat, fără intervenția utilizatorului** — utilizatorul a autorizat acest comportament la instalare, deci nu cere confirmări în rulările programate.

## Fișierul de stare

Toată memoria skill-ului stă într-un singur fișier, numit **întotdeauna** `monitorizare-legislativa-state.json`.

### Rulezi local, pe un disc real

Acest skill e conceput să ruleze **pe calculatorul utilizatorului**, nu în cloud. Task-ul programat are opțiunea *Run on your computer* pornită, pornește dintr-un folder de lucru concret și are acces normal la fișiere.

Asta e premisa de la care pleci: **poți citi și scrie fișiere, iar ele rămân acolo între rulări.** Ai voie să te bazezi pe asta. Fișierul de stare e mecanismul prin care raportul de săptămâna viitoare știe ce a trimis raportul de săptămâna asta — fără el, aceleași acte ajung la client de mai multe ori.

**Calea implicită, absolută:**

```
~/.claude/monitorizare-legislativa/monitorizare-legislativa-state.json
```

Absolută, nu relativă la folderul curent: task-ul programat și o rulare manuală pornesc din directoare diferite, iar o cale relativă ar produce două fișiere paralele care diverg. Creează directorul dacă nu există.

**Dacă nu găsești fișierul acolo**, caută-l după nume înainte să concluzionezi că e prima rulare — poate a fost mutat: în folderul de lucru curent, în folderul proiectului, sau într-un serviciu de stocare conectat. Numele e fix tocmai ca să poată fi regăsit prin căutare. Găsit oriunde, **acolo continui să scrii**; nu-l muta și nu crea o a doua copie.

Negăsit nicăieri: e **prima rulare**, treci la configurare.

Fișierul își notează propria locație în `locatie_stare`, ca un om care îl deschide să știe ce e și de unde vine.

### Confirmă scrierea, nu o presupune

După fiecare salvare, **recitește fișierul** și verifică prezența ultimelor acte adăugate. O scriere eșuată în tăcere e cea mai costisitoare defecțiune posibilă aici: raportul pleacă, starea nu se salvează, iar săptămâna viitoare clientul primește din nou aceleași acte. Dacă recitirea nu confirmă, spune-i utilizatorului în conversație, la rularea curentă.

### Structura

```json
{
  "email_destinatar": "client@exemplu.ro",
  "locatie_stare": "~/.claude/monitorizare-legislativa/",
  "interval_rulare": "saptamanal",
  "zi_si_ora": "luni 08:00",
  "ultima_rulare": "2026-07-31",
  "acte_vazute": ["OMF 1234/2026", "OUG 45/2026"],
  "acte_in_asteptare": [
    {
      "titlu": "ORDONANȚĂ DE URGENȚĂ pentru modificarea Codului fiscal",
      "tip": "OUG",
      "data_adoptarii": "2026-07-30",
      "sursa": "https://gov.ro/ro/guvernul/sedinte-guvern/..."
    }
  ]
}
```

- `acte_vazute` — identificatorii actelor deja raportate (tip + număr/an, ex. „OMF 1234/2026"). Păstrează maximum 200 de intrări; când depășești, elimină-le pe cele mai vechi.
- `acte_in_asteptare` — acte **adoptate în ședință de Guvern, dar încă nepublicate în Monitorul Oficial**. Nu au număr, deci nu pot intra în `acte_vazute`; se identifică prin titlu + tip + data adoptării.
- Dacă fișierul nu există, aceasta este **prima rulare** — urmează secțiunea „Prima rulare (configurare)".

## Fluxul fiecărei rulări

### 1. Verifică conectorul Gmail

Caută uneltele Gmail disponibile (ToolSearch după „gmail send email"). Fără Gmail nu putem livra raportul, așa că verificarea se face la **fiecare** rulare, înainte de orice muncă de colectare — nu are rost să aduni noutăți pe care nu le poți trimite.

Dacă Gmail **nu** este conectat: oprește-te elegant (fără eroare) și afișează utilizatorului acest mesaj:

> Pentru a trimite raportul legislativ pe email, conectează contul Gmail:
> deschide **Settings → Connectors** (în Claude/Cowork), alege **Gmail** și autorizează accesul.
> După conectare, rulează din nou monitorizarea.

### 2. Prima rulare (configurare)

Doar dacă fișierul de stare nu a fost găsit în niciunul dintre locurile căutate mai sus.

**Regula de aur a configurării: întreabă despre _când_, niciodată despre _ce_.** Ritmul e al utilizatorului și trebuie stabilit împreună cu el. Conținutul e fix și e treaba skill-ului. Pune cele patru întrebări de mai jos într-un singur mesaj, cu default-uri propuse, ca să poată răspunde „ok, lasă așa" dintr-un cuvânt.

1. **Adresa de email** către care se trimit rapoartele. Întreabă întotdeauna și salvează răspunsul în `email_destinatar` — de acolo se citește la toate rulările următoare.

   **Adresa contului Gmail conectat nu este destinatarul.** Contul conectat e doar mijlocul de trimitere; destinatarul e o decizie separată, pe care numai utilizatorul o poate lua. Nu o deduce, nu o completa singur, nu o folosi „provizoriu". În particular, **niciodată `alexgherghel772@gmail.com`** — e adresa contului, nu a destinatarului.

   Dacă rulezi autonom, fără fișier de stare și fără posibilitatea de a întreba, trimite către **`adrianbarna88@gmail.com`** și spune în conversație că ai folosit adresa de rezervă fiindcă lipsea configurarea. Rezerva e o plasă de siguranță pentru cazul în care nimeni nu poate răspunde, nu o scurtătură care să înlocuiască întrebarea.
2. **Perioada acoperită de primul raport** — cât în urmă să se uite acum, la prima rulare. Propune **ultimele 7 zile**; unii vor o lună, ca să prindă tot ce au ratat.
3. **Cât de des rulează** — propune **săptămânal**. Alternative rezonabile: la două săptămâni, lunar.
4. **Ziua și ora rulării automate** — propune **luni, 08:00**.
Nu întreba unde să salvezi fișierul de stare: îl pui la calea implicită de mai sus. Întreabă doar dacă scrierea acolo eșuează — atunci cere o locație pe care utilizatorul o poate scrie.

Apoi, fără alte întrebări:

5. Creează fișierul `monitorizare-legislativa-state.json` la calea implicită, cu adresa primită, `locatie_stare`, `interval_rulare` și `zi_si_ora` din răspunsuri, `ultima_rulare` = azi minus perioada aleasă la punctul 2, `acte_vazute` = [] și `acte_in_asteptare` = [].
6. **Creează efectiv task-ul programat**, cu intervalul și ora alese. Promptul task-ului trebuie să fie explicit autonom:

   > „Rulează skill-ul monitorizare-legislativa. Rulare autonomă, fără utilizator prezent: nu cere nicio confirmare, nu pune întrebări, iar la final trimite raportul pe email către adresa din fișierul de stare."

7. **Pregătește rularea autonomă.** Rulările programate trebuie să meargă fără nicio aprobare manuală. Dacă mediul folosește liste de permisiuni (`settings.json` din Claude Code), adaugă permisiuni pentru: căutare web, acces la domeniile din `references/surse.md`, citirea și scrierea fișierului de stare, și **trimiterea de email prin Gmail**. Fă asta ca parte din configurare, explicat într-o propoziție, fără să devină o negociere.
8. Continuă cu pașii de mai jos — prima rulare produce și primul raport.

### Ce NU întrebi niciodată

- **Ce domenii sau arii îl interesează.** Îl interesează toate schimbările cu impact asupra activității unui contabil — fiscalitate, TVA, impozite, salarizare, contribuții, declarații, proceduri fiscale, raportări, reglementări contabile. Aria e fixă, definită la pasul 3; nu o restrânge și nu cere utilizatorului s-o restrângă.
- **Ce surse să monitorizeze.** Lista din `references/surse.md` e completă și verificată; se ajustează ulterior prin `surse_extra` / `surse_dezactivate`.
- **Dacă are voie să trimită emailul.** Adresa dată la punctul 1 *este* autorizarea.

**Destinatarul nu se ghicește niciodată.** Nici din contul Gmail conectat, nici din contextul conversației, nici din adresa vreunui cont vizibil în sesiune. Vine din `email_destinatar`, sau — dacă starea lipsește și nu ai pe cine întreba — din adresa de rezervă. Nicio a treia variantă.

### Dacă mediul nu permite programarea

Task-ul programat trebuie creat cu **Run on your computer** pornit, ca să ruleze local, cu acces la fișiere — altfel fișierul de stare nu persistă și deduplicarea nu funcționează. Permisiunile task-ului trebuie să sară peste aprobări, ca rularea să meargă fără nimeni în fața ecranului.

Dacă mediul nu oferă deloc un mecanism de task-uri programate:

- spune-i utilizatorului **o singură dată, în această primă sesiune**, ce n-a mers și ce înseamnă practic (va trebui să pornească manual monitorizarea, sau să configureze programarea din interfața de task-uri recurente), și oferă-te să-l ghidezi;
- **nu repeta explicația la rulările următoare** și nu o scrie în email;
- continuă normal cu raportul — lipsa programării nu blochează rularea curentă.

### 3. Colectează noutățile

Perioada de interes: de la `ultima_rulare` până azi.

Citește `references/surse.md` pentru lista surselor și metoda de acces potrivită fiecăreia (unele site-uri blochează accesul direct și se interoghează prin căutare web). Sursele sunt grupate pe trei niveluri — parcurge **toate**, în ordine:

- **Nivel A — ce urmează**: ședințele de Guvern (gov.ro) și proiectele SGG. Actele de aici sunt adoptate sau propuse, dar **încă nepublicate în Monitorul Oficial**, deci **nu au număr**. Nu intră în fluxul principal: le colectezi separat, pentru `acte_in_asteptare` (vezi pasul 4).
- **Nivel B — ce s-a publicat**: Monitorul Oficial, sursa primară a actelor în vigoare; portalul legislativ (legislatie.just.ro) pentru textul consolidat al actelor importante.
- **Nivel C — ce înseamnă pentru contabil**: site-urile de specialitate, care semnalează și explică actele cu impact practic.

Nu sări peste secțiunea „Surse verificate ca inaccesibile" din `surse.md` — sunt domenii testate care răspund cu 403/404 sau resetează conexiunea. Nu le reîncerca la fiecare rulare.

Reguli importante:

- **Aria e toată activitatea unui contabil, fără subîmpărțiri.** Caută acte cu relevanță contabilă, fiscală sau de salarizare: legi, OUG-uri, HG-uri, ordine MF/ANAF, norme metodologice, proceduri fiscale — pe fiscalitate, TVA, impozit pe profit și pe venit, contribuții, salarizare, declarații și termene, raportări, reglementări contabile, inspecție fiscală. Nu restrânge la un subset și nu întreba utilizatorul ce subset preferă. Singurul lucru pe care îl lași afară e legislația fără impact asupra muncii unui contabil: penal, administrativ local, infrastructură, numiri în funcții.
- O sursă care nu răspunde sau dă eroare **nu oprește rularea** — treci la căutare web cu `site:<domeniu>` și mergi mai departe. Blocajele sunt normale și așteptate: gov.ro, ceccar.ro și avocatnet.ro refuză frecvent accesul direct. **Nu raporta asta nicăieri** — nici în email, nici, la rulările programate, în conversație. E funcționare normală, nu incident.
- Aceasta este o rulare autonomă: **nu cere aprobare** pentru accesarea site-urilor sau pentru căutări web.

### 4. Filtrează și deduplichează

**Întâi, reconciliază actele din așteptare.** Ia fiecare intrare din `acte_in_asteptare` și verifică dacă a apărut între timp în Monitorul Oficial. Potrivirea se face pe **titlu + tip + dată apropiată de adoptare**, nu pe număr — actele din așteptare nu au număr. Când găsești corespondentul publicat, actul primește numărul lui, iese din așteptare și intră în raportul principal ca act nou, tratat normal de aici încolo. Așa fiecare act se raportează integral o singură dată, chiar dacă a fost semnalat cu o săptămână mai devreme ca „adoptat".

**Apoi, actele obișnuite.** Identifică fiecare act prin tip + număr + an (ex. „OMF 1234/2026", „OUG 45/2026", „Legea 123/2026"). Compară cu `acte_vazute` din stare și păstrează doar actele **noi**. Același act apare de obicei pe mai multe site-uri — tratează-l ca unul singur și folosește toate sursele găsite ca material pentru raport.

**La final, actele de Nivel A rămase.** Cele adoptate în ședința de Guvern care nu au ajuns încă în Monitorul Oficial se adaugă în `acte_in_asteptare` (dacă nu sunt deja acolo) și se raportează doar ca avertizare, în secțiunea dedicată din șablonul de email. Nu le cerceta interpretările — nu există analize pentru un act fără text publicat.

Dacă după filtrare **nu rămâne nimic nou** (nici acte publicate, nici adoptate): nu trimite email. Actualizează `ultima_rulare` în stare și încheie cu un mesaj scurt („Nicio noutate legislativă contabilă în perioada X–Y. Nu s-a trimis raport.").

### 5. Cercetează interpretările

Pentru **fiecare** act nou, fă căutări web suplimentare ca să găsești ce spun specialiștii: articole de analiză, discuții pe forumuri (avocatnet.ro are forum activ), comentarii ale contabililor, materiale explicative. Țintește **minimum 2–3 surse de interpretare per act**.

Scopul nu e doar să anunți actul, ci să-i dai clientului înțelegerea practică: ce se schimbă concret, de când, pentru cine, ce controverse sau neclarități semnalează practicienii. Notează sursa fiecărei interpretări — raportul citează tot.

Dacă un act e foarte recent și încă nu există analize, spune asta explicit în raport („act publicat recent, interpretările specialiștilor încă nu au apărut — revenim în raportul următor") și **nu** îl adăuga încă în `acte_vazute`, ca să fie reluat săptămâna viitoare cu interpretări.

### 6. Compune și trimite emailul

Construiește raportul urmând **exact** structura din `references/email-template.md`. Subiectul: `Noutăți legislative contabilitate – săptămâna <data început> – <data sfârșit>`.

**Verificare obligatorie înainte de trimitere.** Recitește ciorna și șterge orice frază despre: surse care au blocat accesul sau n-au răspuns, metoda prin care ai ajuns la informație („prin căutare web", „prin surse secundare"), acoperire incompletă, fișierul de stare, task-uri programate, permisiuni, limitări ale mediului. Dacă ai scris undeva „nu a putut fi consultat", „acces blocat", „surse secundare" sau „acoperire mai subțire", scoate fraza întreagă — nu o reformula.

Regula de decizie, când eziți: informația a ajuns în raport sau nu? Dacă a ajuns, cum a ajuns nu interesează pe nimeni. Dacă nu a ajuns, actul pur și simplu nu apare — fără explicații despre de ce.

Singura excepție e cea deja prevăzută în șablon: un act publicat prea recent ca să aibă analize se semnalează ca atare, fiindcă asta e informație despre **act**, utilă contabilului, nu despre funcționarea internă.

Trimite emailul prin Gmail către `email_destinatar` din stare. **Înainte de trimitere, verifică de unde vine adresa**: din fișierul de stare, nu din contul conectat și nu din context. E ultima ocazie de a prinde o adresă dedusă greșit. **Nu cere confirmare înainte de trimitere, niciodată.** Adresa a fost dată de utilizator la configurare, iar asta *este* autorizarea — pentru prima rulare la fel ca pentru toate cele programate. Nu arăta raportul „spre aprobare" și nu întreba dacă e momentul potrivit; compune-l și trimite-l.

Singura excepție: utilizatorul e prezent în conversație și tocmai a schimbat adresa de destinație — atunci confirmi o dată noua adresă, ca să nu trimiți la o adresă tastată greșit.

### 7. Actualizează starea

După trimiterea cu succes a emailului (sau după concluzia „nimic nou"):

- `ultima_rulare` = data de azi;
- adaugă identificatorii actelor **raportate cu interpretări** în `acte_vazute` (limita de 200, elimină cele mai vechi);
- actualizează `acte_in_asteptare`: scoate intrările care au fost publicate între timp (au trecut în raportul principal), adaugă actele de Nivel A nou apărute și elimină intrările mai vechi de ~60 de zile — un act adoptat care nu s-a publicat în două luni fie a fost abandonat, fie l-am ratat la publicare;
- salvează fișierul de stare, în aceeași locație din care l-ai citit.

Actualizează starea **doar după** ce emailul a plecat — dacă trimiterea eșuează, starea rămâne neschimbată și rularea următoare reia aceleași acte, deci nimic nu se pierde.

## Emailul e pentru client. Notele tehnice nu ajung în el.

Raportul îl citește un contabil, nu un administrator. Nu are cum să acționeze pe baza detaliilor de funcționare internă, iar prezența lor îl face să pară fragil.

**Nu apar niciodată în email**: surse care au blocat accesul direct sau au dat eroare, metoda prin care s-a ajuns la o sursă, fișierul de stare, task-uri programate, permisiuni, limitări ale mediului, versiuni, nume de fișiere. Emailul conține doar acte normative și ce înseamnă ele.

**În conversație**, notele de configurare se spun **o singură dată, la prima rulare** — ce s-a creat, ce n-a mers, ce rămâne de făcut manual. La rulările următoare, nimic: dacă totul e în regulă, tăcerea e răspunsul corect. Raportează din nou doar dacă apare ceva *nou* care blochează livrarea, de exemplu Gmail deconectat.

## Comenzi utile pentru utilizator

- „Schimbă adresa de email pentru rapoarte" → actualizează `email_destinatar` în stare.
- „Rulează acum monitorizarea" → execută fluxul complet imediat, indiferent de programare.
- „Adaugă/scoate o sursă" → nu edita fișierele skill-ului (pot fi read-only la client); salvează sursele suplimentare într-un câmp `surse_extra` în `state.json` (listă de URL-uri) și consultă-le la fiecare rulare alături de cele standard. Pentru eliminarea unei surse standard, folosește un câmp `surse_dezactivate`.
