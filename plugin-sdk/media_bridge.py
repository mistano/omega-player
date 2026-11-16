"""
media_bridge.py — pont Chaquopy bundlé dans l'APK.
Aucune logique média. Délègue aux extensions chargées dynamiquement.

Plusieurs extensions peuvent être chargées en même temps, chacune sous son propre
nom de module (`ext_<id>`). Parmi elles :
  - une seule est la *source de recherche* (`definir_source`) : c'est elle que
    search / stream_info / related / playlist_meta / fetch_audio / fetch_playlist
    interrogent quand l'appelant ne précise pas `ext=` ;
  - une seule fait la *reconnaissance musicale* (`definir_reconnaissance`) ; à
    défaut, la source si elle sait reconnaître.

Avant d'exécuter le code d'une extension, le pont lui injecte :
  - `extension_id` : son identifiant ;
  - `data_dir()` : crée et renvoie `<dossier>/data`, seul endroit où elle doit
    écrire (conservé au réimport, effacé avec elle) ;
  - `reglage(cle, defaut=None)` : lit `data/reglages.json` à chaque appel.

Une extension peut décrire des pages (`pages()`) que l'app dessine en composants
natifs ; `action()` n'appelle que les fonctions que ces pages déclarent sur un
bouton.

Limite : toutes les extensions partagent un seul interpréteur. Une bibliothèque
embarquée en deux versions par deux extensions n'est chargée qu'une fois, et deux
modules internes de même nom se masquent.

Aucune exception ne sort du pont : une erreur devient
{"error": "extension_error", "message": "<Type>: <message>"}, sans trace complète.
Les erreurs de pages() et action() sont des codes seuls (action_refusee,
pages_invalides, valeur_invalide...) : le texte se compose côté Java, traduit.
JSON strict partout : NaN et infini sont refusés (_dumps).
"""

import sys
import os
import json
import shutil
import importlib.util

# Pas de .pyc écrits à côté du code : __pycache__ est hors de l'empreinte, un .pyc
# déposé là serait exécuté sans avoir été vérifié. Voir aussi _purger_pycache().
sys.dont_write_bytecode = True

_PLUGIN_FILE = "media_plugin.py"
_PREFIXE_MODULE = "ext_"
# Une extension qui sait chercher doit aussi savoir faire ceci.
_REQUISES_SOURCE = ("stream_info", "fetch_audio", "playlist_meta")

_extensions = {}      # id -> module chargé
_dossiers = {}        # id -> dossier de l'extension
_erreurs = {}         # id -> "<Type>: <message>" si le chargement a échoué
_source = None        # id de la source de recherche
_reconnaissance = None  # id de l'extension de reconnaissance


class NonRepresentableEnJson(ValueError):
    """Une valeur renvoyée par l'extension que JSON ne sait pas écrire (NaN, infini)."""


def _dumps(obj):
    """json.dumps strict : NaN et infini refusés, l'app ne lit que du JSON standard."""
    try:
        return json.dumps(obj, allow_nan=False)
    except ValueError as e:
        if "Out of range float" in str(e):
            raise NonRepresentableEnJson("NaN or Infinity is not valid JSON") from None
        raise


def _decrire(exc):
    """Une ligne « Type: message » — jamais de trace complète vers l'interface."""
    return "%s: %s" % (type(exc).__name__, exc)


def _erreur_extension(message):
    return _dumps({"error": "extension_error", "message": message})


def _ok(**extra):
    d = {"ok": True}
    d.update(extra)
    return _dumps(d)


# ── Gestion des extensions ────────────────────────────────────

def _lire_reglages(dossier):
    """Contenu de `<dossier>/data/reglages.json` (écrit par l'app), {} si absent ou illisible."""
    try:
        with open(os.path.join(dossier, "data", "reglages.json"), "r", encoding="utf-8") as f:
            valeurs = json.load(f)
    except (OSError, ValueError):
        return {}
    return valeurs if isinstance(valeurs, dict) else {}


