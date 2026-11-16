# Site vitrine Omega Player

Site statique servi par GitHub Pages à `https://mistano.github.io/omega-player/`.
Pas de bibliothèque, pas de CDN, pas d'analytics, pas de cookie, polices embarquées (OFL).

## Structure

| Chemin | Rôle |
|---|---|
| `index.html` | Page anglaise (langue par défaut, contient la détection de langue) |
| `<lang>/index.html` | Pages fr, de, es, it, pt, ru, ar, ja, ko, zh — **générées, ne pas éditer** |
| `404.html` | Page d'erreur (chemins absolus `/omega-player/`, ne s'affiche stylée que sur Pages) |
| `sdk/index.html` | Page SDK des extensions (anglais, écrite à la main) |
| `i18n/<lang>.json` | Tous les textes, une seule source par langue |
| `nouveautes.json` | Nouveautés par version |
| `_outils/modele.html` | Gabarit des pages (`{{cle}}` échappé, `{{=cle}}` brut) |
| `_outils/rendre.py` | Génère les pages depuis le gabarit + JSON |
| `_outils/medias.py` | Régénère images, icônes, images OG, vidéos et affiches |
| `assets/css/site.css`, `assets/js/site.js` | Style et animations |
| `img/`, `media/`, `fonts/` | Captures, vidéos, polices woff2 + licences |
| `.nojekyll` | Désactive Jekyll sur Pages |

## Mettre à jour

Après toute modification de texte, de gabarit ou de nouveautés, depuis `site/` :

```bash
python -I _outils/rendre.py
```

- **Nouveautés** : ajouter une entrée en tête de `versions` dans `nouveautes.json`
  (`version`, `date` AAAA-MM-JJ, `points` par langue). Une langue absente retombe sur l'anglais.
- **Textes / langue** : éditer `i18n/<lang>.json`. Une clé manquante retombe sur l'anglais
  (le script le signale). Nouvelle langue : copier `en.json`, traduire, ajouter le code à
  `LANGUES` dans `_outils/rendre.py`.
- **Vidéos / captures** : `python -I _outils/medias.py --source <racine du projet>` relit les
  captures brutes (`tools/captures/brut/`) et les vidéos promo du dépôt principal, et réécrit
  `img/` et `media/` (+ `media/videos.json`, lu par `rendre.py`). Relancer `rendre.py` ensuite.

## Vidéos retenues

Table `VIDEOS` de `_outils/medias.py` (fichiers), `FILM` et `BOBINES` de `_outils/rendre.py` (place sur
la page). Chaque vidéo existe en `-fr` et `-en` ; la page française lit `-fr`, toutes les autres
langues lisent `-en` (une ligne le dit sous le film).

