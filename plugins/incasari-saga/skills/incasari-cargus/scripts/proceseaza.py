#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transforma borderourile de incasari (curieri, marketplace-uri, procesatori de plati)
in fisiere XML de import pentru programul de contabilitate Saga (Import documente ->
Incasari).

Fiecare *sursa* (Cargus, eMAG, Sameday, Trendyol, Skroutz, PlatiOnline) e un agent
separat, cu task-ul lui programat (decizia din 11.09.2026): o rulare proceseaza doar
borderourile sursei date cu --sursa si le lasa neatinse pe ale celorlalte. Formatul
se recunoaste dupa coloane, nu dupa numele fisierului (Trendyol si Skroutz au acelasi
format, "waybill"); valuta e data de folder. Fiecare sursa are jurnalul si raportul ei
in procesate/, ca task-urile sa nu-si calce evidenta unul altuia.

Fara dependinte externe: .xlsx e citit direct din stdlib (zipfile + ElementTree),
.csv cu modulul csv, ca skill-ul sa mearga pe orice PC unde exista python3.

Fiecare rand de borderou e legat de factura lui din folderul de facturi (export XML
din Saga, <VFPData><c_xml>): la Cargus cheia e RefExp1 = inf_suplm, iar numele (fara
diacritice) si totalul sunt dublul control. <FacturaNumar> primeste nr_iesire de pe
factura. Randurile fara factura sigura NU intra in XML, ci in raportul trimis pe
e-mail. O factura stinsa deja printr-un borderou (al oricarei surse, dupa jurnale) nu
se mai stinge a doua oara.

Cerinte: Python 3.8+, doar biblioteca standard. Se porneste cu `python3` pe
macOS/Linux si cu `py -3` (sau `python`) pe Windows; in rest comenzile sunt identice
si merg la fel in bash si in PowerShell.

Utilizare:
    proceseaza.py                        # proceseaza doar fisierele noi (sursa cargus)
    proceseaza.py --sursa <sursa>        # alta sursa: cargus, emag, sameday, trendyol,
                                         # skroutz, plationline
    proceseaza.py --dry-run              # arata ce ar face, nu scrie nimic
    proceseaza.py --folder <cale>        # ignora config.json, foloseste calea data; se
                                         # poate repeta, valuta vine din numele folderului
                                         # (ron / eur / huf) daca lipseste --moneda
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
import csv
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
# 26.08.2026): skill-ul se livreaza fara nicio cale setata, iar prima
# configurare o face references/configurare.md din skill. Un config.json
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

# Sursele = agentii, cate un task programat pe fiecare (decizia din 11.09.2026).
# `format` spune cum arata fisierul; doua surse pot avea acelasi format (Trendyol si
# Skroutz). O sursa fara profil implementat nu poate fi rulata inca, dar fisierele ei
# sunt recunoscute, ca sa nu fie luate drept "format nerecunoscut" de altii.
SURSE = {
    "cargus": {"eticheta": "Cargus / Packeta", "format": "cargus"},
    "emag": {"eticheta": "eMAG", "format": "emag"},
    "sameday": {"eticheta": "Sameday", "format": "sameday"},
    "trendyol": {"eticheta": "Trendyol", "format": "waybill"},
    "skroutz": {"eticheta": "Skroutz", "format": "waybill"},
    "plationline": {"eticheta": "PlatiOnline", "format": "plationline"},
}
# Sursa care raporteaza si fisierele pe care nu le recunoaste niciun format, o singura
# data pe luna, in loc de sase ori. Tot ea pastreaza numele vechi de jurnal si raport,
# ca task-ul Cargus existent sa mearga neschimbat.
SURSA_COLECTOARE = "cargus"


def jurnal_sursa(sursa):
    return JURNAL if sursa == SURSA_COLECTOARE else ".procesate-%s.json" % sursa


def raport_sursa(sursa):
    return RAPORT_EMAIL if sursa == SURSA_COLECTOARE else "ultimul-raport-%s.txt" % sursa


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


def citeste_csv(cale):
    """Returneaza list[list] ca citeste_xlsx: celulele goale devin None.

    Exportul PlatiOnline vine cu ';' si fiecare valoare intre '#' (#131.70#); marcajele
    se scot aici, ca restul scriptului sa vada doar valorile. Valorile raman text.
    """
    brut = cale.read_bytes()
    for codec in ("utf-8-sig", "cp1250", "cp1252"):
        try:
            text = brut.decode(codec)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = brut.decode("cp1252", "replace")
    linii = text.splitlines()
    mostra = "\n".join(linii[:10])
    delim = ";" if mostra.count(";") >= mostra.count(",") else ","
    randuri = []
    for rand in csv.reader(linii, delimiter=delim):
        celule = []
        for v in rand:
            v = v.strip()
            if len(v) >= 2 and v.startswith("#") and v.endswith("#"):
                v = v[1:-1].strip()
            celule.append(v if v else None)
        while celule and celule[-1] is None:
            celule.pop()
        randuri.append(celule)
    return randuri


def citeste_tabel(cale):
    """.xlsx sau .csv -> list[list]."""
    if cale.suffix.lower() == ".csv":
        return citeste_csv(cale)
    return citeste_xlsx(cale)


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


# Grecesc -> latin, dupa conventia pe care o au deja facturile din Saga ("greeklish",
# litera cu litera): Μιχάλης -> MIXALIS (χ -> x, η -> i), Θανάσης -> THANASIS, ου -> oy.
_GRECESC = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i", "θ": "th",
    "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "ks", "ο": "o", "π": "p",
    "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "f", "χ": "x", "ψ": "ps",
    "ω": "o",
}
# Chirilic bulgaresc -> latin (sistemul oficial bulgaresc), pentru clientii eMAG BG.
_CHIRILIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sht", "ъ": "a", "ь": "y", "ю": "yu", "я": "ya",
}
_NELATIN = re.compile("[Ͱ-Ͽἀ-῿Ѐ-ӿ]+")


def _litera_latina(c):
    mic = c.lower()
    if mic in _GRECESC or mic in _CHIRILIC:          # й inainte sa-si piarda semnul
        return _GRECESC.get(mic) or _CHIRILIC.get(mic)
    baza = unicodedata.normalize("NFD", mic)[0]       # fara accent (tonos)
    return _GRECESC.get(baza) or _CHIRILIC.get(baza) or baza


def translitereaza(s):
    """Cuvintele grecesti si chirilice -> litere latine; restul ramane neatins.

    Exporturile Saga sunt Windows-1252, deci numele grecesti stau pe facturi deja
    transliterate. Aceeasi transliterare serveste si la Explicatie, si la comparatia de
    nume. Un text fara litere grecesti sau chirilice iese identic.
    """
    def cuvant(m):
        w = m.group(0)
        lat = "".join(_litera_latina(c) for c in w)
        if w.isupper():
            return lat.upper()
        return lat[:1].upper() + lat[1:] if w[:1].isupper() else lat
    return _NELATIN.sub(cuvant, s)


