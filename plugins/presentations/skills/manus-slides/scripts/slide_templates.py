"""
Slide Templates - Template catalog and HTML generators for Manus-style slides.

8 categories, 32 templates. Each generates self-contained HTML with Tailwind CSS.
Adapted from Manus AI template system.

Usage:
    python slide_templates.py list
    python slide_templates.py get <template_key> '{"title": "Hello", "content": "World"}'
    python slide_templates.py categories
"""

import json
import sys

# --- Template Categories ---

CATEGORIES = {
    "landing": {
        "name": "Landing",
        "description": "Bold headlines, gradient backgrounds, CTA buttons",
        "templates": ["landing-hero", "landing-features", "landing-cta", "landing-stats"],
    },
    "portfolio": {
        "name": "Portfolio",
        "description": "Image-focused, grids, minimal text",
        "templates": ["portfolio-gallery", "portfolio-case", "portfolio-showcase", "portfolio-grid"],
    },
    "event": {
        "name": "Event",
        "description": "Date/time prominent, countdown, RSVP aesthetic",
        "templates": ["event-announce", "event-schedule", "event-speaker", "event-venue"],
    },
    "dashboard": {
        "name": "Dashboard",
        "description": "Charts, metrics, dark themes",
        "templates": ["dashboard-metrics", "dashboard-chart", "dashboard-kpi", "dashboard-table"],
    },
    "minimal": {
        "name": "Minimal",
        "description": "Clean, whitespace, typography-focused",
        "templates": ["minimal-text", "minimal-quote", "minimal-split", "minimal-list"],
    },
    "dark": {
        "name": "Dark",
        "description": "Dark backgrounds, neon accents, tech-style",
        "templates": ["dark-neon", "dark-gradient", "dark-code", "dark-cyber"],
    },
    "professional": {
        "name": "Professional",
        "description": "Corporate, formal, structured layouts",
        "templates": ["professional-title", "professional-content", "professional-comparison", "professional-timeline"],
    },
    "creative": {
        "name": "Creative",
        "description": "Animations, unusual layouts, artistic",
        "templates": ["creative-bold", "creative-magazine", "creative-collage", "creative-gradient"],
    },
}

# --- Base HTML wrapper ---

def _wrap_html(body_content: str, title: str = "Slide", extra_css: str = "") -> str:
    """Wrap slide content in full HTML document."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@400;700;900&display=swap" rel="stylesheet">
<style>
  body {{ margin: 0; padding: 0; width: 1280px; height: 720px; overflow: hidden; font-family: 'Inter', sans-serif; }}
  .slide {{ width: 1280px; height: 720px; position: relative; overflow: hidden; }}
  .font-display {{ font-family: 'Playfair Display', serif; }}
  {extra_css}
</style>
</head>
<body>
{body_content}
</body>
</html>"""


# --- Template Generators ---
# Each returns complete HTML string for a 1280x720 slide.

