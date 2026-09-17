"""
media_bridge.py — pont Chaquopy bundlé dans l'APK.
Aucune logique média. Délègue au plugin chargé dynamiquement.
"""

import sys
import json

_plugin = None


def reload_plugin():
    """Appelé par PluginManager.reloadBridgePlugin() après changement de provider."""
    global _plugin
    _plugin = None
    # Purger du cache modules si présent
    sys.modules.pop("media_plugin", None)


def _load():
    global _plugin
    if _plugin is not None:
        return _plugin
    try:
        import media_plugin as p
        _plugin = p
    except ImportError:
        _plugin = None
    return _plugin


def _no_plugin():
    return json.dumps({
        "error": "no_plugin",
        "message": "Aucun plugin média installé. Importez un plugin dans les paramètres."
    })


# ── Interface publique ────────────────────────────────────────

def search(query: str, max_results: int = 20, offset: int = 0) -> str:
    p = _load(); return p.search(query, max_results, offset) if p else _no_plugin()

def stream_info(url: str) -> str:
    p = _load(); return p.stream_info(url) if p else _no_plugin()

def related(source_id: str, max_results: int = 10) -> str:
    p = _load(); return p.related(source_id, max_results) if p else _no_plugin()

def playlist_meta(url: str, max_items: int = 200) -> str:
    p = _load(); return p.playlist_meta(url, max_items) if p else _no_plugin()

def fetch_audio(url: str, out_dir: str) -> str:
    p = _load(); return p.fetch_audio(url, out_dir) if p else _no_plugin()

def fetch_playlist(url: str, out_dir: str, max_items: int = 200) -> str:
    p = _load(); return p.fetch_playlist(url, out_dir, max_items) if p else _no_plugin()

def recognize(pcm: bytes, sample_rate: int) -> str:
    """Capacité optionnelle du plugin : reconnaissance d'un extrait capté au micro.

    L'app ne transmet que du son brut — PCM mono, entiers 16 bits signés,
    little-endian, à `sample_rate` Hz — et ne présume rien de ce qui en sera fait.
    Empreinte, format, service interrogé : tout appartient au plugin. Un plugin
    sans recognize() renvoie "unsupported".
    """
    p = _load()
    if p is None:
        return _no_plugin()
    fn = getattr(p, "recognize", None)
    if fn is None:
        return json.dumps({
            "error": "unsupported",
            "message": "Le plugin actif ne fournit pas la reconnaissance musicale."
        })
    return fn(pcm, sample_rate)

def plugin_status() -> str:
    p = _load()
    if p is None:
        return json.dumps({"loaded": False, "path": None, "engineAvailable": False})
    engine_ok = getattr(p, "_ENGINE_OK", False)
    path = getattr(sys.modules.get("media_plugin"), "__file__", "unknown")
    caps = ["source"] + (["recognize"] if callable(getattr(p, "recognize", None)) else [])
    return json.dumps({"loaded": True, "engineAvailable": engine_ok, "path": path,
                       "capabilities": caps})
