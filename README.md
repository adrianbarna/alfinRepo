# Monitorizare Legislație Contabilă

Plugin pentru Claude (Cowork / Claude Code) care monitorizează **săptămânal** legislația contabilă și fiscală din România și trimite un **raport detaliat pe email** cu noutățile apărute și interpretările specialiștilor.

## Ce face

O dată pe săptămână, automat:

1. Verifică sursele de specialitate: **Monitorul Oficial**, **avocatnet.ro**, **ANAF**, **contzilla.ro**, **contabilul.ro**.
2. Identifică actele normative noi cu impact contabil/fiscal (legi, OUG, HG, ordine MF/ANAF).
3. Pentru fiecare act nou, caută pe internet analizele și părerile contabililor (articole, forumuri).
4. Trimite un email cu raportul: ce prevede fiecare act, de când se aplică, pe cine afectează, ce spun specialiștii — totul cu linkuri către surse.

Dacă într-o săptămână nu apare nimic nou, nu primiți email.

## Instalare (o singură dată)

**Pasul 1 — Instalați plugin-ul.** În Claude (aplicația desktop) sau Claude Code, rulați:

```
/plugin marketplace add <URL-ul acestui repo git>
```

apoi:

```
/plugin install monitorizare-legislativa@lacramioara-conta
```

**Pasul 2 — Conectați Gmail.** Deschideți **Settings → Connectors**, alegeți **Gmail** și autorizați accesul. Fără Gmail, raportul nu poate fi trimis (asistentul vă va reaminti dacă lipsește).

**Pasul 3 — Prima rulare.** Scrieți în conversație:

> Rulează monitorizarea legislativă

La prima rulare, asistentul:
- vă întreabă **către ce adresă de email** să trimită rapoartele;
- vă propune **programarea săptămânală** (alegeți ziua și ora — de ex. luni la 08:00);
- vă cere acordul să configureze **permisiunile** necesare, ca rulările programate să meargă complet automat, fără să vă mai ceară aprobări;
- generează și primul raport, cu noutățile din ultimele 7 zile.

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
- Sursele și metoda de acces a fiecăreia: [skills/contaChangeSkill/references/surse.md](skills/contaChangeSkill/references/surse.md).
- Formatul raportului: [skills/contaChangeSkill/references/email-template.md](skills/contaChangeSkill/references/email-template.md).
- Logica completă de rulare: [skills/contaChangeSkill/SKILL.md](skills/contaChangeSkill/SKILL.md).