**Format selon l'écran** : sur ordinateur (900 px et plus) uniquement des 16:9, sur mobile
(moins de 900 px, le seuil du bandeau de l'addition) uniquement des 9:16. Chaque emplacement porte ses
deux liens, la feuille de style cache l'autre (`f169` / `f916`) : son affiche `lazy` n'est pas demandée,
et sans JS la vignette visible mène au bon fichier.

| Emplacement | 16:9 (ordinateur) | 9:16 (mobile) | Ton |
|---|---|---|---|
| film principal | `fiche` = V0-musique | `addition` = V1-musique | sage |
| rail 1 « Plus jamais de blanc » | `blanc-16x9` = V2H-musique | `blanc` = V2-musique | sage |
| rail 2 « 27 ambiances » | `ambiances-16x9` = V3H-musique | `ambiances` = V3-musique | sage |
| rail 3 « rythme fou » | `fou` = V5-musique | `fou-9x16` = V4-musique | sage |
| rail 4 bande-annonce | `film` = V11-final-leger | `film-9x16` = V10-final-leger | déglinguée |
| rail 5 télé-achat | `teleachat` = V9-musique | `teleachat-9x16` = V8-musique | déglinguée |
| rail 6 documentaire | `documentaire-16x9` = V13-musique | `documentaire` = V12-musique | déglinguée |
| rail 7 YouTube Poop | `ytp-16x9` = V15-musique | `ytp-9x16` = V14-musique | déglinguée |
| rail 8 diaporama | `diaporama-16x9` = V17-final-leger | `diaporama-9x16` = V16-final-leger | déglinguée |

- Une source absente ou illisible (rendu en cours) est **sautée** par `medias.py`, et `rendre.py`
  saute l'emplacement dans ce format : ni plantage ni vignette cassée. Une fois le rendu fini, depuis
  la racine du dépôt Omega Player :
  `python -I omega-player-release/site/_outils/medias.py --source . --seulement videos`
  puis, depuis `site/` : `python -I _outils/rendre.py`.
- Le diaporama (V16/V17) est lu dans le sous-dossier `DIAPORAMA` de `sorties/motion/` (constante de
  `medias.py`, chaîne vide = racine) : la changer quand le nouveau rendu arrive.
- Poids : `BUDGET_MO` (8 Mo) par fichier ; le visiteur ne télécharge que ce qu'il lance.
- **Ne jamais prendre `V10-*-musique*` ni `V11-*-musique*`** : pour V10 et V11, seule la
  variante `-final-leger` est publiable (garde-fou dans `medias.py`).
- Avant d'ajouter une vidéo, regarder le bas de l'image sur toute la durée : aucun texte entre
  crochets (repères de montage) ne doit rester.
- Aucune balise `<video>` dans le HTML : la vignette est un lien vers le `.mp4`, le script la
  remplace par un lecteur au clic (film en place, rail dans un `<dialog>`). Rien ne se charge
  ni ne joue avant, une seule lecture à la fois, pause quand le lecteur sort de l'écran.

## Appareils en volume et mouvement

- Téléphones, montres, tablette et pochettes sont des volumes **CSS** (`transform-style:
  preserve-3d`, plaques empilées, dos, reflet) générés par `rendre.py` (`telephone()`,
  `montre()`, décors du récit). Aucune bibliothèque 3D.
  Sur la chaîne `preserve-3d`, pas d'`opacity`, `filter`, `overflow` ni `mask` : ils aplatissent la scène.
- Ce qui suit le défilement est en CSS (`animation-timeline: view()` sous `@supports`, repli
  statique ailleurs). Le script ne fait que : étape active du récit (IntersectionObserver),
  tour du téléphone avec changement d'écran à mi-course (WAAPI), inclinaison au pointeur
  (souris seulement), cycle d'écrans du héros, vidéos.
- Les boucles (flottement, orbites, ruban) sont mises en pause hors écran (classe `.hors`).
- `prefers-reduced-motion` : tout est posé, sans boucle ni tour ; le contenu est identique.
- Sans JavaScript, la page reste lisible et les vignettes ouvrent les fichiers vidéo.

## Pochettes et crédits

- Tout ce qui est montré (pochettes flottantes, ruban, écrans de téléphone et de montre) vient
  du catalogue de démonstration **CC0 1.0** (Free Music Archive) des vidéos promo ; détail dans
  `tools/captures/CREDITS-CC0.md` du dépôt principal, résumé dans le pied de page (`footer_credits`).
  Musique des vidéos : voir `tools/captures/CREDITS-MUSIQUE.md`.
- **Exception : la capture tablette** (`img/tablet/`) vient encore de la galerie Play
  (tableaux du Met, domaine public) : il n'existe pas de capture tablette sur le catalogue CC0.
  Pour la refaire : préparer un AVD tablette avec `tools/captures/catalogue_cc0.py`, lancer
  `tools/captures/captures.py` sur ce profil, puis pointer `TABLETTE` de `medias.py` sur le
  nouveau dossier brut. Non fait ici (l'émulateur en service porte un état de démonstration).

## Vérifier

Servir depuis le dossier parent de `site/`, puis contrôler au minimum : 360 px sans défilement
horizontal dans les 11 langues (l'allemand et le russe sont les plus longs), arabe en RTL,
passe `prefers-reduced-motion`, console vide, aucune requête hors du site ni `.mp4` avant clic.
Premier chargement mesuré (fr, sans défiler) : environ 0,5 Mo, 30 requêtes.

## Publication (à faire par le propriétaire)

Rien n'a été commité ni publié.

1. Relire le site en local : `python -I -m http.server 8000` depuis le dossier parent de `site/`,
   puis ouvrir `http://127.0.0.1:8000/site/`.
2. Choisir la source Pages : soit publier le contenu de `site/` à la racine d'une branche
   `gh-pages`, soit utiliser un workflow GitHub Actions « Deploy to Pages » avec `path: site`.
   (Le mode « branche + dossier » de Pages n'accepte que `/` ou `/docs`.)
3. Commiter, pousser, puis dans *Settings → Pages* activer la source choisie.
4. Vérifier `https://mistano.github.io/omega-player/`, une page de langue, `sdk/` et une URL inexistante (404).
