"""Construit les pages du site a partir des textes.

    python -I site/_outils/rendre.py

Sources : i18n/<langue>.json (les textes, une cle par chaine), nouveautes.json
(une entree par version), media/videos.json (duree et format des videos, ecrit
par medias.py) et _outils/modele.html (la mise en page).
Sortie : index.html (anglais, langue par defaut) et <langue>/index.html.

Une cle absente d'une langue retombe sur l'anglais : on peut publier une
traduction incomplete sans casser la page. Le script signale chaque repli.

Les appareils en volume (telephone, montre, tablette) et les decors qui les
entourent sont ecrits ici, pas dans le gabarit : chaque appareil est fait
d'une pile de plaques (son epaisseur), d'un dos, d'une face et d'un reflet,
et le meme balisage sert au heros, au recit et aux cartes.
"""
import html
import json
import random
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
URL = "https://mistano.github.io/omega-player/"
PLAY = "https://play.google.com/store/apps/details?id=com.mistano.omegaplayer&hl="
# Nombre d'ambiances affiche par les textes : le jeton {ambiances} des i18n/*.json est remplace
# par cette valeur a la construction. Seul endroit a changer quand le catalogue change
# (puis relancer ce script). L'outil de regeneration des videos la tient a jour.
AMBIANCES = 29
LANGUES = ["en", "fr", "de", "es", "it", "pt", "ru", "ar", "ja", "ko", "zh"]
HL = {"zh": "zh-CN", "pt": "pt-PT"}
BALISE_LANG = {"zh": "zh-Hans"}
# Langue de l'interface montree dans les captures et les videos : seules
# l'anglaise et la francaise existent.
UI = {"fr": "fr"}
OG = {"fr": "fr"}
FACTURE = ["crossfade", "volume", "eq", "spatial", "queue", "playlists", "moods", "auto", "wear", "privacy"]
# Videos selon l'ecran : sur ordinateur, uniquement des 16:9 ; sur mobile
# (moins de 900 px, le seuil du bandeau de l'addition), uniquement des 9:16.
# Chaque emplacement a donc deux cles (fichiers media/<cle>-<ui>.*, ecrits par
# medias.py) : (cle 16:9, titre 16:9, cle 9:16, titre 9:16). Les deux liens
# sont dans la page, la feuille de style n'en montre qu'un : sans script, la
# vignette visible mene au bon fichier.
FILM = ("fiche", "addition")
# Galerie, dans l'ordre : + ton (« calm » = version sage, « wild » = deglinguee).
BOBINES = [("blanc-16x9", "v_blanc", "blanc", "v_blanc", "calm"),
           ("ambiances-16x9", "v_ambiances", "ambiances", "v_ambiances", "calm"),
           ("fou", "v_fou", "fou-9x16", "v_fou", "calm"),
           ("cirque", "v_cirque", "cirque-9x16", "v_cirque", "wild"),
           ("teleachat", "v_teleachat", "teleachat-9x16", "v_teleachat", "wild"),
           ("film", "v_film", "film-9x16", "v_film", "wild"),
           ("documentaire-16x9", "v_documentaire", "documentaire", "v_documentaire", "wild"),
           ("ytp-16x9", "v_ytp", "ytp-9x16", "v_ytp", "wild"),
           ("diaporama-16x9", "v_diaporama", "diaporama-9x16", "v_diaporama", "wild"),
           ("popups-16x9", "v_popups", "popups-9x16", "v_popups", "wild")]

# Detection au premier passage, sur la page anglaise (racine) seulement : si le
# visiteur n'a jamais choisi de langue et que son navigateur en prefere une
# autre que le site connait, on l'y envoie. Le choix explicite (clic dans le
# selecteur) est memorise et gagne toujours.
DETECTION = (
    "try{if(!localStorage.getItem('omega-lang')){var L=%s,n=(navigator.languages||[navigator.language||'']);"
    "for(var i=0;i<n.length;i++){var c=(n[i]||'').toLowerCase().slice(0,2);if(c==='en')break;"
    "if(L.indexOf(c)>0){location.replace(c+'/'+location.hash);break}}}}catch(e){}"
) % json.dumps(LANGUES)


def charger(nom):
    return json.loads((SITE / nom).read_text(encoding="utf-8"))