def _landing_hero(data: dict) -> str:
    title = data.get("title", "Welcome")
    subtitle = data.get("subtitle", "")
    cta = data.get("cta", "")
    gradient_from = data.get("gradient_from", "indigo-600")
    gradient_to = data.get("gradient_to", "purple-700")

    body = f"""<div class="slide flex flex-col items-center justify-center bg-gradient-to-br from-{gradient_from} to-{gradient_to} text-white p-16 text-center">
  <h1 class="text-6xl font-black mb-6 leading-tight max-w-4xl">{title}</h1>
  {"<p class='text-2xl text-white/80 mb-10 max-w-2xl'>" + subtitle + "</p>" if subtitle else ""}
  {"<button class='px-8 py-4 bg-white text-indigo-700 font-bold rounded-full text-lg hover:scale-105 transition-transform shadow-xl'>" + cta + "</button>" if cta else ""}
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _landing_features(data: dict) -> str:
    title = data.get("title", "Features")
    features = data.get("features", [])
    if not features:
        features = [{"icon": "1", "name": "Feature 1", "desc": "Description"},
                     {"icon": "2", "name": "Feature 2", "desc": "Description"},
                     {"icon": "3", "name": "Feature 3", "desc": "Description"}]

    cards = ""
    for f in features[:4]:
        cards += f"""<div class="bg-white/10 backdrop-blur rounded-2xl p-6 text-center">
      <div class="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold">{f.get('icon', '#')}</div>
      <h3 class="text-xl font-bold mb-2">{f.get('name', '')}</h3>
      <p class="text-white/70 text-sm">{f.get('desc', '')}</p>
    </div>"""

    body = f"""<div class="slide flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 to-indigo-900 text-white p-16">
  <h2 class="text-4xl font-bold mb-12">{title}</h2>
  <div class="grid grid-cols-{min(len(features), 4)} gap-8 max-w-5xl">{cards}</div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _landing_cta(data: dict) -> str:
    title = data.get("title", "Ready to start?")
    subtitle = data.get("subtitle", "")
    cta = data.get("cta", "Get Started")

    body = f"""<div class="slide flex flex-col items-center justify-center bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white p-16 text-center">
  <h1 class="text-5xl font-black mb-6">{title}</h1>
  {"<p class='text-xl text-white/80 mb-10 max-w-2xl'>" + subtitle + "</p>" if subtitle else ""}
  <button class="px-10 py-5 bg-white text-violet-700 font-bold rounded-full text-xl shadow-2xl hover:scale-105 transition-transform">{cta}</button>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _landing_stats(data: dict) -> str:
    title = data.get("title", "By the Numbers")
    stats = data.get("stats", [])
    if not stats:
        stats = [{"value": "10K+", "label": "Users"}, {"value": "99%", "label": "Uptime"}, {"value": "50+", "label": "Countries"}]

    cards = ""
    for s in stats[:4]:
        cards += f"""<div class="text-center">
      <div class="text-5xl font-black text-white mb-2">{s.get('value', '0')}</div>
      <div class="text-lg text-white/60">{s.get('label', '')}</div>
    </div>"""

    body = f"""<div class="slide flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 to-slate-800 text-white p-16">
  <h2 class="text-4xl font-bold mb-16">{title}</h2>
  <div class="flex gap-20">{cards}</div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _portfolio_gallery(data: dict) -> str:
    title = data.get("title", "Our Work")
    items = data.get("items", [{"label": "Project 1"}, {"label": "Project 2"}, {"label": "Project 3"}, {"label": "Project 4"}])

    cards = ""
    colors = ["from-pink-500 to-rose-500", "from-blue-500 to-cyan-500", "from-amber-500 to-orange-500", "from-emerald-500 to-teal-500"]
    for i, item in enumerate(items[:4]):
        c = colors[i % len(colors)]
        cards += f"""<div class="bg-gradient-to-br {c} rounded-xl aspect-video flex items-end p-4">
      <span class="text-white font-bold text-lg">{item.get('label', '')}</span>
    </div>"""

    body = f"""<div class="slide flex flex-col bg-white p-16">
  <h2 class="text-4xl font-bold text-gray-900 mb-10">{title}</h2>
  <div class="grid grid-cols-2 gap-6 flex-1">{cards}</div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _portfolio_case(data: dict) -> str:
    title = data.get("title", "Case Study")
    client = data.get("client", "")
    description = data.get("description", "")
    result = data.get("result", "")

    body = f"""<div class="slide flex bg-white">
  <div class="w-1/2 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center p-12">
    <div class="text-white text-center">
      <div class="text-lg text-gray-400 mb-4">Case Study</div>
      <h2 class="text-4xl font-bold">{title}</h2>
      {"<div class='mt-4 text-gray-300'>" + client + "</div>" if client else ""}
    </div>
  </div>
  <div class="w-1/2 flex flex-col justify-center p-12">
    {"<p class='text-lg text-gray-600 mb-8'>" + description + "</p>" if description else ""}
    {"<div class='bg-green-50 border-l-4 border-green-500 p-4'><p class='text-green-800 font-semibold'>" + result + "</p></div>" if result else ""}
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _portfolio_showcase(data: dict) -> str:
    return _portfolio_gallery(data)  # variant of gallery


def _portfolio_grid(data: dict) -> str:
    return _portfolio_gallery(data)  # variant of gallery


