// AllNightLong — Proposition de conception : météo, sessions, lieux
// Compilation : typst compile plan-meteo-sessions.typ

#set document(title: "AllNightLong — Météo, sessions et lieux")
#set page(
  paper: "a4",
  margin: (x: 2cm, y: 2.2cm),
  header: context {
    if counter(page).get().first() > 1 [
      #set text(size: 8pt, fill: luma(120))
      AllNightLong — Météo, sessions et lieux #h(1fr) Proposition de conception
    ]
  },
  footer: context [
    #set text(size: 8pt, fill: luma(120))
    #h(1fr) #counter(page).display("1 / 1", both: true)
  ],
)
#set text(font: ("Segoe UI", "Libertinus Serif"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.62em)
#show table: set par(justify: false)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  v(0.8em)
  block(text(size: 15pt, weight: "bold", fill: rgb("#3b3fb8"), it))
  v(0.2em)
}
#show heading.where(level: 2): it => {
  v(0.4em)
  block(text(size: 11.5pt, weight: "bold", it))
}
#show raw.where(block: false): it => box(
  fill: luma(240), inset: (x: 2.5pt), outset: (y: 2pt), radius: 2pt,
  text(font: "Consolas", size: 8.8pt, it),
)

// ───────────────────────── Palette de l'application (thème sombre) ─────────────────────────
#let C = (
  bg: rgb("#121214"),
  panel: rgb("#161619"),
  field: rgb("#202024"),
  border: rgb("#2a2a2d"),
  line: rgb("#3a3a3f"),
  accent: rgb("#6366f1"),
  muted: rgb("#8b8b94"),
  fg: rgb("#ececef"),
  low: rgb("#64748b"),
  mid: rgb("#94a3b8"),
  high: rgb("#cbd5e1"),
  hum: rgb("#38bdf8"),
  temp: rgb("#f59e0b"),
  seeing: rgb("#a78bfa"),
  green: rgb("#4ade80"),
  yellow: rgb("#eab308"),
  red: rgb("#ef4444"),
)

// ───────────────────────── Briques de maquette ─────────────────────────
#let t(body, size: 6.5pt, fill: C.fg, weight: "regular") = text(size: size, fill: fill, weight: weight, body)
#let lbl(s) = t(s, size: 5pt, fill: C.muted)
#let fieldbox(value, hint: none) = box(
  width: 100%, inset: (x: 4pt, y: 3pt), fill: C.field, stroke: 0.5pt + C.line, radius: 2pt,
  if hint == none { t(value) } else { [#t(value) #h(1fr) #t(hint, size: 5pt, fill: C.muted)] },
)
#let fld(label, value, hint: none) = stack(spacing: 2pt, lbl(label), fieldbox(value, hint: hint))
#let btn(s, primary: false) = box(
  inset: (x: 5pt, y: 3pt), radius: 2pt,
  fill: if primary { C.accent } else { C.field },
  stroke: 0.5pt + (if primary { C.accent } else { C.line }),
  t(s, weight: "bold", size: 5.5pt),
)
#let chip(s) = box(
  inset: (x: 5pt, y: 2.5pt), radius: 6pt,
  fill: C.accent.transparentize(70%), stroke: 0.5pt + C.accent,
  t(s, size: 5.5pt),
)
#let section-title(s) = t(upper(s), size: 5.5pt, weight: "bold", fill: C.fg)
#let window(title: "", height: auto, body) = block(
  width: 100%, height: height, fill: C.bg, radius: 5pt, stroke: 0.6pt + C.border, clip: true, breakable: false,
  stack(
    block(
      width: 100%, fill: C.panel, inset: (x: 6pt, y: 4pt), stroke: (bottom: 0.5pt + C.border),
      grid(columns: (1fr, auto), t(title, size: 5.5pt, fill: C.muted, weight: "bold"), t("—   ▢   ✕", size: 5.5pt, fill: C.muted)),
    ),
    body,
  ),
)
#let tabs(items, active) = grid(
  columns: items.len() * (1fr,),
  ..items.enumerate().map(((i, s)) => block(
    width: 100%, inset: (y: 4.5pt),
    stroke: (bottom: if i == active { 1.3pt + C.accent } else { 0.5pt + C.border }),
    align(center, t(s, size: 6pt, weight: if i == active { "bold" } else { "regular" }, fill: if i == active { C.fg } else { C.muted })),
  )),
)
#let side-item(title, right, sub, active: false) = block(
  width: 100%, inset: (x: 6pt, y: 4pt), spacing: 0pt,
  fill: if active { C.field } else { none },
  stroke: (left: if active { 1.5pt + C.accent } else { none }, bottom: 0.4pt + C.border),
  stack(spacing: 2.5pt, grid(columns: (1fr, auto), t(title, weight: "bold"), t(right, size: 5pt, fill: C.muted)), t(sub, size: 5pt, fill: C.muted)),
)
#let night-header(s, active: false) = block(
  width: 100%, inset: (x: 6pt, y: 3.5pt), spacing: 0pt,
  fill: if active { C.accent.transparentize(80%) } else { C.panel },
  stroke: (bottom: 0.4pt + C.border, left: if active { 1.5pt + C.accent } else { none }),
  t(s, size: 5.2pt, fill: if active { C.fg } else { C.muted }, weight: "bold"),
)
#let thumb(date, place-name, targets, shade: 30%) = block(
  width: 100%, height: 52pt, radius: 3pt, clip: true, spacing: 0pt,
  fill: gradient.radial(C.accent.transparentize(shade), C.bg, center: (40%, 35%), radius: 80%),
  stroke: 0.5pt + C.line,
  align(bottom + left, block(inset: 4pt, stack(spacing: 2pt, t(date, size: 5.5pt, weight: "bold"), t(place-name, size: 4.5pt, fill: C.muted), t(targets, size: 4.5pt, fill: C.accent)))),
)
#let toggle(color, s, on: true) = box(
  inset: (x: 3pt, y: 2pt), radius: 2pt, stroke: 0.4pt + C.line, fill: if on { C.field } else { none },
  [#box(width: 5pt, height: 5pt, fill: if on { color } else { none }, stroke: 0.6pt + color, radius: 1pt) #h(1.5pt) #t(s, size: 5pt, fill: if on { C.fg } else { C.muted })],
)
#let caption-note(s) = align(center, text(size: 8pt, fill: luma(110), style: "italic", s))

// ───────────────────────── Données météo réelles (extraites des notes) ─────────────────────────
// Session NGC 7380 du 02/10/2026, relevés meteoblue horaires
#let wx-oct02 = (
  (h: 21, lbl: "21h00", low: 34, mid: 0, high: 0, see: 1.39, idx: "4-2", jet: 16, temp: 13, hum: 91, dew: "11.6", src: "meteoblue"),
  (h: 22, lbl: "22h00", low: 37, mid: 0, high: 0, see: 2.15, idx: "4-2", jet: 16, temp: 12, hum: 93, dew: "10.9", src: "meteoblue"),
  (h: 23, lbl: "23h00", low: 36, mid: 0, high: 0, see: 2.36, idx: "4-3", jet: 17, temp: 12, hum: 94, dew: "11.1", src: "meteoblue"),
  (h: 24, lbl: "00h00", low: 0, mid: 0, high: 0, see: 2.39, idx: "4-3", jet: 19, temp: 12, hum: 95, dew: "11.2", src: "open-meteo"),
  (h: 25, lbl: "01h00", low: 7, mid: 0, high: 28, see: 2.49, idx: "4-3", jet: 19, temp: 11, hum: 95, dew: "10.2", src: "open-meteo"),
  (h: 26, lbl: "02h00", low: 28, mid: 0, high: 67, see: 2.35, idx: "4-3", jet: 20, temp: 10, hum: 94, dew: "9.1", src: "open-meteo"),
)
// Session NGC 672 + IC 1727 du 30/10/2026
#let wx-oct30 = (
  (h: 20, lbl: "20h00", low: 0, mid: 0, high: 0, see: 2.33, idx: "4-2", jet: 24, temp: 8, hum: 94),
  (h: 22, lbl: "22h00", low: 5, mid: 0, high: 0, see: 2.26, idx: "4-2", jet: 25, temp: 7, hum: 97),
  (h: 24, lbl: "00h00", low: 5, mid: 0, high: 0, see: 2.14, idx: "3-1", jet: 26, temp: 6, hum: 99),
  (h: 26, lbl: "02h00", low: 0, mid: 0, high: 0, see: 2.01, idx: "3-1", jet: 32, temp: 6, hum: 88),
)

// ───────────────────────── Graphe météo ─────────────────────────
#let wx-chart(data, band, axis, width: 300pt, height: 120pt, tip: none) = {
  let (a0, a1) = axis
  let ml = 22pt
  let mr = 18pt
  let mt = 6pt
  let mb = 13pt
  let pw = width - ml - mr
  let ph = height - mt - mb
  let x(hh) = ml + pw * (hh - a0) / (a1 - a0)
  let yp(v) = mt + ph * (1 - v / 100)
  let ys(v) = mt + ph * (1 - v / 3)
  let area(lo, hi, color) = {
    let upper = data.map(p => (x(p.h), yp(hi(p))))
    let lower = data.rev().map(p => (x(p.h), yp(lo(p))))
    place(top + left, polygon(fill: color, stroke: none, ..upper, ..lower))
  }
  let series(f, yfn, color, dash: none) = {
    for i in range(data.len() - 1) {
      let a = data.at(i)
      let b = data.at(i + 1)
      place(top + left, line(
        start: (x(a.h), yfn(f(a))), end: (x(b.h), yfn(f(b))),
        stroke: (paint: color, thickness: 1pt, dash: dash),
      ))
    }
    for p in data {
      place(top + left, dx: x(p.h) - 1.3pt, dy: yfn(f(p)) - 1.3pt, circle(radius: 1.3pt, fill: color, stroke: none))
    }
  }
  box(width: width, height: height, fill: C.panel, radius: 3pt, {
    // Créneau de l'observation
    place(top + left, dx: x(band.at(0)), dy: mt, rect(width: x(band.at(1)) - x(band.at(0)), height: ph, fill: C.accent.transparentize(84%), stroke: none))
    place(top + left, dx: x(band.at(0)) + 2pt, dy: mt + 1.5pt, t("observation", size: 4.3pt, fill: C.accent))
    // Grille et axes
    for v in (0, 25, 50, 75, 100) {
      place(top + left, line(start: (ml, yp(v)), end: (ml + pw, yp(v)), stroke: 0.3pt + C.border))
      place(top + left, dx: 2pt, dy: yp(v) - 2.5pt, t(str(v) + " %", size: 4.2pt, fill: C.muted))
    }
    for s in (0, 1, 2, 3) {
      place(top + left, dx: ml + pw + 3pt, dy: ys(s) - 2.5pt, t(str(s) + "″", size: 4.2pt, fill: C.seeing))
    }
    for hh in range(calc.ceil(a0), calc.floor(a1) + 1) {
      place(top + left, dx: x(hh) - 4pt, dy: mt + ph + 3pt, t(str(calc.rem(hh, 24)) + "h", size: 4.5pt, fill: C.muted))
    }
    // Nuages empilés (bas / moyens / hauts)
    area(p => 0, p => p.low, C.low.transparentize(20%))
    area(p => p.low, p => p.low + p.mid, C.mid.transparentize(30%))
    area(p => p.low + p.mid, p => p.low + p.mid + p.high, C.high.transparentize(45%))
    // Courbes
    series(p => p.hum, yp, C.hum)
    series(p => p.see, ys, C.seeing, dash: "dashed")
    // Info-bulle au survol
    if tip != none {
      let p = data.at(tip)
      place(top + left, line(start: (x(p.h), mt), end: (x(p.h), mt + ph), stroke: (paint: C.fg, thickness: 0.4pt, dash: "dotted")))
      place(top + left, dx: x(p.h) - 82pt, dy: mt + 4pt, block(
        fill: C.bg, stroke: 0.5pt + C.line, radius: 2pt, inset: 4pt,
        stack(
          spacing: 2.2pt,
          t(p.lbl + " TU", size: 5pt, weight: "bold"),
          t("Nuages " + str(p.low) + " / " + str(p.mid) + " / " + str(p.high) + " %", size: 4.6pt),
          t("Seeing " + str(p.see) + "″ · index " + p.idx, size: 4.6pt, fill: C.seeing),
          t("Humidité " + str(p.hum) + " %", size: 4.6pt, fill: C.hum),
          t("Temp. " + str(p.temp) + " °C · jet " + str(p.jet) + " m/s", size: 4.6pt),
        ),
      ))
    }
  })
}
#let wx-legend = stack(dir: ltr, spacing: 3pt,
  toggle(C.low, "Nuages bas"), toggle(C.mid, "moyens"), toggle(C.high, "hauts"),
  toggle(C.hum, "Humidité"), toggle(C.seeing, "Seeing"),
  toggle(C.temp, "Température", on: false), toggle(C.temp, "Point de rosée", on: false), toggle(C.muted, "Jet stream", on: false),
)