def barres():
    rnd = random.Random(42)
    out = []
    for i in range(40):
        h = 0.25 + 0.75 * abs(rnd.gauss(0.45, 0.3)) % 1
        out.append('<i style="--h:%.2f;--d:%.2fs;--o:%.2fs"></i>' % (h, 0.7 + rnd.random() * 0.9, -rnd.random() * 2))
    return "".join(out)


def image(chemin, l, h, alt="", jpg=True, paresse=True, extra="", prioritaire=False):
    """<picture> AVIF + WebP (+ JPEG de repli). `chemin` sans extension."""
    att = ' loading="lazy" decoding="async"' if paresse else ""
    if prioritaire:
        att += ' fetchpriority="high"'
    repli = f"{chemin}.jpg" if jpg else f"{chemin}.webp"
    webp = f'<source type="image/webp" srcset="{chemin}.webp">' if jpg else ""
    return (f'<picture{extra}><source type="image/avif" srcset="{chemin}.avif">{webp}'
            f'<img src="{repli}" width="{l}" height="{h}" alt="{html.escape(alt, quote=True)}"{att}></picture>')


def telephone(ecrans, classe="", tranches=6, attributs="", pose=""):
    """Telephone en volume. `ecrans` : les <picture> empiles dans l'ecran."""
    plaques = "".join(f'<i class="tel__tr" style="--z:{i}"></i>' for i in range(1, tranches + 1))
    style = f"--n:{tranches}" + (f";--p:{pose}" if pose else "")
    return (f'<div class="tel {classe}" style="{style}"{attributs}><div class="tel__corps">{plaques}'
            f'<i class="tel__dos"></i><div class="tel__face"><div class="tel__ecran">{ecrans}</div>'
            f'<i class="tel__reflet"><i></i></i></div></div></div>')


def montre(ecran, classe="", tranches=4):
    plaques = "".join(f'<i class="montre__tr" style="--z:{i}"></i>' for i in range(1, tranches + 1))
    return (f'<div class="montre {classe}" style="--n:{tranches}"><div class="montre__corps">'
            f'<i class="montre__bracelet montre__bracelet--h"></i><i class="montre__bracelet montre__bracelet--b"></i>'
            f'{plaques}<i class="montre__couronne"></i><div class="montre__face">{ecran}</div>'
            f'<i class="montre__reflet"></i></div></div>')


def pochette(base, nom, pose, classe=""):
    return (f'<div class="poch {classe}" style="--p:{pose}">'
            f'{image(f"{base}img/covers/{nom}", 320, 320, jpg=False)}</div>')


def minutes(s):
    s = round(s)
    return f"{s // 60}:{s % 60:02d}"


