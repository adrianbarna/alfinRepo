#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transforma borderourile de ramburs Cargus / Packeta (.xlsx) in fisiere XML de
import pentru programul de contabilitate Saga (Import documente -> Incasari).

Fara dependinte externe: .xlsx e citit direct din stdlib (zipfile + ElementTree),
ca skill-ul sa mearga pe orice PC unde exista python3.

Fiecare rand de borderou e legat de factura lui din folderul de facturi (export XML
din Saga, <VFPData><c_xml>): cheia e RefExp1 = inf_suplm, iar numele (fara diacritice)
si totalul sunt dublul control. <FacturaNumar> primeste nr_iesire de pe factura.
Randurile fara factura sigura NU intra in XML, ci in raportul trimis pe e-mail.

Cerinte: Python 3.8+, doar biblioteca standard. Se porneste cu `python3` pe
macOS/Linux si cu `py -3` (sau `python`) pe Windows; in rest comenzile sunt identice
si merg la fel in bash si in PowerShell.

Utilizare:
    proceseaza.py                        # proceseaza doar fisierele noi
    proceseaza.py --dry-run              # arata ce ar face, nu scrie nimic
    proceseaza.py --folder <cale>        # ignora config.json, foloseste calea data
    proceseaza.py --reproceseaza <nume>  # forteaza un fisier deja procesat
    proceseaza.py --set-folder <cale> [--moneda RON]   # scrie config.json
    proceseaza.py --facturi <cale>       # folderul cu facturi, doar pentru rularea asta
    proceseaza.py --set-facturi <cale>   # salveaza folderul de facturi in config.json
    proceseaza.py --set-email a@b.ro,c@d.ro   # cui se trimite raportul
    proceseaza.py --arata-config         # arata configurarea curenta si iese
    proceseaza.py --fara-facturi         # nu lega facturile (FacturaNumar ramane gol)
    proceseaza.py --json                 # raport JSON in loc de text

Coduri de iesire:
    0 = a mers (posibil cu avertismente)
    1 = eroare
    2 = configurare lipsa / cale inexistenta -> skill-ul trebuie sa intrebe utilizatorul
