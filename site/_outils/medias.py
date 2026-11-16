"""Regenere les images et videos du site a partir des sources du projet.

Usage (depuis n'importe ou) :
    python -I site/_outils/medias.py --source <racine du projet Omega Player>
    python -I site/_outils/medias.py --source <racine> --seulement images
    python -I site/_outils/medias.py --source <racine> --seulement videos

Par defaut, --source vaut le dossier deux niveaux au-dessus de site/
(omega-player-release/ est une copie de travail rangee dans le projet).

Besoins : Pillow (avec WebP et AVIF), ffmpeg et ffprobe dans le PATH.
Le script n'ecrit que dans site/img, site/media et site/favicon.ico, et ne
supprime que les fichiers derives qu'une version precedente de ce meme script
y avait ecrits (liste PERIMES).

Ce que montre le site
---------------------
Tout vient du catalogue de demonstration des videos promo, pas de celui de la
galerie Play : douze morceaux et leurs pochettes publies sous CC0 1.0 sur Free
Music Archive (tools/captures/CREDITS-CC0.md), plus « Je suis un saumon », le
titre livre avec l'application. Les tableaux du Met de la galerie Play ne
servent plus, et la capture tablette est elle aussi prise sur le catalogue CC0 (accueil).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = Path(__file__).resolve().parent
SITE = ICI.parent

# --- Images ---------------------------------------------------------------
# Captures fixes prises pour les videos (theme Rose, catalogue CC0), en
# francais et en anglais. 1080x1921 : la derniere ligne est rognee.
TELEPHONE = {"fr": "tools/captures/brut/video/captures-fr", "en": "tools/captures/brut/video/captures-en"}
ECRANS = ["01-accueil", "02-lecteur", "03-effets", "04-file", "05-bibliotheque", "06-playlists", "07-themes"]
# Quatre ambiances filmees (Lava Lamp, Matrix, Aurora, Light) : une image de
# chaque rush, a l'instant donne.
AMBIANCES = {"fr": "tools/captures/brut/video/fr", "en": "tools/captures/brut/video/en"}
AMBIANCE_T = 3.0
MONTRE = ["tools/captures/brut/video/montre/01-lecteur.png", "tools/captures/brut/video/montre/02-bibliotheque.png"]
# Capture tablette 2026-11-16 : accueil sur le catalogue CC0 (Medium_Tablet,
# paysage, theme Turquoise par defaut). L'ecran des themes ne convient pas :
# il porte les badges et la section PREMIUM par construction. L'ancienne
# capture (Met + PREMIUM) est gardee a cote : 07-themes-met-premium.png.
# Le fichier du site garde son nom img/tablet/07-themes (reference par rendre.py).
TABLETTE = "tools/captures/brut/tablette/01-accueil-cc0.png"
# Pochettes CC0 : extraites des MP3 du catalogue (image embarquee par
# catalogue_cc0.py, celle de la page de l'album sur Free Music Archive).
CATALOGUE = "tools/captures/brut/cc0"
POCHETTES = {
    "tropical": "03 - Shaloza - Mirihi.mp3",
    "jazz": "05 - Art Flower - Another Life.mp3",
    "rock": "06 - Art Flower - Blue Marillion.mp3",
    "espace": "07 - Art Flower - Beyond the Clouds.mp3",
    "lofi": "08 - HoliznaCC0 - Morning Coffee.mp3",
    "goldberg": "10 - Kimiko Ishizaka - Aria.mp3",
    "whispered": "12 - Ondrosik - Whispered.mp3",
}
ICONE = "omega-player-release/icon.png"

# --- Videos ---------------------------------------------------------------
# cle -> (version, suffixe de la source, instant de l'affiche en secondes).
# Les sources sont les rendus complets ; le script encode lui-meme la version
# web (PROFIL). Exception : V10 et V11 n'ont qu'une source permise, « -final-leger »
# (les « -musique » portent d'anciens faux sous-titres entre crochets, retires
# a la demande du proprietaire) ; le script refuse tout autre fichier V10/V11.
MOTION = "tools/captures/brut/video/sorties/motion"
# Dossier du rendu « Diaporama » sous MOTION : a changer quand le nouveau
# rendu (avec bruitages) arrive, puis relancer medias.py et rendre.py.
DIAPORAMA = "regeneration-20261116-110917"
VIDEOS = {
    "fiche": ("V0", "musique", 9.0),         # 16:9, la video de la fiche Play
    "addition": ("V1", "musique", 5.6),      # 9:16, « L'addition »
    "ambiances": ("V3", "musique", 4.6),     # 9:16, « 27 ambiances »
    "film": ("V11", "final-leger", 20.0),    # 16:9, bande-annonce de blockbuster
    "teleachat": ("V9", "musique", 3.2),     # 16:9, tele-achat VHS
    "documentaire": ("V12", "musique", 9.0), # 9:16, documentaire animalier
    # Le site montre les 9:16 sur mobile et les 16:9 sur ordinateur : chaque
    # emplacement a son jumeau dans l'autre format (rendre.py, FILM et BOBINES).
    "fou": ("V5", "musique", 2.6),                     # 16:9, la video classique au rythme fou
    "film-9x16": ("V10", "final-leger", 20.0),         # 9:16, jumeau de « film »
    "teleachat-9x16": ("V8", "musique", 8.3),          # 9:16, jumeau de « teleachat »
    "documentaire-16x9": ("V13", "musique", 9.0),      # 16:9, jumeau de « documentaire »
    "ytp-16x9": ("V15", "musique", 1.5),               # 16:9, YouTube Poop
    "ytp-9x16": ("V14", "musique", 1.5),               # 9:16, YouTube Poop
    "fou-9x16": ("V4", "musique", 2.6),                # 9:16, jumeau de « fou »
    "blanc": ("V2", "musique", 3.0),                   # 9:16, « Plus jamais de blanc »
    # Jumeaux 16:9 de V2 et V3, rendus a part (V2H, V3H). Une source absente
    # ou illisible (rendu en cours) est sautee : l'emplacement n'apparait pas
    # dans ce format tant que medias.py puis rendre.py n'ont pas ete relances.
    "blanc-16x9": ("V2H", "musique", 3.0),             # 16:9, jumeau de « blanc »
    "ambiances-16x9": ("V3H", "musique", 4.6),         # 16:9, jumeau de « ambiances »
    # « Diaporama » (V16 9:16 / V17 16:9) : rendu dans un sous-dossier de MOTION,
    # nomme par DIAPORAMA juste au-dessus de VIDEOS (chaine vide = racine de MOTION).
    "diaporama-9x16": (f"{DIAPORAMA}/V16".lstrip("/"), "final-leger", 15.0),
    "diaporama-16x9": (f"{DIAPORAMA}/V17".lstrip("/"), "final-leger", 15.0),
}
LANGUES_VIDEO = ["fr", "en"]
COTE = 720            # petit cote de la version web
PROFIL = ["-c:v", "libx264", "-preset", "slow", "-crf", "27", "-maxrate", "1800k", "-bufsize", "3600k",
          "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "112k", "-movflags", "+faststart"]
BUDGET_MO = 8.0       # au-dela, le script s'arrete : une video du site reste legere

# Fichiers derives d'anciennes versions de ce script, a retirer.
PERIMES = ["media/omega-fr.mp4", "media/omega-en.mp4"] + [
    f"media/poster-{l}.{e}" for l in ("fr", "en") for e in ("avif", "webp", "jpg")] + [
    f"img/tablet/01-accueil.{e}" for e in ("avif", "webp", "jpg")] + [
    f"img/wear/{n}.png" for n in ("01-lecteur", "02-bibliotheque")]


def enregistrer(im, base: Path, largeur=None, jpg=True, qualite=(55, 80, 82)):
    base.parent.mkdir(parents=True, exist_ok=True)
    if largeur and im.width != largeur:
        im = im.resize((largeur, round(im.height * largeur / im.width)), Image.LANCZOS)
    rgb = im.convert("RGB")
    rgb.save(base.with_suffix(".avif"), quality=qualite[0], speed=4)
    rgb.save(base.with_suffix(".webp"), quality=qualite[1], method=6)
    if jpg:
        rgb.save(base.with_suffix(".jpg"), quality=qualite[2], optimize=True, progressive=True)


def flou(im, base: Path):
    """Lueur d'ambiance : l'ecran lui-meme, tres flou et tout petit. La page
    l'agrandit, ce qui evite tout filtre de flou calcule par le navigateur."""
    petit = im.convert("RGB").resize((36, 64), Image.LANCZOS).filter(ImageFilter.GaussianBlur(5))
    petit.save(base.with_suffix(".webp"), quality=70, method=6)


