---
name: monitorizare-stiri-conta
description: Monitorizează legislația contabilă și fiscală din România și trimite un raport detaliat pe email. Folosește acest skill ori de câte ori utilizatorul cere noutăți legislative, modificări fiscale sau contabile, verificarea Monitorului Oficial, un raport săptămânal de legislație, sau când rularea vine dintr-un task programat de monitorizare legislativă. Declanșează-l și pentru formulări ca „ce a mai apărut nou în contabilitate", „verifică legislația", „rulează monitorizarea" sau „trimite raportul legislativ". Pentru configurarea inițială există skill-ul separat initial-config-monitorizare-stiri-conta.
---

# Monitorizare legislație contabilă

Acest skill transformă Claude într-un asistent de veghe legislativă pentru un cabinet de contabilitate din România. La fiecare rulare: verifică sursele de specialitate pentru acte normative noi, cercetează interpretările specialiștilor pentru fiecare noutate și trimite un raport detaliat pe email. Skill-ul este gândit să ruleze **săptămânal, programat, fără intervenția utilizatorului** — utilizatorul a autorizat acest comportament la configurare, deci nu cere confirmări în rulările programate.

**Acest skill doar rulează monitorizarea.** Configurarea inițială — folderul pentru fișierul de stare, adresa destinatarului, ritmul, fișa pentru task-ul programat — e treaba skill-ului pereche **`initial-config-monitorizare-stiri-conta`**. Nu configura nimic aici.

## Fișierul de stare

Toată memoria skill-ului stă într-un singur fișier, numit **întotdeauna** `monitorizare-legislativa-state.json`.

### Fișierul stă pe calculatorul utilizatorului, într-un folder conectat

Sesiunea rulează în cloud, dar fișierul de stare **nu** stă în cloud — sandbox-ul se pierde între rulări. Stă **pe calculatorul utilizatorului**, într-un folder pe care el l-a conectat în aplicația Claude (Cowork). Ajungi la el prin puntea către dispozitiv: uneltele `mcp__remote-devices__*` (`get_device_info`, `device_list_dir`, `device_bash`, `device_stage_files`, `device_commit_files`).

Asta e premisa de la care pleci: **poți citi și scrie fișiere în folderul conectat, iar ele rămân acolo între rulări.** Fișierul de stare e mecanismul prin care raportul de săptămâna viitoare știe ce a trimis raportul de săptămâna asta — fără el, aceleași acte ajung la destinatar de mai multe ori.

**Calea nu e fixă și nu e implicită.** Folderul diferă de la un utilizator la altul; a fost stabilit o singură dată, la configurare, și se **refolosește mereu**, din două locuri:

1. din **promptul task-ului programat**, care conține calea absolută a fișierului;
2. din **fișierul însuși**, care își notează locația în `locatie_stare` (calea absolută de pe calculatorul utilizatorului, ex. `/Users/adrian/Documents/alfin/conta/`).

Un folder conectat `/Users/adrian/Documents/alfin/conta` apare în `device_bash` la `$HOME/mnt/conta/` (ultimul segment al căii devine numele montării). Deci fișierul se citește/scrie cu `device_bash` la `$HOME/mnt/<nume-folder>/monitorizare-legislativa-state.json`, iar în `locatie_stare` e notată **calea reală de pe calculator**, nu cea de montare.

**Cum găsești fișierul la fiecare rulare**, în ordinea asta:

1. Dacă promptul rulării indică o cale, folosește-o.
2. Altfel, cheamă `get_device_info` și, pentru fiecare folder din `connectedFolders`, caută după nume: `device_bash` cu `find "$HOME/mnt" -maxdepth 3 -name monitorizare-legislativa-state.json`. Numele e fix tocmai ca să poată fi regăsit prin căutare.
3. Găsit oriunde, **acolo continui să scrii**; nu-l muta și nu crea o a doua copie.