// ───────────────────────── Grille météo ─────────────────────────
#let wx-table(data) = {
  let hdr = ("Heure TU", "Bas %", "Moy. %", "Haut %", "Seeing ″", "Idx 1", "Idx 2", "Jet m/s", "Temp °C", "Hum. %", "Rosée °C", "Source")
  let cell(s, manual: false, dim: false) = t(s, size: 5.3pt, fill: if dim { C.muted } else { C.fg })
  let rows = data.map(p => {
    let manual = p.src == "meteoblue"
    let (i1, i2) = p.idx.split("-")
    (
      cell(p.lbl.replace("h", ":")),
      cell(str(p.low)), cell(str(p.mid)), cell(str(p.high)),
      if manual { cell(str(p.see)) } else { cell("—", dim: true) },
      if manual { cell(i1) } else { cell("—", dim: true) },
      if manual { cell(i2) } else { cell("—", dim: true) },
      cell(str(p.jet)), cell(str(p.temp)), cell(str(p.hum)), cell(p.dew),
      if manual { t("✎ meteoblue", size: 5pt, fill: C.accent, weight: "bold") } else { t("Open-Meteo", size: 5pt, fill: C.muted) },
    )
  })
  table(
    columns: (auto,) + 11 * (1fr,),
    stroke: 0.3pt + C.border,
    inset: (x: 3pt, y: 3.2pt),
    align: center + horizon,
    fill: (x, y) => if y == 0 { C.panel } else if data.at(y - 1).src == "meteoblue" { C.accent.transparentize(88%) } else { C.bg },
    ..hdr.map(s => t(s, size: 5pt, weight: "bold", fill: C.muted)),
    ..rows.flatten(),
  )
}

// ───────────────────────── Entités du schéma ─────────────────────────
#let entity(name, fields, w: 130pt, h: 80pt, kind: "new") = {
  let col = if kind == "new" { rgb("#4f46e5") } else if kind == "mod" { rgb("#b45309") } else { luma(90) }
  block(
    width: w, height: h, fill: white, stroke: 0.8pt + col, radius: 3pt, clip: true,
    stack(
      block(width: 100%, fill: col, inset: (x: 5pt, y: 3.5pt), text(size: 7.5pt, fill: white, weight: "bold", font: "Consolas", name)),
      block(inset: (x: 5pt, y: 4pt), stack(spacing: 3pt, ..fields.map(f => text(size: 6.3pt, font: "Consolas", f)))),
    ),
  )
}
#let card(s, dx, dy) = place(top + left, dx: dx, dy: dy, text(size: 7pt, weight: "bold", fill: luma(70), s))
#let link-line(a, b) = place(top + left, line(start: a, end: b, stroke: 0.9pt + luma(80)))

#let step(body) = block(
  width: 100%, inset: 6pt, radius: 3pt, stroke: 0.6pt + rgb("#6366f1"), fill: rgb("#6366f1").transparentize(92%),
  align(center, text(size: 8pt, body)),
)
#let arrow = text(size: 12pt, fill: rgb("#6366f1"), "→")

// ════════════════════════════════════ DOCUMENT ════════════════════════════════════

#align(center)[
  #v(1.5em)
  #text(size: 22pt, weight: "bold")[AllNightLong]
  #v(-0.4em)
  #text(size: 14pt, fill: rgb("#3b3fb8"))[Météo, sessions d'observation et lieux]
  #v(0.2em)
  #text(size: 9pt, fill: luma(110))[Proposition de conception · version de travail · 17 novembre 2026]
  #v(1em)
]

#block(fill: luma(245), inset: 10pt, radius: 4pt, width: 100%)[
  *En résumé.* Les notes des observations contiennent des relevés météo saisis à la main, au format meteoblue. On propose de :
  + récupérer automatiquement la météo via *Open-Meteo* (gratuit, sans clé), tout en laissant l'utilisateur corriger ou compléter les valeurs, par exemple avec meteoblue ;
  + l'afficher dans le rapport d'observation sous forme de *graphe interactif* et de *grille éditable* ;
  + introduire des *sessions* (une nuit dans un lieu), des *observations multi-cibles* et une liste de *lieux enregistrés* choisis sur une carte.
  + afficher la *hauteur des cibles* au cours de la nuit (calcul local), avec crépuscules et Lune ;
  + gérer *plusieurs images* par observation (logiciels, palettes), filtrées par cible, rangées dans un dossier choisi dans un *panneau de réglages*.

  Cette version intègre les premiers retours de l'utilisateur : les décisions prises sont récapitulées en section 7.1.
]

= Constat : ce que contiennent les notes aujourd'hui

La base compte 62 observations, dont 59 ont le champ `other_objects` (« Autres objets dans le champ / Notes ») rempli. Environ 25 d'entre elles, réparties sur une vingtaine de nuits, contiennent un ou plusieurs relevés météo de la forme :

#align(center, raw("22h00 TU ( 0-30-50 / 1.30 / 4-3 / 30 ms / 11°C / 92% )"))

Ce format reprend les colonnes du tableau « Astronomy Seeing » de meteoblue :

#table(
  columns: (auto, 1fr, auto),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([*Position*], [*Grandeur*], [*Unité*]),
  [`0-30-50`], [Couverture nuageuse basse, moyenne, haute], [%],
  [`1.30`], [Seeing], [seconde d'arc],
  [`4-3`], [Index 1 et Index 2 de seeing (meteoblue)], [échelle 1–5],
  [`30 ms`], [Vitesse du jet stream], [m/s],
  [`11°C`], [Température], [°C],
  [`92%`], [Humidité relative], [%],
)

Les autres données qui reviennent dans les notes : Bortle (6 à 7), phase de la Lune, qualité du ciel, bilan des poses, comparaison des logiciels d'empilement Siril et Stacking Wizard, autres objets du champ.

*Problèmes constatés :*
- *formats instables :* `0_0_0` ou `0-0-0`, `9ms` ou `9 ms`, `17C`, humidité `??` ;
- *copies suspectes :* les relevés du 14/08 sont identiques, au chiffre près, à ceux du 02/03 ;
- *observations conjointes dupliquées :* une fiche par cible, avec tous les champs de session recopiés à la main. Il y a déjà des divergences (`19:30` contre `19:31`, `25,1°C` contre `25.1`, `LP dual band` contre `LP dual bande`) ;
- *lieu en texte libre :* « Jardin », `50,5244 / 2,6400`, `50.52440 N / 2.63972 E`… soit au moins sept variantes pour un même jardin.

= Source des données météo

#table(
  columns: (1.1fr, 1fr, 1fr),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([*Grandeur*], [*Open-Meteo (automatique)*], [*meteoblue (manuel)*]),
  [Nuages bas / moyens / hauts], [✅ `cloud_cover_low/mid/high`], [✅],
  [Température, humidité], [✅ `temperature_2m`, `relative_humidity_2m`], [✅],
  [Point de rosée], [✅ `dew_point_2m` (utile contre la buée)], [—],
  [Jet stream], [≈ vent à 250 hPa (`wind_speed_250hPa`)], [✅],
  [Seeing, Index 1 / Index 2], [❌ (calcul propre à meteoblue)], [✅],
  [Coût], [Gratuit, sans clé (usage non commercial)], [API payante : saisie manuelle],
  [Historique], [Oui : dates passées disponibles], [Non (hors API payante)],
)

*Principe retenu :* Open-Meteo remplit automatiquement tout ce qu'il peut. L'utilisateur peut ensuite modifier n'importe quelle valeur, ajouter les colonnes seeing et index, ou coller directement une ligne au format meteoblue.

*Règles de cohabitation :*
- *fenêtre récupérée :* le créneau de l'observation, avec une marge avant et après (1 h par défaut, réglable, voir 4.7). Les relevés restent rattachés à la session. Si une deuxième observation s'ajoute à la même nuit, la fenêtre s'élargit pour la couvrir et seules les heures manquantes sont récupérées ;
- chaque relevé porte sa *source* (`open-meteo`, `meteoblue`, `manuel`) et un indicateur *modifié* ;
- « Rafraîchir depuis Open-Meteo » ne remplace que les relevés Open-Meteo *non modifiés*. Les saisies de l'utilisateur ne sont jamais écrasées ;
- les relevés sont enregistrés en base : une fois récupérés, ils s'affichent sans connexion ;
- les valeurs Open-Meteo et meteoblue viennent de modèles différents. Elles ne sont pas identiques, et la colonne « Source » permet de le voir.

= Modèle de données proposé

Trois niveaux : le *lieu*, la *session* (une nuit dans ce lieu) et l'*observation* (une prise de vue : un champ, un instrument). Une observation peut viser *plusieurs cibles*, ce qui donne une relation N–N avec les cibles. La météo est rattachée à la session : toutes les observations de la nuit la partagent.