def _injecter(module, ext_id, dossier):
    """Ce que le pont offre à l'extension, posé avant l'exécution de son code."""
    data = os.path.join(dossier, "data")

    def data_dir():
        os.makedirs(data, exist_ok=True)
        return data

    def reglage(cle, defaut=None):
        return _lire_reglages(dossier).get(cle, defaut)

    module.extension_id = ext_id
    module.data_dir = data_dir
    module.reglage = reglage


def _capacites(module):
    return {
        "source": callable(getattr(module, "search", None)),
        "recognize": callable(getattr(module, "recognize", None)),
        "pages": callable(getattr(module, "pages", None)),
    }


def _purger_pycache(dossier):
    """Efface les __pycache__ du code (hors data/), sans suivre aucun lien.

    Ils sont exclus de l'empreinte : Python les chargerait à la place des .py
    vérifiés. data/ n'est pas couvert par l'empreinte, rien à y protéger.
    """
    for racine, dirs, _fichiers in os.walk(dossier, followlinks=False):
        if racine == dossier and "data" in dirs:
            dirs.remove("data")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
            cible = os.path.join(racine, "__pycache__")
            try:
                if os.path.islink(cible):
                    os.unlink(cible)
                else:
                    shutil.rmtree(cible)
            except OSError:
                pass


def _sous(chemin, dossier):
    try:
        chemin = os.path.realpath(chemin)
        dossier = os.path.realpath(dossier)
    except (OSError, ValueError):
        return False
    return chemin.startswith(dossier + os.sep)


def charger(ext_id, dossier):
    """Charge (ou recharge) l'extension `ext_id` depuis `dossier`.

    Renvoie {"ok": true, "capacites": {...}} ou une erreur extension_error, qui est
    aussi mémorisée pour capacites() et les appels suivants.
    """
    global _source, _reconnaissance
    ext_id = str(ext_id)
    dossier = str(dossier)
    # Un rechargement garde les rôles de l'extension, s'il réussit.
    etait_source = _source == ext_id
    etait_reconnaissance = _reconnaissance == ext_id
    decharger(ext_id)
    _purger_pycache(dossier)
    _dossiers[ext_id] = dossier
    nom = _PREFIXE_MODULE + ext_id
    chemin = os.path.join(dossier, _PLUGIN_FILE)
    try:
        spec = importlib.util.spec_from_file_location(nom, chemin)
        if spec is None or spec.loader is None:
            raise ImportError("%s is unreadable" % _PLUGIN_FILE)
        module = importlib.util.module_from_spec(spec)
        _injecter(module, ext_id, dossier)
        # Le dossier sur le chemin : l'extension importe ses propres modules.
        if dossier not in sys.path:
            sys.path.insert(0, dossier)
        sys.modules[nom] = module
        spec.loader.exec_module(module)
        caps = _capacites(module)
        if caps["source"]:
            manquantes = [f for f in _REQUISES_SOURCE
                          if not callable(getattr(module, f, None))]
            if manquantes:
                raise AttributeError("missing function: " + ", ".join(manquantes))
    except BaseException as e:  # SyntaxError, SystemExit à l'import... rien ne sort
        sys.modules.pop(nom, None)
        _erreurs[ext_id] = _decrire(e)
        return _erreur_extension(_erreurs[ext_id])
    _extensions[ext_id] = module
    _erreurs.pop(ext_id, None)
    if etait_source and caps["source"]:
        _source = ext_id
    if etait_reconnaissance and caps["recognize"]:
        _reconnaissance = ext_id
    return _ok(capacites=caps)