def image_video(source: Path, t: float, largeur=None) -> Image.Image:
    filtre = ["-vf", f"scale={largeur}:-2"] if largeur else []
    brut = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(source), "-frames:v", "1",
                           *filtre, "-f", "image2pipe", "-c:v", "png", "-"], check=True, capture_output=True).stdout
    import io
    return Image.open(io.BytesIO(brut)).convert("RGB")


def police(nom, taille):
    return ImageFont.truetype(str(SITE / "fonts" / nom), taille)


def image_partage(src: Path, langue: str, titre: str, sous_titre: str):
    """Image Open Graph 1200x630 : fond de la marque, icone, titre, ecran."""
    W, H = 1200, 630
    fond = Image.new("RGB", (W, H), "#05090B")
    halo = Image.new("RGB", (W, H), "#05090B")
    d = ImageDraw.Draw(halo)
    d.ellipse((620, -160, 1320, 540), fill="#5a1f4a")
    d.ellipse((-200, 380, 500, 900), fill="#0b4f4a")
    fond = Image.blend(fond, halo.filter(ImageFilter.GaussianBlur(140)), 0.9)
    ecran = Image.open(src / TELEPHONE[langue] / "02-lecteur.png").convert("RGB").crop((0, 0, 1080, 1920))
    ecran = ecran.resize((300, 533), Image.LANCZOS)
    cadre = Image.new("RGBA", (324, 557), (0, 0, 0, 0))
    ImageDraw.Draw(cadre).rounded_rectangle((0, 0, 323, 556), 38, fill="#16252a")
    masque = Image.new("L", (300, 533), 0)
    ImageDraw.Draw(masque).rounded_rectangle((0, 0, 299, 532), 28, fill=255)
    cadre.paste(ecran, (12, 12), masque)
    cadre = cadre.rotate(-8, expand=True, resample=Image.BICUBIC)
    fond.paste(cadre, (790, 40), cadre)
    icone = Image.open(src / ICONE).convert("RGBA").resize((96, 96), Image.LANCZOS)
    fond.paste(icone, (72, 72), icone)
    d = ImageDraw.Draw(fond)
    d.text((72, 210), "Omega Player", font=police("archivo-latin-800-normal.woff2", 84), fill="#eef6f5")
    y = 320
    for ligne in titre.split("\n"):
        d.text((72, y), ligne, font=police("ibm-plex-sans-latin-600-normal.woff2", 40), fill="#00e5cc")
        y += 54
    d.text((72, 520), sous_titre, font=police("ibm-plex-sans-latin-400-normal.woff2", 28), fill="#a9c2c0")
    fond.save(SITE / "img" / f"og-{langue}.jpg", quality=86, optimize=True)