#block(width: 100%, height: 345pt, breakable: false, {
  place(top + left, dx: 0pt, dy: 0pt, entity("location", (
    "id            PK", "label", "lat, lon", "elevation_m", "bortle", "notes",
  ), h: 75pt))
  place(top + left, dx: 175pt, dy: 0pt, entity("session", (
    "id            PK", "location_id   FK", "night_date", "bortle", "moon_phase", "sky_notes",
  ), h: 75pt))
  place(top + left, dx: 350pt, dy: 0pt, entity("weather_reading", (
    "id            PK", "session_id    FK", "time_utc", "cloud_low/mid/high", "seeing_arcsec", "index1, index2",
    "jet_stream_ms", "temp_c", "humidity_pct", "dew_point_c", "source", "edited",
  ), h: 130pt))
  place(top + left, dx: 175pt, dy: 105pt, entity("observation", (
    "id            PK", "session_id    FK", "start_utc, end_utc", "sensor, filter", "sensor_temp", "sub_exposure",
    "img_total", "instrument (opt.)", "notes",
  ), h: 100pt, kind: "mod"))
  place(top + left, dx: 175pt, dy: 235pt, entity("observation_target", (
    "observation_id  FK", "target_id       FK", "altitude", "img_good/pass/bad", "notes",
  ), h: 74pt))
  place(top + left, dx: 350pt, dy: 235pt, entity("targets", (
    "id            PK", "name, usual_name", "ra, dec, …", "notes",
  ), h: 65pt, kind: "old"))

  link-line((130pt, 38pt), (175pt, 38pt))
  card("1", 133pt, 28pt)
  card("N", 166pt, 28pt)
  link-line((305pt, 38pt), (350pt, 38pt))
  card("1", 308pt, 28pt)
  card("N", 341pt, 28pt)
  link-line((240pt, 75pt), (240pt, 105pt))
  card("1", 245pt, 77pt)
  card("N", 245pt, 95pt)
  link-line((240pt, 205pt), (240pt, 235pt))
  card("1", 245pt, 207pt)
  card("N", 245pt, 225pt)
  link-line((305pt, 268pt), (350pt, 268pt))
  card("N", 308pt, 258pt)
  card("1", 341pt, 258pt)
  place(top + left, dx: 0pt, dy: 105pt, entity("observation_image", (
    "id            PK", "observation_id FK", "path (relatif)", "kind", "software", "palette", "caption", "is_favorite",
  ), h: 100pt))
  place(top + left, dx: 0pt, dy: 235pt, entity("image_target", (
    "image_id      FK", "target_id     FK",
  ), h: 45pt))
  link-line((130pt, 150pt), (175pt, 150pt))
  card("N", 133pt, 140pt)
  card("1", 166pt, 140pt)
  link-line((65pt, 205pt), (65pt, 235pt))
  card("1", 70pt, 207pt)
  card("N", 70pt, 225pt)
  link-line((65pt, 280pt), (65pt, 314pt))
  link-line((65pt, 314pt), (415pt, 314pt))
  link-line((415pt, 314pt), (415pt, 300pt))
  card("N", 70pt, 283pt)
  card("1", 420pt, 302pt)
  place(bottom + center, text(size: 8pt)[
    #box(width: 8pt, height: 8pt, fill: rgb("#4f46e5"), radius: 1pt) nouvelle table #h(10pt)
    #box(width: 8pt, height: 8pt, fill: rgb("#b45309"), radius: 1pt) table existante modifiée #h(10pt)
    #box(width: 8pt, height: 8pt, fill: luma(90), radius: 1pt) table existante inchangée
  ])
})

== Répartition des champs actuels

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([*Niveau*], [*Champs*]),
  [Lieu], [coordonnées (aujourd'hui `location` en texte libre), altitude, Bortle par défaut],
  [Session], [date de la nuit, Bortle (repris du lieu, modifiable), Lune, conditions du ciel, relevés météo],
  [Observation], [date et heure TU de début et de fin (issues des FITS), instrument (optionnel), capteur, filtre, température du capteur, pose unitaire, nombre total de poses, notes de la séance],
  [Observation × cible], [hauteur de la cible (`altitude` : 27° pour M 81, 57° pour M 82 dans la même prise de vue) ; poses retenues, à revoir et rejetées, qui peuvent varier d'une cible à l'autre (580 contre 560 pour NGC 6820/6823) ; notes propres à cette cible dans cette observation],
  [Image], [autant que souhaité par observation : brute, traitées (logiciel, palette), astrométrie. Chacune est étiquetée avec les cibles qu'elle montre (aucune = champ entier) ; une image favorite sert de vignette],
)

Les données montrent que plusieurs observations peuvent avoir lieu la même nuit : le 02/03, il y a le champ d'Orion puis M 101 ; le 25/04, NGC 4244 puis NGC 4889. Le niveau « session » est donc distinct de l'observation. Un champ *instrument*, optionnel, permettra de distinguer deux appareils si l'utilisateur en utilise un jour plusieurs en même temps.

*Dates et heures.* Aujourd'hui, une observation a trois champs : une date, une heure de début et une heure de fin. Quand l'observation passe minuit (44 observations sur 62), rien n'indique si la date est celle du soir ou celle du matin, et les deux cas existent. IC 1848 et Sh2-132 portent toutes deux la date du 14/11. IC 1848 a pourtant été observée du 13/11 19:30 au 14/11 02:41 (date du matin), Sh2-132 du 14/11 18:56 au 14/11 23:19 (date du soir). Lues avec la même convention, les deux fiches se chevauchent de 19:30 à 23:19. *Décision :*
- le début et la fin de chaque observation sont enregistrés en *deux champs date + heure TU complets* (`2026-11-13 19:30:00`) ;
- la date affichée (« Rapport du … », cartes, listes) est la *date du début* ;
- la session regroupe les observations d'une même nuit dans un même lieu. Une observation commencée après minuit (par exemple à 00:30) est rattachée à la nuit commencée la veille.

== Création d'une observation

L'utilisateur n'a pas à gérer les sessions : il saisit une date et choisit un lieu, et la session est créée ou retrouvée automatiquement. Elle n'apparaît pas comme un écran à part. Changer de lieu ou de nuit, c'est changer de session.

#grid(
  columns: (1fr, auto, 1fr, auto, 1fr, auto, 1fr),
  column-gutter: 4pt,
  align: horizon,
  step[Saisie du *début* (date + heure TU) et choix du *lieu*], arrow,
  step[Session existante pour cette nuit et ce lieu ?\ *oui* → rattacher\ *non* → créer], arrow,
  step[Appel *Open-Meteo* sur le créneau ± marge (relevés horaires)], arrow,
  step[Relevés enregistrés (source `open-meteo`) puis affichés],
)

// ───────────────────────── Éphémérides (calcul local, basse précision) ─────────────────────────
#let jd-at(y, m, d) = 2451544.5 + (datetime(year: y, month: m, day: d) - datetime(year: 2000, month: 1, day: 1)).days()
#let alt-of(ra, dec, jd, lat, lon) = {
  let gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0)
  let H = gmst + lon - ra
  let s = calc.sin(lat * 1deg) * calc.sin(dec * 1deg) + calc.cos(lat * 1deg) * calc.cos(dec * 1deg) * calc.cos(H * 1deg)
  calc.asin(calc.max(-1.0, calc.min(1.0, s))).deg()
}
#let ecl-to-eq(lam, beta, d) = {
  let e = 23.439 - 0.00000036 * d
  let ra = calc.atan2(calc.cos(lam * 1deg), calc.sin(lam * 1deg) * calc.cos(e * 1deg) - calc.tan(beta * 1deg) * calc.sin(e * 1deg)).deg()
  let dec = calc.asin(calc.sin(beta * 1deg) * calc.cos(e * 1deg) + calc.cos(beta * 1deg) * calc.sin(e * 1deg) * calc.sin(lam * 1deg)).deg()
  (ra, dec)
}
#let sun-radec(jd) = {
  let d = jd - 2451545.0
  let g = 357.529 + 0.98560028 * d
  let q = 280.459 + 0.98564736 * d
  ecl-to-eq(q + 1.915 * calc.sin(g * 1deg) + 0.020 * calc.sin(2 * g * 1deg), 0, d)
}
#let moon-state(jd) = {
  let d = jd - 2451545.0
  let L = 218.316 + 13.176396 * d
  let Mp = 134.963 + 13.064993 * d
  let F = 93.272 + 13.229350 * d
  let D = 297.850 + 12.190749 * d
  let M = 357.529 + 0.98560028 * d
  let s(x) = calc.sin(x * 1deg)
  let lam = L + 6.289 * s(Mp) + 1.274 * s(2 * D - Mp) + 0.658 * s(2 * D) + 0.214 * s(2 * Mp) - 0.186 * s(M) - 0.114 * s(2 * F)
  let beta = 5.128 * s(F)
  let (ra, dec) = ecl-to-eq(lam, beta, d)
  (ra: ra, dec: dec, illum: (1 - calc.cos(D * 1deg)) / 2)
}
#let hm(t) = {
  let tt = calc.rem(t, 24)
  let h = calc.floor(tt)
  let m = int(calc.round((tt - h) * 60))
  if m == 60 { h += 1; m = 0 }
  let p(n) = if n < 10 { "0" + str(n) } else { str(n) }
  p(calc.rem(h, 24)) + ":" + p(m)
}
#let night-data(date, lat, lon, targets) = {
  let J = jd-at(..date)
  let samples = range(0, 205).map(i => {
    let t = 15 + i / 12
    let jd = J + t / 24
    let (sra, sdec) = sun-radec(jd)
    let mo = moon-state(jd)
    let ma = alt-of(mo.ra, mo.dec, jd, lat, lon)
    (
      t: t,
      sun: alt-of(sra, sdec, jd, lat, lon),
      moon: ma - 0.95 * calc.cos(ma * 1deg),
      illum: mo.illum,
      tg: targets.map(g => alt-of(g.ra, g.dec, jd, lat, lon)),
    )
  })
  let night = samples.filter(s => s.sun < -0.833)
  let dark = night.filter(s => s.sun < -18)
  (night: night, dark: dark)
}