def _event_announce(data: dict) -> str:
    title = data.get("title", "Event Name")
    date = data.get("date", "")
    location = data.get("location", "")
    tagline = data.get("tagline", "")

    body = f"""<div class="slide flex flex-col items-center justify-center bg-gradient-to-br from-amber-500 to-orange-600 text-white p-16 text-center">
  {"<div class='text-lg font-semibold tracking-widest uppercase mb-6 text-white/80'>" + tagline + "</div>" if tagline else ""}
  <h1 class="text-6xl font-black mb-8 font-display">{title}</h1>
  {"<div class='text-2xl mb-2'>" + date + "</div>" if date else ""}
  {"<div class='text-xl text-white/80'>" + location + "</div>" if location else ""}
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _event_schedule(data: dict) -> str:
    title = data.get("title", "Schedule")
    items = data.get("items", [])
    if not items:
        items = [{"time": "09:00", "name": "Opening", "desc": "Welcome address"},
                 {"time": "10:00", "name": "Keynote", "desc": "Main presentation"},
                 {"time": "12:00", "name": "Lunch", "desc": "Networking break"}]

    rows = ""
    for item in items[:6]:
        rows += f"""<div class="flex items-start gap-6 py-4 border-b border-gray-200">
      <div class="text-xl font-bold text-amber-600 w-20 shrink-0">{item.get('time', '')}</div>
      <div><div class="text-lg font-bold text-gray-900">{item.get('name', '')}</div>
      <div class="text-gray-500">{item.get('desc', '')}</div></div>
    </div>"""

    body = f"""<div class="slide flex flex-col bg-white p-16">
  <h2 class="text-4xl font-bold text-gray-900 mb-10">{title}</h2>
  <div class="flex-1 overflow-hidden">{rows}</div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _event_speaker(data: dict) -> str:
    title = data.get("title", "Speaker")
    name = data.get("name", "John Doe")
    role = data.get("role", "CEO")
    bio = data.get("bio", "")

    body = f"""<div class="slide flex bg-white">
  <div class="w-2/5 bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
    <div class="w-48 h-48 rounded-full bg-white/30 flex items-center justify-center text-6xl font-bold text-white">{name[0] if name else '?'}</div>
  </div>
  <div class="w-3/5 flex flex-col justify-center p-16">
    <div class="text-sm text-amber-600 font-semibold uppercase tracking-wider mb-2">{title}</div>
    <h2 class="text-4xl font-bold text-gray-900 mb-2">{name}</h2>
    <div class="text-xl text-gray-500 mb-6">{role}</div>
    {"<p class='text-gray-600 leading-relaxed'>" + bio + "</p>" if bio else ""}
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _event_venue(data: dict) -> str:
    return _event_announce(data)  # variant


def _dashboard_metrics(data: dict) -> str:
    title = data.get("title", "Key Metrics")
    metrics = data.get("metrics", [])
    if not metrics:
        metrics = [{"label": "Revenue", "value": "$1.2M", "change": "+12%"},
                   {"label": "Users", "value": "45.2K", "change": "+8%"},
                   {"label": "Conversion", "value": "3.4%", "change": "+0.5%"},
                   {"label": "Retention", "value": "87%", "change": "-2%"}]

    cards = ""
    for m in metrics[:4]:
        change = m.get("change", "")
        is_positive = change.startswith("+") if change else True
        color = "text-green-400" if is_positive else "text-red-400"
        cards += f"""<div class="bg-gray-800 rounded-xl p-6">
      <div class="text-gray-400 text-sm mb-2">{m.get('label', '')}</div>
      <div class="text-3xl font-bold text-white mb-1">{m.get('value', '0')}</div>
      <div class="{color} text-sm font-semibold">{change}</div>
    </div>"""

    body = f"""<div class="slide flex flex-col bg-gray-900 p-16">
  <h2 class="text-3xl font-bold text-white mb-10">{title}</h2>
  <div class="grid grid-cols-4 gap-6">{cards}</div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _dashboard_chart(data: dict) -> str:
    title = data.get("title", "Performance")
    subtitle = data.get("subtitle", "")

    body = f"""<div class="slide flex flex-col bg-gray-900 p-16">
  <h2 class="text-3xl font-bold text-white mb-2">{title}</h2>
  {"<p class='text-gray-400 mb-8'>" + subtitle + "</p>" if subtitle else "<div class='mb-8'></div>"}
  <div class="flex-1 bg-gray-800 rounded-xl p-8 flex items-end gap-3">
    <div class="bg-blue-500 rounded-t w-1/12" style="height:40%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:55%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:35%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:70%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:60%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:80%"></div>
    <div class="bg-cyan-400 rounded-t w-1/12" style="height:90%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:75%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:65%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:85%"></div>
    <div class="bg-blue-500 rounded-t w-1/12" style="height:70%"></div>
    <div class="bg-blue-400/50 rounded-t w-1/12" style="height:50%"></div>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _dashboard_kpi(data: dict) -> str:
    return _dashboard_metrics(data)  # variant


def _dashboard_table(data: dict) -> str:
    title = data.get("title", "Data Table")
    headers = data.get("headers", ["Name", "Value", "Change", "Status"])
    rows = data.get("rows", [["Item 1", "$100", "+5%", "Active"], ["Item 2", "$200", "-3%", "Pending"]])

    thead = "".join(f"<th class='text-left text-gray-400 text-sm font-semibold pb-3 px-4'>{h}</th>" for h in headers)
    tbody = ""
    for row in rows[:8]:
        cells = "".join(f"<td class='py-3 px-4 text-gray-300'>{c}</td>" for c in row)
        tbody += f"<tr class='border-b border-gray-800'>{cells}</tr>"

    body = f"""<div class="slide flex flex-col bg-gray-900 p-16">
  <h2 class="text-3xl font-bold text-white mb-8">{title}</h2>
  <div class="bg-gray-800 rounded-xl p-6 flex-1 overflow-hidden">
    <table class="w-full"><thead><tr class="border-b border-gray-700">{thead}</tr></thead>
    <tbody>{tbody}</tbody></table>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _minimal_text(data: dict) -> str:
    title = data.get("title", "")
    content = data.get("content", "")

    body = f"""<div class="slide flex flex-col items-center justify-center bg-white p-24 text-center">
  <h1 class="text-5xl font-bold text-gray-900 mb-8 font-display">{title}</h1>
  <p class="text-xl text-gray-500 max-w-3xl leading-relaxed">{content}</p>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _minimal_quote(data: dict) -> str:
    quote = data.get("quote", data.get("content", ""))
    author = data.get("author", "")

    body = f"""<div class="slide flex flex-col items-center justify-center bg-gray-50 p-24 text-center">
  <div class="text-6xl text-gray-300 mb-6 font-display">&ldquo;</div>
  <blockquote class="text-3xl text-gray-800 max-w-3xl leading-relaxed font-display italic">{quote}</blockquote>
  {"<cite class='mt-8 text-lg text-gray-500 not-italic'>&mdash; " + author + "</cite>" if author else ""}
