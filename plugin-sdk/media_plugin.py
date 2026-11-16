# =============================================================================
#  media_plugin.py - Omega Player extension template
#
#  This file is the entry point of your extension. Put it at the ROOT of your
#  ZIP, next to manifest.json. README.html (exported with it) is the full guide.
#
#  As shipped, it is a working, offline DEMO SOURCE: three fictional tracks,
#  searchable, with a settings page. Import it as is to see every part of the
#  contract in action, then replace the catalogue with your own service.
#
#  Search source - all four or none (the app refuses to load a partial source):
#    search(query, max_results=20, offset=0)
#    stream_info(url)
#    fetch_audio(url, out_dir)
#    playlist_meta(url, max_items=200)
#  Optional:
#    related(source_id, max_results=10)
#    fetch_playlist(url, out_dir, max_items=200)
#    recognize(pcm, sample_rate)         (see the end of this file)
#    pages()                             (settings and free pages)
#
#  Capabilities are DETECTED: the app checks callable(getattr(module, name)).
#  Define a function and the capability exists; remove it and it is gone.
#
#  Return a JSON string or a dict / list (the bridge serialises it). On failure
#  return {"error": "readable message"}. An exception does not crash the app:
#  the bridge catches it and shows "extension_error" with its type and message.
#
#  Injected by the app BEFORE this file runs (do not define them yourself):
#    extension_id            your id, from manifest.json
#    data_dir()              creates and returns <your folder>/data: the only
#                            place to write. Kept on re-import, erased on delete.
#    reglage(cle, defaut)    reads one value saved by your settings page
# =============================================================================

import json
import os

# ── Demo catalogue (replace with your service) ───────────────────────────────

_PLAYLIST_ID = "demo-playlist"
_BASE_URL = "https://example.com/demo/"


def _track(source_id, title, artist, duration_s, url, thumbnail=""):
    """One track, in the shape every list of the contract uses."""
    duration_s = int(duration_s or 0)
    minutes, seconds = divmod(duration_s, 60)
    return {
        "sourceId": source_id,            # stable: dedup key, cache key, download id
        "title": title,
        "artist": artist,
        "durationMs": duration_s * 1000,
        "duration": "%d:%02d" % (minutes, seconds) if duration_s else "",
        "thumbnailUrl": thumbnail,        # "" when you have none
        "url": url,
        "description": "",
    }


_CATALOGUE = [
    _track("demo-1", "Morning Lines", "The Placeholder Trio", 184, _BASE_URL + "demo-1"),
    _track("demo-2", "Static Garden", "Example Ensemble", 221, _BASE_URL + "demo-2"),
    _track("demo-3", "Quiet Index", "The Placeholder Trio", 197, _BASE_URL + "demo-3"),
]


def _find(url_or_id):
    """The app passes either a sourceId (download of a search result) or a URL."""
    for track in _CATALOGUE:
        if url_or_id in (track["sourceId"], track["url"]):
            return track
    return None


# ── Small cache in data_dir() ────────────────────────────────────────────────

def _cache_path():
    return os.path.join(data_dir(), "recent_searches.json")


def _read_recent():
    try:
        with open(_cache_path(), "r", encoding="utf-8") as f:
            recent = json.load(f)
    except (OSError, ValueError):
        return []
    return recent if isinstance(recent, list) else []


def _remember(query):
    recent = [q for q in _read_recent() if q != query]
    recent.insert(0, query)
    with open(_cache_path(), "w", encoding="utf-8") as f:
        json.dump(recent[:10], f)


# ── Search source ────────────────────────────────────────────────────────────

def search(query, max_results=20, offset=0):
    """{"results": [track], "offset": int, "total_fetched": int}"""
    q = (query or "").strip().lower()
    match_artist = reglage("match_artist", True)
    only_artist = (reglage("only_artist", "") or "").strip().lower()

    found = []
    for track in _CATALOGUE:
        if only_artist and track["artist"].lower() != only_artist:
            continue
        text = track["title"].lower()
        if match_artist:
            text += " " + track["artist"].lower()
        if q in text:
            found.append(dict(track))   # a copy: the bridge adds legacy keys

    if q:
        _remember(query.strip())
    page = found[offset:offset + max_results]
    return {"results": page, "offset": offset, "total_fetched": len(page)}


