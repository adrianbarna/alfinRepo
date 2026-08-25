---
name: initial-config-monitorizare-stiri-conta
description: Configurarea inițială a monitorizării de știri contabile, rulată o singură dată, cu utilizatorul prezent. Stabilește folderul conectat pentru fișierul de stare, adresa destinatarului, ritmul și ora, creează fișierul de stare și îi dă utilizatorului valorile exacte de completat în dialogul de creare a task-ului programat. Folosește acest skill când utilizatorul cere configurarea, instalarea sau resetarea monitorizării („configurează monitorizarea", „setup monitorizare știri conta") sau când skill-ul monitorizare-stiri-conta nu găsește fișierul de stare.
---

# Configurarea inițială a monitorizării de știri contabile

Acest skill rulează **o singură dată, cu utilizatorul prezent**. Stabilește tot ce ține de *unde* și *când* — folderul pentru fișierul de stare, destinatarul, ritmul — creează fișierul de stare și pregătește programarea. Nu colectează știri și nu trimite emailuri: rularea propriu-zisă e treaba skill-ului pereche **`monitorizare-stiri-conta`**.

**Acest skill NU creează task-ul programat.** Task-ul îl creează utilizatorul, manual, din aplicație (**Scheduled tasks → New task**), iar skill-ul îi dă la final **fișa completă** cu fiecare câmp de completat. Motivul: creat de el, în dialogul aplicației, utilizatorul vede și aprobă exact ce rulează în numele lui — permisiunile, legarea de calculator — iar task-ul îi aparține de la început, cu tot cu butonul de editare.

## Mediul în care lucrezi

Sesiunea rulează în cloud; sandbox-ul se pierde între rulări. Fișierul de stare trebuie deci să stea **pe calculatorul utilizatorului**, într-un folder conectat în aplicația Claude, accesat prin puntea către dispozitiv: uneltele `mcp__remote-devices__*` (`get_device_info`, `device_bash` etc.). Un folder conectat `/Users/nume/Documents/clienti/test` apare în `device_bash` la `$HOME/mnt/test/` — ultimul segment al căii devine numele montării. În fișier și în fișa task-ului se notează **calea reală de pe calculator**, nu cea de montare.

## Întrebările

**Regula de aur: întreabă despre _unde_ și _când_, niciodată despre _ce_.** Destinatarul, folderul și ritmul sunt ale utilizatorului. Conținutul monitorizării e fix și e treaba skill-ului de rulare. Pune cele cinci întrebări într-un singur mesaj (ideal cu AskUserQuestion), cu default-uri propuse, ca să poată răspunde „ok, lasă așa" dintr-un cuvânt.