</div>"""
    return _wrap_html(body, data.get("page_title", "Quote"))


def _minimal_split(data: dict) -> str:
    title = data.get("title", "")
    left = data.get("left", "")
    right = data.get("right", "")

    body = f"""<div class="slide flex bg-white">
  <div class="w-1/2 flex flex-col justify-center p-16 bg-gray-50">
    <h2 class="text-4xl font-bold text-gray-900 mb-6 font-display">{title}</h2>
    <p class="text-lg text-gray-600 leading-relaxed">{left}</p>
  </div>
  <div class="w-1/2 flex flex-col justify-center p-16">
    <p class="text-lg text-gray-600 leading-relaxed">{right}</p>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _minimal_list(data: dict) -> str:
    title = data.get("title", "")
    items = data.get("items", [])
    if not items:
        items = ["Point one", "Point two", "Point three"]

    list_items = "".join(
        f"<li class='py-3 border-b border-gray-100 text-lg text-gray-700'>{item}</li>"
        for item in items[:8]
    )

    body = f"""<div class="slide flex flex-col justify-center bg-white p-24">
  <h2 class="text-4xl font-bold text-gray-900 mb-10 font-display">{title}</h2>
  <ul class="max-w-3xl">{list_items}</ul>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _dark_neon(data: dict) -> str:
    title = data.get("title", "")
    content = data.get("content", "")
    accent = data.get("accent", "cyan")

    css = f".neon-text {{ text-shadow: 0 0 20px rgb(var(--neon-color)), 0 0 40px rgb(var(--neon-color)); }}"
    body = f"""<div class="slide flex flex-col items-center justify-center bg-black p-16 text-center">
  <h1 class="text-6xl font-black text-{accent}-400 mb-8" style="text-shadow: 0 0 30px currentColor, 0 0 60px currentColor">{title}</h1>
  <p class="text-xl text-gray-400 max-w-3xl">{content}</p>