#let alt-chart(date, lat, lon, targets, obs: (), minalt: 25, width: 100%, height: 150pt) = {
  let nd = night-data(date, lat, lon, targets)
  let night = nd.night
  let t0 = night.first().t
  let t1 = night.last().t
  let ml = 22pt
  let mr = 18pt
  let mt = 16pt
  let strip = 9pt
  let mb = 14pt + obs.len() * strip
  let pw = width - ml - mr
  let ph = height - mt - mb
  let x(t) = ml + pw * (t - t0) / (t1 - t0)
  let y(a) = mt + ph * (1 - calc.max(a, 0) / 90)
  let curve(f, color, dash: none, thick: 1.1pt) = {
    for i in range(night.len() - 1) {
      let a = night.at(i)
      let b = night.at(i + 1)
      if f(a) >= 0 and f(b) >= 0 {
        place(top + left, line(start: (x(a.t), y(f(a))), end: (x(b.t), y(f(b))), stroke: (paint: color, thickness: thick, dash: dash)))
      }
    }
  }
  box(width: width, height: height, fill: C.panel, radius: 3pt, {
    // Crépuscules / nuit noire
    let twi = rgb("#3b2f5c").transparentize(35%)
    if nd.dark.len() > 0 {
      let d0 = nd.dark.first().t
      let d1 = nd.dark.last().t
      place(top + left, dx: x(t0), dy: mt, rect(width: x(d0) - x(t0), height: ph, fill: twi, stroke: none))
      place(top + left, dx: x(d1), dy: mt, rect(width: x(t1) - x(d1), height: ph, fill: twi, stroke: none))
      place(top + left, dx: x(d0), dy: mt, rect(width: x(d1) - x(d0), height: ph, fill: rgb("#07090f"), stroke: none))
    }
    // Grille
    for a in (0, 30, 60, 90) {
      place(top + left, line(start: (ml, y(a)), end: (ml + pw, y(a)), stroke: 0.3pt + C.border))
      place(top + left, dx: 3pt, dy: y(a) - 2.5pt, t(str(a) + "°", size: 4.5pt, fill: C.muted))
    }
    for h in range(calc.ceil(t0), calc.floor(t1) + 1) {
      if calc.rem(h, 2) == 0 {
        place(top + left, line(start: (x(h), mt), end: (x(h), mt + ph), stroke: (paint: C.line, thickness: 0.3pt, dash: "dotted")))
        place(top + left, dx: x(h) - 5pt, dy: mt + ph + 3pt, t(str(calc.rem(h, 24)) + "h", size: 4.5pt, fill: C.muted))
      }
    }
    place(top + left, dx: x(t0) + 1pt, dy: mt + ph + 3pt, t(hm(t0), size: 4.5pt, weight: "bold"))
    place(top + left, dx: x(t1) - 15pt, dy: mt + ph + 3pt, t(hm(t1), size: 4.5pt, weight: "bold"))
    // Hauteur minimale (horizon personnel)
    place(top + left, line(start: (ml, y(minalt)), end: (ml + pw, y(minalt)), stroke: (paint: C.temp, thickness: 0.7pt, dash: "dashed")))
    place(top + left, dx: ml + pw - 58pt, dy: y(minalt) - 8pt, t("Hauteur minimale " + str(minalt) + "°", size: 4.5pt, fill: C.temp))
    // Lune puis cibles
    curve(s => s.moon, rgb("#fbbf24"), dash: "dashed", thick: 0.9pt)
    for (k, g) in targets.enumerate() {
      curve(s => s.tg.at(k), g.color)
      let best = night.fold(night.first(), (m, s) => if s.tg.at(k) > m.tg.at(k) { s } else { m })
      let ba = best.tg.at(k)
      place(top + left, dx: x(best.t) - 2pt, dy: y(ba) - 2pt, circle(radius: 2pt, fill: C.fg, stroke: 0.8pt + g.color))
      place(top + left, dx: x(best.t) - 30pt, dy: y(ba) - 11pt, t(g.name + " · " + hm(best.t) + " TU · " + str(calc.round(ba)) + "°", size: 4.6pt, weight: "bold"))
    }
    // Créneaux d'observation (bandeaux sous l'axe)
    for (k, o) in obs.enumerate() {
      let yy = mt + ph + 12pt + k * strip
      place(top + left, dx: x(o.from), dy: yy, rect(width: x(o.to) - x(o.from), height: strip - 3pt, radius: 1.5pt, fill: o.color.transparentize(55%), stroke: 0.5pt + o.color))
      place(top + left, dx: x(o.from) + 3pt, dy: yy + 0.6pt, t(o.label + "  " + hm(o.from) + "–" + hm(o.to), size: 4.3pt))
    }
  })
}
#let alt-legend(illum) = stack(dir: ltr, spacing: 3pt,
  toggle(rgb("#60a5fa"), "Cible(s)"),
  toggle(rgb("#fbbf24"), "Lune " + str(calc.round(illum * 100)) + " %"),
  toggle(rgb("#3b2f5c"), "Crépuscule"),
  toggle(rgb("#07090f"), "Nuit noire"),
  toggle(C.temp, "Hauteur minimale"),
  toggle(C.muted, "Horizon du lieu", on: false),
)

#let here = (lat: 50.5247, lon: 2.6403)
#let m31 = (name: "M 31", ra: 10.6846, dec: 41.2692, color: rgb("#60a5fa"))
#let nd17 = night-data((2026, 11, 17), here.lat, here.lon, (m31,))
#let m31-best = nd17.night.fold(nd17.night.first(), (m, s) => if s.tg.at(0) > m.tg.at(0) { s } else { m })

= Interface

// ───────────────────────── Briques supplémentaires ─────────────────────────
#let sort-switch(s) = box(
  inset: (x: 3pt, y: 2.5pt), radius: 2pt, fill: C.field, stroke: 0.5pt + C.line,
  [#t("⇅", size: 6pt, weight: "bold") #t(s, size: 5pt, fill: C.muted)],
)
#let search-row(placeholder, sort) = block(inset: 5pt, spacing: 0pt, grid(
  columns: (1fr, auto, auto), column-gutter: 3pt,
  fieldbox(placeholder), sort-switch(sort), btn("+"),
))
#let poses-bar(g, p, b, width: 50pt) = box(width: width, height: 2.5pt, radius: 1pt, clip: true, grid(
  columns: (g * 1fr, p * 1fr, b * 1fr), rows: 2.5pt, fill: (C.green, C.yellow, C.red), [], [], [],
))
#let card-box(title, body) = block(
  width: 100%, fill: rgb("#1e1e21"), stroke: 0.5pt + C.line, radius: 3pt, inset: 5pt, spacing: 0pt,
  stack(
    spacing: 4.5pt,
    block(width: 100%, stroke: (bottom: 0.4pt + C.line), inset: (bottom: 2.5pt), t(upper(title), size: 5pt, weight: "bold", fill: C.muted)),
    body,
  ),
)
#let kv(k, v, fill: C.fg) = stack(spacing: 1.8pt, lbl(k), t(v, size: 6.2pt, fill: fill))
#let img-box(title, h, shade: 40%) = stack(
  spacing: 2pt, lbl(title),
  block(width: 100%, height: h, radius: 3pt, stroke: 0.5pt + C.line, fill: gradient.radial(C.accent.transparentize(shade), C.bg, center: (50%, 45%), radius: 70%)),
)

// Observations réelles d'octobre-novembre 2026 (base de données ; météo résumée depuis les notes)
#let obs-list = (
  (date: "14/11/2026", tg: "Sh2-132", tu: "18:56–23:19", filt: "LP dual band", tot: 545, g: 545, p: 0, b: 141, dur: 91, cl: 70, see: "1.37"),
  (date: "13/11/2026", tg: "IC 1848", tu: "19:30–02:41", filt: "LP dual band", tot: 1466, g: 1458, p: 7, b: 235, dur: 244, cl: 43, see: "1.83"),
  (date: "07/11/2026", tg: "IC 1795", tu: "20:04–22:55", filt: "LP dual band", tot: 452, g: 411, p: 41, b: 75, dur: 75, cl: 82, see: "0.89"),
  (date: "30/10/2026", tg: "NGC 672 · IC 1727", tu: "20:39–02:36", filt: "IRCUT", tot: 800, g: 510, p: 290, b: 317, dur: 133, cl: 5, see: "2.19"),
  (date: "14/10/2026", tg: "NGC 925", tu: "21:34–02:31", filt: "IRCUT", tot: 691, g: 691, p: 0, b: 265, dur: 115, cl: 39, see: "2.49"),
  (date: "11/10/2026", tg: "M 33", tu: "22:32–02:40", filt: "IRCUT", tot: 590, g: 587, p: 3, b: 433, dur: 98, cl: 44, see: "1.96"),
  (date: "06/10/2026", tg: "NGC 7129 · NGC 7142", tu: "21:53–02:41", filt: "LP dual band", tot: 720, g: 717, p: 3, b: 76, dur: 120, cl: 2, see: "1.99"),
  (date: "05/10/2026", tg: "IC 1396A", tu: "21:43–02:23", filt: "LP dual band", tot: 690, g: 690, p: 0, b: 159, dur: 115, cl: 64, see: "1.30"),
  (date: "02/10/2026", tg: "NGC 7380", tu: "20:07–02:01", filt: "LP dual band", tot: 769, g: 720, p: 49, b: 192, dur: 128, cl: 67, see: "2.19"),
)
#let obs-card(o, shade: 35%) = block(
  width: 100%, height: 66pt, radius: 3pt, clip: true, spacing: 0pt, stroke: 0.5pt + C.line,
  fill: gradient.radial(C.accent.transparentize(shade), C.bg, center: (45%, 35%), radius: 80%),
  align(bottom + left, block(inset: 4pt, stack(
    spacing: 2.4pt,
    t(o.date, size: 6pt, weight: "bold"),
    t(o.tg, size: 5pt, fill: C.accent, weight: "bold"),
    t("Jardin · " + o.filt, size: 4.5pt, fill: C.muted),
    poses-bar(o.g, o.p, o.b),
  ))),
)
#let obs-sidebar(h) = block(height: h, width: 100%, fill: C.panel, stroke: (right: 0.5pt + C.border), stack(
  tabs(("Cibles", "Observations"), 1),
  search-row("Filtrer (cible, lieu…)", "récent"),
  side-item("Toutes les observations", "", "triées par date", active: true),
  side-item("Novembre 2026", "3", "Sh2-132, IC 1848, IC 1795"),
  side-item("Octobre 2026", "6", "NGC 672, NGC 925, M 33…"),
  side-item("Septembre 2026", "8", "NGC 6946, IC 1318A…"),
  side-item("Août 2026", "5", "NGC 6888, IC 5070…"),
))

== Colonne de gauche : onglets, recherche et tri

La colonne de gauche reçoit deux onglets, *Cibles* et *Observations*. Dans les deux, un *interrupteur de tri* se place à gauche du bouton « + ». Pour les cibles, il bascule entre A→Z et Z→A ; pour les observations, entre « plus récentes d'abord » et « plus anciennes d'abord ».

#window(title: "AllNightLong", height: 162pt, grid(
  columns: (132pt, 1fr),
  block(height: 148pt, width: 100%, fill: C.panel, stroke: (right: 0.5pt + C.border), stack(
    tabs(("Cibles", "Observations"), 0),
    search-row("Rechercher un objet…", "A→Z"),
    side-item("IC 1727", "TRI", "Pas de nom usuel"),
    side-item("IC 1848", "CAS", "Nébuleuse de l'Âme"),
    side-item("M 81", "UMA", "Galaxie de Bode", active: true),
    side-item("M 82", "UMA", "Galaxie du Cigare"),
    side-item("NGC 672", "TRI", "Pas de nom usuel"),
  )),
  block(inset: 8pt, width: 100%, stack(
    spacing: 7pt,
    block(width: 100%, fill: C.panel, stroke: 0.5pt + C.border, radius: 3pt, inset: 6pt, grid(
      columns: (1fr, 1fr, 1fr, 1fr), column-gutter: 5pt, row-gutter: 5pt,
      grid.cell(colspan: 4, [#t("M 81", size: 9pt, weight: "bold") #h(4pt) #t("Galaxie de Bode · Grande Ourse", size: 5.5pt, fill: C.muted) #h(1fr) #t("fiche actuelle, inchangée", size: 5pt, fill: C.yellow)]),
      fld("Type", "Galaxie spirale"), fld("Magnitude", "6.94"), fld("RA", "09 55 33"), fld("Dec", "+69 03 55"),
    )),
    grid(columns: (1fr, auto), section-title("Historique des observations"), btn("+ Nouveau rapport", primary: true)),
    grid(
      columns: (1fr, 1fr, 1fr, 1fr), column-gutter: 5pt,
      thumb("25/02/2026", "Jardin", "M 81 + M 82"),
      thumb("12/03/2026", "Jardin", "M 81", shade: 50%),
      thumb("—", "", "", shade: 95%),
      thumb("—", "", "", shade: 95%),
    ),
  )),
))
#caption-note[Maquette, onglet Cibles. La fiche de l'objet est *simplifiée pour le document* : dans l'application, la fiche actuelle (constellation, désignations, type, magnitude, brillance, taille, coordonnées, notes) ne change pas. Seuls l'interrupteur de tri et les onglets sont nouveaux, et une vignette peut désormais couvrir plusieurs cibles (25/02 : M 81 + M 82).]