Dacă `connectedFolders` e gol, nu e lipsă de configurare — e **lipsă de acces**. Nu crea fișierul în cloud și nu ghici calea. Într-o rulare programată, oprește-te și raportează că task-ul nu are folderul conectat (de regulă task-ul a fost creat fără *Require this computer*). Într-o rulare cu utilizatorul prezent, roagă-l să conecteze folderul (butonul de folder din panoul Context sau „Add folder" din aplicație) și continuă după ce apare în `connectedFolders`.

**Negăsit în niciun folder conectat: monitorizarea nu e configurată.** Nu configura aici:

- cu utilizatorul **prezent** → pornește skill-ul **`initial-config-monitorizare-stiri-conta`** (sau spune-i să scrie „Configurează monitorizarea știrilor contabile") și reia raportarea abia după ce configurarea s-a terminat;
- într-o rulare **programată** → oprește-te și raportează scurt că monitorizarea nu e configurată și că e nevoie de o rulare manuală de configurare. Nu crea fișiere, nu ghici destinatar, nu trimite nimic.

### Confirmă scrierea, nu o presupune

După fiecare salvare, **recitește fișierul** și verifică prezența ultimelor acte adăugate. O scriere eșuată în tăcere e cea mai costisitoare defecțiune posibilă aici: raportul pleacă, starea nu se salvează, iar săptămâna viitoare destinatarul primește din nou aceleași acte. Dacă recitirea nu confirmă, spune-i utilizatorului în conversație, la rularea curentă.

### Structura

```json
{
  "email_destinatar": "client@exemplu.ro",
  "locatie_stare": "/Users/adrian/Documents/alfin/conta/",
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
- `locatie_stare` — folderul de pe calculatorul utilizatorului în care stă fișierul, cale absolută. Se scrie la configurare și nu se mai schimbă decât dacă utilizatorul cere explicit mutarea.

## Fluxul fiecărei rulări

### 1. Verifică conectorul Gmail

Caută uneltele Gmail disponibile (ToolSearch după `mcp__Gmail__send_message`). Fără Gmail nu putem livra raportul, așa că verificarea se face la **fiecare** rulare, înainte de orice muncă de colectare — nu are rost să aduni noutăți pe care nu le poți trimite.

Conectorul are **două niveluri**, și ambele trebuie să fie pornite: (a) autorizat la nivel de cont (Settings → Connectors) și (b) **activat în sesiunea curentă** — în chat, respectiv în task-ul programat. Un conector autorizat dar neactivat apare cu `enabledInChat: false` și uneltele lui lipsesc. Cazul tipic de eșec e exact acesta: Gmail merge în chat-ul în care s-a făcut configurarea, dar rularea programată pornește o sesiune nouă în care conectorul nu e activat.

Dacă uneltele Gmail **lipsesc**: oprește-te elegant (fără eroare) și afișează utilizatorului acest mesaj:

> Pentru a trimite raportul legislativ pe email, Gmail trebuie să fie disponibil în această sesiune:
> 1. dacă nu l-ai autorizat încă: **Settings → Connectors → Gmail** și autorizează accesul;
> 2. dacă e autorizat, activează-l pentru acest chat / task: butonul **+** din caseta de mesaj (sau panoul **Context**) → Connectors → pornește **Gmail**.
> După aceea, rulează din nou monitorizarea.

Într-o rulare programată nu ai pe cine ruga; raportezi lipsa și te oprești, fără să trimiți nimic și fără să modifici starea.

### 2. Colectează noutățile

**Perioada e exact de la `ultima_rulare` până azi.** O citești din fișierul de stare; nu o alegi tu.

Nu lărgi fereastra. Nici „ca să fim siguri", nici ca să prinzi ce s-ar fi putut rata, nici pentru că o săptămână pare puțin. Actele mai vechi au fost deja raportate — a le relua înseamnă exact dubla raportare pe care fișierul de stare există ca s-o prevină.

Cazuri limită:
- `ultima_rulare` lipsește sau nu se poate citi, dar fișierul de stare există → folosește `interval_rulare` (implicit 7 zile), nu mai mult;
- fereastra iese sub o zi, pentru că ultima rulare a fost recent → e în regulă, raportează ce e nou în intervalul acela sau nimic;
- doar **prima** rulare folosește o fereastră mai lungă, și doar pe cea aleasă de utilizator la configurare.

Citește `references/surse.md` pentru lista surselor și metoda de acces potrivită fiecăreia (unele site-uri blochează accesul direct și se interoghează prin căutare web). Sursele sunt grupate pe trei niveluri — parcurge **toate**, în ordine:

- **Nivel A — ce urmează**: ședințele de Guvern (gov.ro) și proiectele SGG. Actele de aici sunt adoptate sau propuse, dar **încă nepublicate în Monitorul Oficial**, deci **nu au număr**. Nu intră în fluxul principal: le colectezi separat, pentru `acte_in_asteptare` (vezi pasul 3).
- **Nivel B — ce s-a publicat**: Monitorul Oficial, sursa primară a actelor în vigoare; portalul legislativ (legislatie.just.ro) pentru textul consolidat al actelor importante.
- **Nivel C — ce înseamnă pentru contabil**: site-urile de specialitate, care semnalează și explică actele cu impact practic.

Nu sări peste secțiunea „Surse verificate ca inaccesibile" din `surse.md` — sunt domenii testate care răspund cu 403/404 sau resetează conexiunea. Nu le reîncerca la fiecare rulare.

Reguli importante:

- **Filtrează strict pe relevanță contabilă.** Testul, pentru fiecare act: *schimbă ceva în munca unui contabil din România?* Dacă nu, îl lași afară — indiferent cât de important e actul în sine. Un act major de infrastructură sau de sănătate rămâne în afara raportului.

  Ce intră: fiscalitate, TVA, impozit pe profit și pe venit, contribuții, salarizare, declarații și termene, raportări, reglementări contabile, proceduri fiscale, inspecție fiscală. Ca formă: legi, OUG-uri, HG-uri, ordine MF/ANAF, norme metodologice.

  Ce nu intră, oricât de vizibil ar fi în presă: penal, administrativ local, infrastructură, mediu, educație, sănătate, energie, numiri în funcții, titluri și distincții, concesiuni, urbanism.

  Aria contabilă e fixă și nu se negociază cu utilizatorul: în interiorul ei nu alegi un subset preferat, iar în afara ei nu ieși. Filtrul de relevanță contabilă e cel mai important lucru pe care îl faci la acest pas: un raport plin de acte irelevante e mai rău decât unul scurt.
- O sursă care nu răspunde sau dă eroare **nu oprește rularea** — treci la căutare web cu `site:<domeniu>` și mergi mai departe. Blocajele sunt normale și așteptate: gov.ro, ceccar.ro și avocatnet.ro refuză frecvent accesul direct. **Nu raporta asta nicăieri** — nici în email, nici, la rulările programate, în conversație. E funcționare normală, nu incident.
- Aceasta este o rulare autonomă: **nu cere aprobare** pentru accesarea site-urilor sau pentru căutări web.

### 3. Filtrează și deduplichează

**Întâi, reconciliază actele din așteptare.** Ia fiecare intrare din `acte_in_asteptare` și verifică dacă a apărut între timp în Monitorul Oficial. Potrivirea se face pe **titlu + tip + dată apropiată de adoptare**, nu pe număr — actele din așteptare nu au număr. Când găsești corespondentul publicat, actul primește numărul lui, iese din așteptare și intră în raportul principal ca act nou, tratat normal de aici încolo. Așa fiecare act se raportează integral o singură dată, chiar dacă a fost semnalat cu o săptămână mai devreme ca „adoptat".

**Apoi, actele obișnuite.** Identifică fiecare act prin tip + număr + an (ex. „OMF 1234/2026", „OUG 45/2026", „Legea 123/2026"). Compară cu `acte_vazute` din stare și păstrează doar actele **noi**. Același act apare de obicei pe mai multe site-uri — tratează-l ca unul singur și folosește toate sursele găsite ca material pentru raport.

**La final, actele de Nivel A rămase.** Cele adoptate în ședința de Guvern care nu au ajuns încă în Monitorul Oficial se adaugă în `acte_in_asteptare` (dacă nu sunt deja acolo) și se raportează doar ca avertizare, în secțiunea dedicată din șablonul de email. Nu le cerceta interpretările — nu există analize pentru un act fără text publicat.

Dacă după filtrare **nu rămâne nimic nou** (nici acte publicate, nici adoptate): nu trimite email. Actualizează `ultima_rulare` în stare și încheie cu un mesaj scurt („Nicio noutate legislativă contabilă în perioada X–Y. Nu s-a trimis raport.").

### 4. Cercetează interpretările

Pentru **fiecare** act nou, fă căutări web suplimentare ca să găsești ce spun specialiștii: articole de analiză, discuții pe forumuri (avocatnet.ro are forum activ), comentarii ale contabililor, materiale explicative. Țintește **minimum 2–3 surse de interpretare per act**.

Scopul nu e doar să anunți actul, ci să-i dai destinatarului înțelegerea practică: ce se schimbă concret, de când, pentru cine, ce controverse sau neclarități semnalează practicienii. Notează sursa fiecărei interpretări — raportul citează tot.

Dacă un act e foarte recent și încă nu există analize, spune asta explicit în raport („act publicat recent, interpretările specialiștilor încă nu au apărut — revenim în raportul următor") și **nu** îl adăuga încă în `acte_vazute`, ca să fie reluat săptămâna viitoare cu interpretări.

### 5. Compune și trimite emailul

Construiește raportul urmând **exact** structura din `references/email-template.md`. Subiectul: `Noutăți legislative contabilitate – săptămâna <data început> – <data sfârșit>`.

**Verificare obligatorie înainte de trimitere.** Recitește ciorna și șterge orice frază despre: surse care au blocat accesul sau n-au răspuns, metoda prin care ai ajuns la informație („prin căutare web", „prin surse secundare"), acoperire incompletă, fișierul de stare, task-uri programate, permisiuni, limitări ale mediului. Dacă ai scris undeva „nu a putut fi consultat", „acces blocat", „surse secundare" sau „acoperire mai subțire", scoate fraza întreagă — nu o reformula.

Regula de decizie, când eziți: informația a ajuns în raport sau nu? Dacă a ajuns, cum a ajuns nu interesează pe nimeni. Dacă nu a ajuns, actul pur și simplu nu apare — fără explicații despre de ce.

Singura excepție e cea deja prevăzută în șablon: un act publicat prea recent ca să aibă analize se semnalează ca atare, fiindcă asta e informație despre **act**, utilă contabilului, nu despre funcționarea internă.

**Destinatarul nu se ghicește niciodată.** Nici din contul Gmail conectat, nici din contextul conversației, nici din adresa vreunui cont vizibil în sesiune. Vine din `email_destinatar`, stabilit la configurare. Dacă lipsește și nu ai pe cine întreba, nu trimiți — nu inventezi un destinatar.

Trimite emailul prin Gmail către `email_destinatar` din stare. **Înainte de trimitere, verifică de unde vine adresa**: din fișierul de stare, nu din contul conectat și nu din context. E ultima ocazie de a prinde o adresă dedusă greșit. **Nu cere confirmare înainte de trimitere, niciodată.** Adresa a fost dată de utilizator la configurare, iar asta *este* autorizarea — pentru rulările manuale la fel ca pentru cele programate. Nu arăta raportul „spre aprobare" și nu întreba dacă e momentul potrivit; compune-l și trimite-l.

Singura excepție: utilizatorul e prezent în conversație și tocmai a schimbat adresa de destinație — atunci confirmi o dată noua adresă, ca să nu trimiți la o adresă tastată greșit.

### 6. Actualizează starea

După trimiterea cu succes a emailului (sau după concluzia „nimic nou"):

- `ultima_rulare` = data de azi;
- adaugă identificatorii actelor **raportate cu interpretări** în `acte_vazute` (limita de 200, elimină cele mai vechi);
- actualizează `acte_in_asteptare`: scoate intrările care au fost publicate între timp (au trecut în raportul principal), adaugă actele de Nivel A nou apărute și elimină intrările mai vechi de ~60 de zile — un act adoptat care nu s-a publicat în două luni fie a fost abandonat, fie l-am ratat la publicare;
- salvează fișierul de stare, în aceeași locație din care l-ai citit — pe calculatorul utilizatorului, prin `device_bash` (scriere în loc, cu un scurt script python de citire‑modificare‑scriere, nu prin retastarea conținutului din output), apoi recitește-l și confirmă că ultimele acte adăugate sunt acolo.

Actualizează starea **doar după** ce emailul a plecat — dacă trimiterea eșuează, starea rămâne neschimbată și rularea următoare reia aceleași acte, deci nimic nu se pierde.

## Emailul e pentru client. Notele tehnice nu ajung în el.

Raportul îl citește un contabil, nu un administrator. Nu are cum să acționeze pe baza detaliilor de funcționare internă, iar prezența lor îl face să pară fragil.

**Nu apar niciodată în email**: surse care au blocat accesul direct sau au dat eroare, metoda prin care s-a ajuns la o sursă, fișierul de stare, task-uri programate, permisiuni, limitări ale mediului, versiuni, nume de fișiere. Emailul conține doar acte normative și ce înseamnă ele.

**În conversație**, notele de funcționare se spun **o singură dată, la configurare sau la prima rulare** — ce s-a creat, ce n-a mers, ce rămâne de făcut manual. La rulările următoare, nimic: dacă totul e în regulă, tăcerea e răspunsul corect. Raportează din nou doar dacă apare ceva *nou* care blochează livrarea, de exemplu Gmail deconectat.

## Comenzi utile pentru utilizator

- „Schimbă adresa de email pentru rapoarte" → actualizează `email_destinatar` în stare.
- „Rulează acum monitorizarea" → execută fluxul complet imediat, indiferent de programare.
- „Configurează / reconfigurează monitorizarea" → skill-ul `initial-config-monitorizare-stiri-conta`.
- „Schimbă ziua/ora rulării" → task-ul programat e creat și deținut de utilizator; ghidează-l să-l editeze el: **Scheduled** → task-ul de monitorizare → editare → **Frequency**, ziua și ora noi. Apoi actualizează tu `zi_si_ora` în fișierul de stare, ca cele două să rămână în sincron.
- „Mută fișierul de stare în alt folder" → singurul caz în care `locatie_stare` se schimbă: folderul nou trebuie să fie **conectat**; copiază fișierul acolo cu `device_bash`, actualizează `locatie_stare`, apoi spune-i utilizatorului să editeze **Instructions** din task-ul programat cu noua cale. Nu șterge vechiul fișier (device_bash nu poate șterge implicit) — mută-l în `_to_delete/` și spune-i utilizatorului.
- „Adaugă/scoate o sursă" → nu edita fișierele skill-ului (folderul plugin-ului e rescris la fiecare actualizare); salvează sursele suplimentare într-un câmp `surse_extra` în fișierul de stare (listă de URL-uri) și consultă-le la fiecare rulare alături de cele standard. Pentru eliminarea unei surse standard, folosește un câmp `surse_dezactivate`.