"""

import argparse
import datetime as _dt
import json
import os
import platform
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def _radacina_proiect():
    """<proiect>/.claude/skills/<skill>/ -> <proiect>; instalat ca plugin -> None."""
    p = SKILL_ROOT.parents
    if len(p) >= 3 and p[0].name == "skills" and p[1].name == ".claude":
        return p[2]
    return None


PROJECT_ROOT = _radacina_proiect()

# Configul sta la nivel de utilizator, NU in folderul skill-ului (decizia din
# 26.08.2026): skill-ul se copiaza pe masina clientului fara nicio cale setata,
# iar prima configurare o face skill-ul config-incasari-cargus. Un config.json
# ramas langa skill (instalari vechi) are inca prioritate, ca sa nu se piarda.
CONFIG_LOCAL = SKILL_ROOT / "config.json"
CONFIG_UTILIZATOR = Path.home() / ".claude" / "incasari-saga" / "config.json"


def cale_config():
    din_mediu = os.environ.get("INCASARI_CONFIG")
    if din_mediu:
        return Path(din_mediu).expanduser()
    return CONFIG_LOCAL if CONFIG_LOCAL.exists() else CONFIG_UTILIZATOR

DIR_PROCESATE = "procesate"
JURNAL = ".procesate.json"
RAPORT_EMAIL = "ultimul-raport.txt"

CONT_CLIENT = "4111"
PREFIX_EXPLICATIE = "Incasare ramburs client"

DIR_FACTURI_IMPLICIT = "facturi"
# Diferenta borderou vs factura: pana la TOL_TACITA e rotunjire normala si tace;
# intre TOL_TACITA si TOL_MAX trece, dar avertizeaza; peste TOL_MAX nu confirma factura.
TOL_TACITA = Decimal("0.01")
TOL_MAX = Decimal("0.10")

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


# --------------------------------------------------------------------------
# Citire .xlsx din stdlib
# --------------------------------------------------------------------------

_BUILTIN_DATE_FMT = set(range(14, 23)) | set(range(45, 48))
_DATE_CHARS = re.compile(r"[yYdD]|mmm", re.UNICODE)
_EPOCH = _dt.datetime(1899, 12, 30)


def _col_index(ref):
    """'AB12' -> 27 (index 0-based al coloanei)."""
    n = 0
    for ch in ref:
        if ch.isdigit():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def _text(el):
    return "".join(el.itertext()) if el is not None else ""


def _shared_strings(z):
    try:
        raw = z.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(raw)
    return [_text(si) for si in root.findall("m:si", NS)]


def _date_styles(z):
    """Indecsii de stil (cellXfs) care reprezinta date calendaristice."""
    try:
        root = ET.fromstring(z.read("xl/styles.xml"))
    except KeyError:
        return set()
    custom = {}
    for nf in root.iter("{%s}numFmt" % NS["m"]):
        code = nf.get("formatCode", "")
        custom[int(nf.get("numFmtId"))] = bool(_DATE_CHARS.search(code))
    styles = set()
    cell_xfs = root.find("m:cellXfs", NS)
    if cell_xfs is None:
        return styles
    for i, xf in enumerate(cell_xfs.findall("m:xf", NS)):
        fmt_id = int(xf.get("numFmtId", 0))
        if fmt_id in _BUILTIN_DATE_FMT or custom.get(fmt_id):
            styles.add(i)
    return styles


def _first_sheet_path(z):
    try:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    except KeyError:
        return "xl/worksheets/sheet1.xml"
    targets = {r.get("Id"): r.get("Target") for r in rels}
    sheets = wb.find("m:sheets", NS)
    if sheets is not None:
        for sh in sheets.findall("m:sheet", NS):
            rid = sh.get("{%s}id" % NS_R)
            target = targets.get(rid)
            if target:
                target = target.lstrip("/")
                return target if target.startswith("xl/") else "xl/" + target
    return "xl/worksheets/sheet1.xml"


def _serial_to_date(value):
    try:
        return _EPOCH + _dt.timedelta(days=float(value))
    except (TypeError, ValueError, OverflowError):
        return None


def citeste_xlsx(cale):
    """Returneaza list[list] — randurile foii, celulele lipsa devin None."""
    with zipfile.ZipFile(cale) as z:
        shared = _shared_strings(z)
        date_styles = _date_styles(z)
        sheet = ET.fromstring(z.read(_first_sheet_path(z)))

    randuri = []
    data_el = sheet.find("m:sheetData", NS)
    if data_el is None:
        return randuri

    for row in data_el.findall("m:row", NS):
        celule = {}
        for c in row.findall("m:c", NS):
            ref = c.get("r") or ""
            idx = _col_index(ref) if ref else len(celule)
            tip = c.get("t")
            v = c.find("m:v", NS)
            if tip == "s":
                val = shared[int(v.text)] if v is not None and v.text else None
            elif tip == "inlineStr":
                val = _text(c.find("m:is", NS)) or None
            elif tip in ("str", "e"):
                val = v.text if v is not None else None
            else:
                val = v.text if v is not None else None
                if val is not None:
                    stil = c.get("s")
                    if stil is not None and int(stil) in date_styles:
                        d = _serial_to_date(val)
                        if d is not None:
                            val = d
                    else:
                        try:
                            f = float(val)
                            val = int(f) if f.is_integer() else f
                        except ValueError:
                            pass
            if val is not None and val != "":
                celule[idx] = val
        randuri.append(
            [celule.get(i) for i in range(max(celule) + 1)] if celule else []
        )
    return randuri


# --------------------------------------------------------------------------
# Normalizari
# --------------------------------------------------------------------------

def ca_text(v):
    if v is None:
        return ""
    if isinstance(v, _dt.datetime):
        return v.strftime("%d.%m.%Y")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def normalizeaza_data(v):
    """-> 'dd.mm.yyyy' sau None daca nu se poate interpreta."""
    if isinstance(v, _dt.datetime):
        return v.strftime("%d.%m.%Y")
    s = ca_text(v)
    if not s:
        return None
    s = s.split(" ")[0]
    m = re.match(r"^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$", s)
    if m:
        return "%02d.%02d.%s" % (int(m.group(1)), int(m.group(2)), m.group(3))
    m = re.match(r"^(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})$", s)
    if m:
        return "%02d.%02d.%s" % (int(m.group(3)), int(m.group(2)), m.group(1))
    d = _serial_to_date(s) if re.match(r"^\d+(\.\d+)?$", s) else None
    return d.strftime("%d.%m.%Y") if d else None


def normalizeaza_suma(v):
    """'268,89' / '1.234,56' / 268.89 -> Decimal cu 2 zecimale, sau None."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        d = Decimal(str(v))
    else:
        s = str(v).strip().replace("\xa0", "").replace(" ", "")
        s = re.sub(r"(?i)(lei|ron|eur|huf)$", "", s).strip()
        if not s:
            return None
        neg = s.startswith("-")
        s = s.lstrip("+-")
        if "," in s and "." in s:
            # ultimul separator e cel zecimal
            s = s.replace(".", "") if s.rindex(",") > s.rindex(".") else s.replace(",", "")
        s = s.replace(",", ".")
        if s.count(".") > 1:  # 1.234.567 -> separatori de mii
            s = s.replace(".", "")
        try:
            d = Decimal(s)
        except InvalidOperation:
            return None
        if neg:
            d = -d
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# Facturi: export XML din Saga (<VFPData><c_xml>...), de obicei Windows-1252
# --------------------------------------------------------------------------

_DECL = re.compile(r"^\s*<\?xml[^>]*\?>", re.IGNORECASE)
_ENC = re.compile(rb"""encoding\s*=\s*["']([\w.-]+)["']""", re.IGNORECASE)

# Diacriticele romanesti cu virgula/sedila nu se descompun prin NFKD, deci le dam explicit.
_DIACRITICE = {
    "\u0219": "s", "\u015f": "s", "\u0218": "S", "\u015e": "S",
    "\u021b": "t", "\u0163": "t", "\u021a": "T", "\u0162": "T",
}

# Forme juridice si zgomot: nu spun nimic despre identitatea persoanei.
_CUVINTE_IGNORATE = {
    "srl", "srld", "sa", "sca", "snc", "pfa", "ii", "if", "sc", "s", "r", "l",
    "persoana", "fizica", "autorizata", "intreprindere", "individuala",
}


