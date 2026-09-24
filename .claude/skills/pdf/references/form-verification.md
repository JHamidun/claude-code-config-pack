# Post-fill verification (проверка заполненной формы)

A clean run of `update_page_form_field_values()` only means the names and values were accepted. It does not prove that every field on the page is reachable, or that a viewer will draw the values. Do the checks below; the helpers were tested with pypdf 6.2.0 on a reportlab form with text fields, a checkbox, a radio group and a hierarchical field.

### 1. Field tree vs. page widgets
`get_fields()` walks `/AcroForm/Fields` and its `/Kids`. A viewer draws the `/Widget` annotations listed in each page's `/Annots`. The two can drift apart:
- **orphan widget** — drawn on the page but not reachable from `/AcroForm/Fields`: it is missing from the `get_fields()` dict and never gets filled;
- **field without a widget** — gets a `/V`, but nothing on the page shows it.

Kid widgets of radio groups and of hierarchical fields carry no `/T` of their own, so the name is built up the `/Parent` chain, the same way `get_fields()` names fields (`address.zip`). Run the audit on the input before filling and on the output afterwards:
```python
from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, ContentStream, DictionaryObject, NameObject


def full_name(node):
    parts = []
    while node is not None:
        if "/T" in node:
            parts.append(str(node["/T"]))
        node = node.get("/Parent")
        node = node.get_object() if node is not None else None
    return ".".join(reversed(parts))


def page_widgets(doc):
    """(page number, reference, widget) for every /Widget annotation; doc is a reader or writer."""
    for pno, page in enumerate(doc.pages, 1):
        for ref in page.get("/Annots") or []:
            w = ref.get_object()
            if w.get("/Subtype") == "/Widget":
                yield pno, ref, w


def audit_form(path):
    r = PdfReader(path)
    acro = r.trailer["/Root"].get("/AcroForm")
    stack = list(acro.get_object().get("/Fields", [])) if acro else []
    reachable = set()  # object numbers reachable from /AcroForm/Fields through /Kids
    while stack:
        ref = stack.pop()
        if ref.idnum not in reachable:
            reachable.add(ref.idnum)
            stack.extend(ref.get_object().get("/Kids", []))
    fields = r.get_fields() or {}
    drawn, orphans = set(), []
    for pno, ref, w in page_widgets(r):
        name = full_name(w)
        if getattr(ref, "idnum", None) in reachable:
            drawn.add(name)
        else:
            orphans.append({"name": name, "page": pno,
                            "parent": "/Parent" in w, "clash": name in fields})
    # Terminal fields (no kids with their own /T) need at least one drawn widget.
    no_widget = [n for n, f in fields.items()
                 if not any("/T" in k.get_object() for k in f.get("/Kids", []))
                 and n not in drawn]
    return {"orphans": orphans, "no_widget": no_widget}
```

### 2. Repairing orphans
`writer.reattach_fields()` appends orphaned widgets to `/AcroForm/Fields`, but it only checks whether a widget is a *top-level* entry there and ignores `/Parent`. On a form with any hierarchy it also appends correctly nested widgets (`address.zip`) and radio kids, producing duplicate fields — in the test `/Fields` grew from 4 entries to 8 and pypdf started warning `address.zip already parsed`. Use it only when no widget in the file has a `/Parent` (or when the file has no `/AcroForm` at all). Otherwise append just the orphans the audit found. Skip an orphan whose name already belongs to a field (`clash`): two fields with one name fight over the value — decide which one is real and link the widget into that field's `/Kids` (setting its `/Parent`) by hand.
```python
def reattach_orphans(src, dst):
    report = audit_form(src)
    manual = [o for o in report["orphans"] if o["parent"] or o["clash"]]
    if manual:
        print("link by hand:", manual)
    safe = {o["name"] for o in report["orphans"] if o not in manual}
    w = PdfWriter(clone_from=PdfReader(src))
    fields = w.root_object["/AcroForm"]["/Fields"]
    for _, ref, obj in page_widgets(w):
        if full_name(obj) in safe and ref not in fields:
            fields.append(ref)
    w.write(dst)
```

### 3. Values and appearances
Reopen the output and check each field: `/V` holds the intended value, and every widget of the field has an appearance. Text and choice widgets need a non-empty `/AP /N` stream (a plain-ASCII value appears in it literally). Checkbox and radio widgets need an `/AS` that names a state present in `/AP /N`, and for any value other than `/Off` at least one widget must have `/AS` equal to it. A checkbox accepts only its own on-state name — reportlab uses `/Yes`, not `/On`; pypdf silently leaves `/V /Off` for a wrong name.
```python
def check_filled(path, expected):
    """expected: {qualified field name: value as given to the fill step}. Returns problems."""
    r = PdfReader(path)
    fields = r.get_fields() or {}
    widgets = {}
    for pno, _, w in page_widgets(r):
        widgets.setdefault(full_name(w), []).append((pno, w))
    problems = []
    for name, want in expected.items():
        want = str(want)
        f = fields.get(name)
        if f is None:
            problems.append(f"{name}: not in the field tree")
            continue
        if str(f.get("/V")) != want:
            problems.append(f"{name}: /V={f.get('/V')!r}, expected {want!r}")
        states = []
        for pno, w in widgets.get(name, []):
            ap = w.get("/AP")
            n = ap.get_object().get("/N") if ap is not None else None
            n = n.get_object() if n is not None else None
            if n is None:
                problems.append(f"{name} p{pno}: no /AP /N")
            elif hasattr(n, "get_data"):  # text / choice: a single stream
                data = n.get_data()
                plain = want.isascii() and not set(want) & set("()\\\r\n")
                if not data.strip():
                    problems.append(f"{name} p{pno}: empty /AP /N stream")
                elif plain and want.encode() not in data:
                    problems.append(f"{name} p{pno}: value not drawn in /AP /N")
            else:  # checkbox / radio: a dict of states, /AS picks one
                states.append(str(w.get("/AS")))
                if w.get("/AS") not in n:
                    problems.append(f"{name} p{pno}: /AS={w.get('/AS')} has no appearance")
        if states and want != "/Off" and want not in states:
            problems.append(f"{name}: no widget shows {want} (/AS: {states})")
    return problems
```