def decharger(ext_id):
    """Oublie l'extension : module, chemin, erreur, et ses rôles de source / reconnaissance."""
    global _source, _reconnaissance
    ext_id = str(ext_id)
    _extensions.pop(ext_id, None)
    _erreurs.pop(ext_id, None)
    sys.modules.pop(_PREFIXE_MODULE + ext_id, None)
    dossier = _dossiers.pop(ext_id, None)
    if dossier is not None:
        # Ses modules internes aussi : sinon un rechargement réutiliserait l'ancien code.
        for nom, module in list(sys.modules.items()):
            fichier = getattr(module, "__file__", None)
            if isinstance(fichier, str) and _sous(fichier, dossier):
                sys.modules.pop(nom, None)
        if dossier not in _dossiers.values():
            while dossier in sys.path:
                sys.path.remove(dossier)
    if _source == ext_id:
        _source = None
    if _reconnaissance == ext_id:
        _reconnaissance = None
    return _ok()


def definir_source(ext_id):
    """Choisit la source de recherche. `None` ou "" : plus de source."""
    global _source
    if not ext_id:
        _source = None
        return _ok()
    ext_id = str(ext_id)
    module = _extensions.get(ext_id)
    if module is None:
        # Une source dont le chargement a échoué reste désignée : la recherche
        # affiche alors son erreur au lieu de « aucune source ».
        if ext_id in _erreurs:
            _source = ext_id
        return _absente(ext_id)
    if not callable(getattr(module, "search", None)):
        return _dumps({"error": "unsupported",
                           "message": "This extension cannot search."})
    _source = ext_id
    return _ok()


def definir_reconnaissance(ext_id):
    """Choisit l'extension de reconnaissance. `None` ou "" : retour à la source."""
    global _reconnaissance
    if not ext_id:
        _reconnaissance = None
        return _ok()
    ext_id = str(ext_id)
    module = _extensions.get(ext_id)
    if module is None:
        return _absente(ext_id)
    if not callable(getattr(module, "recognize", None)):
        return _dumps({"error": "unsupported",
                           "message": "This extension cannot recognize music."})
    _reconnaissance = ext_id
    return _ok()


def capacites(ext_id):
    """Ce que l'extension définit réellement, ou l'erreur de son chargement."""
    ext_id = str(ext_id)
    module = _extensions.get(ext_id)
    if module is None:
        d = {"chargee": False, "source": False, "recognize": False, "pages": False}
        if ext_id in _erreurs:
            d["error"] = _erreurs[ext_id]
        return _dumps(d)
    d = {"chargee": True}
    d.update(_capacites(module))
    return _dumps(d)


def _absente(ext_id):
    # « absente » distingue une extension nommée mais non chargée (désactivée,
    # supprimée, ou dont le chargement a échoué) d'un plantage pendant l'appel :
    # l'appli ne réessaie pas le téléchargement et ne bascule pas sur une autre.
    if ext_id in _erreurs:
        d = {"error": "extension_error", "message": _erreurs[ext_id]}
    else:
        d = {"error": "no_plugin",
             "message": "Extension \"%s\" is not loaded." % ext_id}
    d["absente"] = True
    return _dumps(d)


def _no_plugin():
    return _dumps({
        "error": "no_plugin",
        "message": "No search source. Import an extension in Settings."
    })


# ── Pages (réglages, pages libres) ────────────────────────────
# Une page est une description que l'app dessine en composants natifs : jamais de
# HTML, de lien ni de prix. Le contrat complet est dans docs/PLAN-EXTENSIONS.md,
# « Contrat des pages ».

# Bornes du parcours de pages(), comptées exactement comme PagesExtension (Java) :
# une action n'est acceptée que si l'app affiche son bouton, et réciproquement.
#   - les _PAGES_MAX premières entrées de la liste, valides ou non ;
#   - une page compte si c'est un objet avec un "id" chaîne non vide, pas déjà vu ;
#   - les _ELEMENTS_MAX premiers éléments de chaque page ;
#   - au plus _ARTICLES_MAX articles affichés par page, toutes listes confondues
#     (un article affiché a un titre non vide) ;
#   - un bouton = "action" chaîne non vide, hors noms réservés, et un libellé non vide.
_PAGES_MAX = 50
_ELEMENTS_MAX = 200
_ARTICLES_MAX = 200