def appareils(base, ui, t):
    """Les appareils et scenes en volume de la page : cles brutes du gabarit."""
    tel = f"{base}img/phone/{ui}/"

    def ecran(nom, alt="", paresse=True, extra="", prioritaire=False):
        return image(tel + nom, 720, 1280, alt, paresse=paresse, extra=extra, prioritaire=prioritaire)

    def amb(i):
        return image(f"{tel}ambiance-{i}", 540, 960, jpg=False)

    out = {}

    # Heros : le lecteur devant, l'accueil derriere, trois pochettes a des
    # profondeurs differentes, la montre au premier plan. Les ecrans suivants
    # du telephone (data-cycle) ne sont charges qu'apres le premier affichage.
    suite = html.escape(json.dumps([tel + "03-effets", tel + "06-playlists"]), quote=True)
    out["hero_scene"] = (
        telephone(ecran("01-accueil"), "tel--fond", 2)
        + pochette(base, "lofi", "translate3d(-96%,-150%,-150px) rotateZ(-8deg)", "poch--a")
        + pochette(base, "espace", "translate3d(128%,168%,130px) rotateZ(7deg)", "poch--b")
        + pochette(base, "tropical", "translate3d(170%,-215%,-60px) rotateZ(12deg)", "poch--c")
        + telephone(ecran("02-lecteur", t["alt_player"], paresse=False, extra=' class="is-on"', prioritaire=True),
                    "tel--hero", 6, f' data-cycle="{suite}"')
        + montre(image(f"{base}img/wear/01-lecteur", 454, 454, t["alt_wear_player"]), "montre--hero"))

    # Recit, petits ecrans : chaque etape porte son telephone et deux calques.
    etapes = [("02-lecteur", "alt_player"), ("03-effets", "alt_effects"), ("04-file", "alt_queue"),
              ("06-playlists", "alt_playlists"), ("07-themes", "alt_themes")]
    calques = [
        pochette(base, "rock", "translate3d(-88%,-70%,-90px) rotateZ(-7deg)")
        + pochette(base, "jazz", "translate3d(92%,82%,70px) rotateZ(6deg)"),
        '<i class="onde"></i><i class="onde"></i>'
        + pochette(base, "goldberg", "translate3d(94%,-92%,60px) rotateZ(8deg)"),
        pochette(base, "tropical", "translate3d(-92%,62%,80px) rotateZ(-6deg)")
        + pochette(base, "lofi", "translate3d(94%,-80%,-70px) rotateZ(7deg)"),
        pochette(base, "espace", "translate3d(-94%,-84%,60px) rotateZ(-8deg)")
        + pochette(base, "whispered", "translate3d(90%,70%,-80px) rotateZ(6deg)"),
        f'<div class="poch poch--ecran" style="--p:translate3d(-74%,-6%,-110px) rotateZ(-9deg)">{amb(1)}</div>'
        f'<div class="poch poch--ecran" style="--p:translate3d(76%,6%,-60px) rotateZ(8deg)">{amb(2)}</div>',
    ]
    for i, (nom, alt) in enumerate(etapes):
        out[f"shot{i}"] = (f'<div class="mini"><div class="mini__rig">{calques[i]}'
                           f'{telephone(ecran(nom, t[alt]), "tel--mini", 3)}</div></div>')

    # Recit, grands ecrans : un seul telephone epingle, cinq decors autour.
    lueurs = "".join(
        f'<img src="{tel}{nom}-flou.webp" width="36" height="64" alt="" loading="lazy" decoding="async"'
        + (' class="is-on"' if i == 0 else "") + ">" for i, (nom, _) in enumerate(etapes))
    ecrans = "".join(ecran(nom, extra=' class="is-on"' if i == 0 else "") for i, (nom, _) in enumerate(etapes))
    courbe = ('<svg class="fondu" viewBox="0 0 600 160" aria-hidden="true">'
              '<path class="fondu__a" pathLength="1" d="M10 30 H230 C320 30 330 130 420 130 H590"/>'
              '<path class="fondu__b" pathLength="1" d="M10 130 H180 C270 130 280 30 370 30 H590"/></svg>')

    def ligne(nom, pose):
        return f'<div class="ligne" style="--p:{pose}">{image(f"{base}img/covers/{nom}", 320, 320, jpg=False)}<i></i></div>'

    mur = [("rock", -190, -150, -150, 24), ("lofi", -225, 0, -80, 28), ("goldberg", -185, 150, -170, 22),
           ("tropical", 190, -160, -150, -24), ("espace", 225, -10, -80, -28), ("jazz", 185, 140, -170, -22)]
    eventail = [(1, -128, -3, -190, 30, -6), (3, -70, 4, -90, 20, -3), (2, 70, 4, -90, -20, 3), (4, 128, -3, -190, -30, 6)]
    out["stage"] = (
        f'<div class="story__flou">{lueurs}</div>'
        '<div class="scene scene--recit"><div class="scene__rig" data-rig><div class="scene__pose">'
        '<div class="decor decor--0">' + courbe
        + pochette(base, "rock", "translate3d(-225%,-110%,-120px) rotateY(24deg) rotateZ(-5deg)")
        + pochette(base, "jazz", "translate3d(190%,100%,90px) rotateY(-22deg) rotateZ(5deg)") + '</div>'
        '<div class="decor decor--1"><i class="orbite orbite--a"><i></i></i><i class="orbite orbite--b"><i></i></i>'
        '<i class="onde"></i><i class="onde"></i><i class="onde"></i></div>'
        '<div class="decor decor--2">'
        + ligne("tropical", "translate3d(58%,-260%,150px) rotateY(-18deg)")
        + ligne("lofi", "translate3d(68%,0%,100px) rotateY(-18deg)")
        + ligne("espace", "translate3d(58%,260%,50px) rotateY(-18deg)") + '</div>'
        '<div class="decor decor--3">'
        + "".join(pochette(base, n, f"translate3d({x}%,{y}%,{z}px) rotateY({r}deg)") for n, x, y, z, r in mur) + '</div>'
        '<div class="decor decor--4">'
        + "".join(telephone(amb(i), "tel--eventail", 2,
                            pose=f"translate3d({x}%,{y}%,{z}px) rotateY({ry}deg) rotateZ({rz}deg)")
                  for i, x, y, z, ry, rz in eventail) + '</div>'
        + telephone(ecrans, "tel--scene", 6, " data-stage")
        + '</div></div></div>')

    out["montres"] = (montre(image(f"{base}img/wear/01-lecteur", 454, 454, t["alt_wear_player"]), "montre--g")
                      + montre(image(f"{base}img/wear/02-bibliotheque", 454, 454, t["alt_wear_library"]), "montre--d"))
    plaques = "".join(f'<i class="tab__tr" style="--z:{i}"></i>' for i in range(1, 5))
    out["tablette"] = (
        f'<div class="tab"><div class="tab__corps">{plaques}<div class="tab__face">'
        f'{image(f"{base}img/tablet/07-themes", 1600, 900, t["alt_tablet"])}</div><i class="tab__reflet"></i></div></div>')
    return out