== Onglet Observations : deux propositions

Dans cet onglet, la colonne de gauche sert à *naviguer dans le temps* (toutes les observations, ou un mois), et la zone principale affiche les observations. Cliquer sur une observation ouvre son rapport, en lecture (voir 4.3). Il n'y a pas d'écran « session » séparé : le rapport montre déjà tout ce qui concerne la nuit.

=== Proposition A : cartes (continuité avec l'existant)

Les observations s'affichent en *cartes avec vignette*, comme l'historique de l'onglet Cibles, regroupées par mois.

#window(title: "AllNightLong", height: 220pt, grid(
  columns: (132pt, 1fr),
  obs-sidebar(206pt),
  block(inset: 8pt, width: 100%, stack(
    spacing: 6pt,
    grid(columns: (1fr, auto), section-title("Novembre 2026"), btn("+ Nouveau rapport", primary: true)),
    grid(columns: (1fr,) * 4, column-gutter: 5pt, ..obs-list.slice(0, 3).map(o => obs-card(o)), []),
    section-title("Octobre 2026"),
    grid(columns: (1fr,) * 4, column-gutter: 5pt, ..obs-list.slice(3, 7).map(o => obs-card(o, shade: 55%))),
  )),
))
#caption-note[Maquette, proposition A, avec les observations réelles d'octobre et novembre 2026. La barre de couleur reprend les poses bonnes / passables / rejetées.]

=== Proposition B : grille

Les observations s'affichent en *tableau*, une ligne par observation. Chaque colonne peut être triée en cliquant sur son en-tête.

#let obs-grid = table(
  columns: (auto, auto, 1fr, auto, auto, auto, auto, auto),
  stroke: (x, y) => (bottom: 0.3pt + C.border),
  inset: (x: 3pt, y: 3.6pt),
  align: left + horizon,
  fill: (x, y) => if y == 0 { C.panel } else if y == 4 { C.field } else { none },
  ..("", "Date ▼", "Cibles", "Créneau TU", "Filtre", "Poses", "Durée", "Météo").map(s => t(s, size: 5pt, weight: "bold", fill: C.muted)),
  ..obs-list.map(o => (
    box(width: 13pt, height: 9pt, radius: 1pt, fill: gradient.radial(C.accent.transparentize(40%), C.bg, radius: 80%)),
    t(o.date, size: 5.5pt),
    t(o.tg, size: 5.5pt, weight: "bold"),
    t(o.tu, size: 5.3pt, fill: C.muted),
    t(o.filt, size: 5.3pt, fill: C.muted),
    [#poses-bar(o.g, o.p, o.b, width: 26pt) #h(2pt) #t(str(o.g) + " / " + str(o.tot), size: 4.6pt, fill: C.muted)],
    t(str(o.dur) + " min", size: 5.3pt),
    t("☁ " + str(o.cl) + " % · " + o.see + "″", size: 5.3pt),
  )).flatten(),
)

#window(title: "AllNightLong", height: 220pt, grid(
  columns: (132pt, 1fr),
  obs-sidebar(206pt),
  block(inset: 8pt, width: 100%, stack(
    spacing: 6pt,
    grid(columns: (1fr, auto), section-title("Toutes les observations"), btn("+ Nouveau rapport", primary: true)),
    obs-grid,
  )),
))
#caption-note[Maquette, proposition B, mêmes observations. La colonne Météo résume la nuit : couverture nuageuse maximale et seeing moyen, tirés des relevés.]

#table(
  columns: (auto, 1fr, 1fr),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([], [*A — Cartes*], [*B — Grille*]),
  [*Points forts*], [Même présentation que l'onglet Cibles et que l'appli actuelle : rien à réapprendre. Très visuel : on reconnaît une observation à son image. Gros éléments, faciles à cliquer.], [Beaucoup d'observations visibles d'un coup. Tri par colonne (date, poses, météo…). Permet de comparer les nuits entre elles.],
  [*Points faibles*], [Peu d'informations par carte : il faut ouvrir le rapport pour comparer. Long défilement quand les observations s'accumulent.], [Plus dense, petits caractères, moins visuel. Nouvelle façon de faire pour l'utilisateur.],
)

*Choix retenu :* la proposition A, que l'utilisateur préfère nettement. La grille l'intéresse aussi : elle pourra venir plus tard, sous forme d'un réglage « affichage : cartes / tableau » (voir 4.7). Elle ne fait pas partie de la première version.

== Rapport d'observation

Le rapport garde la mise en page actuelle : les trois encadrés (session, matériel et pose, images) en haut, les images dans la colonne de droite. Il passe d'un mode à l'autre avec le bouton « Modifier ce rapport ».

*Ce qui change :*
- *pas de bandeau « session » :* la session n'est pas un objet que l'utilisateur manipule. Elle découle de la *date* et du *lieu* du rapport. Changer de lieu ou de nuit, c'est changer de session, ce qui correspond à la réalité : un déplacement, c'est une autre séance ;
- *un seul lieu par observation :* « + Nouveau lieu… » est une entrée de la liste déroulante des lieux. Elle sert à ajouter un lieu au catalogue, pas un deuxième lieu à l'observation ;
- *le tableau des cibles est la liste des cibles :* on ajoute une ligne pour ajouter une cible et on la retire avec ✕ ;
- *deux niveaux de notes :* une note *par cible observée*, sous sa ligne dans le tableau des cibles (ce qui concerne cette cible ce soir-là), et les *notes de la séance*, sous le tableau, au-dessus des conditions de la nuit (ciel, matériel, déroulement). Les notes générales de la fiche cible (onglet Cibles) restent inchangées ;
- *début et fin en date + heure TU :* le rapport est daté du jour du début ;
- *autant d'images que souhaité* (voir ci-dessous) : la colonne « image traitée » du tableau des cibles disparaît, elle faisait doublon avec la colonne de droite.

=== Gestion des images

Aujourd'hui, une observation a deux images : une brute et une traitée. À l'usage, l'utilisateur fait *plusieurs traitements* d'une même observation : empilement sous Siril ou sous Stacking Wizard, palette naturelle ou Hubble, version recadrée ou non (pour l'astrométrie). Ses notes en parlent, mais l'application ne peut pas les stocker.

*Proposition :* une observation peut avoir autant d'images que souhaité. Chaque image a :
- un *type* : brute, traitée, astrométrie ;
- le *logiciel* utilisé et la *palette* (listes proposées, saisie libre possible) : Siril, Stacking Wizard, AstroWizard, Photoshop… ; naturelle (RVB), Hubble, fausses couleurs… ;
- les *cibles visibles* sur l'image. Une image peut en montrer plusieurs (les Dentelles du Cygne couvrent NGC 6992, NGC 6995 et IC 1340). Une image sans cible désigne le *champ entier*, typiquement l'image brute ;
- une *étoile ⭐* pour l'image favorite, qui sert de vignette dans les cartes (onglet Cibles et onglet Observations).

*Stockage :* les images ne sont pas copiées. L'application enregistre leur chemin *relativement au dossier des images* choisi dans les réglages (aujourd'hui `E:\Astro\…`, voir 4.7).

*Filtrage par cible :* la colonne de droite devient une galerie avec ascenseur. En haut, une rangée de boutons (« Toutes · NGC 672 · IC 1727 ») filtre les images. Cliquer sur une ligne du tableau des cibles sélectionne le bouton correspondant : les deux restent synchronisés, et le filtre est toujours visible, ce qui évite l'impression que des images ont disparu. Le filtre d'une cible montre ses images *et* celles du champ entier. Quand le champ ne contient qu'une cible, la rangée de boutons n'apparaît pas.

=== Mode lecture

#let ngc672 = (name: "NGC 672 · IC 1727", ra: 26.977, dec: 27.433, color: rgb("#60a5fa"))
#let nd30 = night-data((2026, 10, 30), here.lat, here.lon, (ngc672,))
#let win30 = nd30.night.filter(s => s.t >= 20.65 and s.t <= 26.6)
#let mid30 = win30.at(calc.floor(win30.len() / 2)).tg.at(0)
#let max30 = calc.max(..win30.map(s => s.tg.at(0)))
#let dg(v) = str(calc.round(v)) + "°"
#let filt-btn(s, on: false) = box(
  inset: (x: 4pt, y: 2.5pt), radius: 6pt,
  fill: if on { C.accent } else { C.field }, stroke: 0.5pt + (if on { C.accent } else { C.line }),
  t(s, size: 5pt, weight: if on { "bold" } else { "regular" }),
)
#let img-tile(title, sub, h, shade: 40%, fav: false) = stack(
  spacing: 2pt,
  grid(columns: (1fr, auto), t(title, size: 5.3pt, weight: "bold"), if fav { t("⭐", size: 6pt) } else { [] }),
  block(width: 100%, height: h, radius: 3pt, spacing: 0pt, stroke: if fav { 0.8pt + C.yellow } else { 0.5pt + C.line },
    fill: gradient.radial(C.accent.transparentize(shade), C.bg, center: (50%, 45%), radius: 70%)),
  t(sub, size: 4.6pt, fill: C.muted),
)
#let tgt-head(cols) = cols.map(s => t(s, size: 5pt, weight: "bold", fill: C.muted))