# Jamais appelables depuis une page : le contrat média, ce que le pont injecte, et
# pages() elle-même. Les noms en « _ » (fonctions internes) sont refusés aussi.
# Même liste dans PagesExtension.ACTIONS_RESERVEES.
_NOMS_RESERVES = frozenset((
    "reglage", "data_dir", "extension_id", "search", "stream_info", "fetch_audio",
    "related", "playlist_meta", "fetch_playlist", "recognize", "pages",
))

# String.trim() de Java : retire les caractères <= U+0020, rien d'autre.
_BLANCS_JAVA = "".join(chr(c) for c in range(0x21))


def _erreur_page(code):
    """Une erreur de page ou d'action : un code seul, le texte se compose côté Java."""
    return _dumps({"error": code})


def _action_permise(nom):
    return isinstance(nom, str) and nom != "" and not nom.startswith("_") \
        and nom not in _NOMS_RESERVES


def _texte_non_vide(v):
    """Comme TexteTraduit.choisir(...) non vide : chaîne, nombre, booléen, ou
    {langue: texte} avec au moins un texte non blanc."""
    if isinstance(v, str):
        return v != ""
    if isinstance(v, (bool, int, float)):
        return True
    if isinstance(v, dict):
        return any(isinstance(t, str) and t.strip(_BLANCS_JAVA) != "" for t in v.values())
    return False


def _lire_pages(module):
    """Appelle pages() de l'extension : la liste, ou None si ce n'en est pas une.

    Une exception levée par l'extension remonte (rattrapée par l'appelant)."""
    retour = module.pages()
    if isinstance(retour, str):
        try:
            retour = json.loads(retour)
        except ValueError:
            return None
    return retour if isinstance(retour, list) else None


def _actions_declarees(pages_):
    """Les noms d'action des boutons que l'app affiche : la liste blanche de action().

    Relu sur le JSON tel que Java le recevra (tuples -> listes, clés -> chaînes) :
    les deux côtés parcourent exactement la même chose."""
    pages_ = json.loads(_dumps(pages_))
    noms = set()

    def bouton(b):
        if isinstance(b, dict) and _action_permise(b.get("action")) \
                and _texte_non_vide(b.get("libelle")):
            noms.add(b["action"])

    vues = set()
    for page in pages_[:_PAGES_MAX]:
        if not isinstance(page, dict):
            continue
        pid = page.get("id")
        if not isinstance(pid, str) or pid == "" or pid in vues:
            continue
        vues.add(pid)
        elements = page.get("elements")
        if not isinstance(elements, list):
            continue
        articles = 0
        for el in elements[:_ELEMENTS_MAX]:
            if not isinstance(el, dict):
                continue
            if el.get("type") == "bouton":
                bouton(el)
            elif el.get("type") == "liste" and isinstance(el.get("elements"), list):
                for article in el["elements"]:
                    if articles >= _ARTICLES_MAX:
                        break
                    if not isinstance(article, dict) or not _texte_non_vide(article.get("titre")):
                        continue
                    articles += 1
                    bouton(article.get("bouton"))
    return noms


def pages(ext_id):
    """{"pages": [...]} tel que l'extension le décrit, sérialisé ici ; ou une erreur.

    Codes : extension_error (l'extension a levé, "message" = « Type: message »),
    pages_invalides (pas une liste, ou illisible), valeur_invalide (NaN, infini),
    unsupported (pas de pages()), et ceux d'une extension absente."""
    ext_id = str(ext_id)
    module = _extensions.get(ext_id)
    if module is None:
        return _absente(ext_id)
    if not callable(getattr(module, "pages", None)):
        return _erreur_page("unsupported")
    try:
        brutes = _lire_pages(module)
    except BaseException as e:
        return _erreur_extension(_decrire(e))
    if brutes is None:
        return _erreur_page("pages_invalides")
    try:
        return _dumps({"pages": brutes})
    except NonRepresentableEnJson:
        return _erreur_page("valeur_invalide")
    except BaseException:  # une valeur que json ne sait pas écrire (octets, objet…)
        return _erreur_page("pages_invalides")