</div>"""
    return _wrap_html(body, data.get("page_title", title), css)


def _dark_gradient(data: dict) -> str:
    title = data.get("title", "")
    content = data.get("content", "")

    body = f"""<div class="slide flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white p-16 text-center">
  <h1 class="text-5xl font-bold mb-8 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">{title}</h1>
  <p class="text-xl text-gray-300 max-w-3xl">{content}</p>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _dark_code(data: dict) -> str:
    title = data.get("title", "Code")
    code = data.get("code", "// Your code here")
    language = data.get("language", "javascript")

    body = f"""<div class="slide flex flex-col bg-gray-950 p-16">
  <h2 class="text-3xl font-bold text-white mb-8">{title}</h2>
  <div class="flex-1 bg-gray-900 rounded-xl p-8 font-mono text-sm overflow-hidden">
    <div class="text-gray-500 mb-4">{language}</div>
    <pre class="text-green-400 whitespace-pre-wrap leading-relaxed">{code}</pre>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _dark_cyber(data: dict) -> str:
    return _dark_neon(data)  # variant with different accent


def _professional_title(data: dict) -> str:
    title = data.get("title", "Presentation Title")
    subtitle = data.get("subtitle", "")
    author = data.get("author", "")
    date = data.get("date", "")
    color = data.get("color", "blue")

    body = f"""<div class="slide flex bg-white">
  <div class="w-2 bg-{color}-600"></div>
  <div class="flex-1 flex flex-col justify-center p-20">
    <h1 class="text-5xl font-bold text-gray-900 mb-4">{title}</h1>
    {"<p class='text-2xl text-gray-500 mb-8'>" + subtitle + "</p>" if subtitle else ""}
    <div class="flex gap-8 text-gray-400 mt-auto">
      {"<span>" + author + "</span>" if author else ""}
      {"<span>" + date + "</span>" if date else ""}
    </div>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _professional_content(data: dict) -> str:
    title = data.get("title", "Content")
    content = data.get("content", "")
    bullets = data.get("bullets", [])

    bullets_html = ""
    if bullets:
        items = "".join(f"<li class='py-2 text-gray-600'>{b}</li>" for b in bullets[:8])
        bullets_html = f"<ul class='list-disc pl-6 space-y-1 mt-6'>{items}</ul>"

    body = f"""<div class="slide flex flex-col bg-white p-16">
  <div class="w-16 h-1 bg-blue-600 mb-8"></div>
  <h2 class="text-4xl font-bold text-gray-900 mb-6">{title}</h2>
  {"<p class='text-lg text-gray-600 leading-relaxed max-w-4xl'>" + content + "</p>" if content else ""}
  {bullets_html}
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _professional_comparison(data: dict) -> str:
    title = data.get("title", "Comparison")
    left_title = data.get("left_title", "Option A")
    right_title = data.get("right_title", "Option B")
    left_items = data.get("left_items", ["Feature 1", "Feature 2"])
    right_items = data.get("right_items", ["Feature 1", "Feature 2"])

    left_html = "".join(f"<li class='py-2 text-gray-600'>{i}</li>" for i in left_items[:6])
    right_html = "".join(f"<li class='py-2 text-gray-600'>{i}</li>" for i in right_items[:6])

    body = f"""<div class="slide flex flex-col bg-white p-16">
  <h2 class="text-4xl font-bold text-gray-900 mb-10">{title}</h2>
  <div class="flex gap-8 flex-1">
    <div class="flex-1 bg-blue-50 rounded-xl p-8">
      <h3 class="text-xl font-bold text-blue-800 mb-4">{left_title}</h3>
      <ul class="list-disc pl-5 space-y-1">{left_html}</ul>
    </div>
    <div class="flex-1 bg-gray-50 rounded-xl p-8">
      <h3 class="text-xl font-bold text-gray-800 mb-4">{right_title}</h3>
      <ul class="list-disc pl-5 space-y-1">{right_html}</ul>
    </div>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _professional_timeline(data: dict) -> str:
    title = data.get("title", "Timeline")
    items = data.get("items", [])
    if not items:
        items = [{"date": "Q1", "event": "Planning"}, {"date": "Q2", "event": "Development"}, {"date": "Q3", "event": "Launch"}]

    nodes = ""
    for i, item in enumerate(items[:5]):
        nodes += f"""<div class="flex flex-col items-center text-center flex-1">
      <div class="w-4 h-4 rounded-full bg-blue-600 mb-3"></div>
      <div class="font-bold text-gray-900">{item.get('date', '')}</div>
      <div class="text-sm text-gray-500 mt-1">{item.get('event', '')}</div>
    </div>"""

    body = f"""<div class="slide flex flex-col justify-center bg-white p-16">
  <h2 class="text-4xl font-bold text-gray-900 mb-16">{title}</h2>
  <div class="relative">
    <div class="absolute top-2 left-0 right-0 h-0.5 bg-gray-200"></div>
    <div class="flex justify-between">{nodes}</div>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _creative_bold(data: dict) -> str:
    title = data.get("title", "BOLD")
    subtitle = data.get("subtitle", "")

    body = f"""<div class="slide flex flex-col items-center justify-center bg-yellow-400 p-16 text-center">
  <h1 class="text-8xl font-black text-black leading-none">{title}</h1>
  {"<p class='text-2xl text-black/60 mt-6'>" + subtitle + "</p>" if subtitle else ""}
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _creative_magazine(data: dict) -> str:
    title = data.get("title", "")
    content = data.get("content", "")
    category = data.get("category", "")

    body = f"""<div class="slide flex bg-white">
  <div class="w-1/2 bg-gradient-to-br from-rose-400 to-pink-600 p-12 flex flex-col justify-end">
    {"<div class='text-sm text-white/80 uppercase tracking-widest mb-4'>" + category + "</div>" if category else ""}
    <h1 class="text-5xl font-black text-white leading-tight font-display">{title}</h1>
  </div>
  <div class="w-1/2 flex items-center p-12">
    <p class="text-lg text-gray-600 leading-relaxed">{content}</p>
  </div>
</div>"""
    return _wrap_html(body, data.get("page_title", title))