def fara_diacritice(s):
    s = "".join(_DIACRITICE.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def cheie_nume(s):
    """'Marian Ghita SRL' -> frozenset{'marian','ghita'} (ordinea nu conteaza)."""
    curat = re.sub(r"[^a-z0-9]+", " ", fara_diacritice(ca_text(s)).lower())
    return frozenset(t for t in curat.split() if t and t not in _CUVINTE_IGNORATE)


def nume_se_potrivesc(a, b):
    """Egale sau unul inclus in celalalt ('Pavel Adriana' ~ 'PAVEL ADRIANA ANA PFA')."""
    ka, kb = cheie_nume(a), cheie_nume(b)
    if not ka or not kb:
        return False
    return ka <= kb or kb <= ka


def _decodeaza(brut):
    codecuri = []
    m = _ENC.search(brut[:200])
    if m:
        codecuri.append(m.group(1).decode("ascii", "ignore"))
    codecuri += ["utf-8", "cp1252"]
    for c in codecuri:
        try:
            return brut.decode(c)
        except (UnicodeDecodeError, LookupError):
            continue
    return brut.decode("cp1252", "replace")


def citeste_facturi_xml(cale):
    """-> list[dict]: nr_iesire, denumire, total, inf_suplm, data, sursa."""
    # expat nu stie Windows-1252: decodam noi si scoatem declaratia de encoding.
    root = ET.fromstring(_DECL.sub("", _decodeaza(cale.read_bytes()), count=1))
    facturi = []
    for f in root.iter("c_xml"):
        def camp(tag):
            e = f.find(tag)
            return (e.text or "").strip() if e is not None and e.text else ""
        nr = camp("nr_iesire")
        if not nr:
            continue
        facturi.append({
            "nr_iesire": nr,
            "denumire": camp("denumire"),
            "total": normalizeaza_suma(camp("total")),
            "inf_suplm": camp("inf_suplm"),
            "data": camp("data"),
            "sursa": cale.name,
        })
    return facturi


def incarca_facturi(folder):
    """Indexeaza toate exporturile din folder (si subfoldere) dupa inf_suplm si nume.

    Exporturile se suprapun: unul poate acoperi mai multe luni, iar aceeasi factura
    poate aparea in doua. Castiga exportul a carui perioada se termina mai tarziu;
    daca versiunile difera, se semnaleaza - o factura corectata in tacere e mai rea
    decat una raportata.
    """
    idx = {"dupa_inf": {}, "dupa_nume": {}, "numar": 0, "fisiere": [], "erori": [],
           "de_la": None, "pana_la": None, "corectate": []}

    exporturi = []
    for cale in sorted(folder.rglob("*")):
        if not cale.is_file() or cale.suffix.lower() != ".xml" or cale.name.startswith("~$"):
            continue
        try:
            facturi = citeste_facturi_xml(cale)
        except Exception as exc:
            idx["erori"].append("%s: %s" % (cale.name, exc))
            continue
        date = sorted(f["data"] for f in facturi if f["data"])
        exporturi.append({"nume": cale.name, "facturi": facturi,
                          "de_la": date[0] if date else "",
                          "pana_la": date[-1] if date else ""})

    idx["fisiere"] = [e["nume"] for e in exporturi]
    exporturi.sort(key=lambda e: (e["pana_la"], e["nume"]))

    vazute = {}
    for e in exporturi:
        for f in e["facturi"]:
            veche = vazute.get(f["nr_iesire"])
            if veche is not None and (veche["total"] != f["total"]
                                      or veche["denumire"] != f["denumire"]):
                idx["corectate"].append(
                    "factura %s difera intre exporturi: %s '%s' in %s -> %s '%s' in %s "
                    "(se foloseste a doua)"
                    % (f["nr_iesire"], veche["total"], veche["denumire"], veche["sursa"],
                       f["total"], f["denumire"], f["sursa"]))
            vazute[f["nr_iesire"]] = f

    for f in vazute.values():
        if f["inf_suplm"]:
            idx["dupa_inf"].setdefault(f["inf_suplm"], []).append(f)
        k = cheie_nume(f["denumire"])
        if k:
            idx["dupa_nume"].setdefault(k, []).append(f)

    toate = [f["data"] for f in vazute.values() if f["data"]]
    if toate:
        idx["de_la"], idx["pana_la"] = min(toate), max(toate)
    idx["numar"] = len(vazute)
    return idx


def perioada_facturi(idx):
    """'01.05.2026-31.07.2026' sau '' daca nu se stie."""
    if not idx or not idx.get("de_la"):
        return ""
    return "%s-%s" % (normalizeaza_data(idx["de_la"]) or idx["de_la"],
                      normalizeaza_data(idx["pana_la"]) or idx["pana_la"])


def _dupa_nume(dest, idx):
    k = cheie_nume(dest)
    if not k:
        return []
    gasite = list(idx["dupa_nume"].get(k, []))
    if gasite:
        return gasite
    # nume incomplet pe colet fata de factura (persoana fizica vs PFA cu nume lung)
    return [f for kf, lst in idx["dupa_nume"].items() if k < kf for f in lst]


def alege_factura(ref, dest, suma, idx):
    """-> (factura | None, suma_de_scris, avertismente, motiv_esec | None).

    Cheia e RefExp1 = inf_suplm; numele si totalul doar confirma. Cautarea dupa nume
    e strict rezerva, pentru cand RefExp1 nu duce nicaieri - altfel un omonim cu
    aceeasi suma ar face ambigua o potrivire deja sigura. Totalul departajeaza cand
    raman mai multi candidati (tipic: factura initiala plus stornarea ei).

    `total` de pe factura e in valuta facturii, deci comparatia cu suma din borderou
    e directa, oricare ar fi valuta folderului (confirmat de client, 25.08.2026).
    """
    av = []

    def dif(f):
        return abs(f["total"] - suma) if f["total"] is not None else None

    def filtreaza(candidati):
        buni = [f for f in candidati if dif(f) is not None and dif(f) <= TOL_MAX]
        if len(buni) > 1:
            exacte = [f for f in buni if f["total"] == suma]
            if len(exacte) == 1:
                return exacte
        return buni

    dupa_ref = idx["dupa_inf"].get(ref, [])
    buni, sursa = filtreaza(dupa_ref), "RefExp1"
    if len(buni) != 1:
        dupa_nume = [f for f in _dupa_nume(dest, idx) if not any(f is x for x in dupa_ref)]
        alternativ = filtreaza(dupa_nume)
        if len(alternativ) == 1 and len(buni) != 1:
            buni, sursa = alternativ, "nume"
        elif not buni:
            buni = alternativ
            sursa = "nume"

    if not buni:
        if dupa_ref:
            detaliu = ", ".join("%s = %s" % (f["nr_iesire"], f["total"]) for f in dupa_ref[:4])
            return None, suma, av, ("totalul nu confirma factura de pe RefExp1 %s "
                                    "(borderou %s; gasite: %s)" % (ref, suma, detaliu))
        return None, suma, av, "nicio factura pe RefExp1 %s si niciuna pe numele '%s'" % (ref, dest)
    if len(buni) > 1:
        return None, suma, av, "mai multe facturi se potrivesc: %s" % ", ".join(
            f["nr_iesire"] for f in buni)

    f = buni[0]
    if sursa == "nume":
        av.append("factura %s gasita doar dupa nume: RefExp1 %s nu duce la o factura "
                  "confirmata de total" % (f["nr_iesire"], ref))
    stornuri = [x["nr_iesire"] for x in dupa_ref
                if x is not f and x["total"] is not None and x["total"] < 0]
    if stornuri:
        av.append("RefExp1 %s are si factura de storno (%s) - de verificat"
                  % (ref, ", ".join(stornuri)))
    if not nume_se_potrivesc(dest, f["denumire"]):
        av.append("numele difera: borderou '%s' vs factura %s '%s'"
                  % (dest, f["nr_iesire"], f["denumire"]))

    # In XML intra suma de pe factura, ca factura sa se stinga exact.
    suma_finala = f["total"] if f["total"] is not None else suma
    d = dif(f)
    if d is not None and d > TOL_TACITA:
        av.append("suma luata din factura %s: borderou %s -> factura %s (diferenta %s)"
                  % (f["nr_iesire"], suma, f["total"], d))
    return f, suma_finala, av, None


# --------------------------------------------------------------------------
# Recunoasterea formatului
# --------------------------------------------------------------------------

COLOANE_CERUTE = ("awb", "destinatar", "suma", "data op", "refexp1")
COLOANE_EMAG = ("order id", "fraction value", "client name")


def gaseste_header(randuri):
    """-> (index_rand, {nume_coloana_lower: index_coloana}) sau (None, None)."""
    for i, rand in enumerate(randuri[:5]):
        nume = {ca_text(v).lower(): j for j, v in enumerate(rand) if ca_text(v)}
        if "awb" in nume and "destinatar" in nume:
            return i, nume
    return None, None


def pare_emag(randuri):
    for rand in randuri[:5]:
        nume = {ca_text(v).lower() for v in rand if ca_text(v)}
        if sum(1 for c in COLOANE_EMAG if c in nume) >= 2:
            return True
    return False


# --------------------------------------------------------------------------
# Conversia unui borderou
# --------------------------------------------------------------------------

def proceseaza_borderou(cale, moneda, cont, facturi=None):
    """-> dict cu linii, avertismente, randuri sarite, totaluri.

    `facturi` = indexul din incarca_facturi(); None inseamna fara legare de facturi
    (FacturaNumar ramane gol si niciun rand nu e sarit din lipsa de factura).
    """
    rez = {
        "fisier": cale.name,
        "linii": [],
        "avertismente": [],
        "sarite": [],
        "total": Decimal("0.00"),
        "total_sarit": Decimal("0.00"),
        "pe_data": {},
        "corectate": 0,
        "corectie": Decimal("0.00"),
        "eroare": None,
    }

    try:
        randuri = citeste_xlsx(cale)
    except Exception as exc:  # zip corupt, fisier deschis in Excel etc.
        rez["eroare"] = "nu am putut citi fisierul: %s" % exc
        return rez

    idx_header, nume = gaseste_header(randuri)
    if idx_header is None:
        rez["eroare"] = (
            "format eMAG, nesuportat de acest skill (vezi mappings.md)"
            if pare_emag(randuri)
            else "format nerecunoscut: nu am gasit un rand de header cu 'Awb' si 'Destinatar'"
        )
        return rez

    lipsa = [c for c in COLOANE_CERUTE if c not in nume]
    if lipsa:
        rez["eroare"] = "lipsesc coloanele: %s" % ", ".join(lipsa)
        return rez

    c_dest, c_suma = nume["destinatar"], nume["suma"]
    c_data, c_ref = nume["data op"], nume["refexp1"]

    def celula(rand, idx):
        return rand[idx] if idx < len(rand) else None

    vazute = {}
    for i, rand in enumerate(randuri[idx_header + 1:], start=idx_header + 2):
        if not rand or all(v is None or ca_text(v) == "" for v in rand):
            continue

        data = normalizeaza_data(celula(rand, c_data))
        suma = normalizeaza_suma(celula(rand, c_suma))
        dest = ca_text(celula(rand, c_dest))
        ref = ca_text(celula(rand, c_ref))

        lipsuri = []
        if not data:
            lipsuri.append("Data OP")
        if suma is None:
            lipsuri.append("Suma")
        if not dest:
            lipsuri.append("Destinatar")
        if not ref:
            lipsuri.append("RefExp1")
        if lipsuri:
            rez["sarite"].append({"rand": i, "motiv": "lipseste " + ", ".join(lipsuri),
                                  "destinatar": dest, "refexp1": ref,
                                  "suma": str(suma) if suma is not None else "",
                                  "data": data or ""})
            if suma is not None:
                rez["total_sarit"] += suma
            continue

        if suma <= 0:
            rez["avertismente"].append(
                "randul %d: suma %s nu e pozitiva (%s)" % (i, suma, dest))
        if ref in vazute:
            rez["avertismente"].append(
                "randul %d: RefExp1 %s apare si pe randul %d" % (i, ref, vazute[ref]))
        else:
            vazute[ref] = i

        factura_nr = ""
        if facturi is not None:
            factura, suma_xml, av, motiv = alege_factura(ref, dest, suma, facturi)
            for a in av:
                rez["avertismente"].append("randul %d: %s" % (i, a))
            if factura is None:
                rez["sarite"].append({"rand": i, "motiv": motiv,
                                      "destinatar": dest, "refexp1": ref,
                                      "suma": str(suma), "data": data})
                rez["total_sarit"] += suma
                continue
            factura_nr = factura["nr_iesire"]
            if suma_xml != suma:
                rez["corectate"] += 1
                rez["corectie"] += suma_xml - suma
                suma = suma_xml

        rez["linii"].append({"rand": i, "Data": data, "Numar": ref, "Suma": suma,
                             "Cont": cont, "Explicatie": "%s - %s" % (PREFIX_EXPLICATIE, dest),
                             "FacturaID": ref, "FacturaNumar": factura_nr, "Moneda": moneda})
        rez["total"] += suma
        rez["pe_data"][data] = rez["pe_data"].get(data, Decimal("0.00")) + suma

    # Multe randuri fara nicio factura, cu borderoul in afara perioadei acoperite:
    # cauza probabila e un export lipsa, nu sute de potriviri ratate.
    negasite = [x for x in rez["sarite"] if x["motiv"].startswith("nicio factura")]
    if facturi is not None and negasite and len(negasite) >= max(5, (len(rez["linii"]) + len(negasite)) // 5):
        rez["avertismente"].insert(0, (
            "%d randuri nu au nicio factura, iar exporturile acopera %s: "
            "probabil lipseste un export de facturi"
            % (len(negasite), perioada_facturi(facturi) or "o perioada necunoscuta")))

    # RefExp1 in afara tiparului dominant de lungime
    lungimi = {}
    for l in rez["linii"]:
        lungimi.setdefault(len(l["Numar"]), []).append(l)
    if len(lungimi) > 1:
        dominanta = max(lungimi, key=lambda k: len(lungimi[k]))
        for lung, grup in sorted(lungimi.items()):
            if lung == dominanta:
                continue
            for l in grup:
                rez["avertismente"].append(
                    "randul %d: RefExp1 '%s' are %d caractere, restul au %d"
                    % (l["rand"], l["Numar"], lung, dominanta))
    return rez


def construieste_xml(linii):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<Incasari>"]
    for l in linii:
        out.append("  <Linie>")
        out.append("    <Data>%s</Data>" % escape_xml(l["Data"]))
        out.append("    <Numar>%s</Numar>" % escape_xml(l["Numar"]))
        out.append("    <Suma>%s</Suma>" % l["Suma"])
        out.append("    <Cont>%s</Cont>" % l["Cont"])
        out.append("    <ContClient>%s</ContClient>" % CONT_CLIENT)
        out.append("    <Explicatie>%s</Explicatie>" % escape_xml(l["Explicatie"]))
        out.append("    <FacturaID>%s</FacturaID>" % escape_xml(l["FacturaID"]))
        out.append("    <FacturaNumar>%s</FacturaNumar>"
                   % escape_xml(l.get("FacturaNumar", "")))
        out.append("    <CodFiscal></CodFiscal>")
        out.append("    <Moneda>%s</Moneda>" % l["Moneda"])
        out.append("  </Linie>")
    out.append("</Incasari>")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# Config si jurnal
# --------------------------------------------------------------------------

def cont_pentru(moneda):
    return "5125" if moneda.upper() == "RON" else "5126"


def rezolva(cale):
    """Cale din config -> Path existent, sau None."""
    p = Path(cale).expanduser()
    if not p.is_absolute() and PROJECT_ROOT is not None:
        candidat = (PROJECT_ROOT / p).resolve()
        if candidat.is_dir():
            return candidat
    return p.resolve() if p.is_dir() else None


def stocheaza(cale):
    """Path -> forma de salvat in config (relativa la proiect daca se poate)."""
    p = Path(cale).expanduser().resolve()
    if PROJECT_ROOT is not None:
        try:
            return str(p.relative_to(PROJECT_ROOT))
        except ValueError:
            pass
    return str(p)


def _consola_utf8():
    """Iesirea in UTF-8 si fara crash: consola Windows (cp1252/cp1250) nu stie s, t."""
    if os.environ.get("PYTHONIOENCODING"):
        return
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            try:
                flux.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _scrie(cale, text):
    """Text UTF-8 cu LF, identic pe orice sistem (write_text ar pune CRLF pe Windows)."""
    with open(cale, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def citeste_config():
    cale = cale_config()
    if not cale.exists():
        return None
    try:
        return json.loads(cale.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def scrie_config(cfg):
    cale = cale_config()
    cale.parent.mkdir(parents=True, exist_ok=True)
    _scrie(cale, json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    return cale


def rezolva_facturi(cfg, arg):
    """-> (Path | None, sursa_textuala). Ordinea: --facturi, config, 'facturi/'."""
    for cale, sursa in ((arg, "--facturi"),
                        ((cfg or {}).get("facturi"), "config.json"),
                        (DIR_FACTURI_IMPLICIT, "implicit")):
        if not cale:
            continue
        gasit = rezolva(cale)
        if gasit is not None:
            return gasit, sursa
        if sursa != "implicit":
            return None, sursa
    return None, "implicit"


def normalizeaza_email(brut):
    """'a@b.ro, c@d.ro' sau lista -> lista de adrese curatate."""
    if isinstance(brut, str):
        brut = re.split(r"[,;\s]+", brut)
    return [a.strip() for a in (brut or []) if a and a.strip()]


def citeste_jurnal(dir_procesate):
    f = dir_procesate / JURNAL
    if not f.exists():
        return {}
    try:
        date = json.loads(f.read_text(encoding="utf-8"))
        return date.get("procesate", {})
    except (json.JSONDecodeError, OSError):
        return {}


def scrie_jurnal(dir_procesate, procesate):
    _scrie(dir_procesate / JURNAL,
           json.dumps({"procesate": procesate}, ensure_ascii=False, indent=2) + "\n")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def eroare_config(mesaj, ca_json):
    date = {"stare": "config_lipsa", "mesaj": mesaj}
    print(json.dumps(date, ensure_ascii=False, indent=2) if ca_json else mesaj)
    return 2


def main(argv=None):
    _consola_utf8()
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", help="proceseaza aceasta cale, ignorand config.json")
    ap.add_argument("--moneda", default="RON", help="valuta folderului (implicit RON)")
    ap.add_argument("--set-folder", dest="set_folder",
                    help="salveaza calea in config.json si iese")
    ap.add_argument("--facturi", help="folderul cu facturi, doar pentru rularea asta")
    ap.add_argument("--set-facturi", dest="set_facturi",
                    help="salveaza folderul de facturi in config.json si iese")
    ap.add_argument("--set-email", dest="set_email",
                    help="adresele pentru raport, separate prin virgula; iese dupa salvare")
    ap.add_argument("--arata-config", action="store_true", dest="arata_config",
                    help="arata configurarea curenta si iese")
    ap.add_argument("--fara-facturi", action="store_true", dest="fara_facturi",
                    help="nu lega facturile (FacturaNumar ramane gol, nimic nu se sare)")
    ap.add_argument("--reproceseaza", action="append", default=[],
                    metavar="NUME", help="forteaza un fisier deja procesat")
    ap.add_argument("--dry-run", action="store_true", help="nu scrie nimic pe disc")
    ap.add_argument("--json", action="store_true", dest="ca_json",
                    help="raport JSON in loc de text")
    a = ap.parse_args(argv)

    moneda = a.moneda.upper()

    if a.arata_config:
        cale = cale_config()
        cfg = citeste_config() or {}
        sistem = "%s (%s)" % (platform.system() or "?", sys.platform)
        if a.ca_json:
            print(json.dumps({"python": platform.python_version(), "sistem": sistem,
                              "config": str(cale), "exista": cale.exists(),
                              "foldere": cfg.get("foldere", []),
                              "facturi": cfg.get("facturi"),
                              "email": normalizeaza_email(cfg.get("email"))},
                             ensure_ascii=False, indent=2))
            return 0
        print("Python %s pe %s" % (platform.python_version(), sistem))
        print("Config: %s%s" % (cale, "" if cale.exists() else " (nu exista inca)"))
        if not cfg.get("foldere"):
            print("Borderouri: neconfigurat -> --set-folder <cale> [--moneda RON]")
        for f in cfg.get("foldere", []):
            print("Borderouri %s (cont %s): %s%s"
                  % (f.get("moneda", "?"), f.get("cont", "?"), f.get("cale"),
                     "" if rezolva(f.get("cale", "")) else "  ! FOLDERUL NU EXISTA"))
        if cfg.get("facturi"):
            print("Facturi: %s%s"
                  % (cfg["facturi"],
                     "" if rezolva(cfg["facturi"]) else "  ! FOLDERUL NU EXISTA"))
        else:
            print("Facturi: neconfigurat -> --set-facturi <cale>")
        adrese = normalizeaza_email(cfg.get("email"))
        print("E-mail: %s" % (", ".join(adrese) if adrese
                              else "neconfigurat -> --set-email a@b.ro,c@d.ro"))
        return 0

    if a.set_facturi:
        p = Path(a.set_facturi).expanduser()
        if not p.is_absolute() and PROJECT_ROOT is not None and (PROJECT_ROOT / p).is_dir():
            p = PROJECT_ROOT / p
        if not p.is_dir():
            print("Calea nu exista sau nu e un folder: %s" % a.set_facturi, file=sys.stderr)
            return 1
        cfg = citeste_config() or {"foldere": []}
        cfg["facturi"] = stocheaza(p)
        unde = scrie_config(cfg)
        print("Salvat in %s: facturi -> %s" % (unde, cfg["facturi"]))
        return 0

    if a.set_email:
        adrese = normalizeaza_email(a.set_email)
        if not adrese:
            print("Nu am primit nicio adresa de e-mail.", file=sys.stderr)
            return 1
        cfg = citeste_config() or {"foldere": []}
        cfg["email"] = adrese
        unde = scrie_config(cfg)
        print("Salvat in %s: raportul se trimite catre %s" % (unde, ", ".join(adrese)))
        return 0

    if a.set_folder:
        p = Path(a.set_folder).expanduser()
        if not p.is_absolute() and PROJECT_ROOT is not None and (PROJECT_ROOT / p).is_dir():
            p = PROJECT_ROOT / p
        if not p.is_dir():
            print("Calea nu exista sau nu e un folder: %s" % a.set_folder, file=sys.stderr)
            return 1
        cfg = citeste_config() or {"foldere": []}
        intrare = {"cale": stocheaza(p), "moneda": moneda, "cont": cont_pentru(moneda)}
        cfg["foldere"] = [f for f in cfg.get("foldere", [])
                          if f.get("moneda", "").upper() != moneda] + [intrare]
        unde = scrie_config(cfg)
        print("Salvat in %s: %s -> %s (cont %s)"
              % (unde, intrare["cale"], moneda, intrare["cont"]))
        return 0

    cfg = citeste_config()
    if a.folder:
        foldere = [{"cale": a.folder, "moneda": moneda, "cont": cont_pentru(moneda)}]
    else:
        if not cfg or not cfg.get("foldere"):
            return eroare_config(
                "Nu stiu unde tii borderourile. Intreaba utilizatorul si ruleaza "
                "apoi: proceseaza.py --set-folder <cale>", a.ca_json)
        foldere = cfg["foldere"]

    facturi = None
    dir_facturi = None
    if not a.fara_facturi:
        dir_facturi, sursa_facturi = rezolva_facturi(cfg, a.facturi)
        if dir_facturi is None:
            return eroare_config(
                "Nu gasesc folderul cu facturi (cautat: %s). Intreaba utilizatorul unde "
                "tine exportul XML de facturi din Saga si ruleaza: "
                "proceseaza.py --set-facturi <cale>" % sursa_facturi, a.ca_json)
        facturi = incarca_facturi(dir_facturi)
        if not facturi["numar"]:
            motiv = ("niciunul dintre XML-uri nu s-a putut citi (%s)"
                     % "; ".join(facturi["erori"]) if facturi["erori"]
                     else "nu contine niciun XML cu facturi")
            return eroare_config(
                "Folderul de facturi %s: %s. Intreaba utilizatorul unde e exportul "
                "corect si ruleaza: proceseaza.py --set-facturi <cale>"
                % (dir_facturi, motiv), a.ca_json)

    adrese = normalizeaza_email((cfg or {}).get("email"))
    raport = {"stare": "ok", "dry_run": a.dry_run, "foldere": [],
              "facturi": ({"cale": str(dir_facturi), "numar": facturi["numar"],
                           "fisiere": facturi["fisiere"], "erori": facturi["erori"],
                           "perioada": perioada_facturi(facturi),
                           "corectate": facturi["corectate"]}
                          if facturi is not None else None),
              "email": {"catre": adrese, "neconfigurat": not adrese}}
    lipsa = []

    for intrare in foldere:
        folder = rezolva(intrare["cale"])
        if folder is None:
            lipsa.append(intrare["cale"])
            continue
        mon = intrare.get("moneda", "RON").upper()
        cont = intrare.get("cont") or cont_pentru(mon)
        dir_procesate = folder / DIR_PROCESATE
        jurnal = citeste_jurnal(dir_procesate)

        r_folder = {"cale": str(folder), "moneda": mon, "cont": cont,
                    "procesate": [], "sarite_deja": [], "esuate": []}

        xlsx = sorted(p for p in folder.glob("*.xlsx") if not p.name.startswith("~$"))
        for cale in xlsx:
            if cale.name in jurnal and cale.name not in a.reproceseaza:
                r_folder["sarite_deja"].append(cale.name)
                continue

            rez = proceseaza_borderou(cale, mon, cont, facturi)
            if rez["eroare"]:
                r_folder["esuate"].append({"fisier": cale.name, "motiv": rez["eroare"]})
                continue
            if not rez["linii"]:
                # Nimic de importat, dar randurile sarite trebuie totusi raportate.
                r_folder["esuate"].append({
                    "fisier": cale.name,
                    "motiv": ("niciun rand nu a putut fi legat de o factura"
                              if rez["sarite"] else "niciun rand valid de incasare"),
                    "sarite": rez["sarite"],
                    "total_sarit": str(rez["total_sarit"]),
                    "avertismente": rez["avertismente"],
                    "moneda": mon,
                })
                continue

            # Numele borderoului, dar fara spatii (cerinta clientului, 31.08.2026).
            iesire = dir_procesate / (re.sub(r"\s+", "_", cale.stem) + ".xml")
            if not a.dry_run:
                dir_procesate.mkdir(parents=True, exist_ok=True)
                _scrie(iesire, construieste_xml(rez["linii"]))
                jurnal[cale.name] = {
                    "procesat_la": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "xml": iesire.name,
                    "linii": len(rez["linii"]),
                    "total": str(rez["total"]),
                }
                scrie_jurnal(dir_procesate, jurnal)

            r_folder["procesate"].append({
                "fisier": cale.name,
                "xml": str(iesire),
                "linii": len(rez["linii"]),
                "total": str(rez["total"]),
                "pe_data": {k: str(v) for k, v in sorted(rez["pe_data"].items())},
                "avertismente": rez["avertismente"],
                "sarite": rez["sarite"],
                "total_sarit": str(rez["total_sarit"]),
                "corectate": rez["corectate"],
                "corectie": str(rez["corectie"]),
            })

        raport["foldere"].append(r_folder)

    if lipsa and not raport["foldere"]:
        return eroare_config(
            "Folderul configurat nu exista: %s. Intreaba utilizatorul unde tine acum "
            "borderourile si ruleaza: proceseaza.py --set-folder <cale>"
            % ", ".join(lipsa), a.ca_json)
    if lipsa:
        raport["foldere_lipsa"] = lipsa

    noi = [p for f in raport["foldere"] for p in f["procesate"]]
    de_semnalat = [e for f in raport["foldere"] for e in f["esuate"] if e.get("sarite")]
    if noi or de_semnalat:
        raport["email"]["subiect"] = subiect_email(raport)
        raport["email"]["corp"] = corp_email(raport)
        if not a.dry_run:
            for f in raport["foldere"]:
                if f["procesate"] or any(e.get("sarite") for e in f["esuate"]):
                    cale_raport = Path(f["cale"]) / DIR_PROCESATE / RAPORT_EMAIL
                    cale_raport.parent.mkdir(parents=True, exist_ok=True)
                    _scrie(cale_raport, raport["email"]["corp"])
                    f["raport"] = str(cale_raport)

    if a.ca_json:
        print(json.dumps(raport, ensure_ascii=False, indent=2))
    else:
        print(text_raport(raport))
    return 0


def _sarite_din(raport):
    for f in raport["foldere"]:
        for p in f["procesate"] + [e for e in f["esuate"] if e.get("sarite")]:
            yield p


def subiect_email(raport):
    fisiere = [p["fisier"] for p in _sarite_din(raport)]
    sarite = sum(len(p["sarite"]) for p in _sarite_din(raport))
    coada = " - %d randuri fara factura" % sarite if sarite else " - fara probleme"
    return "Incasari Saga: %s%s" % (", ".join(fisiere), coada)


def _detalii_sarite(p, moneda):
    r = []
    if p.get("sarite"):
        r.append("")
        r.append("  NU AU INTRAT IN XML - %d randuri, %s %s de verificat manual:"
                 % (len(p["sarite"]), p["total_sarit"], moneda))
        for x in p["sarite"]:
            r.append("    randul %s | %s | %s | %s %s"
                     % (x["rand"], x.get("data") or "?", x["destinatar"] or "?",
                        x.get("suma") or "?", moneda))
            r.append("      RefExp1 %s: %s" % (x["refexp1"] or "-", x["motiv"]))
    if p.get("avertismente"):
        r.append("")
        r.append("  De verificat (au intrat totusi in XML):")
        for w in p["avertismente"]:
            r.append("    - %s" % w)
    return r


def corp_email(raport):
    """Textul raportului: ce a intrat in XML si, mai ales, ce NU a intrat."""
    r = []
    if raport["dry_run"]:
        r.append("MOD DE PROBA (--dry-run): nu s-a scris nimic pe disc.\n")
    fact = raport.get("facturi")
    if fact:
        r.append("Facturi citite: %d din %s (%s), acoperind %s."
                 % (fact["numar"], fact["cale"], ", ".join(fact["fisiere"]) or "-",
                    fact["perioada"] or "o perioada necunoscuta"))
        for e in fact["erori"]:
            r.append("  ATENTIE fisier de facturi necitit: %s" % e)
        for c in fact["corectate"]:
            r.append("  ATENTIE %s" % c)
    else:
        r.append("Rulare fara legarea facturilor: <FacturaNumar> a ramas gol peste tot.")
    r.append("")

    for f in raport["foldere"]:
        for p in f["procesate"]:
            r.append("%s -> %s" % (p["fisier"], Path(p["xml"]).name))
            r.append("  %d linii importabile, total %s %s"
                     % (p["linii"], p["total"], f["moneda"]))
            if p.get("corectate"):
                r.append("  la %d linii suma vine de pe factura, nu din borderou "
                         "(diferenta totala %s %s)"
                         % (p["corectate"], p["corectie"], f["moneda"]))
            if len(p["pe_data"]) > 1:
                r.append("  pe data: " + ", ".join(
                    "%s = %s" % (d, s) for d, s in p["pe_data"].items()))

            r.extend(_detalii_sarite(p, f["moneda"]))
            r.append("")

        for e in f["esuate"]:
            r.append("NEPROCESAT %s: %s" % (e["fisier"], e["motiv"]))
            if e.get("sarite"):
                r.extend(_detalii_sarite(e, e.get("moneda", f["moneda"])))
                r.append("  Fisierul NU e marcat ca procesat: se reia automat dupa ce "
                         "adaugi facturile lipsa.")
            r.append("")
    for c in raport.get("foldere_lipsa", []):
        r.append("Folder configurat inexistent: %s" % c)
    return "\n".join(r).rstrip() + "\n"


def text_raport(raport):
    r = []
    if raport["dry_run"]:
        r.append("MOD DE PROBA (--dry-run): nu s-a scris nimic pe disc.\n")
    fact = raport.get("facturi")
    if fact:
        r.append("Facturi: %d din %s (%s), acoperind %s"
                 % (fact["numar"], fact["cale"], ", ".join(fact["fisiere"]) or "-",
                    fact["perioada"] or "o perioada necunoscuta"))
        for e in fact["erori"]:
            r.append("  ! fisier de facturi necitit: %s" % e)
        for c in fact["corectate"]:
            r.append("  ! %s" % c)
    else:
        r.append("Facturi: nelegate (--fara-facturi), FacturaNumar ramane gol")
    for f in raport["foldere"]:
        r.append("Folder: %s  [%s, cont %s]" % (f["cale"], f["moneda"], f["cont"]))
        if not f["procesate"]:
            r.append("  Niciun borderou nou.")
        for p in f["procesate"]:
            r.append("  + %s -> %s" % (p["fisier"], Path(p["xml"]).name))
            r.append("      %d linii, total %s %s" % (p["linii"], p["total"], f["moneda"]))
            if p.get("corectate"):
                r.append("      %d linii cu suma de pe factura (diferenta %s %s)"
                         % (p["corectate"], p["corectie"], f["moneda"]))
            if len(p["pe_data"]) > 1:
                r.append("      pe data: " + ", ".join(
                    "%s = %s" % (d, s) for d, s in p["pe_data"].items()))
            for s in p["sarite"]:
                r.append("      SARIT randul %s: %s (%s)"
                         % (s["rand"], s["motiv"], s["destinatar"] or "?"))
            if p["sarite"]:
                r.append("      total nescris din randurile sarite: %s" % p["total_sarit"])
            if p.get("raport"):
                r.append("      raport pentru e-mail: %s" % p["raport"])
            for w in p["avertismente"]:
                r.append("      ATENTIE %s" % w)
        if f["sarite_deja"]:
            r.append("  Deja procesate (sarite): %s" % ", ".join(f["sarite_deja"]))
        for e in f["esuate"]:
            r.append("  ! %s: %s" % (e["fisier"], e["motiv"]))
            if e.get("sarite"):
                r.append("      %d randuri sarite, %s %s - detaliile in raport"
                         % (len(e["sarite"]), e["total_sarit"], e.get("moneda", f["moneda"])))
    for c in raport.get("foldere_lipsa", []):
        r.append("! Folder configurat inexistent: %s" % c)
    em = raport.get("email") or {}
    if em.get("subiect"):
        if em.get("neconfigurat"):
            r.append("E-MAIL: nicio adresa configurata. Intreaba utilizatorul cui se "
                     "trimite raportul si ruleaza: proceseaza.py --set-email a@b.ro,c@d.ro")
        else:
            r.append("E-mail de trimis catre: %s" % ", ".join(em["catre"]))
        r.append("  subiect: %s" % em["subiect"])
    return "\n".join(r)


if __name__ == "__main__":
    sys.exit(main())