0. **Folderul de pe calculator în care se ține fișierul de stare.** Cheamă `get_device_info` înainte să întrebi:
   - dacă `connectedFolders` conține **un singur** folder, propune-l ca default („Salvez fișierul de stare în `<cale>` — e ok?");
   - dacă conține **mai multe**, cere-i să aleagă unul dintre ele;
   - dacă e **gol**, cere-i să conecteze un folder (butonul de folder din panoul **Context** sau „Add folder" în aplicația Claude) și așteaptă să apară în `connectedFolders` înainte de a merge mai departe. Nu accepta o cale tastată care nu e conectată — nu ai cum să scrii acolo.

   Răspunsul (calea absolută, ex. `/Users/nume/Documents/clienti/test`) devine `locatie_stare` și intră în fișa task-ului. **De aici încolo nu se mai întreabă niciodată.**

1. **Adresa de email** către care se trimit rapoartele. Întreabă întotdeauna și salveaz-o în `email_destinatar`.

   **Adresa contului Gmail conectat nu este destinatarul.** Contul conectat e doar mijlocul de trimitere; destinatarul e o decizie separată, pe care numai utilizatorul o poate lua. Nu o deduce, nu o completa singur, nu o folosi „provizoriu". Nu există adresă de rezervă.

2. **Perioada acoperită de primul raport** — cât în urmă să se uite prima rulare. Propune **ultimele 7 zile**; unii vor o lună, ca să prindă tot ce au ratat.
3. **Cât de des rulează** — propune **săptămânal**. Alternative rezonabile: la două săptămâni, lunar.
4. **Ziua și ora rulării automate** — propune **luni, 08:00** (ora locală a utilizatorului).

### Ce NU întrebi niciodată

- **Ce domenii sau arii îl interesează.** Raportul acoperă tot ce are impact asupra activității unui contabil — fiscalitate, TVA, impozite, salarizare, contribuții, declarații, proceduri fiscale, raportări, reglementări contabile. Aria e fixă; nu o restrânge și nu cere utilizatorului s-o restrângă.
- **Ce surse să monitorizeze.** Lista din skill-ul de rulare e completă și verificată; se ajustează ulterior prin `surse_extra` / `surse_dezactivate` în fișierul de stare.
- **Dacă are voie să trimită emailul.** Adresa dată la punctul 1 *este* autorizarea.

## Creează fișierul de stare

În folderul ales, prin `device_bash`, scrie `$HOME/mnt/<nume-folder>/monitorizare-legislativa-state.json`:

```json
{
  "email_destinatar": "<adresa de la punctul 1>",
  "locatie_stare": "<calea absolută de la punctul 0>/",
  "interval_rulare": "<ritmul de la punctul 3>",
  "zi_si_ora": "<ziua și ora de la punctul 4>",
  "ultima_rulare": "<azi minus perioada de la punctul 2>",
  "acte_vazute": [],
  "acte_in_asteptare": []
}
```

Recitește fișierul ca să confirmi scrierea. Structura completă și semnificația câmpurilor sunt documentate în skill-ul `monitorizare-stiri-conta` — el e proprietarul fișierului de aici încolo.

## Fișa pentru task-ul programat

Prezintă-i utilizatorului fișa de mai jos, cu toate valorile completate, și spune-i să deschidă **Scheduled tasks → New task** și să copieze câmp cu câmp. Blocul de Instructions dă-i-l într-un bloc de cod, ca să-l poată copia dintr-un click.

| Câmp în dialog | Ce completează |
|---|---|
| **Name** | `Monitorizare legislativă contabilă (<ritm>, <zi> <ora>)` |
| **Instructions** | blocul de mai jos, integral |
| **Work in a project or folder** | folderul ales la punctul 0 — același în care stă fișierul de stare |
| **Model** | lasă Default |
| **Frequency** | ritmul, ziua și ora alese (ora locală) |
| **Permissions** | **Skip all approvals** — rulările merg fără nimeni în fața ecranului; cu „Manually approve", task-ul rămâne blocat așteptând un „da" pe care nu-l dă nimeni |
| **Require this computer** | **pornit** — asta dă rulărilor accesul la folderele conectate de pe calculator; fără el pornesc cu `connectedFolders` gol, nu găsesc fișierul de stare și se opresc. Rulează doar cât timp calculatorul e pornit și treaz. |
| **Run on your computer** | lăsat oprit — e alt mod de execuție (avansat) și nu e necesar aici |

Textul pentru **Instructions**, cu valorile completate:

```
Rulează skill-ul de monitorizare legislativă (monitorizare-legislativa:monitorizare-stiri-conta).
Rulare autonomă, fără utilizator prezent: nu cere nicio confirmare, nu pune întrebări, iar la
final trimite raportul pe email către adresa din fișierul de stare, folosind conectorul Gmail
(mcp__Gmail__send_message).

Fișierul de stare se află pe calculatorul utilizatorului, în folderul conectat:
<locatie_stare>/monitorizare-legislativa-state.json (accesibil prin device_bash la
$HOME/mnt/<nume-folder>/monitorizare-legislativa-state.json). Citește-l de acolo, actualizează-l
tot acolo după trimiterea emailului și verifică scrierea prin recitire.

Dacă folderul nu este conectat sau conectorul Gmail nu este disponibil, nu ghici destinatarul
și nu trimite nimic; raportează clar ce lipsește.
```

## După ce utilizatorul salvează task-ul

Mai rămâne **un pas pe care doar el îl poate face**, și fără el rularea programată eșuează:

- **Activează Gmail pentru task.** Conectorul e activat per chat/task, nu global, iar task-ul nou pornește fără el. Deschide task-ul (**Scheduled** → numele task-ului), apoi butonul **+** din caseta de mesaj sau panoul **Context** → Connectors → pornește **Gmail**. Nu există unealtă prin care să faci asta în locul lui.

Apoi propune-i **testul**: „Run now" pe task (sau „Rulează acum monitorizarea" în chat), ca să verifice că rularea autonomă găsește și folderul, și Gmail-ul.

## Primul raport

După fișă și pașii de mai sus, oferă-i primul raport pe loc: dacă acceptă, continuă în chatul curent cu skill-ul `monitorizare-stiri-conta` — configurarea tocmai s-a terminat, fișierul de stare există, iar `ultima_rulare` e setată pe perioada aleasă la punctul 2.

## Dacă rulările programate raportează `connectedFolders` gol

Task-ul a fost creat fără **Require this computer**, iar comutatorul nu se poate porni din exterior. Spune-i utilizatorului să editeze task-ul (sau să-l șteargă și să-l recreeze cu fișa de mai sus) cu comutatorul pornit. Fișierul de stare nu e afectat — rămâne unde e.