#window(title: "Rapport d'observation", block(inset: 8pt, width: 100%, stack(
  spacing: 6pt,
  grid(columns: (1fr, auto, auto), column-gutter: 6pt, align: horizon,
    t("RAPPORT DU 30/10/2026 — NGC 672 · IC 1727", size: 7pt, weight: "bold"),
    btn("Modifier ce rapport"), t("✕", size: 7pt, fill: C.muted),
  ),
  grid(
    columns: (1fr, 112pt), column-gutter: 8pt,
    stack(
      spacing: 6pt,
      grid(
        columns: (1fr, 1fr, 1fr), column-gutter: 5pt,
        card-box("1. Session", stack(spacing: 4.5pt,
          kv("Lieu", "Jardin · Bortle 6.5"),
          kv("Début (TU)", "30/10/2026 20:39"),
          kv("Fin (TU)", "31/10/2026 02:36"),
          kv("Lune (calculée)", str(calc.round(nd30.night.at(0).illum * 100)) + " %"),
        )),
        card-box("2. Matériel & pose", stack(spacing: 4.5pt,
          kv("Capteur", "Seestar S50 (IMX462)"),
          kv("Filtre", "IRCUT"),
          kv("Temp. capteur", "24.2 °C"),
          kv("Pose unitaire", "10 s"),
        )),
        card-box("3. Images", stack(spacing: 4.5pt,
          kv("Total des poses", "800"),
          kv("Durée totale", "133.3 min"),
          t("Poses retenues : par cible, ci-dessous", size: 5pt, fill: C.muted),
        )),
      ),
      card-box("Cibles du champ", table(
        columns: (0.9fr, 1.3fr, 1.5fr, 0.9fr),
        stroke: (x, y) => (bottom: 0.3pt + C.border), inset: 3pt, align: horizon,
        fill: (x, y) => if y == 1 or y == 2 { C.accent.transparentize(80%) } else { none },
        ..tgt-head(("Cible", "Hauteur (calculée)", "Poses bon / pass / bad", "Images")),
        t("▸ NGC 672", weight: "bold"), t(dg(mid30) + " milieu · max " + dg(max30)), stack(spacing: 2pt, t("510 / 290 / 317"), poses-bar(510, 290, 317, width: 100%)), t("2 (+ 2 du champ)", fill: C.muted),
        table.cell(colspan: 4, t("Note : bras spiraux bien visibles ; IC 1727, voisine, est en interaction avec NGC 672 (exemple).", size: 5.2pt)),
        t("   IC 1727", weight: "bold"), t(dg(mid30) + " milieu · max " + dg(max30)), stack(spacing: 2pt, t("496 / 290 / 331"), poses-bar(496, 290, 331, width: 100%)), t("1 (+ 2 du champ)", fill: C.muted),
        table.cell(colspan: 4, t("Note : pas de note pour cette cible.", size: 5.2pt, fill: C.muted)),
      )),
      card-box("Notes de la séance", t("Ciel clair, Lune phase 85 %, non gênante en début de soirée, brouillard en fin de session. L'empilement « mosaic » sous Siril ne fonctionne pas ; en mode normal, Siril retient 496 images sur 800…", size: 5.4pt)),
      grid(columns: (1fr, auto), align: horizon, section-title("Conditions de la nuit"), box(width: 130pt, tabs(("Graphes", "Tableau météo"), 0))),
      alt-chart((2026, 10, 30), here.lat, here.lon, (ngc672,), height: 108pt, obs: (
        (label: "Observation", from: 20.65, to: 26.6, color: C.accent),
      )),
      wx-chart(wx-oct30, (20.65, 26.6), (nd30.night.first().t, nd30.night.last().t), width: 100%, height: 72pt),
      wx-legend,
    ),
    block(width: 100%, height: 392pt, clip: true, spacing: 0pt, {
      stack(
        spacing: 6pt,
        [#filt-btn("Toutes (5)") #filt-btn("NGC 672", on: true) #filt-btn("IC 1727")],
        img-tile("Siril · RVB", "NGC 672 · traitée · recadrée", 66pt, shade: 30%, fav: true),
        img-tile("AstroWizard · RVB", "NGC 672 · traitée · finition Photoshop", 66pt, shade: 45%),
        img-tile("Brute (Seestar)", "Champ entier", 66pt, shade: 70%),
        img-tile("Non recadrée", "Champ entier · astrométrie", 66pt, shade: 60%),
        img-tile("…", "", 66pt, shade: 80%),
      )
      place(top + right, dx: 0pt, dy: 20pt, rect(width: 2.5pt, height: 130pt, radius: 1.2pt, fill: C.line))
    }),
  ),
)))
#caption-note[Maquette, mode lecture : vraies données de l'observation du 30/10/2026. La ligne NGC 672 est sélectionnée, la galerie n'affiche que ses images et celles du champ entier ; l'ascenseur permet de faire défiler. Les traitements affichés sont des exemples, de même que les poses d'IC 1727 (la base n'a qu'un compteur pour les deux cibles), qui illustrent des poses retenues différentes d'une cible à l'autre. La hauteur, la Lune et les crépuscules sont calculés ; la météo vient de la note.]

=== Mode modification

#let dropdown = block(width: 100%, fill: C.bg, stroke: 0.6pt + C.accent, radius: 2pt, clip: true, spacing: 0pt, stack(
  block(width: 100%, inset: (x: 4pt, y: 2.8pt), spacing: 0pt, fill: C.field, t("✓  Jardin", size: 5.5pt)),
  block(width: 100%, inset: (x: 4pt, y: 2.8pt), spacing: 0pt, t("Gîte de vacances (exemple)", size: 5.5pt, fill: C.muted)),
  block(width: 100%, inset: (x: 4pt, y: 2.8pt), spacing: 0pt, stroke: (top: 0.4pt + C.line), t("+ Nouveau lieu…", size: 5.5pt, fill: C.accent, weight: "bold")),
))
#let check(s, on: true) = [#box(width: 5.5pt, height: 5.5pt, radius: 1pt, stroke: 0.6pt + C.accent, fill: if on { C.accent } else { none }) #t(s, size: 5.3pt)]
#let img-row(title, sub, sel: false, fav: false) = block(
  width: 100%, inset: 3pt, radius: 2pt, spacing: 0pt,
  fill: if sel { C.accent.transparentize(80%) } else { none },
  stroke: if sel { 0.5pt + C.accent } else { (bottom: 0.4pt + C.border) },
  grid(columns: (22pt, 1fr, auto), column-gutter: 4pt, align: horizon,
    box(width: 22pt, height: 15pt, radius: 1.5pt, fill: gradient.radial(C.accent.transparentize(40%), C.bg, radius: 80%)),
    stack(spacing: 2pt, t(title, size: 5.3pt, weight: "bold"), t(sub, size: 4.5pt, fill: C.muted)),
    t((if fav { "⭐ " } else { "" }) + "✕", size: 5.5pt, fill: C.red),
  ),
)

#window(title: "Rapport d'observation", block(inset: 8pt, width: 100%, stack(
  spacing: 6pt,
  grid(columns: (1fr, auto, auto, auto), column-gutter: 4pt, align: horizon,
    t("RAPPORT DU 30/10/2026", size: 7pt, weight: "bold"),
    btn("Enregistrer", primary: true), btn("Annuler"), btn("Supprimer"),
  ),
  grid(
    columns: (1fr, 128pt), column-gutter: 8pt,
    stack(
      spacing: 6pt,
      grid(
        columns: (1fr, 1fr, 1fr), column-gutter: 5pt,
        card-box("1. Session", stack(spacing: 4.5pt,
          fld("Lieu", "Jardin  ▾"),
          dropdown,
          fld("Début (TU)", "30/10/2026  20:39"),
          fld("Fin (TU)", "31/10/2026  02:36"),
        )),
        card-box("2. Matériel & pose", stack(spacing: 4.5pt,
          fld("Capteur", "Seestar S50"),
          fld("Filtre", "IRCUT"),
          fld("Temp. capteur (°C)", "24.2"),
          fld("Pose indiv. (s)", "10"),
        )),
        card-box("3. Images", stack(spacing: 4.5pt,
          fld("Total des poses", "800"),
          t("Poses retenues : par cible, dans le tableau des cibles", size: 5pt, fill: C.muted),
        )),
      ),
      card-box("Cibles du champ", table(
        columns: (1fr, 0.7fr, 0.55fr, 0.55fr, 0.55fr, auto),
        stroke: none, inset: 2.5pt, align: horizon,
        ..tgt-head(("Cible", "Hauteur (°)", "Bon", "Pass", "Bad", "")),
        fieldbox("NGC 672"), fieldbox(str(calc.round(mid30)), hint: "auto"), fieldbox("510"), fieldbox("290"), fieldbox("317"), t("✕", size: 7pt, fill: C.red),
        table.cell(colspan: 5, fieldbox("Bras spiraux bien visibles ; IC 1727, voisine…", hint: "note de la cible")), [],
        fieldbox("IC 1727"), fieldbox(str(calc.round(mid30)), hint: "auto"), fieldbox("496"), fieldbox("290"), fieldbox("331"), t("✕", size: 7pt, fill: C.red),
        table.cell(colspan: 5, fieldbox("", hint: "note de la cible")), [],
        table.cell(colspan: 6, t("+ Ajouter une cible…  (recherche par nom : M 31, NGC 7000, Sh2-132…)", size: 5.5pt, fill: C.accent, weight: "bold")),
      )),
      stack(spacing: 2pt, lbl("Notes de la séance"), block(width: 100%, height: 30pt, inset: 4pt, fill: C.field, stroke: 0.5pt + C.line, radius: 2pt, t("Ciel clair, Lune phase 85 %, non gênante en début de soirée…", size: 5.4pt))),
      t("Météo : modifiable dans l'onglet « Tableau météo » (voir 4.4).", size: 5pt, fill: C.muted),
    ),
    stack(
      spacing: 5pt,
      grid(columns: (1fr, auto), align: horizon, section-title("Images (5)"), btn("+ Ajouter…")),
      img-row("Siril · RVB", "traitée · NGC 672", sel: true, fav: true),
      img-row("AstroWizard · RVB", "traitée · NGC 672"),
      img-row("AstroWizard · RVB", "traitée · IC 1727"),
      img-row("Brute (Seestar)", "champ entier"),
      img-row("Non recadrée", "astrométrie · champ entier"),
      block(width: 100%, fill: rgb("#1e1e21"), stroke: 0.5pt + C.accent, radius: 3pt, inset: 5pt, stack(
        spacing: 4.5pt,
        t("IMAGE SÉLECTIONNÉE", size: 5pt, weight: "bold", fill: C.muted),
        grid(columns: (1fr, 1fr), column-gutter: 4pt, fld("Type", "traitée ▾"), fld("Logiciel", "Siril ▾")),
        fld("Palette", "naturelle (RVB) ▾"),
        stack(spacing: 3pt, lbl("Cibles visibles (aucune = champ entier)"), check("NGC 672"), check("IC 1727", on: false)),
        [#t("⭐", size: 6pt) #t("Image favorite (vignette)", size: 5.3pt)],
      )),
    ),
  ),
)))
#caption-note[Maquette, mode modification : la liste des lieux est dépliée (« Gîte de vacances » est un exemple fictif ; « + Nouveau lieu… » ouvre l'overlay carte, voir 4.5). À droite, la liste des images et les informations de l'image sélectionnée.]


== Grille météo éditable

L'onglet *Tableau météo* du rapport affiche les mêmes relevés que le graphe. Toutes les cellules sont modifiables. Les lignes saisies ou corrigées à la main sont mises en évidence et protégées contre le rafraîchissement.

#window(title: "Rapport — onglet Tableau météo (modification)", block(inset: 8pt, width: 100%, stack(
  spacing: 6pt,
  grid(columns: (1fr, auto, auto, auto), column-gutter: 4pt,
    box(width: 130pt, tabs(("Graphes", "Tableau météo"), 1)),
    btn("Coller une ligne meteoblue"), btn("+ Relevé"), btn("↻ Open-Meteo"),
  ),
  wx-table(wx-oct02),
  t("✎ : lignes collées depuis meteoblue. Seeing et index ne sont fournis que par meteoblue ; « — » = non renseigné.", size: 5pt, fill: C.muted),
)))
#caption-note[Maquette : les 3 premières lignes ont été collées depuis meteoblue, les suivantes viennent d'Open-Meteo. Les valeurs Open-Meteo sont illustratives.]

