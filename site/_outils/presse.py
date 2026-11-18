"""Archive du kit presse : site/presse/omega-player-kit-presse.zip.

    py -I _outils/presse.py --source "<racine du depot Omega Player>"     (depuis site/)

Reprend tel quel ce qui est deja publie sur la fiche Play (fastlane) et l'icone : rien n'est
redessine ici. A relancer quand la galerie Play change.
"""
import argparse, zipfile
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
SORTIE = SITE / "presse" / "omega-player-kit-presse.zip"

A_LIRE = """Omega Player - press kit / kit presse

EN
Omega Player is a free offline music player for Android: it plays the files people already own
(MP3, FLAC, OGG, M4A), with no ads, no account and no server. Crossfade, loudness levelling,
a tempo-aware queue, a 10-band equalizer, binaural 3D audio for headphones, Android Auto and a
Wear OS companion. Android 10 or later. Released on Google Play on 18 November 2026.
Publisher: Mistano (solo developer).
Google Play: https://play.google.com/store/apps/details?id=com.mistano.omegaplayer
Press page: https://mistano.github.io/omega-player/presse/

FR
Omega Player est un lecteur de musique hors ligne et gratuit pour Android : il lit les fichiers
qu'on possede deja (MP3, FLAC, OGG, M4A), sans publicite, sans compte et sans serveur. Fondu
enchaine, volume harmonise, file qui suit le tempo, egaliseur 10 bandes, audio binaural 3D au
casque, Android Auto et une appli Wear OS. Android 10 ou plus. Sorti sur Google Play le
18 novembre 2026. Editeur : Mistano (developpeur seul).

Contents / Contenu
  icone/            app icon 512 px
  banniere/         Play feature graphic (fr, en)
  telephone-fr/, telephone-en/   phone screenshots 1080x1920
  tablette-fr/      tablet screenshots 2560x1440
  montre/           Wear OS screenshots 454x454

Free to use to illustrate an article about Omega Player. / Libre d'usage pour illustrer un
article sur Omega Player.
Album covers shown: public-domain paintings (The Metropolitan Museum of Art, CC0).
Demo tracks were synthesised for the screenshots. / Pochettes : tableaux du domaine public
(Metropolitan Museum of Art, CC0) ; morceaux de demonstration synthetises.
Android, Google Play and Wear OS are trademarks of Google LLC.
"""


def contenu(source):
    meta = source / "fastlane" / "metadata" / "android"
    yield SITE.parent / "icon.png", "icone/omega-player-icone-512.png"
    for lang in ("fr-FR", "en-US"):
        court = lang[:2]
        img = meta / lang / "images"
        yield img / "featureGraphic.png", f"banniere/omega-player-banniere-{court}.png"
        for f in sorted((img / "phoneScreenshots").glob("*.png")):
            yield f, f"telephone-{court}/{f.name}"
    for f in sorted((meta / "fr-FR" / "images" / "tenInchScreenshots").glob("*.png")):
        yield f, f"tablette-fr/{f.name}"
    for f in sorted((meta / "fr-FR" / "images" / "wearScreenshots").glob("*.png")):
        yield f, f"montre/{f.name}"


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--source", required=True, help="racine du depot Omega Player")
    src = Path(a.parse_args().source).resolve()
    fichiers = list(contenu(src))
    manquants = [str(f) for f, _ in fichiers if not f.is_file()]
    assert not manquants, "absents : " + ", ".join(manquants)
    SORTIE.parent.mkdir(exist_ok=True)
    # PNG deja compresses : stockes tels quels. Date fixe pour une archive identique a chaque run.
    with zipfile.ZipFile(SORTIE, "w", zipfile.ZIP_STORED) as z:
        info = zipfile.ZipInfo("omega-player-kit-presse/A-LIRE.txt", (2026, 11, 18, 0, 0, 0))
        z.writestr(info, A_LIRE.encode("utf-8"), zipfile.ZIP_DEFLATED)
        for f, nom in fichiers:
            info = zipfile.ZipInfo("omega-player-kit-presse/" + nom, (2026, 11, 18, 0, 0, 0))
            z.writestr(info, f.read_bytes())
    print(f"{len(fichiers) + 1} fichiers, {SORTIE.stat().st_size / 1e6:.1f} Mo -> {SORTIE}")


if __name__ == "__main__":
    main()