def _pliaza(t):
    """Conventiile de transliterare difera intre surse: pe facturile Trendyol χ -> x si
    ου -> oy (MIXALIS KOYMLELLIS), pe cele Skroutz χ -> ch, ξ -> x, ου -> ou, γκ -> g
    (CHRISTOS, XIOURAS, GIOSIS). Cheia de nume le aduce pe toate la aceeasi forma, pe
    ambele parti ale comparatiei."""
    return t.replace("ch", "x").replace("ks", "x").replace("oy", "ou").replace("gk", "g")


def cheie_nume(s):
    """'Marian Ghita SRL' -> frozenset{'marian','ghita'} (ordinea nu conteaza)."""
    curat = re.sub(r"[^a-z0-9]+", " ", fara_diacritice(translitereaza(ca_text(s))).lower())
    return frozenset(_pliaza(t) for t in curat.split() if t and t not in _CUVINTE_IGNORATE)


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


def _factura(nr, camp, sursa):
    """Factura in forma comuna, oricare ar fi exportul. `camp(nume)` -> valoarea bruta.

    Exportul in lei are `total`. Exportul in valuta nu are: acolo totalul, in valuta
    facturii, e `val_val` + `tva_val` (baza + TVA); la HUF, Saga tine sumele la suta de
    forinti, ca in cursul BNR. `cod_valuta` lipseste din exportul in lei -> RON.
    """
    total = normalizeaza_suma(camp("total"))
    if total is None:
        baza = normalizeaza_suma(camp("val_val"))
        if baza is not None:
            total = baza + (normalizeaza_suma(camp("tva_val")) or Decimal("0.00"))
    data = camp("data")
    valuta = ca_text(camp("cod_valuta")).upper() or "RON"
    # Valoarea in lei a facturii: la valuta, baza + TVA in lei (`baza_tva` + `tva`).
    # Trebuie la clientii greci Trendyol: facturati in EUR, dar platiti in lei.
    total_lei = total
    if valuta != "RON":
        baza_lei = normalizeaza_suma(camp("baza_tva"))
        total_lei = (baza_lei + (normalizeaza_suma(camp("tva")) or Decimal("0.00"))
                     if baza_lei is not None else None)
    return {
        "nr_iesire": nr,
        "denumire": ca_text(camp("denumire")),
        "total": total,
        "total_lei": total_lei,
        "inf_suplm": ca_text(camp("inf_suplm")),
        "data": data.strftime("%Y-%m-%d") if isinstance(data, _dt.datetime) else ca_text(data),
        "valuta": valuta,
        "sursa": sursa,
    }


def citeste_facturi_xml(cale):
    """-> list[dict]: nr_iesire, denumire, total, inf_suplm, data, valuta, sursa."""
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
        facturi.append(_factura(nr, camp, cale.name))
    return facturi


def citeste_facturi_xlsx(cale):
    """Exportul de facturi salvat ca .xlsx (lista in valuta din Saga, 11.09.2026).

    Aceleasi nume de camp ca in XML, ca antet de coloana: nr_iesire, denumire, data,
    cod_valuta, val_val, tva_val, inf_suplm...
    """
    randuri = citeste_xlsx(cale)
    for i, rand in enumerate(randuri[:5]):
        nume = {ca_text(v).lower(): j for j, v in enumerate(rand) if ca_text(v)}
        if "nr_iesire" in nume:
            break
    else:
        raise ValueError("nu am gasit coloana nr_iesire in primele 5 randuri")
    facturi = []
    for rand in randuri[i + 1:]:
        def camp(c, rand=rand):
            j = nume.get(c)
            return rand[j] if j is not None and j < len(rand) else None
        nr = ca_text(camp("nr_iesire"))
        if nr:
            facturi.append(_factura(nr, camp, cale.name))
    return facturi


CITITOARE_FACTURI = {".xml": citeste_facturi_xml, ".xlsx": citeste_facturi_xlsx}


def incarca_facturi(folder):
    """Indexeaza toate exporturile din folder (si subfoldere) dupa inf_suplm si nume.

    Exporturile se suprapun: unul poate acoperi mai multe luni, iar aceeasi factura
    poate aparea in doua. Castiga exportul a carui perioada se termina mai tarziu;
    daca versiunile difera, se semnaleaza - o factura corectata in tacere e mai rea
    decat una raportata.
    """
    idx = {"dupa_inf": {}, "dupa_nume": {}, "numar": 0, "fisiere": [], "erori": [],
           "de_la": None, "pana_la": None, "corectate": [], "pe_valuta": {}, "valute": {}}

    exporturi = []
    for cale in sorted(folder.rglob("*")):
        if not cale.is_file() or cale.name.startswith("~$"):
            continue
        suf = cale.suffix.lower()
        if suf == ".xls":
            # Excel vechi (binar): nu se poate citi din biblioteca standard. Tacem doar
            # daca langa el exista acelasi export salvat intr-o forma citibila.
            if not any(cale.with_suffix(s).exists() or cale.with_suffix(s.upper()).exists()
                       for s in CITITOARE_FACTURI):
                idx["erori"].append("%s: format .xls (Excel vechi), nu se poate citi - "
                                    "salveaza-l ca .xlsx sau exporta-l ca XML" % cale.name)
            continue
        if suf not in CITITOARE_FACTURI:
            continue
        try:
            facturi = CITITOARE_FACTURI[suf](cale)
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
        # Indexul pe toate valutele, plus cate unul pe valuta: un borderou se leaga doar
        # de facturile in valuta folderului lui (un omonim facturat in EUR nu are ce
        # cauta langa un ramburs in lei).
        vedere = idx["valute"].setdefault(f["valuta"], {"dupa_inf": {}, "dupa_nume": {}})
        k = cheie_nume(f["denumire"])
        for tinta in (idx, vedere):
            if f["inf_suplm"]:
                tinta["dupa_inf"].setdefault(f["inf_suplm"], []).append(f)
            if k:
                tinta["dupa_nume"].setdefault(k, []).append(f)
        idx["pe_valuta"][f["valuta"]] = idx["pe_valuta"].get(f["valuta"], 0) + 1

    toate = [f["data"] for f in vazute.values() if f["data"]]
    if toate:
        idx["de_la"], idx["pana_la"] = min(toate), max(toate)
    idx["numar"] = len(vazute)
    return idx


def facturi_in(idx, moneda):
    """Indexul redus la facturile intr-o singura valuta (gol daca nu exista niciuna)."""
    vedere = idx["valute"].get(moneda.upper(), {"dupa_inf": {}, "dupa_nume": {}})
    return dict(idx, dupa_inf=vedere["dupa_inf"], dupa_nume=vedere["dupa_nume"])


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


def _dupa_cheie(ref, idx, sufix=False):
    """Facturile cu inf_suplm = ref. Cu `sufix`, si a doua factura pe aceeasi comanda,
    marcata de Saga cu sufix (Skroutz: 260624-0224606 -> 260624-0224606-2)."""
    gasite = list(idx["dupa_inf"].get(ref, []))
    if sufix and ref:
        prefix = ref + "-"
        gasite += [f for k, lst in idx["dupa_inf"].items()
                   if k.startswith(prefix) and k[len(prefix):].isdigit() for f in lst]
    return gasite


