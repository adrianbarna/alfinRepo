---
name: contaChangeSkill
description: Monitorizează legislația contabilă și fiscală din România și trimite un raport detaliat pe email. Folosește acest skill ori de câte ori utilizatorul cere noutăți legislative, modificări fiscale sau contabile, verificarea Monitorului Oficial, un raport săptămânal de legislație, sau când rularea vine dintr-un task programat de monitorizare legislativă. Declanșează-l și pentru formulări ca „ce a mai apărut nou în contabilitate", „verifică legislația", „rulează monitorizarea" sau „trimite raportul legislativ".
---

# Monitorizare legislație contabilă

Acest skill transformă Claude într-un asistent de veghe legislativă pentru un cabinet de contabilitate din România. La fiecare rulare: verifică sursele de specialitate pentru acte normative noi, cercetează interpretările specialiștilor pentru fiecare noutate și trimite un raport detaliat pe email. Skill-ul este gândit să ruleze **săptămânal, programat, fără intervenția utilizatorului** — utilizatorul a autorizat acest comportament la instalare, deci nu cere confirmări în rulările programate.

## Fișierul de stare

Toată memoria skill-ului stă în `~/.claude/monitorizare-legislativa/state.json`:

```json
{
  "email_destinatar": "client@exemplu.ro",
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

Doar dacă `state.json` nu există:

1. **Întreabă utilizatorul** către ce adresă de email se trimit rapoartele. Nu presupune adresa contului Gmail conectat — clientul poate vrea rapoartele către altă adresă (un coleg, o adresă de birou).
2. Creează `~/.claude/monitorizare-legislativa/state.json` cu adresa primită, `ultima_rulare` = data de azi minus 7 zile (ca prima rulare să aibă conținut de raportat), `acte_vazute` = [] și `acte_in_asteptare` = [].
3. **Propune programarea săptămânală**: creează un task programat (scheduled task) care rulează acest skill o dată pe săptămână — default lunea la 08:00, dar lasă utilizatorul să aleagă ziua și ora. Promptul task-ului programat: „Rulează skill-ul monitorizare-legislativa și trimite raportul săptămânal."
4. **Pregătește rularea autonomă**: rulările programate trebuie să meargă fără aprobare manuală. Dacă mediul folosește liste de permisiuni (settings.json din Claude Code), adaugă — cu acordul utilizatorului, o singură dată, acum — permisiuni pentru: căutare web, acces la domeniile din `references/surse.md`, citirea/scrierea fișierului de stare și trimiterea de email prin Gmail. Explică-i utilizatorului că fără acest pas fiecare rulare programată ar rămâne blocată așteptând aprobări.
5. Continuă apoi cu pașii de mai jos — prima rulare produce și primul raport.

### 3. Colectează noutățile

Perioada de interes: de la `ultima_rulare` până azi.

Citește `references/surse.md` pentru lista surselor și metoda de acces potrivită fiecăreia (unele site-uri blochează accesul direct și se interoghează prin căutare web). Sursele sunt grupate pe trei niveluri — parcurge **toate**, în ordine:

- **Nivel A — ce urmează**: ședințele de Guvern (gov.ro) și proiectele SGG. Actele de aici sunt adoptate sau propuse, dar **încă nepublicate în Monitorul Oficial**, deci **nu au număr**. Nu intră în fluxul principal: le colectezi separat, pentru `acte_in_asteptare` (vezi pasul 4).
- **Nivel B — ce s-a publicat**: Monitorul Oficial, sursa primară a actelor în vigoare; portalul legislativ (legislatie.just.ro) pentru textul consolidat al actelor importante.
- **Nivel C — ce înseamnă pentru contabil**: site-urile de specialitate, care semnalează și explică actele cu impact practic.

Nu sări peste secțiunea „Surse verificate ca inaccesibile" din `surse.md` — sunt domenii testate care răspund cu 403/404 sau resetează conexiunea. Nu le reîncerca la fiecare rulare.

Reguli importante:

- Caută doar acte cu relevanță **contabilă/fiscală/salarizare**: legi, OUG-uri, HG-uri, ordine MF/ANAF, norme metodologice, proceduri fiscale. Ignoră legislația fără impact asupra activității unui contabil (penal, administrativ local etc.).
- O sursă care nu răspunde sau dă eroare **nu oprește rularea** — noteaz-o și mergi mai departe cu celelalte. Menționează în raport, discret la final, dacă o sursă nu a putut fi consultată.
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

Trimite emailul prin Gmail către `email_destinatar` din stare. Trimiterea către această adresă a fost autorizată de utilizator la configurare — în rulările programate **nu cere confirmare** înainte de trimitere. Cere confirmare doar dacă utilizatorul e prezent în conversație și tocmai a modificat ceva la configurație.

### 7. Actualizează starea

După trimiterea cu succes a emailului (sau după concluzia „nimic nou"):

- `ultima_rulare` = data de azi;
- adaugă identificatorii actelor **raportate cu interpretări** în `acte_vazute` (limita de 200, elimină cele mai vechi);
- actualizează `acte_in_asteptare`: scoate intrările care au fost publicate între timp (au trecut în raportul principal), adaugă actele de Nivel A nou apărute și elimină intrările mai vechi de ~60 de zile — un act adoptat care nu s-a publicat în două luni fie a fost abandonat, fie l-am ratat la publicare;
- salvează `state.json`.

Actualizează starea **doar după** ce emailul a plecat — dacă trimiterea eșuează, starea rămâne neschimbată și rularea următoare reia aceleași acte, deci nimic nu se pierde.

## Comenzi utile pentru utilizator

- „Schimbă adresa de email pentru rapoarte" → actualizează `email_destinatar` în stare.
- „Rulează acum monitorizarea" → execută fluxul complet imediat, indiferent de programare.
- „Adaugă/scoate o sursă" → nu edita fișierele skill-ului (pot fi read-only la client); salvează sursele suplimentare într-un câmp `surse_extra` în `state.json` (listă de URL-uri) și consultă-le la fiecare rulare alături de cele standard. Pentru eliminarea unei surse standard, folosește un câmp `surse_dezactivate`.
