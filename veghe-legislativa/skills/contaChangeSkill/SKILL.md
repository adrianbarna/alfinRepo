---
name: contaChangeSkill
description: Monitorizează legislația contabilă și fiscală din România și trimite un raport detaliat pe email. Folosește acest skill ori de câte ori utilizatorul cere noutăți legislative, modificări fiscale sau contabile, verificarea Monitorului Oficial, un raport săptămânal de legislație, sau când rularea vine dintr-un task programat de monitorizare legislativă. Declanșează-l și pentru formulări ca „ce a mai apărut nou în contabilitate", „verifică legislația", „rulează monitorizarea" sau „trimite raportul legislativ".
---

# Monitorizare legislație contabilă

Acest skill transformă Claude într-un asistent de veghe legislativă pentru un cabinet de contabilitate din România. La fiecare rulare: verifică sursele de specialitate pentru acte normative noi, cercetează interpretările specialiștilor pentru fiecare noutate și trimite un raport detaliat pe email. Skill-ul este gândit să ruleze **săptămânal, programat, fără intervenția utilizatorului** — utilizatorul a autorizat acest comportament la instalare, deci nu cere confirmări în rulările programate.

## Fișierul de stare

Toată memoria skill-ului stă într-un singur fișier, numit **întotdeauna** `monitorizare-legislativa-state.json`.

### Fișierul stă pe calculatorul utilizatorului, într-un folder conectat

Sesiunea rulează în cloud, dar fișierul de stare **nu** stă în cloud — sandbox-ul se pierde între rulări. Stă **pe calculatorul utilizatorului**, într-un folder pe care el l-a conectat în aplicația Claude (Cowork). Ajungi la el prin puntea către dispozitiv: uneltele `mcp__remote-devices__*` (`get_device_info`, `device_list_dir`, `device_bash`, `device_stage_files`, `device_commit_files`).

Asta e premisa de la care pleci: **poți citi și scrie fișiere în folderul conectat, iar ele rămân acolo între rulări.** Fișierul de stare e mecanismul prin care raportul de săptămâna viitoare știe ce a trimis raportul de săptămâna asta — fără el, aceleași acte ajung la client de mai multe ori.