def stream_info(url):
    """A single track, or a collection: {"_type": "playlist", ...}."""
    if url in (_PLAYLIST_ID, _BASE_URL + _PLAYLIST_ID):
        meta = playlist_meta(url)
        meta["_type"] = "playlist"
        return meta
    track = _find(url)
    if track is None:
        return {"error": "Unknown demo track: %s" % url}
    return dict(track)


def playlist_meta(url, max_items=200):
    """Collection metadata, without downloading anything."""
    if url not in (_PLAYLIST_ID, _BASE_URL + _PLAYLIST_ID):
        return {"error": "Unknown demo playlist: %s" % url}
    tracks = [dict(t) for t in _CATALOGUE[:max_items]]
    return {
        "id": _PLAYLIST_ID,
        "title": "Demo playlist",
        "artist": "Omega Player SDK",
        "trackCount": len(tracks),
        "results": tracks,
    }


def fetch_audio(url, out_dir):
    """Download one track into out_dir.

    A real source writes the file, then returns:
        {"filePath": "<absolute path, complete on return>", "sourceId": ...,
         "title": ..., "artist": ..., "durationMs": ..., "description": ...,
         "format": "m4a"}
    The demo catalogue has no audio, so this is the clear error the app shows.
    """
    if _find(url) is None:
        return {"error": "Unknown demo track: %s" % url}
    return {"error": "The demo source has no audio. Replace the catalogue with your own service."}


# ── Settings page ────────────────────────────────────────────────────────────
# Keys of the page contract are French on purpose (titre, elements, cle,
# libelle, defaut...): see the glossary in README.html.

def pages():
    recent = _read_recent()
    return [{
        "id": "settings",
        "titre": {"en": "Demo source", "fr": "Source de démonstration"},
        "elements": [
            {"type": "message",
             "texte": {"en": "Last searches: %s" % (", ".join(recent) or "none"),
                       "fr": "Dernières recherches : %s" % (", ".join(recent) or "aucune")}},
            {"type": "texte", "cle": "only_artist",
             "libelle": {"en": "Only this artist", "fr": "Seulement cet artiste"},
             "aide": {"en": "Leave empty to search everything.",
                      "fr": "Vide : tout le catalogue."}},
            {"type": "interrupteur", "cle": "match_artist", "defaut": True,
             "libelle": {"en": "Also match artist names",
                         "fr": "Chercher aussi dans les artistes"}},
            {"type": "bouton", "action": "clear_recent",
             "libelle": {"en": "Clear recent searches",
                         "fr": "Effacer les dernières recherches"}},
        ],
    }]


def clear_recent(reglages):
    """Button action: receives the saved settings, returns a message."""
    try:
        os.remove(_cache_path())
    except FileNotFoundError:
        pass
    return {"message": {"en": "Recent searches cleared.",
                        "fr": "Dernières recherches effacées."},
            "rafraichir": True}


# =============================================================================
#  OPTIONAL: recognize(pcm, sample_rate) - identify what is playing in the room
# =============================================================================
#  Define it and the app's microphone buttons can use this extension.
#
#    pcm          raw PCM, mono, signed 16-bit little-endian, no header
#                 (numpy: np.frombuffer(pcm, dtype="<i2"))
#    sample_rate  samples per second (16000 today): read it, do not assume it
#
#  Return only the result:
#    {"title": "...", "artist": "...", "artworkUrl": "https://..."}  (artworkUrl optional)
#    {"match": None}                                                 nothing recognised
#    {"error": "..."}                                                failure
#
#  This is microphone audio from someone's room. It may hold a conversation, a
#  television or silence. Do not store it, do not forward it as is, and send
#  over the network only what recognition requires.
#
# def recognize(pcm, sample_rate):
#     import numpy as np
#     samples = np.frombuffer(pcm, dtype="<i2")
#     ...
#     return {"match": None}