def videos(base, ui, t, fiche):
    """Facade de la video principale et galerie des autres versions. Aucune
    balise <video> dans la page : elle est creee au clic. Sans script, chaque
    vignette reste un lien direct vers le fichier. Chaque emplacement porte
    ses deux formats ; classes f169 / f916, basculees par la feuille de style."""

    def video(cle, attendu):
        d = fiche[f"{cle}-{ui}"]
        if d["format"] != attendu:
            sys.exit(f"{cle}-{ui} est en {d['format']}, l'emplacement attend du {attendu}.")
        return d

    principale = []
    for cle, fmt in zip(FILM, ("16:9", "9:16")):
        d = video(cle, fmt)
        l, h = (960, 540) if fmt == "16:9" else (540, 960)
        principale.append(
            f'<a class="film__lien f{fmt.replace(":", "")}" href="{base}media/{cle}-{ui}.mp4" data-film data-format="{fmt}">'
            f'{image(f"{base}media/{cle}-{ui}", l, h, "")}'
            f'<span class="film__lecture" aria-hidden="true"><i></i></span>'
            f'<span class="film__duree" aria-hidden="true">{minutes(d["duree_s"])}</span>'
            f'<span class="sr">{html.escape(t["video_play"])}</span></a>')
    cartes = []
    for i, (large, titre_l, haut, titre_h, ton) in enumerate(BOBINES):
        for cle, titre, fmt in ((large, titre_l, "16:9"), (haut, titre_h, "9:16")):
            if f"{cle}-{ui}" not in fiche:
                # Source pas encore rendue (medias.py l'a sautee) : l'emplacement
                # manque dans ce format, rien de casse. Relancer medias.py puis rendre.py.
                print(f"  {cle}-{ui} absente de media/videos.json : emplacement saute en {fmt}", file=sys.stderr)
                continue
            d = video(cle, fmt)
            l, h = (960, 540) if fmt == "16:9" else (540, 960)
            cartes.append(
                f'      <li class="bob bob--{"large" if fmt == "16:9" else "haut"} f{fmt.replace(":", "")}" data-reveal style="--delay:{i * 0.08:.2f}s">'
                f'<a href="{base}media/{cle}-{ui}.mp4" data-bobine data-format="{fmt}">'
                f'<span class="bob__image">{image(f"{base}media/{cle}-{ui}", l, h, "")}'
                f'<i class="bob__lecture" aria-hidden="true"></i></span>'
                f'<span class="bob__ton bob__ton--{ton}">{html.escape(t["tag_" + ton])}</span>'
                # Titre lu par les lecteurs d'ecran seulement : a l'ecran, il devoilerait la DA de la video.
                f'<span class="sr">{html.escape(t[titre])}</span>'
                f'<span class="bob__duree">{minutes(d["duree_s"])}</span></a></li>')
    return "".join(principale), "\n".join(cartes)


