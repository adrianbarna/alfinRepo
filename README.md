# Monitorizare Legislație Contabilă

Plugin pentru Claude (Cowork / Claude Code) care monitorizează **săptămânal** legislația contabilă și fiscală din România și trimite un **raport detaliat pe email** cu noutățile apărute și interpretările specialiștilor.

## Ce face

O dată pe săptămână, automat:

1. Verifică sursele de specialitate, pe trei niveluri:
   - *ce urmează* — **ședințele de Guvern** (gov.ro) și proiectele **SGG**, care anunță actele cu câteva zile înainte de publicare;
   - *ce s-a publicat* — **Monitorul Oficial** și **portalul legislativ** (legislatie.just.ro, text consolidat);
   - *ce înseamnă pentru contabil* — **avocatnet.ro**, **ANAF**, **contzilla.ro**, **legestart.ro**, **CECCAR Business Magazine**, **ceccar.ro**, **contabilul.ro**.
2. Identifică actele normative noi cu impact contabil/fiscal (legi, OUG, HG, ordine MF/ANAF).
3. Pentru fiecare act nou, caută pe internet analizele și părerile contabililor (articole, forumuri).
4. Trimite un email cu raportul: ce prevede fiecare act, de când se aplică, pe cine afectează, ce spun specialiștii — totul cu linkuri către surse.

Dacă într-o săptămână nu apare nimic nou, nu primiți email.

## Instalare (o singură dată)

Nu aveți nevoie de git și nu aveți nevoie de terminal. Totul se face din aplicația Claude sau de pe claude.ai.

**Pasul 1 — Adăugați sursa plugin-ului.** Deschideți **Settings → Customize → Plugins** (sau, în aplicație, meniul **Directory → Plugins**). Alegeți fila **Personal** și apăsați **+** din dreapta. În câmpul URL scrieți exact:

```
adrianbarna/contaLacramioara
```

Lăsați **Sync automatically** pornit — așa primiți actualizările fără să faceți nimic. Apăsați **Sync**.

**Pasul 2 — Activați plugin-ul.** După sincronizare apare cardul **Monitorizare legislativă**. Deschideți-l cu rotița din colț și activați-l.

**Pasul 3 — Conectați Gmail.** În **Settings → Connectors**, alegeți **Gmail** și autorizați accesul. Fără Gmail raportul nu poate fi trimis — asistentul vă spune dacă lipsește și se oprește elegant.

**Pasul 4 — Prima rulare.** Scrieți în conversație:

> Rulează monitorizarea legislativă

La prima rulare, asistentul vă pune **o singură întrebare** — către ce adresă de email trimite rapoartele. Restul îl configurează singur: programează raportul săptămânal (implicit luni la 08:00, se mută oricând), își pregătește permisiunile ca rulările programate să meargă fără aprobări, și generează primul raport cu noutățile din ultimele șapte zile.

<details>
<summary>Instalare din terminal, pentru administratori</summary>

```
/plugin marketplace add adrianbarna/contaLacramioara
/plugin install monitorizare-legislativa@lacramioara-conta
```

Dacă sumarul spune `Run /reload-plugins to activate.`, rulați și `/reload-plugins`.

Pe această cale marketplace-ul se **clonează local**, deci mașina are nevoie de git instalat. Calea din Settings nu are nevoie: clonarea se face pe serverele Anthropic.

</details>

Din acel moment totul e automat: raportul sosește săptămânal pe email.

## Comenzi utile după instalare

| Ce vreți | Ce scrieți |
|---|---|
| Raport imediat, în afara programării | „Rulează acum monitorizarea legislativă" |
| Schimbarea adresei de email | „Schimbă adresa de email pentru rapoartele legislative în ..." |
| Adăugarea unei surse de monitorizat | „Adaugă sursa <URL> la monitorizarea legislativă" |
| Schimbarea zilei/orei de rulare | „Mută monitorizarea legislativă <ziua> la <ora>" |

## Cum funcționează în spate (pentru administrator)

- Skill-ul își ține configurația și istoricul în `~/.claude/monitorizare-legislativa/state.json` (adresa destinatar, data ultimei rulări, lista actelor deja raportate — pentru a nu trimite același act de două ori).
- **Distribuție**: repo public pe GitHub, `adrianbarna/contaLacramioara`. Marketplace-ul se adaugă cu scurtătura `owner/repo`, iar plugin-ul e livrat prin cale relativă (`"source": "./"`) din același repo.
- **De ce cale relativă și nu arhivă zip**: validatorul din Settings → Plugins nu acceptă tipul de sursă `archive` — recunoaște repo-ul, dar sincronizarea eșuează. Cu marketplace-ul clonat, calea relativă se rezolvă corect. Compromisul: instalarea din terminal cere git local.
- **GitLab nu funcționează pentru această cale.** Dialogul de adăugare validează adresa server-side ca repo GitHub și respinge orice adresă GitLab, indiferent de formă — repo, `.git` sau raw.
- **Actualizări**: cu `Sync automatically` pornit, clientul primește versiunea nouă după ce câmpul `version` din `.claude-plugin/plugin.json` e incrementat. Bumpați-l la fiecare release, altfel push-ul nu ajunge la el.
- Sursele și metoda de acces a fiecăreia: [skills/contaChangeSkill/references/surse.md](skills/contaChangeSkill/references/surse.md).
- Formatul raportului: [skills/contaChangeSkill/references/email-template.md](skills/contaChangeSkill/references/email-template.md).
- Logica completă de rulare: [skills/contaChangeSkill/SKILL.md](skills/contaChangeSkill/SKILL.md).