Le bouton *Coller une ligne meteoblue* accepte le format déjà utilisé dans les notes, par exemple `21h00 TU ( 34-0-0 / 1.39 / 4-2 / 16ms / 13°C / 91% )`, avec ses variantes d'écriture (`_` ou `-`, espaces, unités).

== Création d'un lieu sur une carte

Dans le rapport, le lieu se choisit dans une liste déroulante, qui propose aussi « + Nouveau lieu… ». Cette entrée ouvre un overlay avec une carte. Un clic sur la carte place le repère, remplit les coordonnées et propose un libellé tiré de l'adresse du point. Le libellé reste modifiable.

#window(title: "Nouveau lieu", height: 206pt, grid(
  columns: (1fr, 150pt),
  block(width: 100%, height: 192pt, fill: rgb("#ece9e1"), clip: true, spacing: 0pt, {
    place(top + left, dx: 205pt, dy: 105pt, rect(width: 90pt, height: 55pt, fill: rgb("#cfe5bd"), radius: 4pt))
    place(top + left, line(start: (0pt, 62pt), end: (340pt, 92pt), stroke: 6pt + white))
    place(top + left, line(start: (118pt, 0pt), end: (150pt, 192pt), stroke: 4.5pt + white))
    place(top + left, line(start: (0pt, 158pt), end: (340pt, 128pt), stroke: 3pt + white))
    place(top + left, line(start: (250pt, 0pt), end: (230pt, 110pt), stroke: 2.5pt + white))
    for (x0, y0) in ((20pt, 18pt), (45pt, 24pt), (72pt, 30pt), (160pt, 20pt), (185pt, 26pt), (20pt, 92pt), (48pt, 96pt), (78pt, 100pt), (165pt, 104pt), (170pt, 140pt), (40pt, 170pt), (75pt, 165pt), (270pt, 40pt), (290pt, 60pt)) {
      place(top + left, dx: x0, dy: y0, rect(width: 16pt, height: 11pt, fill: rgb("#d9d0c1"), stroke: 0.4pt + rgb("#bdb3a3")))
    }
    place(top + left, dx: 186pt, dy: 52pt, stack(
      spacing: 0pt,
      circle(radius: 5pt, fill: rgb("#e11d48"), stroke: 1pt + white),
      place(dx: 4.2pt, dy: -1pt, polygon(fill: rgb("#e11d48"), stroke: none, (0pt, 0pt), (1.6pt, 6pt), (3.2pt, 0pt))),
    ))
    place(top + left, dx: 6pt, dy: 6pt, stack(
      box(width: 13pt, height: 13pt, fill: white, stroke: 0.5pt + luma(160), align(center + horizon, text(size: 8pt)[+])),
      box(width: 13pt, height: 13pt, fill: white, stroke: 0.5pt + luma(160), align(center + horizon, text(size: 8pt)[−])),
    ))
    place(top + left, dx: 26pt, dy: 6pt, box(width: 150pt, inset: (x: 4pt, y: 3pt), fill: white, stroke: 0.5pt + luma(170), radius: 2pt, text(size: 5.5pt, fill: luma(110))[Rechercher une adresse…]))
    place(bottom + right, dx: -3pt, dy: -3pt, box(fill: white.transparentize(30%), inset: 1.5pt, text(size: 4pt, fill: luma(80))[© contributeurs OpenStreetMap]))
  }),
  block(inset: 8pt, height: 192pt, width: 100%, fill: C.panel, stroke: (left: 0.5pt + C.border), stack(
    spacing: 6.5pt,
    section-title("Nouveau lieu"),
    fld("Libellé (modifiable)", "Jardin"),
    fld("Adresse détectée", "Rue de l'Exemple, Commune"),
    grid(columns: (1fr, 1fr), column-gutter: 4pt, fld("Latitude", "50.52470"), fld("Longitude", "2.64028")),
    grid(columns: (1fr, 1fr), column-gutter: 4pt, fld("Altitude (m)", "auto"), fld("Bortle par défaut", "6.5")),
    v(4pt),
    align(right, [#btn("Annuler") #btn("Enregistrer", primary: true)]),
  )),
))
#caption-note[Maquette : un clic sur la carte place le repère et remplit les champs. L'adresse affichée ici est fictive.]

*Technique proposée :* *Leaflet* pour la carte, les fonds de carte *OpenStreetMap* et le service *Nominatim* pour retrouver l'adresse d'un point, plutôt que Google Maps :
- pas de clé d'API, de compte de facturation ni de quota payant ;
- Google Maps imposerait d'embarquer une clé dans l'application de bureau, donc récupérable par n'importe qui ;
- l'usage d'AllNightLong (quelques clics de temps en temps) reste très en dessous des limites d'usage de Nominatim (1 requête par seconde) ;
- l'altitude du point peut être obtenue automatiquement, gratuitement aussi, via l'API Elevation d'Open-Meteo.

== Hauteur des cibles au cours de la nuit

Le graphe de hauteur proposé par NightAstro peut être *recalculé entièrement dans l'application*, sans service externe. Il suffit des coordonnées de la cible (RA/Dec, déjà dans la fiche), de celles du lieu et de l'heure. Le Soleil (crépuscules) et la Lune (hauteur et phase) se calculent de la même façon.

#window(title: "Hauteur au cours de la nuit — M 31, nuit du 17 au 18/11/2026 · Jardin", block(inset: 8pt, width: 100%, stack(
  spacing: 6pt,
  t("Pas de 5 minutes · du coucher au lever du Soleil · heures en TU", size: 5.2pt, fill: C.muted),
  alt-legend(nd17.night.at(0).illum),
  alt-chart((2026, 11, 17), here.lat, here.lon, (m31,), height: 150pt),
)))
#caption-note[Courbes calculées directement par ce document, avec les formules de basse précision envisagées pour l'application.]