`set_need_appearances_writer(True)` sets `/NeedAppearances true`. Poppler (`pdftoppm`, and `pdf2image` on top of it) then rebuilds widget appearances on its own, and without the right system fonts it cannot draw the ZapfDingbats check and radio glyphs: checkboxes and radios look empty in the PNG although `/V`, `/AS` and `/AP` are correct. To see what a viewer that trusts the stored appearances shows, render a preview copy with the flag off:
```python
def preview_copy(src, dst):
    w = PdfWriter(clone_from=PdfReader(src))
    w.root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(False)
    w.write(dst)
```

### 4. Flatten only when asked
Leave the form editable unless a non-editable copy is explicitly requested. Then:
- **text-only forms:** `writer.update_page_form_field_values(page, values, flatten=True)` stamps the appearances into the page content but leaves the widgets on top of it. Follow with `writer.remove_annotations(subtypes="/Widget")` and delete `/AcroForm` from `writer.root_object`, otherwise the values are drawn twice and the form stays live.
- **forms with checkboxes or radios:** in pypdf 6.2.0 `flatten=True` raises `KeyError: '/Font'` on button appearances that have no font resource (reportlab's do), and radio kids that share one name collide on the XObject `/Fm_<name>` (warning `already added to page resources`), so every kid is stamped with the first kid's picture and the selection is lost. Stamp the widgets yourself, starting from the filled file that already passed `check_filled()`:
```python
def stamp_widgets(writer):
    """Draw each visible widget's current appearance into its page, then drop all
    widgets and /AcroForm. Every widget gets its own XObject name. Assumes the
    appearance streams carry no rotating /Matrix — check the render."""
    for page in writer.pages:
        res = page.get("/Resources")
        res = res.get_object() if res is not None else DictionaryObject()
        page[NameObject("/Resources")] = res
        xobjs = res.get("/XObject")
        xobjs = xobjs.get_object() if xobjs is not None else DictionaryObject()
        res[NameObject("/XObject")] = xobjs
        ops = []
        for i, ref in enumerate(page.get("/Annots") or []):
            w = ref.get_object()
            ap = w.get("/AP")
            if w.get("/Subtype") != "/Widget" or ap is None or int(w.get("/F", 0)) & 2:
                continue  # not a widget, no appearance, or hidden
            n = ap.get_object().get("/N")
            n = n.get_object() if n is not None else None
            if n is not None and not hasattr(n, "get_data"):  # button: /AS picks the state
                n = n.get(w.get("/AS", "/Off"))
                n = n.get_object() if n is not None else None
            if n is None:
                continue
            x1, y1, x2, y2 = (float(v) for v in w["/Rect"])
            bx1, by1, bx2, by2 = (float(v) for v in n.get("/BBox", [0, 0, x2 - x1, y2 - y1]))
            sx = (x2 - x1) / (bx2 - bx1) if bx2 != bx1 else 1
            sy = (y2 - y1) / (by2 - by1) if by2 != by1 else 1
            name = f"/Flat{i}"
            xobjs[NameObject(name)] = n.indirect_reference
            ops.append(f"q {sx:g} 0 0 {sy:g} {x1 - bx1 * sx:g} {y1 - by1 * sy:g} cm {name} Do Q")
        if ops:
            old = page.get_contents()
            body = old.get_data() if old is not None else b""
            new = ContentStream(None, writer)
            new.set_data(b"q\n" + body + b"\nQ\n" + "\n".join(ops).encode() + b"\n")
            page.replace_contents(new)
    writer.remove_annotations(subtypes="/Widget")
    if "/AcroForm" in writer.root_object:
        del writer.root_object[NameObject("/AcroForm")]


# w = PdfWriter(clone_from=PdfReader("filled.pdf")); stamp_widgets(w); w.write("flat.pdf")
```
`remove_annotations(subtypes="/Widget")` removes every widget, signature fields and push buttons included. That is what flattening means, but say so if the form had them.

### 5. Reopen and look
- editable result: `check_filled()` returns `[]` and `audit_form()` reports no orphans;
- flattened result: no `/AcroForm` in the root, no `/Widget` in any page's `/Annots`, `get_fields()` returns `None`, and `page.extract_text()` contains the entered values;
- render every page and look at it: `pdftoppm -png -r 110 <output.pdf> <dir>/page` (or `pdf2image.convert_from_path`). For an editable form render the `preview_copy()`.

