**CRITICAL: You MUST complete these steps in order. Do not skip ahead to writing code.**

If you need to fill out a PDF form, first check to see if the PDF has fillable form fields. Run this script from this file's directory:
 `python scripts/check_fillable_fields.py <file.pdf>`, and depending on the result go to either the "Fillable fields" or "Non-fillable fields" and follow those instructions.

# Fillable fields
If the PDF has fillable form fields:
- Run this script from this file's directory: `python scripts/extract_form_field_info.py <input.pdf> <field_info.json>`. It will create a JSON file with a list of fields in this format:
```
[
  {
    "field_id": (unique ID for the field),
    "page": (page number, 1-based),
    "rect": ([left, bottom, right, top] bounding box in PDF coordinates, y=0 is the bottom of the page),
    "type": ("text", "checkbox", "radio_group", or "choice"),
  },
  // Checkboxes have "checked_value" and "unchecked_value" properties:
  {
    "field_id": (unique ID for the field),
    "page": (page number, 1-based),
    "type": "checkbox",
    "checked_value": (Set the field to this value to check the checkbox),
    "unchecked_value": (Set the field to this value to uncheck the checkbox),
  },
  // Radio groups have a "radio_options" list with the possible choices.
  {
    "field_id": (unique ID for the field),
    "page": (page number, 1-based),
    "type": "radio_group",
    "radio_options": [
      {
        "value": (set the field to this value to select this radio option),
        "rect": (bounding box for the radio button for this option)
      },
      // Other radio options
    ]
  },
  // Multiple choice fields have a "choice_options" list with the possible choices:
  {
    "field_id": (unique ID for the field),
    "page": (page number, 1-based),
    "type": "choice",
    "choice_options": [
      {
        "value": (set the field to this value to select this option),
        "text": (display text of the option)
      },
      // Other choice options
    ],
  }
]
```
- Convert the PDF to PNGs (one image for each page) with this script (run from this file's directory):
`python scripts/convert_pdf_to_images.py <file.pdf> <output_directory>`
Then analyze the images to determine the purpose of each form field (make sure to convert the bounding box PDF coordinates to image coordinates).
- Create a `field_values.json` file in this format with the values to be entered for each field:
```
[
  {
    "field_id": "last_name", // Must match the field_id from `extract_form_field_info.py`
    "description": "The user's last name",
    "page": 1, // Must match the "page" value in field_info.json
    "value": "Simpson"
  },
  {
    "field_id": "Checkbox12",
    "description": "Checkbox to be checked if the user is 18 or over",
    "page": 1,
    "value": "/On" // If this is a checkbox, use its "checked_value" value to check it. If it's a radio button group, use one of the "value" values in "radio_options".
  },
  // more fields
]
```
- Run the `fill_fillable_fields.py` script from this file's directory to create a filled-in PDF:
`python scripts/fill_fillable_fields.py <input pdf> <field_values.json> <output pdf>`
This script will verify that the field IDs and values you provide are valid; if it prints error messages, correct the appropriate fields and try again.

## Post-fill verification (Проверка после заполнения)
A clean run of `fill_fillable_fields.py` only means the IDs and values were accepted. It does not prove that every field on the page is reachable, or that a viewer will draw the values. Do the checks below; the helpers were tested with pypdf 6.2.0 on a reportlab form with text fields, a checkbox, a radio group and a hierarchical field.

### 1. Field tree vs. page widgets
`get_fields()` (and therefore `extract_form_field_info.py`) walks `/AcroForm/Fields` and its `/Kids`. A viewer draws the `/Widget` annotations listed in each page's `/Annots`. The two can drift apart:
- **orphan widget** — drawn on the page but not reachable from `/AcroForm/Fields`: it is missing from `field_info.json` and never gets filled;
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

`fill_fillable_fields.py` sets `/NeedAppearances true`. Poppler (`pdftoppm`, and `pdf2image` inside `convert_pdf_to_images.py`) then rebuilds widget appearances on its own, and on some machines (seen on Windows) it cannot draw the ZapfDingbats check and radio glyphs: checkboxes and radios look empty in the PNG although `/V`, `/AS` and `/AP` are correct. To see what a viewer that trusts the stored appearances shows, render a preview copy with the flag off:
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
- render every page and look at it: `python scripts/convert_pdf_to_images.py <output.pdf> <dir>` or `pdftoppm -png -r 110 <output.pdf> <dir>/page`. For an editable form render the `preview_copy()`.

# Non-fillable fields
If the PDF doesn't have fillable form fields, you'll need to visually determine where the data should be added and create text annotations. Follow the below steps *exactly*. You MUST perform all of these steps to ensure that the the form is accurately completed. Details for each step are below.
- Convert the PDF to PNG images and determine field bounding boxes.
- Create a JSON file with field information and validation images showing the bounding boxes.
- Validate the the bounding boxes.
- Use the bounding boxes to fill in the form.

## Step 1: Visual Analysis (REQUIRED)
- Convert the PDF to PNG images. Run this script from this file's directory:
`python scripts/convert_pdf_to_images.py <file.pdf> <output_directory>`
The script will create a PNG image for each page in the PDF.
- Carefully examine each PNG image and identify all form fields and areas where the user should enter data. For each form field where the user should enter text, determine bounding boxes for both the form field label, and the area where the user should enter text. The label and entry bounding boxes MUST NOT INTERSECT; the text entry box should only include the area where data should be entered. Usually this area will be immediately to the side, above, or below its label. Entry bounding boxes must be tall and wide enough to contain their text.

These are some examples of form structures that you might see:

*Label inside box*
```
┌────────────────────────┐
│ Name:                  │
└────────────────────────┘
```
The input area should be to the right of the "Name" label and extend to the edge of the box.

*Label before line*
```
Email: _______________________
```
The input area should be above the line and include its entire width.

*Label under line*
```
_________________________
Name
```
The input area should be above the line and include the entire width of the line. This is common for signature and date fields.

*Label above line*
```
Please enter any special requests:
________________________________________________
```
The input area should extend from the bottom of the label to the line, and should include the entire width of the line.

*Checkboxes*
```
Are you a US citizen? Yes □  No □
```
For checkboxes:
- Look for small square boxes (□) - these are the actual checkboxes to target. They may be to the left or right of their labels.
- Distinguish between label text ("Yes", "No") and the clickable checkbox squares.
- The entry bounding box should cover ONLY the small square, not the text label.

### Step 2: Create fields.json and validation images (REQUIRED)
- Create a file named `fields.json` with information for the form fields and bounding boxes in this format:
```
{
  "pages": [
    {
      "page_number": 1,
      "image_width": (first page image width in pixels),
      "image_height": (first page image height in pixels),
    },
    {
      "page_number": 2,
      "image_width": (second page image width in pixels),
      "image_height": (second page image height in pixels),
    }
    // additional pages
  ],
  "form_fields": [
    // Example for a text field.
    {
      "page_number": 1,
      "description": "The user's last name should be entered here",
      // Bounding boxes are [left, top, right, bottom]. The bounding boxes for the label and text entry should not overlap.
      "field_label": "Last name",
      "label_bounding_box": [30, 125, 95, 142],
      "entry_bounding_box": [100, 125, 280, 142],
      "entry_text": {
        "text": "Johnson", // This text will be added as an annotation at the entry_bounding_box location
        "font_size": 14, // optional, defaults to 14
        "font_color": "000000", // optional, RRGGBB format, defaults to 000000 (black)
      }
    },
    // Example for a checkbox. TARGET THE SQUARE for the entry bounding box, NOT THE TEXT
    {
      "page_number": 2,
      "description": "Checkbox that should be checked if the user is over 18",
      "entry_bounding_box": [140, 525, 155, 540],  // Small box over checkbox square
      "field_label": "Yes",
      "label_bounding_box": [100, 525, 132, 540],  // Box containing "Yes" text
      // Use "X" to check a checkbox.
      "entry_text": {
        "text": "X",
      }
    }
    // additional form field entries
  ]
}
```

Create validation images by running this script from this file's directory for each page:
`python scripts/create_validation_image.py <page_number> <path_to_fields.json> <input_image_path> <output_image_path>

The validation images will have red rectangles where text should be entered, and blue rectangles covering label text.

### Step 3: Validate Bounding Boxes (REQUIRED)
#### Automated intersection check
- Verify that none of bounding boxes intersect and that the entry bounding boxes are tall enough by checking the fields.json file with the `check_bounding_boxes.py` script (run from this file's directory):
`python scripts/check_bounding_boxes.py <JSON file>`

If there are errors, reanalyze the relevant fields, adjust the bounding boxes, and iterate until there are no remaining errors. Remember: label (blue) bounding boxes should contain text labels, entry (red) boxes should not.

#### Manual image inspection
**CRITICAL: Do not proceed without visually inspecting validation images**
- Red rectangles must ONLY cover input areas
- Red rectangles MUST NOT contain any text
- Blue rectangles should contain label text
- For checkboxes:
  - Red rectangle MUST be centered on the checkbox square
  - Blue rectangle should cover the text label for the checkbox

- If any rectangles look wrong, fix fields.json, regenerate the validation images, and verify again. Repeat this process until the bounding boxes are fully accurate.


### Step 4: Add annotations to the PDF
Run this script from this file's directory to create a filled-out PDF using the information in fields.json:
`python scripts/fill_pdf_form_with_annotations.py <input_pdf_path> <path_to_fields.json> <output_pdf_path>