*Vérification avec la capture NightAstro de la même nuit :*
#table(
  columns: (1fr, auto, auto),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([*Grandeur*], [*NightAstro (heure locale)*], [*Calcul (TU → locale)*]),
  [Coucher du Soleil], [17:03], [#hm(nd17.night.first().t) → #hm(nd17.night.first().t + 1)],
  [Lever du Soleil], [08:09], [#hm(nd17.night.last().t) → #hm(nd17.night.last().t + 1)],
  [Culmination de M 31], [21:43 · 81°], [#hm(m31-best.t) → #hm(m31-best.t + 1) · #calc.round(m31-best.tg.at(0))°],
  [Coucher de la Lune], [≈ 00:30 (lu sur le graphe)], [#{
    let set-s = nd17.night.zip(nd17.night.slice(1)).find(((a, b)) => a.moon >= 0 and b.moon < 0)
    if set-s == none [—] else [#hm(set-s.at(1).t) → #hm(set-s.at(1).t + 1)]
  }],
)

Pour le Soleil et M 31, les écarts sont de quelques minutes (le calcul est fait par pas de 5 minutes) et inférieurs au degré. Pour la Lune, les formules très simplifiées utilisées dans ce document donnent un coucher une dizaine de minutes plus tôt. L'application utilisera une vraie bibliothèque d'éphémérides (voir plus bas), plus précise. La phase calculée reste cohérente avec les notes : 25 % le 14/11, pour « premier croissant, 26–30 % » relevé par l'utilisateur.

=== Dans l'application

Le graphe de hauteur apparaît dans le rapport d'observation (voir 4.3), au-dessus du graphe météo et sur la même échelle de temps. Les cibles d'une même observation sont dans le même champ : leurs courbes se confondent, une seule courbe suffit. Quand deux observations ont lieu la même nuit au même endroit (le 02/03 : le champ d'Orion puis M 101), chacune garde son rapport et son graphe, et elles partagent les mêmes relevés météo. Toutes les heures sont affichées en TU, comme dans les FITS et meteoblue ; seule la comparaison avec NightAstro ci-dessus convertit en heure locale.

*Ce que le calcul apporte en plus :*
- *hauteur de la cible remplie automatiquement :* le champ `altitude` d'une observation est aujourd'hui saisi à la main. On peut le proposer automatiquement (hauteur au milieu du créneau, ou maximale) en le laissant modifiable ;
- *phase de la Lune calculée*, pour la session ;
- *horizon du lieu (plus tard) :* comme NightAstro, on pourrait enregistrer pour chaque lieu les secteurs bloqués (murs, arbres). La note de M 42 du 02/03 parle d'un platane qui a fait écarter 124 poses ; le graphe montrerait le moment où la cible passe derrière.

*Technique :* le calcul se fait côté interface avec une bibliothèque d'éphémérides légère et hors ligne, par exemple *astronomy-engine* (licence MIT), plus précise que les formules simplifiées utilisées ici. Les RA/Dec des cibles sont déjà lus par la carte céleste (`MapModal.svelte`).

== Panneau de réglages

Un écran *Réglages*, ouvert par une roue dentée ⚙ en haut de la fenêtre, regroupe les préférences de l'application. Il sert d'abord à choisir le *dossier des images*. Il accueille aussi les questions qui n'ont pas une seule bonne réponse : plutôt que de trancher, on met en place les deux ou trois choix préférés, et l'utilisateur choisit.

*Chemins relatifs :* un chemin d'image est enregistré *relativement au dossier des images*. Si le dossier change de place ou de lettre de disque (`E:` devient `F:`), il suffit de modifier le réglage : toutes les images se retrouvent. Une image ajoutée hors de ce dossier garde son chemin complet, et l'interface le signale. Une image introuvable est affichée comme un cadre vide avec son chemin, sans bloquer le rapport.

#let radio(s, on: false) = [#box(width: 5.5pt, height: 5.5pt, radius: 2.75pt, stroke: 0.6pt + C.accent, fill: if on { C.accent } else { none }) #t(s, size: 5.5pt, fill: if on { C.fg } else { C.muted })]
#let set-row(label, ctrl, note: none) = grid(
  columns: (118pt, 1fr), column-gutter: 8pt, align: horizon,
  t(label, size: 5.8pt, weight: "bold"),
  stack(spacing: 2.5pt, ctrl, if note != none { t(note, size: 4.8pt, fill: C.muted) }),
)

#window(title: "AllNightLong — Réglages", block(inset: 8pt, width: 100%, stack(
  spacing: 6pt,
  grid(columns: (1fr, auto, auto), column-gutter: 4pt, align: horizon,
    t("⚙  RÉGLAGES", size: 7pt, weight: "bold"), btn("Enregistrer", primary: true), btn("Fermer"),
  ),
  card-box("Images", stack(spacing: 5pt,
    set-row("Dossier des images", grid(columns: (1fr, auto), column-gutter: 4pt, fieldbox("E:\\Astro"), btn("Parcourir…")),
      note: "Les images sont enregistrées par leur chemin dans ce dossier, par exemple « 2026-10-30 NGC 672\\siril_rvb.jpg ». Elles ne sont jamais copiées."),
  )),
  card-box("Météo", stack(spacing: 5pt,
    set-row("Marge autour du créneau", box(width: 60pt, fieldbox("1 h  ▾"))),
    set-row("Récupération automatique", [#radio("à la création du rapport", on: true) #h(8pt) #radio("aussi à l'ouverture, si des relevés manquent")], note: "Q5"),
  )),
  card-box("Hauteur des cibles", stack(spacing: 5pt,
    set-row("Valeur proposée", [#radio("au milieu du créneau", on: true) #h(8pt) #radio("maximale") #h(8pt) #radio("min / max")], note: "Q11"),
    set-row("Hauteur minimale utile", box(width: 60pt, fieldbox("25°")), note: "Q12 · ligne affichée sur le graphe de hauteur"),
  )),
  card-box("Affichage", stack(spacing: 5pt,
    set-row("Onglet Observations", [#radio("cartes", on: true) #h(8pt) #radio("tableau (version ultérieure)")], note: "Q3"),
  )),
)))
#caption-note[Maquette du panneau de réglages. Les réglages marqués d'une question (Q5, Q11, Q12) correspondent aux points encore ouverts (section 7.2) : ils pourraient être tranchés par un réglage plutôt que par une décision définitive.]


= Reprise des données existantes

Une migration unique, précédée d'une sauvegarde automatique de la base (la fonction de backup existe déjà) :
+ *Lieux :* regrouper les coordonnées proches (à quelques dizaines de mètres près) et « Jardin » en un ou deux lieux, à faire valider.
+ *Sessions :* créer une session par nuit et par lieu.
+ *Observations conjointes :* fusionner les fiches qui ont la même nuit, des horaires à quelques minutes près et les mêmes compteurs de poses en une observation à plusieurs cibles. La hauteur est conservée pour chaque cible.
+ *Météo :* extraire automatiquement les relevés présents dans les notes (source `meteoblue`). On peut ensuite compléter les nuits sans relevé avec Open-Meteo.
+ *Images :* les chemins sous `E:\Astro` sont convertis en chemins relatifs à ce dossier, les autres restent complets et sont signalés. `image_raw` devient une image « brute » du champ entier ; `image_processed` devient une image « traitée » étiquetée avec la cible de sa fiche d'origine, et marquée favorite. Après la fusion des fiches conjointes, chaque image reste donc attachée à sa cible. Le logiciel et la palette peuvent être déduits du nom de fichier quand il les mentionne (« wizard », « duoband »…), sinon ils restent à renseigner.
+ *Dates :* l'utilisateur a conservé tous ses FITS (environ 50 Go). La migration lit seulement leur en-tête (`DATE-OBS`, `OBJECT`, filtre, pose), ce qui est rapide malgré le volume, et en tire le début et la fin exacts de chaque observation. Cela tranche les dates du soir et du matin, et corrige au passage les heures saisies à la main. Les rares observations sans FITS retrouvé sont signalées.
+ *Notes :* les notes existantes restent des notes de séance. Les passages qui décrivent une seule cible (« M65, M66 et NGC 3628 forment le Triplet du Lion… ») peuvent être déplacés dans la note de cette cible observée, au cas par cas.
+ *Cas ambigus :* la migration est faite par nous, sur une copie de la base, puis vérifiée avec l'utilisateur avant d'être appliquée. Il n'y a pas d'écran propre à la migration : les cas restants (compteurs différents pour NGC 6820/6823, copie suspecte du 14/08) apparaissent dans l'écran « Données à vérifier » ci-dessous.

== Données à vérifier

Un écran permanent liste les données *suspectes*, détectées par des règles simples (sans intelligence artificielle). Il sert après la migration comme pour les nouvelles saisies. Chaque ligne renvoie au rapport concerné et peut être corrigée ou marquée « c'est normal ».

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([*Règle*], [*Exemple*]),
  [Deux observations qui se chevauchent dans le même lieu (même instrument)], [IC 1848 et Sh2-132, avant correction des dates],
  [Bon + pass + bad ≠ total], [compteur mal recopié],
  [Même ligne météo sur deux nuits différentes], [la copie du 02/03 sur le 14/08],
  [Phase de Lune notée éloignée de la phase calculée], [note datée de la mauvaise nuit],
  [Hauteur saisie éloignée de la hauteur calculée], [hauteur recopiée d'une autre cible],
  [Fin avant le début, durée de plus de 14 h, observation sans FITS ni image], [erreurs de saisie],
)

Le texte des notes reste intact. Rien n'est supprimé, les données sont seulement structurées à côté.

= Découpage en lots

#table(
  columns: (auto, 1fr, auto),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([*Lot*], [*Contenu*], [*Dépend de*]),
  [*1. Lieux*], [Table `location`, API, liste déroulante dans le rapport, overlay carte (Leaflet + Nominatim), autorisation des domaines de cartes dans la configuration Tauri], [—],
  [*2. Sessions et multi-cibles*], [Tables `session` et `observation_target`, adaptation de l'API et du rapport (lieu, début et fin en date + heure TU, tableau des cibles avec note par cible, notes de séance déplacées), champ instrument optionnel, tri de la colonne de gauche, onglet Observations en cartes], [1],
  [*3. Images multiples*], [Tables `observation_image` et `image_target`, galerie avec filtre par cible dans le rapport, ajout de plusieurs images, informations par image, image favorite utilisée comme vignette, panneau de réglages (dossier des images, chemins relatifs), complété par les lots suivants], [2],
  [*4. Météo : données*], [Table `weather_reading`, appel Open-Meteo depuis le backend, récupération à la création, bouton rafraîchir, règles « source / modifié »], [2],
  [*5. Météo : affichage*], [Graphe interactif (bibliothèque légère, par exemple uPlot ou LayerChart), grille éditable, collage d'une ligne meteoblue], [4],
  [*6. Migration*], [Lecture des en-têtes FITS (dates et heures exactes), regroupement des lieux et des observations conjointes, conversion des images, extraction des relevés des notes. Faite par nous sur une copie, puis vérifiée avec l'utilisateur], [1–4],
  [*7. Hauteur des cibles*], [Bibliothèque d'éphémérides, graphe de hauteur (cibles, Lune, crépuscules, créneau) aligné sur le graphe météo, hauteur de la cible proposée automatiquement, phase de la Lune], [1–2],
  [*8. Horizon du lieu* (optionnel)], [Secteurs d'horizon bloqués par lieu, hauteur minimale, affichage dans le graphe de hauteur], [7],
  [*9. Données à vérifier*], [Écran listant les données suspectes selon des règles simples, avec lien vers le rapport et « c'est normal »], [6, 7],
  [*10. Comparaison d'images* (plus tard)], [Deux images côte à côte dans l'application, avec zoom synchronisé], [3],
  [*11. Pré-remplissage depuis le FITS*], [Bouton « Depuis un FITS… » à la création d'un rapport : lecture de l'en-tête du FITS empilé, champs remplis automatiquement et modifiables, cible retrouvée par son nom], [2, 6],
)

Chaque lot passe par la mécanique de migration déjà en place (`schema_version` dans `main.py`), et chaque mise à jour du schéma est précédée d'une sauvegarde.

*Méthode de réalisation :* les lots sont réalisés *un à la fois*, dans l'ordre du tableau (les lots optionnels ou « plus tard » restent à confirmer le moment venu) :
+ une *branche* est créée pour le lot ;
+ le lot y est développé ;
+ il est *testé et validé* par l'utilisateur sur cette branche ;
+ il est fusionné dans la branche principale ;
+ le lot suivant ne commence qu'ensuite.

= Questions

== Réponses reçues

#table(
  columns: (auto, auto, 1fr),
  stroke: 0.4pt + luma(200),
  inset: 5pt,
  fill: (x, y) => if y == 0 { luma(235) },
  table.header([*N°*], [*Sujet*], [*Décision et conséquence dans ce document*]),
  [Q1], [Poses par cible], [Oui, le nombre de poses peut varier d'une cible à l'autre. Les poses retenues, à revoir et rejetées passent au niveau observation × cible (3.1, 4.3) ; le total reste au niveau de l'observation.],
  [Q2], [Notes descriptives], [Une note *par cible observée* s'ajoute aux notes de la fiche cible et aux notes de séance. Les textes descriptifs y sont déplacés au cas par cas (4.3, 5).],
  [Q3], [Cartes ou grille], [Proposition A (cartes), nettement préférée. La grille, jugée intéressante, pourra venir plus tard comme choix d'affichage dans les réglages (4.2, 4.7).],
  [Q4], [Fenêtre météo], [Le créneau de l'observation avec une marge (1 h par défaut, réglable). La fenêtre s'élargit si une autre observation s'ajoute à la même nuit (2).],
  [Q6], [Heures en TU], [Toutes les heures restent en TU, sans heure locale à côté (maquettes 4.3).],
  [Q7], [Instrument], [Les cas relevés étaient des observations successives, pas simultanées. Un champ « instrument » optionnel est ajouté quand même (3).],
  [Q8], [Bortle], [Valeur par défaut selon le lieu, modifiable dans la session (3.1).],
  [Q9], [Validation de la migration], [Faite par nous, sur une copie de la base. Pas d'écran propre à la migration, mais un écran permanent « Données à vérifier », fondé sur des règles simples (5.1).],
  [Q10], [Axe des graphes], [Tranchée par Q6 : axe en TU.],
  [Q13], [Stockage des images], [Pas de copie. Un dossier des images est choisi dans un nouveau panneau de réglages, et les chemins sont enregistrés relativement à ce dossier (4.3, 4.7, 5).],
  [Q14], [Comparaison d'images], [Utile mais pas urgent : l'utilisateur ouvre aujourd'hui plusieurs fenêtres côte à côte. Lot ultérieur (6).],
  [Q15], [Dates des observations], [Deux champs date + heure TU complets pour le début et la fin ; la date affichée est celle du début. IC 1848 (13/11 19:30 → 14/11 02:41) et Sh2-132 (14/11 18:56 → 23:19) sont deux nuits différentes. Les dates exactes sont reprises des en-têtes FITS, tous conservés (3.1, 5).],
  [Q16], [Pré-remplir depuis le FITS], [Intéressant. L'utilisateur désigne le FITS empilé et le rapport se remplit seul (début, fin, cible, filtre, température du capteur, pose unitaire, nombre de poses), en réutilisant la lecture des en-têtes de la migration. Lot 11 (6).],
)

== Questions en suspens

Elles peuvent toutes devenir des *réglages* (4.7) plutôt qu'une décision définitive : c'est indiqué entre crochets.

#let q(n, title, body) = block(
  width: 100%, inset: (left: 8pt, y: 4pt), stroke: (left: 2pt + rgb("#6366f1")), spacing: 9pt,
  [*Q#n — #title* \ #body],
)

#q(5, "Moment de la récupération météo")[À la création du rapport uniquement, avec ensuite un bouton manuel ? Ou aussi automatiquement à l'ouverture si des relevés manquent ? Sans réseau : la récupération se fait plus tard, sans bloquer la saisie. #text(fill: luma(110))[\[réglage possible\]]]
#q(11, "Hauteur de cible automatique")[Quelle valeur proposer dans le champ « hauteur de cible » : la hauteur au milieu du créneau, la hauteur maximale pendant le créneau, ou les deux (min / max) ? #text(fill: luma(110))[\[réglage possible\]]]
#q(12, "Horizon du lieu")[L'horizon par secteurs (murs, arbres) et la hauteur minimale sont-ils prioritaires, ou pour une version ultérieure ? La hauteur minimale est-elle propre au lieu ou à l'utilisateur ? #text(fill: luma(110))[\[réglage possible pour la hauteur minimale\]]]