**Calea nu e fixă și nu e implicită.** Folderul diferă de la un utilizator la altul, așa că se stabilește **o singură dată, la prima rulare**, împreună cu utilizatorul (vezi „Prima rulare"), și după aceea se **refolosește mereu**, din două locuri:

1. din **promptul task-ului programat**, care conține calea absolută a fișierului (task-ul e creat la prima rulare și „știe" calea);
2. din **fișierul însuși**, care își notează locația în `locatie_stare` (calea absolută de pe calculatorul utilizatorului, ex. `/Users/nume/Documents/clienti/test/`).

Un folder conectat `/Users/nume/Documents/clienti/test` apare în `device_bash` la `$HOME/mnt/test/` (ultimul segment al căii devine numele montării). Deci fișierul se citește/scrie cu `device_bash` la `$HOME/mnt/<nume-folder>/monitorizare-legislativa-state.json`, iar în `locatie_stare` și în promptul task-ului se notează **calea reală de pe calculator**, nu cea de montare.

**Cum găsești fișierul la fiecare rulare**, în ordinea asta:

1. Dacă promptul rulării indică o cale, folosește-o.
2. Altfel, cheamă `get_device_info` și, pentru fiecare folder din `connectedFolders`, caută după nume: `device_bash` cu `find "$HOME/mnt" -maxdepth 3 -name monitorizare-legislativa-state.json`. Numele e fix tocmai ca să poată fi regăsit prin căutare.
3. Găsit oriunde, **acolo continui să scrii**; nu-l muta și nu crea o a doua copie.

Dacă `connectedFolders` e gol, nu e „prima rulare" — e **lipsă de acces**. Nu crea fișierul în cloud și nu ghici calea. Într-o rulare programată, oprește-te și raportează că task-ul nu are folderul conectat. Într-o rulare cu utilizatorul prezent, roagă-l să conecteze folderul (butonul de folder din panoul Context sau „Add folder" din aplicație) și continuă după ce apare în `connectedFolders`.

Negăsit în niciun folder conectat: e **prima rulare**, treci la configurare.

### Confirmă scrierea, nu o presupune

După fiecare salvare, **recitește fișierul** și verifică prezența ultimelor acte adăugate. O scriere eșuată în tăcere e cea mai costisitoare defecțiune posibilă aici: raportul pleacă, starea nu se salvează, iar săptămâna viitoare clientul primește din nou aceleași acte. Dacă recitirea nu confirmă, spune-i utilizatorului în conversație, la rularea curentă.

### Structura

```json
{
  "email_destinatar": "client@exemplu.ro",
  "locatie_stare": "/Users/nume/Documents/clienti/test/",
  "task_programat_id": "trig_01XXXXXXXXXXXXXXXXXXXXXX",
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
- `locatie_stare` — folderul de pe calculatorul utilizatorului în care stă fișierul, cale absolută. Se scrie o dată, la prima rulare, și nu se mai schimbă decât dacă utilizatorul cere explicit mutarea.
- `task_programat_id` — id-ul task-ului programat creat la prima rulare (`trig_...`). Servește la regăsirea și actualizarea lui (`update_trigger`) când utilizatorul schimbă ziua/ora, fără să creezi un al doilea task.
- Dacă fișierul nu există în niciun folder conectat, aceasta este **prima rulare** — urmează secțiunea „Prima rulare (configurare)".

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

### 2. Prima rulare (configurare)

Doar dacă fișierul de stare nu a fost găsit în niciun folder conectat.

Prima rulare se face **întotdeauna manual**, cu utilizatorul prezent — ea stabilește destinatarul, folderul și programarea. O rulare programată care nu găsește fișierul de stare nu configurează nimic: se oprește și spune că prima rulare trebuie făcută manual.

**Regula de aur a configurării: întreabă despre _unde_ și _când_, niciodată despre _ce_.** Destinatarul, folderul și ritmul sunt ale utilizatorului și se stabilesc împreună cu el. Conținutul e fix și e treaba skill-ului. Pune cele cinci întrebări de mai jos într-un singur mesaj (ideal cu AskUserQuestion), cu default-uri propuse, ca să poată răspunde „ok, lasă așa" dintr-un cuvânt.

0. **Folderul de pe calculator în care se ține fișierul de stare.** Cheamă `get_device_info` înainte să întrebi:
   - dacă `connectedFolders` conține **un singur** folder, propune-l ca default („Salvez fișierul de stare în `<cale>` — e ok?");
   - dacă conține **mai multe**, cere-i să aleagă unul dintre ele;
   - dacă e **gol**, cere-i să conecteze un folder (butonul de folder din panoul **Context** sau „Add folder" în aplicația Claude) și așteaptă să apară în `connectedFolders` înainte de a merge mai departe. Nu accepta o cale tastată care nu e conectată — nu ai cum să scrii acolo.

   Răspunsul (calea absolută de pe calculator, ex. `/Users/nume/Documents/clienti/test`) devine `locatie_stare` și intră în promptul task-ului programat. **De aici încolo nu se mai întreabă niciodată** — rulările următoare o iau din prompt sau din fișier.

1. **Adresa de email** către care se trimit rapoartele. Întreabă întotdeauna și salvează răspunsul în `email_destinatar` — de acolo se citește la toate rulările următoare.

   **Adresa contului Gmail conectat nu este destinatarul.** Contul conectat e doar mijlocul de trimitere; destinatarul e o decizie separată, pe care numai utilizatorul o poate lua. Nu o deduce din contul conectat, nu o completa singur, nu o folosi „provizoriu".

   Nu există adresă de rezervă. Dacă rulezi autonom, fără fișier de stare și fără pe cine întreba, **nu trimite nimic**: oprește-te și spune că prima rulare trebuie făcută manual, ca să poată fi stabilită adresa. Un raport trimis unde nu trebuie e mai rău decât un raport netrimis.
2. **Perioada acoperită de primul raport** — cât în urmă să se uite acum, la prima rulare. Propune **ultimele 7 zile**; unii vor o lună, ca să prindă tot ce au ratat.
3. **Cât de des rulează** — propune **săptămânal**. Alternative rezonabile: la două săptămâni, lunar.
4. **Ziua și ora rulării automate** — propune **luni, 08:00** (ora locală a utilizatorului; fusul orar e în contextul sesiunii).

Apoi, fără alte întrebări:

5. **Creează fișierul de stare** în folderul ales: `device_bash` scrie `$HOME/mnt/<nume-folder>/monitorizare-legislativa-state.json` cu adresa primită, `locatie_stare` = calea absolută de pe calculator, `interval_rulare` și `zi_si_ora` din răspunsuri, `ultima_rulare` = azi minus perioada aleasă la punctul 2, `acte_vazute` = [] și `acte_in_asteptare` = []. Recitește-l ca să confirmi scrierea.

6. **Creează efectiv task-ul programat**, cu `mcp__claude-code-remote__create_trigger` (dacă e amânat, încarcă-l cu ToolSearch). Nu folosi niciodată CronCreate — trăiește doar în sesiunea curentă și dispare cu ea. Parametrii care contează, fiecare cu motivul lui:

   - `requires_local_device: true` — **obligatoriu și nemodificabil ulterior.** Doar un task creat cu acest flag primește, la aprobare, legarea de calculatorul utilizatorului; fără el, rulările programate pornesc cu `connectedFolders: []`, nu văd fișierul de stare și se opresc. Un task creat fără flag nu se poate repara cu `update_trigger` — trebuie șters și recreat.
   - `cron_expression` — convertit din ora locală în **UTC** (ex. luni 08:00 Europe/Bucharest, UTC+3 vara → `0 5 * * 1`; iarna, UTC+2 → `0 6 * * 1`). Spune-i utilizatorului că ora e fixată în UTC, deci se decalează cu o oră la schimbarea orei de vară/iarnă.
   - `prompt` — complet și de sine stătător (rularea pornește o sesiune nouă, fără memoria acestei conversații), cu **calea fișierului de stare în ambele forme** și cu numele uneltei de email. Șablon, cu valorile completate:

     > „Rulează skill-ul de monitorizare legislativă (monitorizare-legislativa:contaChangeSkill). Rulare autonomă, fără utilizator prezent: nu cere nicio confirmare, nu pune întrebări, iar la final trimite raportul pe email către adresa din fișierul de stare, folosind conectorul Gmail (mcp__Gmail__send_message).
     >
     > Fișierul de stare se află pe calculatorul utilizatorului, în folderul conectat: `<locatie_stare>/monitorizare-legislativa-state.json` (accesibil prin device_bash la `$HOME/mnt/<nume-folder>/monitorizare-legislativa-state.json`). Citește-l de acolo, actualizează-l tot acolo după trimiterea emailului și verifică scrierea prin recitire.
     >
     > Dacă folderul nu este conectat sau conectorul Gmail nu este disponibil, nu ghici destinatarul și nu trimite nimic; raportează clar ce lipsește."

   - `name` — descriptiv, cu ritmul și ora în el, ex. „Monitorizare legislativă contabilă (săptămânal, luni 08:00)".
   - `initiation: "human_request"`.
   - `notifications` — `{"push": true, "email": false}` ca default. Sunt notificările de **finalizare a rulării** (rezumatul „task-ul s-a terminat"), nu raportul legislativ — raportul pleacă oricum prin Gmail către `email_destinatar`. Dacă utilizatorul vrea și rezumatul rulării în inbox, pune `email: true`.

   Salvează `id`-ul returnat (`trig_...`) în `task_programat_id` din fișierul de stare, ca să-l poți actualiza mai târziu în loc să creezi un duplicat.

7. **Spune-i utilizatorului cei doi pași pe care doar el îi poate face**, o singură dată, într-un mesaj scurt — aceștia sunt exact pașii fără de care rularea programată eșuează:

   - **Aprobă task-ul și legarea de calculator.** La creare, aplicația îi cere aprobarea; în același dialog i se oferă legarea task-ului de acest calculator. Trebuie să o accepte — așa primesc rulările programate accesul la folderul cu fișierul de stare. Confirmarea reușitei e textul „bound: this computer" din răspunsul `create_trigger`.
   - **Activează Gmail pentru task.** Conectorul e activat per chat/task, nu global, iar task-ul nou pornește fără el. Deschide task-ul (Scheduled → numele task-ului), apoi butonul **+** din caseta de mesaj sau panoul **Context** → Connectors → pornește **Gmail**. Nu există unealtă prin care să faci asta în locul lui.

   După ambii pași, propune-i un test: „Rulează acum monitorizarea" (sau `fire_trigger` pe `task_programat_id`), ca să verifice că rularea autonomă găsește și folderul, și Gmail-ul.

8. Continuă cu pașii de mai jos — prima rulare produce și primul raport.

### Ce NU întrebi niciodată

- **Ce domenii sau arii îl interesează.** Îl interesează toate schimbările cu impact asupra activității unui contabil — fiscalitate, TVA, impozite, salarizare, contribuții, declarații, proceduri fiscale, raportări, reglementări contabile. Aria e fixă, definită la pasul 3, și nu se negociază cu utilizatorul. Asta nu slăbește filtrul de relevanță contabilă de la pasul 3 — el rămâne strict.
- **Ce surse să monitorizeze.** Lista din `references/surse.md` e completă și verificată; se ajustează ulterior prin `surse_extra` / `surse_dezactivate`.
- **Dacă are voie să trimită emailul.** Adresa dată la punctul 1 *este* autorizarea.

**Destinatarul nu se ghicește niciodată.** Nici din contul Gmail conectat, nici din contextul conversației, nici din adresa vreunui cont vizibil în sesiune. Vine din `email_destinatar`, salvat la prima rulare manuală. Dacă lipsește și nu ai pe cine întreba, nu trimiți — nu inventezi un destinatar.

### Dacă mediul nu permite programarea

Task-ul programat trebuie creat cu `requires_local_device: true` și legat de calculator la aprobare, ca rulările să aibă acces la folderul conectat — altfel fișierul de stare nu e vizibil și deduplicarea nu funcționează. Permisiunile task-ului trebuie să sară peste aprobări, ca rularea să meargă fără nimeni în fața ecranului.

Dacă un task există deja dar a fost creat **fără** legare de calculator (rulările lui raportează `connectedFolders: []`): șterge-l cu `delete_trigger` și recreează-l cu pașii 6–7 de mai sus, păstrând aceeași programare și același prompt. Actualizează `task_programat_id`. Explică într-o propoziție de ce recrearea e necesară (flag-ul nu se poate adăuga ulterior).

Dacă mediul nu oferă deloc un mecanism de task-uri programate:

- spune-i utilizatorului **o singură dată, în această primă sesiune**, ce n-a mers și ce înseamnă practic (va trebui să pornească manual monitorizarea, sau să configureze programarea din interfața de task-uri recurente), și oferă-te să-l ghidezi;
- **nu repeta explicația la rulările următoare** și nu o scrie în email;
- continuă normal cu raportul — lipsa programării nu blochează rularea curentă.

### 3. Colectează noutățile

**Perioada e exact de la `ultima_rulare` până azi.** O citești din fișierul de stare; nu o alegi tu.

Nu lărgi fereastra. Nici „ca să fim siguri", nici ca să prinzi ce s-ar fi putut rata, nici pentru că o săptămână pare puțin. Actele mai vechi au fost deja raportate — a le relua înseamnă exact dubla raportare pe care fișierul de stare există ca s-o prevină.

Cazuri limită:
- `ultima_rulare` lipsește sau nu se poate citi, dar fișierul de stare există → folosește `interval_rulare` (implicit 7 zile), nu mai mult;
- fereastra iese sub o zi, pentru că ultima rulare a fost recent → e în regulă, raportează ce e nou în intervalul acela sau nimic;
- doar **prima** rulare folosește o fereastră mai lungă, și doar pe cea aleasă de utilizator la configurare.

Citește `references/surse.md` pentru lista surselor și metoda de acces potrivită fiecăreia (unele site-uri blochează accesul direct și se interoghează prin căutare web). Sursele sunt grupate pe trei niveluri — parcurge **toate**, în ordine:

- **Nivel A — ce urmează**: ședințele de Guvern (gov.ro) și proiectele SGG. Actele de aici sunt adoptate sau propuse, dar **încă nepublicate în Monitorul Oficial**, deci **nu au număr**. Nu intră în fluxul principal: le colectezi separat, pentru `acte_in_asteptare` (vezi pasul 4).
- **Nivel B — ce s-a publicat**: Monitorul Oficial, sursa primară a actelor în vigoare; portalul legislativ (legislatie.just.ro) pentru textul consolidat al actelor importante.
- **Nivel C — ce înseamnă pentru contabil**: site-urile de specialitate, care semnalează și explică actele cu impact practic.

Nu sări peste secțiunea „Surse verificate ca inaccesibile" din `surse.md` — sunt domenii testate care răspund cu 403/404 sau resetează conexiunea. Nu le reîncerca la fiecare rulare.

Reguli importante:

- **Filtrează strict pe relevanță contabilă.** Testul, pentru fiecare act: *schimbă ceva în munca unui contabil din România?* Dacă nu, îl lași afară — indiferent cât de important e actul în sine. Un act major de infrastructură sau de sănătate rămâne în afara raportului.

  Ce intră: fiscalitate, TVA, impozit pe profit și pe venit, contribuții, salarizare, declarații și termene, raportări, reglementări contabile, proceduri fiscale, inspecție fiscală. Ca formă: legi, OUG-uri, HG-uri, ordine MF/ANAF, norme metodologice.

  Ce nu intră, oricât de vizibil ar fi în presă: penal, administrativ local, infrastructură, mediu, educație, sănătate, energie, numiri în funcții, titluri și distincții, concesiuni, urbanism.

  „Fără subîmpărțiri" înseamnă că **în interiorul** ariei contabile nu alegi un subset preferat — nu că nu filtrezi. Filtrul de relevanță contabilă e cel mai important lucru pe care îl faci la acest pas: un raport plin de acte irelevante e mai rău decât unul scurt.
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
- salvează fișierul de stare, în aceeași locație din care l-ai citit — pe calculatorul utilizatorului, prin `device_bash` (scriere în loc, cu un scurt script python de citire‑modificare‑scriere, nu prin retastarea conținutului din output), apoi recitește-l și confirmă că ultimele acte adăugate sunt acolo.

Actualizează starea **doar după** ce emailul a plecat — dacă trimiterea eșuează, starea rămâne neschimbată și rularea următoare reia aceleași acte, deci nimic nu se pierde.

## Emailul e pentru client. Notele tehnice nu ajung în el.

Raportul îl citește un contabil, nu un administrator. Nu are cum să acționeze pe baza detaliilor de funcționare internă, iar prezența lor îl face să pară fragil.

**Nu apar niciodată în email**: surse care au blocat accesul direct sau au dat eroare, metoda prin care s-a ajuns la o sursă, fișierul de stare, task-uri programate, permisiuni, limitări ale mediului, versiuni, nume de fișiere. Emailul conține doar acte normative și ce înseamnă ele.

**În conversație**, notele de configurare se spun **o singură dată, la prima rulare** — ce s-a creat, ce n-a mers, ce rămâne de făcut manual. La rulările următoare, nimic: dacă totul e în regulă, tăcerea e răspunsul corect. Raportează din nou doar dacă apare ceva *nou* care blochează livrarea, de exemplu Gmail deconectat.

## Comenzi utile pentru utilizator

- „Schimbă adresa de email pentru rapoarte" → actualizează `email_destinatar` în stare.
- „Rulează acum monitorizarea" → execută fluxul complet imediat, indiferent de programare.
- „Schimbă ziua/ora rulării" → `update_trigger` pe `task_programat_id` cu noul `cron_expression` (în UTC) și noul `name`; actualizează `zi_si_ora` în stare. Nu crea un al doilea task.
- „Mută fișierul de stare în alt folder" → singurul caz în care `locatie_stare` se schimbă: folderul nou trebuie să fie conectat; copiază fișierul acolo cu `device_bash`, actualizează `locatie_stare`, apoi `update_trigger` cu promptul refăcut pe noua cale (`delete_trigger` + recreare dacă task-ul nu era legat de calculator). Nu șterge vechiul fișier (device_bash nu poate șterge implicit) — mută-l în `_to_delete/` și spune-i utilizatorului.
- „Adaugă/scoate o sursă" → nu edita fișierele skill-ului (pot fi read-only la client); salvează sursele suplimentare într-un câmp `surse_extra` în `state.json` (listă de URL-uri) și consultă-le la fiecare rulare alături de cele standard. Pentru eliminarea unei surse standard, folosește un câmp `surse_dezactivate`.