def images(src: Path):
    for langue, dossier in TELEPHONE.items():
        for nom in ECRANS:
            im = Image.open(src / dossier / f"{nom}.png").convert("RGB").crop((0, 0, 1080, 1920))
            enregistrer(im, SITE / "img" / "phone" / langue / nom, 720)
            flou(im, SITE / "img" / "phone" / langue / f"{nom}-flou")
        for i in range(1, 5):
            im = image_video(src / AMBIANCES[langue] / f"06-ambiance-{i}.mp4", AMBIANCE_T)
            enregistrer(im, SITE / "img" / "phone" / langue / f"ambiance-{i}", 540, jpg=False)
            flou(im, SITE / "img" / "phone" / langue / f"ambiance-{i}-flou")

    for cle, fichier in POCHETTES.items():
        brut = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src / CATALOGUE / fichier), "-an",
                               "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"],
                              check=True, capture_output=True).stdout
        import io
        im = Image.open(io.BytesIO(brut)).convert("RGB")
        cote = min(im.size)
        im = im.crop(((im.width - cote) // 2, (im.height - cote) // 2, (im.width + cote) // 2, (im.height + cote) // 2))
        enregistrer(im, SITE / "img" / "covers" / cle, 320, jpg=False, qualite=(50, 76, 80))

    enregistrer(Image.open(src / TABLETTE), SITE / "img" / "tablet" / "07-themes", 1600)
    for chemin in MONTRE:
        enregistrer(Image.open(src / chemin), SITE / "img" / "wear" / Path(chemin).stem, qualite=(60, 84, 86))

    icone = Image.open(src / ICONE).convert("RGBA")
    for taille, nom in ((180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png"), (32, "favicon-32.png")):
        icone.resize((taille, taille), Image.LANCZOS).save(SITE / "img" / nom, optimize=True)
    icone.save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    icone.resize((96, 96), Image.LANCZOS).save(SITE / "img" / "icon-96.webp", quality=90)

    image_partage(src, "en", "Free offline music player\nfor Android", "No ads · No account · Nothing leaves your phone")
    image_partage(src, "fr", "Lecteur de musique hors ligne\ngratuit pour Android", "Sans pub · Sans compte · Rien ne sort du téléphone")


def sonde(fichier: Path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(fichier)],
                       check=True, capture_output=True, text=True)
    j = json.loads(r.stdout)
    return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])


def videos(src: Path):
    media = SITE / "media"
    media.mkdir(exist_ok=True)
    fiche = {}
    for cle, (version, suffixe, t_affiche) in VIDEOS.items():
        for langue in LANGUES_VIDEO:
            nom = f"{version}-{langue}-{suffixe}.mp4"
            if version in ("V10", "V11") and suffixe != "final-leger":
                sys.exit(f"Refuse : {nom}. Pour V10/V11, seule la source « -final-leger » est permise.")
            source = src / MOTION / nom
            try:
                l, h, duree = sonde(source)
            except subprocess.CalledProcessError:
                print(f"saute (source absente ou illisible) : {nom}")
                continue
            paysage = l > h
            echelle = f"scale=-2:{COTE}" if paysage else f"scale={COTE}:-2"
            cible = media / f"{cle}-{langue}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-vf", echelle, *PROFIL, str(cible)], check=True)
            poids = cible.stat().st_size / 1e6
            if poids > BUDGET_MO:
                sys.exit(f"{cible.name} pese {poids:.1f} Mo, au-dessus du budget de {BUDGET_MO} Mo.")
            affiche = image_video(cible, t_affiche)
            enregistrer(affiche, media / f"{cle}-{langue}", 960 if paysage else 540, qualite=(50, 76, 80))
            fiche[f"{cle}-{langue}"] = {"source": nom, "format": "16:9" if paysage else "9:16",
                                        "duree_s": round(duree, 1), "poids_mo": round(poids, 2)}
            print(f"{cible.name}  <- {nom}  {duree:.1f} s  {poids:.2f} Mo")
    (media / "videos.json").write_text(json.dumps(fiche, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default=str(SITE.parents[1]))
    p.add_argument("--seulement", choices=["images", "videos"])
    a = p.parse_args()
    src = Path(a.source)
    if a.seulement != "videos":
        images(src)
    if a.seulement != "images":
        videos(src)
    for relatif in PERIMES:
        f = SITE / relatif
        if f.exists():
            f.unlink()
            print(f"retire (derive perime) : {relatif}")


if __name__ == "__main__":
    main()