def page(code, textes, en, nouveautes, fiche):
    manquantes = [k for k in en if k not in textes]
    if manquantes:
        print(f"  {code} : {len(manquantes)} cle(s) en anglais : {', '.join(manquantes)}", file=sys.stderr)
    t = {k: v.replace("{ambiances}", str(AMBIANCES)) if isinstance(v, str) else v
         for k, v in {**en, **textes}.items()}
    base = "" if code == "en" else "../"
    url = URL if code == "en" else f"{URL}{code}/"
    play = PLAY + HL.get(code, code)
    ui = UI.get(code, "en")

    def lien_langue(c, nom):
        cible = base + ("" if c == "en" else f"{c}/")
        cible = cible or "./"
        courant = ' aria-current="page"' if c == code else ""
        return (f'      <li><a href="{cible}" hreflang="{BALISE_LANG.get(c, c)}" lang="{BALISE_LANG.get(c, c)}" '
                f'data-lang="{c}"{courant}>{html.escape(nom)}</a></li>')

    noms = {c: charger(f"i18n/{c}.json")["name"] for c in LANGUES}
    hreflang = "\n".join(
        f'<link rel="alternate" hreflang="{BALISE_LANG.get(c, c)}" href="{URL if c == "en" else URL + c + "/"}">'
        for c in LANGUES) + f'\n<link rel="alternate" hreflang="x-default" href="{URL}">'

    def facture(classe):
        return "\n".join(
            f'        <li class="{classe}" data-bill-item="{k}"><span>{html.escape(t["b_" + k])}</span>'
            f'<span>{html.escape(t["zero"])}</span></li>' for k in FACTURE)

    blocs = []
    for v in nouveautes["versions"]:
        points = v["points"].get(code) or v["points"]["en"]
        lis = "".join(f"<li>{html.escape(p)}</li>" for p in points)
        blocs.append(
            f'    <article class="release" data-reveal>\n'
            f'      <h3><span>{html.escape(t["news_version"])} {html.escape(v["version"])}</span>'
            f'<time datetime="{v["date"]}">{v["date"]}</time></h3>\n'
            f'      <ul>{lis}</ul>\n    </article>')

    film, bobines = videos(base, ui, t, fiche)
    ruban = "".join(f"<span>{html.escape(t[k])}</span>" for k in ("chip_ads", "chip_account", "chip_sub", "chip_offline"))
    brut = {
        **appareils(base, ui, t), "film": film, "bobines": bobines, "ruban": ruban * 4,
        "video_english": "" if code in ("fr", "en") else f'<p class="film__langue">{html.escape(t["video_english"])}</p>',
        "lang": BALISE_LANG.get(code, code), "base": base, "url": url, "home": "./",
        "og_image": f"{URL}img/og-{OG.get(code, 'en')}.jpg", "play": html.escape(play),
        "ui": ui, "hreflang": hreflang, "bars": barres(),
        "detect": DETECTION if code == "en" else "",
        "presse": "fr" if code == "fr" else "en",  # la page presse n'existe qu'en fr et en
        "languages": "\n".join(lien_langue(c, noms[c]) for c in LANGUES),
        "news": "\n".join(blocs), "bill": facture("bill__item"), "receipt": facture(""),
    }
    modele = (SITE / "_outils" / "modele.html").read_text(encoding="utf-8")

    def remplacer(m):
        cle = m.group(1)
        if cle.startswith("="):
            return brut[cle[1:]]
        return html.escape(t[cle], quote=True)

    sortie = re.sub(r"\{\{([=a-z0-9_]+)\}\}", remplacer, modele)
    cible = SITE / ("index.html" if code == "en" else f"{code}/index.html")
    cible.parent.mkdir(exist_ok=True)
    cible.write_text(sortie, encoding="utf-8", newline="\n")
    print(f"{code} -> {cible.relative_to(SITE).as_posix()}")


def page_404(en):
    """404.html : servie par Pages pour toute adresse inconnue, a n'importe
    quelle profondeur, d'ou les chemins absolus."""
    b = "/omega-player/"
    t = en
    corps = f"""<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 — Omega Player</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#05090B">
<link rel="icon" href="{b}favicon.ico" sizes="any">
<link rel="stylesheet" href="{b}assets/css/site.css">
</head>
<body class="lost">
<main class="lost__main">
  <p class="lost__code" aria-hidden="true">4<span>0</span>4</p>
  <h1 class="h2">{html.escape(t["notfound_title"])}</h1>
  <p>{html.escape(t["notfound_body"])}</p>
  <p><a class="btn" href="{b}">{html.escape(t["notfound_home"])}<span class="btn__arrow" aria-hidden="true"></span></a></p>
</main>
</body>
</html>
"""
    (SITE / "404.html").write_text(corps, encoding="utf-8", newline="\n")
    print("404 -> 404.html")


def main():
    en = charger("i18n/en.json")
    nouveautes = charger("nouveautes.json")
    fiche = charger("media/videos.json")
    for code in LANGUES:
        page(code, charger(f"i18n/{code}.json"), en, nouveautes, fiche)
    page_404(en)


if __name__ == "__main__":
    main()