def action(ext_id, nom, arg_json=None):
    """Appelle l'action `nom` d'un bouton de page : `fn(reglages)` ou `fn(reglages, arg)`.

    `nom` n'est appelé que s'il figure comme action d'un bouton que l'app affiche
    dans pages() de cette extension, relu à chaque appel, et jamais s'il commence
    par « _ » ou désigne le contrat média ou une fonction injectée (_NOMS_RESERVES).
    `arg_json` : l'argument du bouton en JSON, None ou "" s'il n'en a pas.
    Retour attendu de l'extension : {"message": str|{lang: str}, "rafraichir": bool, "page": id}.

    Codes d'erreur : action_refusee, action_introuvable, pages_invalides,
    retour_invalide, valeur_invalide, extension_error (avec "message")."""
    ext_id = str(ext_id)
    module = _extensions.get(ext_id)
    if module is None:
        return _absente(ext_id)
    if not _action_permise(nom) or not callable(getattr(module, "pages", None)):
        return _erreur_page("action_refusee")
    try:
        brutes = _lire_pages(module)
    except BaseException as e:
        return _erreur_extension(_decrire(e))
    if brutes is None:
        return _erreur_page("pages_invalides")
    try:
        declarees = _actions_declarees(brutes)
    except NonRepresentableEnJson:
        return _erreur_page("valeur_invalide")
    except BaseException:
        return _erreur_page("pages_invalides")
    if nom not in declarees:
        return _erreur_page("action_refusee")
    fn = getattr(module, nom, None)
    if not callable(fn):
        return _erreur_page("action_introuvable")
    try:
        reglages = _lire_reglages(_dossiers.get(ext_id, ""))
        if arg_json is None or arg_json == "":
            retour = fn(reglages)
        else:
            retour = fn(reglages, json.loads(arg_json))
    except BaseException as e:
        return _erreur_extension(_decrire(e))
    if retour is None:
        return _dumps({})
    if isinstance(retour, str):
        try:
            retour = json.loads(retour)
        except ValueError:
            retour = {"message": retour}
    if not isinstance(retour, dict):
        return _erreur_page("retour_invalide")
    try:
        return _dumps(retour)
    except NonRepresentableEnJson:
        return _erreur_page("valeur_invalide")
    except BaseException:
        return _erreur_page("retour_invalide")


# ── Compatibilité ─────────────────────────────────────────────

def reload_plugin():
    """Recharge la source depuis son dossier (ancien point d'entrée de PluginManager)."""
    if _source is None:
        return _no_plugin()
    ext_id = _source
    dossier = _dossiers.get(ext_id)
    if dossier is None:
        return _no_plugin()
    return charger(ext_id, dossier)


def plugin_status() -> str:
    """Décrit la source de recherche, comme avant l'arrivée de plusieurs extensions."""
    module = _extensions.get(_source) if _source else None
    if module is None:
        etat = {"loaded": False, "path": None}
        if _source and _source in _erreurs:
            etat["error"] = _erreurs[_source]
        return _dumps(etat)
    caps = ["source"] + (["recognize"] if callable(getattr(module, "recognize", None)) else [])
    return _dumps({"loaded": True,
                       "path": getattr(module, "__file__", "unknown"),
                       "capabilities": caps})


# ── Alias de vocabulaire ──────────────────────────────────────
# Le vocabulaire public est sourceId / artist / trackCount ; Java et la colonne SQL
# gardent videoId / channelName / videoCount. On recopie vers l'ancienne clé quand
# elle manque, sans jamais écraser une valeur que l'extension a fournie.