def _creative_collage(data: dict) -> str:
    return _portfolio_gallery(data)  # variant


def _creative_gradient(data: dict) -> str:
    return _dark_gradient(data)  # variant


# --- Template Registry ---

TEMPLATES = {
    "landing-hero": _landing_hero,
    "landing-features": _landing_features,
    "landing-cta": _landing_cta,
    "landing-stats": _landing_stats,
    "portfolio-gallery": _portfolio_gallery,
    "portfolio-case": _portfolio_case,
    "portfolio-showcase": _portfolio_showcase,
    "portfolio-grid": _portfolio_grid,
    "event-announce": _event_announce,
    "event-schedule": _event_schedule,
    "event-speaker": _event_speaker,
    "event-venue": _event_venue,
    "dashboard-metrics": _dashboard_metrics,
    "dashboard-chart": _dashboard_chart,
    "dashboard-kpi": _dashboard_kpi,
    "dashboard-table": _dashboard_table,
    "minimal-text": _minimal_text,
    "minimal-quote": _minimal_quote,
    "minimal-split": _minimal_split,
    "minimal-list": _minimal_list,
    "dark-neon": _dark_neon,
    "dark-gradient": _dark_gradient,
    "dark-code": _dark_code,
    "dark-cyber": _dark_cyber,
    "professional-title": _professional_title,
    "professional-content": _professional_content,
    "professional-comparison": _professional_comparison,
    "professional-timeline": _professional_timeline,
    "creative-bold": _creative_bold,
    "creative-magazine": _creative_magazine,
    "creative-collage": _creative_collage,
    "creative-gradient": _creative_gradient,
}

# Category aliases: "professional" -> "professional-content", etc.
CATEGORY_DEFAULTS = {
    "landing": "landing-hero",
    "portfolio": "portfolio-gallery",
    "event": "event-announce",
    "dashboard": "dashboard-metrics",
    "minimal": "minimal-text",
    "dark": "dark-gradient",
    "professional": "professional-content",
    "creative": "creative-bold",
}


def get_template_html(template_key: str, slide_data: dict) -> str:
    """Generate HTML for a slide using the specified template."""
    # Try exact match first
    if template_key in TEMPLATES:
        return TEMPLATES[template_key](slide_data)

    # Try category default
    if template_key in CATEGORY_DEFAULTS:
        return TEMPLATES[CATEGORY_DEFAULTS[template_key]](slide_data)

    # Fallback to professional-content
    return TEMPLATES["professional-content"](slide_data)


def list_templates() -> list:
    """Return all available templates with metadata."""
    result = []
    for category_key, cat in CATEGORIES.items():
        for tmpl_key in cat["templates"]:
            result.append({
                "key": tmpl_key,
                "category": category_key,
                "category_name": cat["name"],
                "description": cat["description"],
            })
    return result


# --- CLI ---

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: slide_templates.py <command> [args...]"}))
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        print(json.dumps(list_templates(), indent=2))

    elif command == "categories":
        print(json.dumps(CATEGORIES, indent=2))

    elif command == "get":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Usage: get <template_key> <data_json>"}))
            sys.exit(1)

        template_key = sys.argv[2]
        data = json.loads(sys.argv[3])
        html = get_template_html(template_key, data)
        print(html)

    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