def alege_factura(ref, dest, suma, idx, eticheta="RefExp1", sufix=False):
    """-> (factura | None, suma_de_scris, avertismente, motiv_esec | None).

    Cheia e RefExp1 = inf_suplm; numele si totalul doar confirma. Cautarea dupa nume
    e strict rezerva, pentru cand RefExp1 nu duce nicaieri - altfel un omonim cu
    aceeasi suma ar face ambigua o potrivire deja sigura. Totalul departajeaza cand
    raman mai multi candidati (tipic: factura initiala plus stornarea ei).

    `total` de pe factura e in valuta facturii, deci comparatia cu suma din borderou
    e directa, oricare ar fi valuta folderului (confirmat de client, 25.08.2026).
    `eticheta` = numele cheii in mesaje (RefExp1 la Cargus, Order ID la eMAG...).
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

    dupa_ref = _dupa_cheie(ref, idx, sufix)
    buni, sursa = filtreaza(dupa_ref), "cheie"
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
            return None, suma, av, ("totalul nu confirma factura de pe %s %s "
                                    "(borderou %s; gasite: %s)" % (eticheta, ref, suma, detaliu))
        return None, suma, av, "nicio factura pe %s %s si niciuna pe numele '%s'" % (
            eticheta, ref, dest)
    if len(buni) > 1:
        return None, suma, av, "mai multe facturi se potrivesc: %s" % ", ".join(
            f["nr_iesire"] for f in buni)

    f = buni[0]
    if sursa == "nume":
        av.append("factura %s gasita doar dupa nume: %s %s nu duce la o factura "
                  "confirmata de total" % (f["nr_iesire"], eticheta, ref))
    stornuri = [x["nr_iesire"] for x in dupa_ref
                if x is not f and x["total"] is not None and x["total"] < 0]
    if stornuri:
        av.append("%s %s are si factura de storno (%s) - de verificat"
                  % (eticheta, ref, ", ".join(stornuri)))
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

# Coloanele (litere mici) care identifica fiecare format. Toate trebuie sa stea pe
# acelasi rand de header, cautat in primele 5 randuri: Cargus, Sameday, eMAG si
# Trendyol/Skroutz au deasupra harta pusa de client, PlatiOnline trei randuri de
# preambul. Cargus si Sameday au amandoua `AWB`, dar doar Cargus are `Destinatar` simplu.
FORMATE = (
    ("cargus", ("awb", "destinatar")),
    ("sameday", ("awb", "nume destinatar", "suma ramburs")),
    ("emag", ("order id", "fraction type", "client name")),
    ("waybill", ("waybill", "recipient", "amount")),
    ("plationline", ("statementid", "order number", "amount")),
)

COLOANE_CERUTE = ("awb", "destinatar", "suma", "data op", "refexp1")

# Trendyol si Skroutz au acelasi format; ii desparte continutul coloanei Waybill:
# Skroutz pune codul comenzii (aallzz-nnnnnnn, ex. 260518-9008682), Trendyol un numar.
_COD_SKROUTZ = re.compile(r"^\d{6}-\d{7}$")

MESAJ_NERECUNOSCUT = ("format nerecunoscut: nu se potriveste cu niciun borderou cunoscut "
                      "(Cargus, eMAG, Sameday, Trendyol / Skroutz, PlatiOnline)")


def gaseste_header(randuri):
    """-> (format, index_rand, {nume_coloana_lower: index_coloana}) sau (None, None, None)."""
    for i, rand in enumerate(randuri[:5]):
        nume = {ca_text(v).lower(): j for j, v in enumerate(rand) if ca_text(v)}
        for fmt, cerute in FORMATE:
            if all(c in nume for c in cerute):
                return fmt, i, nume
    return None, None, None


def identifica(cale):
    """Citeste fisierul si spune carei surse ii apartine.

    -> dict: randuri, format, idx_header, nume, sursa (None = nerecunoscut), eroare.
    """
    info = {"randuri": None, "format": None, "idx_header": None, "nume": None,
            "sursa": None, "eroare": None}
    try:
        randuri = citeste_tabel(cale)
    except Exception as exc:  # zip corupt, fisier deschis in Excel etc.
        info["eroare"] = "nu am putut citi fisierul: %s" % exc
        return info
    fmt, idx, nume = gaseste_header(randuri)
    info.update(randuri=randuri, format=fmt, idx_header=idx, nume=nume)
    if fmt is None:
        info["eroare"] = MESAJ_NERECUNOSCUT
    elif fmt == "waybill":
        c = nume["waybill"]
        coduri = [ca_text(r[c]) for r in randuri[idx + 1:] if c < len(r) and ca_text(r[c])]
        skroutz = sum(1 for x in coduri if _COD_SKROUTZ.match(x))
        info["sursa"] = "skroutz" if coduri and skroutz * 2 > len(coduri) else "trendyol"
    else:
        info["sursa"] = fmt
    return info


# --------------------------------------------------------------------------
# Conversia unui borderou
# --------------------------------------------------------------------------

def rezultat_gol(cale):
    return {
        "fisier": cale.name,
        "linii": [],
        "avertismente": [],
        "sarite": [],
        "total": Decimal("0.00"),
        "total_sarit": Decimal("0.00"),
        "pe_data": {},
        "corectate": 0,
        "corectie": Decimal("0.00"),
        "ignorate": [],        # randuri care nu sunt incasari (suma 0, platit si returnat)
        "cheie": "RefExp1",    # numele cheii in raport
        "eroare": None,
    }


def proceseaza_cargus(cale, info, moneda, cont, facturi=None, folosite=None, partiale=None):
    """Profilul Cargus / Packeta -> dict cu linii, avertismente, randuri sarite, totaluri.

    `info` = rezultatul lui identifica(). `facturi` = indexul din incarca_facturi();
    None inseamna fara legare de facturi (FacturaNumar ramane gol si niciun rand nu e
    sarit din lipsa de factura). `folosite` = {nr_iesire: unde a fost stinsa}, din
    jurnalele tuturor surselor.
    """
    rez = rezultat_gol(cale)
    randuri, idx_header, nume = info["randuri"], info["idx_header"], info["nume"]
    folosite = folosite if folosite is not None else {}
    in_valuta = facturi_in(facturi, moneda) if facturi is not None else None

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
            factura, suma_xml, av, motiv = alege_factura(ref, dest, suma, in_valuta)
            if factura is not None and factura["nr_iesire"] in folosite:
                # Aceeasi factura stinsa din doua borderouri = incasare dubla in Saga.
                motiv = ("factura %s e deja stinsa prin %s"
                         % (factura["nr_iesire"], folosite[factura["nr_iesire"]]))
                factura, av = None, []
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

    # RefExp1 in afara tiparului dominant de lungime - doar fara facturi. Cand facturile
    # sunt legate, factura insasi confirma cheia: 9822 si 26540717, semnalate luni la
    # rand ca "greseli de tastare", sunt inf_suplm reale (MCS36218, MCS36251), iar 98xx
    # e a doua serie de comenzi (apare si la PlatiOnline). O cheie gresita tot iese la
    # iveala: nu gaseste factura si cade pe cautarea dupa nume, cu avertisment.
    lungimi = {}
    for l in rez["linii"]:
        lungimi.setdefault(len(l["Numar"]), []).append(l)
    if facturi is None and len(lungimi) > 1:
        dominanta = max(lungimi, key=lambda k: len(lungimi[k]))
        for lung, grup in sorted(lungimi.items()):
            if lung == dominanta:
                continue
            for l in grup:
                rez["avertismente"].append(
                    "randul %d: RefExp1 '%s' are %d caractere, restul au %d"
                    % (l["rand"], l["Numar"], lung, dominanta))
    return rez


# --------------------------------------------------------------------------
# Profilurile noi (11.09.2026): eMAG, PlatiOnline, Skroutz, Sameday, Trendyol.
# Regulile sunt in references/mappings.md; aici doar cum se aplica.
# --------------------------------------------------------------------------

FEREASTRA_ZILE = 15   # legare dupa nume: factura la cel mult atatea zile de borderou
FEREASTRA_STORNO = 60  # stornarea vine de obicei la cateva saptamani dupa livrare
FRACTIUNI_EMAG = {"co cashing", "cod cashing", "refund co", "refund cod", "voucher"}


def _celula(rand, idx):
    return rand[idx] if idx is not None and idx < len(rand) else None


def _coloana(nume, *variante, prefix=False):
    """Indexul coloanei cu unul din numele date (sau care incepe cu el, cu prefix)."""
    for v in variante:
        if v in nume:
            return nume[v]
    if prefix:
        for v in variante:
            for k, j in nume.items():
                if k.startswith(v):
                    return j
    return None


def _randuri_date(info):
    """(numarul randului in fisier, rand) sub header, fara randurile goale."""
    idx = info["idx_header"]
    for i, rand in enumerate(info["randuri"][idx + 1:], start=idx + 2):
        if rand and not all(v is None or ca_text(v) == "" for v in rand):
            yield i, rand


def _zi(v):
    """'2026-07-02' / '02.07.2026' / datetime -> date, sau None."""
    if isinstance(v, _dt.datetime):
        return v.date()
    s = ca_text(v)[:10]
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def data_americana(v):
    """'6/27/2026 7:27:54 AM' -> '27.06.2026'. PlatiOnline scrie luna inaintea zilei."""
    s = ca_text(v).split(" ")[0]
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        return "%02d.%02d.%s" % (int(m.group(2)), int(m.group(1)), m.group(3))
    return normalizeaza_data(v)


def _nume_explicatie(nume):
    return re.sub(r"\s+", " ", translitereaza(ca_text(nume))).strip()


def _adauga_linie(rez, rand, data, numar, suma, cont, nume, factura, moneda, partial=False):
    rez["linii"].append({
        "rand": rand, "Data": data, "Numar": numar, "Suma": suma, "Cont": cont,
        "Explicatie": "%s - %s" % (PREFIX_EXPLICATIE, _nume_explicatie(nume)),
        "FacturaID": numar, "FacturaNumar": factura["nr_iesire"] if factura else "",
        "Moneda": moneda, "partial": partial})
    rez["total"] += suma
    rez["pe_data"][data] = rez["pe_data"].get(data, Decimal("0.00")) + suma


def _scrie_potrivire(rez, rand, data, numar, nume, suma, f, suma_xml, av, cont, moneda,
                     partial=False):
    for a in av:
        rez["avertismente"].append("randul %s: %s" % (rand, a))
    if suma_xml != suma:
        rez["corectate"] += 1
        rez["corectie"] += suma_xml - suma
    _adauga_linie(rez, rand, data, numar, suma_xml, cont, nume, f, moneda, partial)


def _sari(rez, rand, motiv, nume, ref, suma, data):
    rez["sarite"].append({"rand": rand, "motiv": motiv, "destinatar": ca_text(nume),
                          "refexp1": ref, "suma": str(suma) if suma is not None else "",
                          "data": data or ""})
    if suma is not None:
        rez["total_sarit"] += suma


def _ignora(rez, rand, motiv, nume, ref, suma):
    rez["ignorate"].append({"rand": rand, "motiv": motiv, "destinatar": ca_text(nume),
                            "refexp1": ref, "suma": str(suma) if suma is not None else ""})


def _lipsuri(**campuri):
    return [n.replace("_", " ") for n, v in campuri.items() if v is None or v == ""]


def _semnaleaza_export_lipsa(rez, facturi):
    """Ca la Cargus: multe randuri fara nicio factura = probabil lipseste un export."""
    negasite = [x for x in rez["sarite"] if x["motiv"].startswith("nicio factura")]
    if facturi is not None and negasite and len(negasite) >= max(
            5, (len(rez["linii"]) + len(negasite)) // 5):
        rez["avertismente"].insert(0, (
            "%d randuri nu au nicio factura, iar exporturile acopera %s: "
            "probabil lipseste un export de facturi"
            % (len(negasite), perioada_facturi(facturi) or "o perioada necunoscuta")))


def _deja_stinsa(f, ocupate):
    nr = f["nr_iesire"]
    return "factura %s e deja stinsa prin %s" % (nr, ocupate[nr]) if nr in ocupate else None


def alege_factura_nume(nume, suma, data, idx, ocupate, camp="total"):
    """Borderourile fara cheie comuna cu factura (Sameday, Trendyol): nume + suma + data.

    Candidatii: facturile pe acelasi nume (ca la rezerva Cargus), nestinse inca, cu
    totalul la cel mult TOL_MAX de suma si data la cel mult FEREASTRA_ZILE zile. Intre
    mai multi castiga suma exacta, apoi data cea mai apropiata; o egalitate ramane
    ambigua. `camp` = "total_lei" compara cu valoarea in lei a unei facturi in valuta.
    -> (factura | None, suma_de_scris, avertismente, motiv)
    """
    av = []
    toate = _dupa_nume(nume, idx)
    if not toate:
        return None, suma, av, "nicio factura pe numele '%s'" % nume
    libere = [f for f in toate if f["nr_iesire"] not in ocupate]
    if not libere:
        return None, suma, av, "facturile pe numele '%s' sunt deja stinse (%s)" % (
            nume, ", ".join(f["nr_iesire"] for f in toate[:4]))
    d0 = _zi(data)

    def dist(f):
        z = _zi(f["data"])
        return abs((z - d0).days) if z and d0 else None

    buni = [f for f in libere if f.get(camp) is not None and abs(f[camp] - suma) <= TOL_MAX]
    if not buni:
        return None, suma, av, "nicio factura pe numele '%s' cu totalul %s (gasite: %s)" % (
            nume, suma, ", ".join("%s = %s" % (f["nr_iesire"], f.get(camp)) for f in libere[:4]))
    fereastra = FEREASTRA_ZILE if suma > 0 else FEREASTRA_STORNO
    aproape = [f for f in buni if dist(f) is not None and dist(f) <= fereastra]
    if not aproape:
        return None, suma, av, ("facturile pe numele '%s' cu totalul %s sunt la peste %d zile "
                                "de %s: %s" % (nume, suma, fereastra, data,
                                               ", ".join(f["nr_iesire"] for f in buni[:4])))
    if len(aproape) > 1:
        exacte = [f for f in aproape if f[camp] == suma]
        aproape = exacte or aproape
    if len(aproape) > 1:
        cea_mai_mica = min(dist(f) for f in aproape)
        aproape = [f for f in aproape if dist(f) == cea_mai_mica]
    if len(aproape) > 1:
        return None, suma, av, "mai multe facturi se potrivesc: %s" % ", ".join(
            f["nr_iesire"] for f in aproape)
    f = aproape[0]
    if dist(f) > 3:
        av.append("factura %s e la %d zile de data din borderou (%s)"
                  % (f["nr_iesire"], dist(f), data))
    d = abs(f[camp] - suma)
    if d > TOL_TACITA:
        av.append("suma luata din factura %s: borderou %s -> factura %s (diferenta %s)"
                  % (f["nr_iesire"], suma, f[camp], d))
    return f, f[camp], av, None


def alege_factura_emag(ref, nume, suma, idx, ocupate, partiale):
    """Ca alege_factura pe Order ID, plus platile partiale (decizia din 11.09.2026).

    O comanda cu o singura factura, din care borderoul aduce doar o parte (voucherul
    intr-o virare, rambursul in alta), intra cu suma din borderou si avertisment; a doua
    virare stinge restul. `partiale` = cat s-a incasat deja pe fiecare factura.
    -> (factura | None, suma_de_scris, avertismente, motiv, e_partiala)
    """
    f, suma_xml, av, motiv = alege_factura(ref, nume, suma, idx, "Order ID")
    if f is not None:
        nr = f["nr_iesire"]
        if nr in ocupate:
            return None, suma, [], _deja_stinsa(f, ocupate), False
        if nr in partiale:
            return None, suma, [], ("factura %s are deja incasat %s din %s; inca o data suma "
                                    "intreaga ar dubla incasarea" % (nr, partiale[nr], f["total"])), False
        return f, suma_xml, av, None, False
    pozitive = [x for x in _dupa_cheie(ref, idx) if x["total"] is not None and x["total"] > 0]
    if suma > 0 and len(pozitive) == 1:
        x = pozitive[0]
        nr = x["nr_iesire"]
        if nr in ocupate:
            return None, suma, [], _deja_stinsa(x, ocupate), False
        platit = partiale.get(nr, Decimal("0.00"))
        rest = x["total"] - platit
        if platit and abs(suma - rest) <= TOL_MAX:
            return x, rest, ["completeaza factura %s: %s incasat anterior + %s acum = %s"
                             % (nr, platit, rest, x["total"])], None, False
        if suma < rest:
            av = ["plata partiala: %s din factura %s de %s (raman de incasat %s)"
                  % (suma, nr, x["total"], rest - suma)]
            if not nume_se_potrivesc(nume, x["denumire"]):
                av.append("numele difera: borderou '%s' vs factura %s '%s'"
                          % (nume, nr, x["denumire"]))
            return x, suma, av, None, True
    return None, suma, [], motiv, False


def proceseaza_emag(cale, info, moneda, cont, facturi=None, folosite=None, partiale=None):
    """eMAG RO/BG/HU: o linie pe comanda (fractiunile adunate), Data = Payout date."""
    rez = rezultat_gol(cale)
    rez["cheie"] = "Order ID"
    ocupate = dict(folosite or {})
    partiale = partiale if partiale is not None else {}
    nume = info["nume"]
    c_plata, c_id = _coloana(nume, "payout date"), _coloana(nume, "order id")
    c_tip, c_client = _coloana(nume, "fraction type"), _coloana(nume, "client name")
    c_val = _coloana(nume, "fraction value", prefix=True)
    if c_plata is None or c_val is None:
        rez["eroare"] = "lipsesc coloanele: %s" % ", ".join(
            n for n, c in (("Payout date", c_plata), ("Fraction value", c_val)) if c is None)
        return rez
    antet = next(k for k, j in nume.items() if j == c_val)
    m = re.search(r"\[([a-z]{3})\]", antet)
    if m and m.group(1).upper() != moneda:
        rez["avertismente"].append("coloana '%s' e in %s, dar folderul e %s"
                                   % (antet, m.group(1).upper(), moneda))

    comenzi = {}
    for i, rand in _randuri_date(info):
        oid, tip = ca_text(_celula(rand, c_id)), ca_text(_celula(rand, c_tip))
        client = ca_text(_celula(rand, c_client))
        data = normalizeaza_data(_celula(rand, c_plata))
        val = normalizeaza_suma(_celula(rand, c_val))
        lipsuri = _lipsuri(Payout_date=data, Order_ID=oid, Fraction_value=val)
        if lipsuri:
            _sari(rez, i, "lipseste " + ", ".join(lipsuri), client, oid, val, data)
            continue
        if tip.lower() not in FRACTIUNI_EMAG:
            _sari(rez, i, "tip de fractiune necunoscut: '%s'" % tip, client, oid, val, data)
            continue
        if moneda == "HUF":   # Saga tine HUF la suta de forinti, ca in cursul BNR
            val = (val / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        c = comenzi.setdefault(oid, {"randuri": [], "suma": Decimal("0.00"), "nume": "",
                                     "date": set(), "tipuri": []})
        c["randuri"].append(i)
        c["suma"] += val
        c["date"].add(data)
        c["tipuri"].append(tip)
        c["nume"] = c["nume"] or client

    vedere = facturi_in(facturi, moneda) if facturi is not None else None
    for oid, c in comenzi.items():
        rand = ", ".join(str(x) for x in c["randuri"])
        data = max(c["date"], key=lambda d: (d[6:], d[3:5], d[:2]))
        if len(c["date"]) > 1:
            rez["avertismente"].append("randurile %s: comanda %s are mai multe date de virare "
                                       "(%s), s-a luat %s" % (rand, oid, ", ".join(sorted(c["date"])), data))
        suma = c["suma"]
        if suma == 0:
            _ignora(rez, rand, "suma neta 0: %s" % " + ".join(c["tipuri"]), c["nume"], oid, suma)
            continue
        if vedere is None:
            _adauga_linie(rez, rand, data, oid, suma, cont, c["nume"], None, moneda)
            continue
        f, suma_xml, av, motiv, partial = alege_factura_emag(oid, c["nume"], suma, vedere,
                                                             ocupate, partiale)
        if f is None:
            _sari(rez, rand, motiv, c["nume"], oid, suma, data)
            continue
        if not partial:
            ocupate[f["nr_iesire"]] = cale.name
        _scrie_potrivire(rez, rand, data, oid, c["nume"], suma, f, suma_xml, av, cont, moneda,
                         partial)
    _semnaleaza_export_lipsa(rez, facturi)
    return rez


def _facturi_b2b(suma, data, idx, ocupate, zile=3):
    """Comenzile B2B (seria MCSCOD) se platesc cu cardul de o persoana, dar se factureaza
    pe firma, fara inf_suplm: singurele repere sunt suma si ziua (factura in 0-3 zile)."""
    d0 = _zi(data)
    if d0 is None or suma <= 0:
        return []
    gasite = []
    for lst in idx["dupa_nume"].values():
        for f in lst:
            if f["inf_suplm"] or f["nr_iesire"] in ocupate or f["total"] is None:
                continue
            z = _zi(f["data"])
            if z and 0 <= (z - d0).days <= zile and abs(f["total"] - suma) <= TOL_TACITA:
                gasite.append(f)
    return gasite


def proceseaza_plationline(cale, info, moneda, cont, facturi=None, folosite=None,
                           partiale=None):
    """PlatiOnline (.csv): cheia Order Number = inf_suplm; B2B dupa suma + zi."""
    rez = rezultat_gol(cale)
    rez["cheie"] = "Order Number"
    ocupate = dict(folosite or {})
    nume = info["nume"]
    c_client, c_ord = _coloana(nume, "client"), _coloana(nume, "order number")
    c_tip, c_val = _coloana(nume, "settle/credit"), _coloana(nume, "amount")
    c_val_mon, c_data = _coloana(nume, "currency"), _coloana(nume, "date")
    vedere = facturi_in(facturi, moneda) if facturi is not None else None
    vazute = {}
    for i, rand in _randuri_date(info):
        client, ref = ca_text(_celula(rand, c_client)), ca_text(_celula(rand, c_ord))
        suma = normalizeaza_suma(_celula(rand, c_val))
        data = data_americana(_celula(rand, c_data))
        lipsuri = _lipsuri(Date=data, Order_Number=ref, Amount=suma)
        if lipsuri:
            _sari(rez, i, "lipseste " + ", ".join(lipsuri), client, ref, suma, data)
            continue
        if ca_text(_celula(rand, c_tip)).lower().startswith("credit"):
            suma = -abs(suma)   # banii intorsi clientului
        mon = ca_text(_celula(rand, c_val_mon)).upper()
        if mon and mon != moneda:
            rez["avertismente"].append("randul %d: plata e in %s, dar folderul e %s"
                                       % (i, mon, moneda))
        if suma == 0:
            _ignora(rez, i, "suma 0", client, ref, suma)
            continue
        if ref in vazute:
            rez["avertismente"].append("randul %d: Order Number %s apare si pe randul %d"
                                       % (i, ref, vazute[ref]))
        else:
            vazute[ref] = i
        if vedere is None:
            _adauga_linie(rez, i, data, ref, suma, cont, client, None, moneda)
            continue
        f, suma_xml, av, motiv = alege_factura(ref, client, suma, vedere, "Order Number")
        if f is not None and f["nr_iesire"] in ocupate:
            f, av, motiv = None, [], _deja_stinsa(f, ocupate)
        if f is None and motiv and motiv.startswith("nicio factura"):
            b2b = _facturi_b2b(suma, data, vedere, ocupate)
            if len(b2b) == 1:
                f, suma_xml = b2b[0], b2b[0]["total"]
                av = ["factura B2B %s (%s) gasita dupa suma si zi: pe factura nu e Order Number"
                      % (f["nr_iesire"], f["denumire"])]
            elif b2b:
                motiv = "mai multe facturi B2B cu aceeasi suma si zi: %s" % ", ".join(
                    x["nr_iesire"] for x in b2b)
        if f is None:
            _sari(rez, i, motiv, client, ref, suma, data)
            continue
        ocupate[f["nr_iesire"]] = cale.name
        _scrie_potrivire(rez, i, data, ref, client, suma, f, suma_xml, av, cont, moneda)
    _semnaleaza_export_lipsa(rez, facturi)
    return rez


def proceseaza_skroutz(cale, info, moneda, cont, facturi=None, folosite=None, partiale=None):
    """Skroutz: cheia Waybill = inf_suplm (codul comenzii), inclusiv cu sufix (-2)."""
    rez = rezultat_gol(cale)
    rez["cheie"] = "Waybill"
    ocupate = dict(folosite or {})
    nume = info["nume"]
    c_wb, c_data = _coloana(nume, "waybill"), _coloana(nume, "pickup date")
    c_nume, c_val = _coloana(nume, "recipient"), _coloana(nume, "amount")
    vedere = facturi_in(facturi, moneda) if facturi is not None else None
    vazute = {}
    for i, rand in _randuri_date(info):
        ref, client = ca_text(_celula(rand, c_wb)), ca_text(_celula(rand, c_nume))
        suma, data = normalizeaza_suma(_celula(rand, c_val)), normalizeaza_data(_celula(rand, c_data))
        lipsuri = _lipsuri(Pickup_date=data, Waybill=ref, Amount=suma)
        if lipsuri:
            _sari(rez, i, "lipseste " + ", ".join(lipsuri), client, ref, suma, data)
            continue
        if suma == 0:
            _ignora(rez, i, "suma 0", client, ref, suma)
            continue
        if ref in vazute:
            rez["avertismente"].append("randul %d: Waybill %s apare si pe randul %d"
                                       % (i, ref, vazute[ref]))
        else:
            vazute[ref] = i
        if vedere is None:
            _adauga_linie(rez, i, data, ref, suma, cont, client, None, moneda)
            continue
        f, suma_xml, av, motiv = alege_factura(ref, client, suma, vedere, "Waybill", sufix=True)
        if f is not None and f["nr_iesire"] in ocupate:
            f, av, motiv = None, [], _deja_stinsa(f, ocupate)
        if f is None:
            _sari(rez, i, motiv, client, ref, suma, data)
            continue
        ocupate[f["nr_iesire"]] = cale.name
        _scrie_potrivire(rez, i, data, ref, client, suma, f, suma_xml, av, cont, moneda)
    _semnaleaza_export_lipsa(rez, facturi)
    return rez


def proceseaza_sameday(cale, info, moneda, cont, facturi=None, folosite=None, partiale=None):
    """Sameday: fara numar de comanda, deci nume + suma + data (ziua AWB-ului)."""
    rez = rezultat_gol(cale)
    rez["cheie"] = "AWB"
    ocupate = dict(folosite or {})
    nume = info["nume"]
    c_awb, c_nume = _coloana(nume, "awb"), _coloana(nume, "nume destinatar")
    c_val, c_data = _coloana(nume, "suma ramburs"), _coloana(nume, "data")
    vedere = facturi_in(facturi, moneda) if facturi is not None else None
    for i, rand in _randuri_date(info):
        awb, client = ca_text(_celula(rand, c_awb)), ca_text(_celula(rand, c_nume))
        suma, data = normalizeaza_suma(_celula(rand, c_val)), normalizeaza_data(_celula(rand, c_data))
        lipsuri = _lipsuri(Data=data, Nume_destinatar=client, Suma_ramburs=suma)
        if lipsuri:
            _sari(rez, i, "lipseste " + ", ".join(lipsuri), client, awb, suma, data)
            continue
        if suma == 0:
            _ignora(rez, i, "suma 0", client, awb, suma)
            continue
        if vedere is None:
            _adauga_linie(rez, i, data, awb, suma, cont, client, None, moneda)
            continue
        f, suma_xml, av, motiv = alege_factura_nume(client, suma, data, vedere, ocupate)
        if f is None:
            _sari(rez, i, motiv, client, awb, suma, data)
            continue
        ocupate[f["nr_iesire"]] = cale.name
        _scrie_potrivire(rez, i, data, f["inf_suplm"] or awb, client, suma, f, suma_xml, av,
                         cont, moneda)
    _semnaleaza_export_lipsa(rez, facturi)
    return rez


def proceseaza_trendyol(cale, info, moneda, cont, facturi=None, folosite=None, partiale=None):
    """Trendyol: nume + suma + data; coletele aceleiasi comenzi se aduna; clientii
    facturati in EUR se incaseaza in lei, la valoarea in lei a facturii (11.09.2026)."""
    rez = rezultat_gol(cale)
    rez["cheie"] = "Waybill"
    ocupate = dict(folosite or {})
    nume = info["nume"]
    c_wb, c_data = _coloana(nume, "waybill"), _coloana(nume, "pickup date")
    c_nume, c_val = _coloana(nume, "recipient"), _coloana(nume, "amount")
    vedere = facturi_in(facturi, moneda) if facturi is not None else None
    in_eur = facturi_in(facturi, "EUR") if facturi is not None and moneda == "RON" else None

    def cauta(client, suma, data):
        f, s, av, motiv = alege_factura_nume(client, suma, data, vedere, ocupate)
        if f is None and in_eur is not None:
            g, s2, av2, motiv2 = alege_factura_nume(client, suma, data, in_eur, ocupate,
                                                    "total_lei")
            if g is not None:
                av2.insert(0, "clientul e facturat in EUR: factura %s de %s EUR; incasarea "
                              "intra in lei, la valoarea in lei a facturii (%s)"
                           % (g["nr_iesire"], g["total"], g["total_lei"]))
                return g, s2, av2, None
            if motiv.startswith("nicio factura pe numele") and not motiv2.startswith(
                    "nicio factura pe numele"):
                motiv = "client facturat in EUR: " + motiv2
        return f, s, av, motiv

    randuri = []
    for i, rand in _randuri_date(info):
        ref, client = ca_text(_celula(rand, c_wb)), ca_text(_celula(rand, c_nume))
        suma, data = normalizeaza_suma(_celula(rand, c_val)), normalizeaza_data(_celula(rand, c_data))
        lipsuri = _lipsuri(Pickup_date=data, Recipient=client, Amount=suma)
        if lipsuri:
            _sari(rez, i, "lipseste " + ", ".join(lipsuri), client, ref, suma, data)
            continue
        if suma == 0:
            _ignora(rez, i, "suma 0", client, ref, suma)
            continue
        randuri.append({"rand": i, "ref": ref, "nume": client, "suma": suma, "data": data})

    # Acelasi client, aceeasi zi, acelasi semn = coletele unei singure comenzi.
    grupe = {}
    for r in randuri:
        grupe.setdefault((cheie_nume(r["nume"]), r["data"], r["suma"] > 0), []).append(r)
    for grup in grupe.values():
        prim = grup[0]
        if vedere is None:
            for r in grup:
                _adauga_linie(rez, r["rand"], r["data"], r["ref"], r["suma"], cont, r["nume"],
                              None, moneda)
            continue
        if len(grup) > 1:
            total = sum((r["suma"] for r in grup), Decimal("0.00"))
            f, s, av, motiv = cauta(prim["nume"], total, prim["data"])
            if f is not None:
                rand = ", ".join(str(r["rand"]) for r in grup)
                av.insert(0, "%d colete ale aceleiasi comenzi (%s), %s in total"
                          % (len(grup), ", ".join(r["ref"] for r in grup), total))
                ocupate[f["nr_iesire"]] = cale.name
                _scrie_potrivire(rez, rand, prim["data"], f["inf_suplm"] or prim["ref"],
                                 prim["nume"], total, f, s, av, cont, moneda)
                continue
        for r in grup:
            f, s, av, motiv = cauta(r["nume"], r["suma"], r["data"])
            if f is None:
                _sari(rez, r["rand"], motiv, r["nume"], r["ref"], r["suma"], r["data"])
                continue
            ocupate[f["nr_iesire"]] = cale.name
            _scrie_potrivire(rez, r["rand"], r["data"], f["inf_suplm"] or r["ref"], r["nume"],
                             r["suma"], f, s, av, cont, moneda)
    _semnaleaza_export_lipsa(rez, facturi)
    return rez


# Sursa -> functia care ii proceseaza borderourile. O sursa lipsa de aici nu poate fi
# rulata inca (--sursa refuza), dar fisierele ei sunt deja recunoscute si ocolite.
PROFILURI = {
    "cargus": proceseaza_cargus,
    "emag": proceseaza_emag,
    "plationline": proceseaza_plationline,
    "skroutz": proceseaza_skroutz,
    "sameday": proceseaza_sameday,
    "trendyol": proceseaza_trendyol,
}


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


VALUTE_CUNOSCUTE = ("RON", "EUR", "HUF")


def moneda_din_folder(cale, implicit="RON"):
    """'.../borderouri/eur' -> 'EUR'. Valuta e data de folder; altfel `implicit`."""
    nume = Path(cale).name.upper()
    return nume if nume in VALUTE_CUNOSCUTE else implicit


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


def citeste_jurnal(dir_procesate, sursa=SURSA_COLECTOARE):
    f = dir_procesate / jurnal_sursa(sursa)
    if not f.exists():
        return {}
    try:
        date = json.loads(f.read_text(encoding="utf-8"))
        return date.get("procesate", {})
    except (json.JSONDecodeError, OSError):
        return {}


def scrie_jurnal(dir_procesate, procesate, sursa=SURSA_COLECTOARE):
    _scrie(dir_procesate / jurnal_sursa(sursa),
           json.dumps({"procesate": procesate}, ensure_ascii=False, indent=2) + "\n")


def incarca_folosite(foldere, sursa, reproceseaza):
    """-> (folosite, partiale), din jurnalele TUTUROR surselor din folderele date.

    folosite = {nr_iesire: 'fisier (Sursa)'} - facturile stinse de tot;
    partiale = {nr_iesire: Decimal} - cat s-a incasat deja pe facturile platite in bucati
    (eMAG: voucherul intr-o virare, rambursul in alta).
    Fiecare task scrie doar jurnalul lui, dar le citeste pe toate, ca aceeasi factura
    sa nu fie stinsa din doua borderouri. Borderourile reprocesate acum de sursa
    curenta nu se numara.
    """
    folosite, partiale = {}, {}
    for folder in foldere:
        dir_procesate = folder / DIR_PROCESATE
        for s in SURSE:
            for fisier, intrare in citeste_jurnal(dir_procesate, s).items():
                if s == sursa and fisier in reproceseaza:
                    continue
                for nr in intrare.get("facturi", []):
                    folosite.setdefault(nr, "%s (%s)" % (fisier, SURSE[s]["eticheta"]))
                for nr, suma in (intrare.get("partiale") or {}).items():
                    partiale[nr] = partiale.get(nr, Decimal("0.00")) + (
                        normalizeaza_suma(suma) or Decimal("0.00"))
    return folosite, partiale


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
    ap.add_argument("--sursa", default=SURSA_COLECTOARE, choices=sorted(SURSE),
                    help="ce borderouri se proceseaza (implicit %s)" % SURSA_COLECTOARE)
    ap.add_argument("--folder", action="append", default=[],
                    help="proceseaza aceasta cale, ignorand config.json (se poate repeta)")
    ap.add_argument("--moneda", default=None,
                    help="valuta folderului (implicit din numele lui: ron/eur/huf, altfel RON)")
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
        moneda = (a.moneda or moneda_din_folder(p)).upper()
        cfg = citeste_config() or {"foldere": []}
        intrare = {"cale": stocheaza(p), "moneda": moneda, "cont": cont_pentru(moneda)}
        cfg["foldere"] = [f for f in cfg.get("foldere", [])
                          if f.get("moneda", "").upper() != moneda] + [intrare]
        unde = scrie_config(cfg)
        print("Salvat in %s: %s -> %s (cont %s)"
              % (unde, intrare["cale"], moneda, intrare["cont"]))
        return 0

    sursa = a.sursa
    if sursa not in PROFILURI:
        mesaj = ("Sursa '%s' nu e inca implementata in script (implementate: %s). "
                 "Maparea ei e in references/mappings.md." % (sursa, ", ".join(sorted(PROFILURI))))
        if a.ca_json:
            print(json.dumps({"stare": "eroare", "mesaj": mesaj}, ensure_ascii=False, indent=2))
        else:
            print(mesaj, file=sys.stderr)
        return 1

    cfg = citeste_config()
    if a.folder:
        foldere = []
        for f in a.folder:
            mon = (a.moneda or moneda_din_folder(f)).upper()
            foldere.append({"cale": f, "moneda": mon, "cont": cont_pentru(mon)})
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
    raport = {"stare": "ok", "dry_run": a.dry_run, "sursa": sursa, "foldere": [],
              "facturi": ({"cale": str(dir_facturi), "numar": facturi["numar"],
                           "fisiere": facturi["fisiere"], "erori": facturi["erori"],
                           "perioada": perioada_facturi(facturi),
                           "pe_valuta": facturi["pe_valuta"],
                           "corectate": facturi["corectate"]}
                          if facturi is not None else None),
              "email": {"catre": adrese, "neconfigurat": not adrese}}
    lipsa = []

    rezolvate = []
    for intrare in foldere:
        folder = rezolva(intrare["cale"])
        if folder is None:
            lipsa.append(intrare["cale"])
        else:
            rezolvate.append((intrare, folder))
    folosite, partiale = incarca_folosite([f for _, f in rezolvate], sursa, a.reproceseaza)
    profil = PROFILURI[sursa]

    for intrare, folder in rezolvate:
        mon = intrare.get("moneda", "RON").upper()
        cont = intrare.get("cont") or cont_pentru(mon)
        dir_procesate = folder / DIR_PROCESATE
        jurnal = citeste_jurnal(dir_procesate, sursa)

        r_folder = {"cale": str(folder), "moneda": mon, "cont": cont,
                    "procesate": [], "sarite_deja": [], "esuate": [], "alte_surse": []}

        fisiere = sorted(p for p in folder.iterdir()
                         if p.is_file() and p.suffix.lower() in (".xlsx", ".csv")
                         and not p.name.startswith("~$"))
        for cale in fisiere:
            if cale.name in jurnal and cale.name not in a.reproceseaza:
                r_folder["sarite_deja"].append(cale.name)
                continue

            info = identifica(cale)
            if info["sursa"] is None:
                # Necitit sau nerecunoscut: il raporteaza doar sursa colectoare, o data.
                if sursa == SURSA_COLECTOARE:
                    r_folder["esuate"].append({"fisier": cale.name, "motiv": info["eroare"]})
                continue
            if info["sursa"] != sursa:
                # Al altui agent: ramane neatins, nu se raporteaza pe e-mail.
                r_folder["alte_surse"].append({
                    "fisier": cale.name, "sursa": info["sursa"],
                    "procesat": cale.name in citeste_jurnal(dir_procesate, info["sursa"])})
                continue

            rez = profil(cale, info, mon, cont, facturi, folosite, partiale)
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
                    "ignorate": rez["ignorate"],
                    "cheie": rez["cheie"],
                    "moneda": mon,
                })
                continue

            # Facturile stinse aici nu mai pot fi stinse de un borderou procesat dupa el,
            # nici in rularea asta, nici in ale altor surse (le citesc din jurnal).
            # O plata partiala nu stinge factura: se aduna la ce s-a incasat deja pe ea.
            stinse = sorted({l["FacturaNumar"] for l in rez["linii"]
                             if l.get("FacturaNumar") and not l.get("partial")})
            for nr in stinse:
                folosite.setdefault(nr, "%s (%s)" % (cale.name, SURSE[sursa]["eticheta"]))
            partiale_noi = {}
            for l in rez["linii"]:
                if l.get("partial"):
                    partiale_noi[l["FacturaNumar"]] = (partiale_noi.get(l["FacturaNumar"],
                                                                        Decimal("0.00")) + l["Suma"])
            for nr, s in partiale_noi.items():
                partiale[nr] = partiale.get(nr, Decimal("0.00")) + s

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
                    "facturi": stinse,
                }
                if partiale_noi:
                    jurnal[cale.name]["partiale"] = {k: str(v) for k, v in sorted(partiale_noi.items())}
                scrie_jurnal(dir_procesate, jurnal, sursa)

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
                "ignorate": rez["ignorate"],
                "cheie": rez["cheie"],
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
                    cale_raport = Path(f["cale"]) / DIR_PROCESATE / raport_sursa(sursa)
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
    # Cargus pastreaza subiectul de dinainte; celelalte surse se numesc, fiindca
    # fiecare agent trimite raportul lui.
    sursa = raport.get("sursa", SURSA_COLECTOARE)
    eticheta = "" if sursa == SURSA_COLECTOARE else " " + SURSE[sursa]["eticheta"]
    return "Incasari Saga%s: %s%s" % (eticheta, ", ".join(fisiere), coada)


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
            r.append("      %s %s: %s" % (p.get("cheie", "RefExp1"), x["refexp1"] or "-",
                                          x["motiv"]))
    if p.get("ignorate"):
        r.append("")
        r.append("  Nu intra in XML, nefiind incasari - %d randuri:" % len(p["ignorate"]))
        for x in p["ignorate"]:
            r.append("    randul %s | %s | %s %s | %s"
                     % (x["rand"], x["destinatar"] or "?", x.get("suma") or "0", moneda,
                        x["motiv"]))
    if p.get("avertismente"):
        r.append("")
        r.append("  De verificat (au intrat totusi in XML):")
        for w in p["avertismente"]:
            r.append("    - %s" % w)
    return r


def _pe_valuta(fact):
    return ", ".join("%s %d" % (v, n) for v, n in sorted(fact["pe_valuta"].items()))


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
        if len(fact.get("pe_valuta") or {}) > 1:
            r.append("  pe valute: %s" % _pe_valuta(fact))
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
        if len(fact.get("pe_valuta") or {}) > 1:
            r.append("  pe valute: %s" % _pe_valuta(fact))
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
            for s in p.get("ignorate", []):
                r.append("      IGNORAT randul %s: %s (%s)"
                         % (s["rand"], s["motiv"], s["destinatar"] or "?"))
            if p.get("raport"):
                r.append("      raport pentru e-mail: %s" % p["raport"])
            for w in p["avertismente"]:
                r.append("      ATENTIE %s" % w)
        if f["sarite_deja"]:
            r.append("  Deja procesate (sarite): %s" % ", ".join(f["sarite_deja"]))
        if f.get("alte_surse"):
            r.append("  Lasate altor agenti: %s" % ", ".join(
                "%s (%s%s)" % (x["fisier"], SURSE[x["sursa"]]["eticheta"],
                               ", procesat" if x["procesat"] else ", neprocesat inca")
                for x in f["alte_surse"]))
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