def _aliaser(noeud):
    if isinstance(noeud, dict):
        if "videoId" not in noeud and "sourceId" in noeud:
            noeud["videoId"] = noeud["sourceId"]
        if "videoCount" not in noeud and "trackCount" in noeud:
            noeud["videoCount"] = noeud["trackCount"]
        if "channelName" not in noeud:
            if "artist" in noeud:
                noeud["channelName"] = noeud["artist"]
            elif "uploader" in noeud:
                noeud["channelName"] = noeud["uploader"]
        for v in noeud.values():
            _aliaser(v)
    elif isinstance(noeud, list):
        for v in noeud:
            _aliaser(v)


def _normaliser(retour, alias=True):
    """Applique les alias au JSON renvoyé ; une chaîne non-JSON reste telle quelle.

    Un dict ou une liste rendus directement sont sérialisés : Java attend une chaîne.
    `alias=False` (recognize) : même sérialisation, sans toucher aux clés.
    """
    if isinstance(retour, (dict, list)):
        if alias:
            _aliaser(retour)
        return _dumps(retour)
    if not isinstance(retour, str):
        return retour if retour is None else _dumps(retour)
    try:
        data = json.loads(retour)
    except ValueError:
        return retour
    if alias:
        _aliaser(data)
    try:
        return _dumps(data)
    except NonRepresentableEnJson:
        # Une chaîne déjà écrite par l'extension, avec NaN dedans : rendue telle
        # quelle, comme avant les alias, plutôt qu'une erreur.
        return retour


def _appeler(nom, args, ext):
    """Appelle `nom` de l'extension `ext` (défaut : la source) ; aucune exception ne sort."""
    ext_id = str(ext) if ext else _source
    if not ext_id:
        return _no_plugin()
    module = _extensions.get(ext_id)
    if module is None:
        return _absente(ext_id)
    try:
        return _normaliser(getattr(module, nom)(*args))
    except BaseException as e:  # SystemExit d'une extension compris : rien ne sort
        return _erreur_extension(_decrire(e))


# ── Contrat média ─────────────────────────────────────────────

def search(query: str, max_results: int = 20, offset: int = 0, ext=None) -> str:
    return _appeler("search", (query, max_results, offset), ext)

def stream_info(url: str, ext=None) -> str:
    return _appeler("stream_info", (url,), ext)

def related(source_id: str, max_results: int = 10, ext=None) -> str:
    return _appeler("related", (source_id, max_results), ext)

def playlist_meta(url: str, max_items: int = 200, ext=None) -> str:
    return _appeler("playlist_meta", (url, max_items), ext)

def fetch_audio(url: str, out_dir: str, ext=None) -> str:
    return _appeler("fetch_audio", (url, out_dir), ext)

def fetch_playlist(url: str, out_dir: str, max_items: int = 200, ext=None) -> str:
    return _appeler("fetch_playlist", (url, out_dir, max_items), ext)

def recognize(pcm: bytes, sample_rate: int, ext=None) -> str:
    """Capacité optionnelle : reconnaissance d'un extrait capté au micro.

    L'app ne transmet que du son brut — PCM mono, entiers 16 bits signés,
    little-endian, à `sample_rate` Hz — et ne présume rien de ce qui en sera fait.
    Empreinte, format, service interrogé : tout appartient à l'extension, qui
    ne renvoie que le résultat, au format neutre {"title", "artist", "artworkUrl"?}
    ou {"match": null} (rien trouvé). Sans `ext`, c'est l'extension de
    reconnaissance qui répond, à défaut la source.
    Une extension sans recognize() renvoie "unsupported".
    """
    ext_id = str(ext) if ext else (_reconnaissance or _source)
    if not ext_id:
        return _no_plugin()
    module = _extensions.get(ext_id)
    if module is None:
        return _absente(ext_id)
    fn = getattr(module, "recognize", None)
    if not callable(fn):
        return _dumps({
            "error": "unsupported",
            "message": "The selected extension does not provide music recognition."
        })
    try:
        return _normaliser(fn(pcm, sample_rate), alias=False)
    except BaseException as e:
        return _erreur_extension(_decrire(e))
