# =============================================================================
#  media_plugin.py — OmegaPlayer Plugin Template
#
#  This file is the entry point of your plugin.
#  It must be placed at the ROOT of your ZIP (not inside a subfolder).
#
#  REQUIRED functions (called by media_bridge.py):
#    - search(query, max_results, offset)  → str (JSON)
#    - stream_info(url)                    → str (JSON)
#    - fetch_audio(url, out_dir)           → str (JSON)
#    - playlist_meta(url)                  → str (JSON)
#
#  OPTIONAL functions (improve the experience):
#    - related(source_id, max_results)     → str (JSON)
#    - fetch_playlist(url, out_dir)        → str (JSON)
#    - recognize(pcm, sample_rate)         → str (JSON)   see the bottom of this file
#
#  CAPABILITIES ARE DETECTED, NOT DECLARED.
#  media_bridge.plugin_status() does callable(getattr(plugin, "recognize", None)).
#  Defining the function enables music recognition in the app; removing it
#  disables it cleanly. The "capabilities" array in manifest.json is
#  documentation only — the Java side reads "plugin_version" and nothing else.
#
#  manifest.json ships NEXT TO this file and its "plugin_version" IS the
#  plugin identity: the app installs into plugins/plugin_<version>/ and will
#  NOT re-extract a version it already has. Bump it on every build.
#
#  Return type: always a JSON string.
#  On error:    {"error": "descriptive message"}
#
#  Dependencies: place your third-party libraries inside the ZIP next to this
#  file — they will be automatically available via sys.path.
#
#  To publish your plugin: name your GitHub repository with the prefix
#  omega-player-plugin (e.g. omega-player-plugin-soundcloud)
# =============================================================================

import json
import logging
import os
import sys

# ── Path setup ────────────────────────────────────────────────────────────────
# Allows importing modules placed in the same folder as this file.
_self_path = os.path.dirname(__file__)
if _self_path not in sys.path:
    sys.path.insert(0, _self_path)

# ── Logger ────────────────────────────────────────────────────────────────────
def _log(msg: str):
    logging.getLogger("media_plugin").warning(msg)


# ── Dependency check ──────────────────────────────────────────────────────────
def _check():
    """
    Verify that your dependencies are available.
    Raise a RuntimeError with a clear message if a library is missing.
    """
    # Example:
    # try:
    #     import my_library
    # except ImportError as e:
    #     raise RuntimeError(f"Missing dependency: {e}")
    pass


# ── Metadata injection (optional but recommended) ─────────────────────────────
def _inject_metadata(file_path: str, title: str, artist: str, thumb_url: str):
    """
    Inject title, artist and cover art into the downloaded audio file.
    Implement this function if you want metadata to appear correctly
    in the OmegaPlayer library.

    Formats supported with mutagen (no ffmpeg required):
      .m4a / .mp4  → MP4Cover (covr atom)
      .mp3         → ID3 APIC frame
      .flac        → VorbisComment + Picture block
      .opus        → OggOpus + Picture (base64)
      .webm        → EBML text tags only, cover saved as sidecar .jpg

    You can use an official OmegaPlayer plugin as a reference implementation.
    """
    pass  # TODO: implement if needed


# =============================================================================
#  REQUIRED PUBLIC FUNCTIONS
# =============================================================================

def search(query: str, max_results: int = 40, offset: int = 0) -> str:
    """
    Search for tracks matching `query`.

    Parameters:
        query       : text entered by the user
        max_results : maximum number of results to return
        offset      : pagination — start index in the result set

    Expected JSON return (success):
    {
        "results": [
            {
                "videoId":      "unique_identifier",   <- used by stream_info / fetch_audio
                "title":        "Track title",
                "channelName":  "Artist or channel name",
                "durationMs":   210000,                <- duration in milliseconds (0 if unknown)
                "duration":     "3:30",                <- formatted duration (optional)
                "thumbnailUrl": "https://...",         <- thumbnail URL
                "url":          "https://...",         <- track page URL
                "description":  "..."                  <- optional, max 300 chars
            },
            ...
        ],
        "offset": 0,
        "total_fetched": 40
    }

    Expected JSON return (error):
    {"error": "message", "results": []}
    """
    _check()
    try:
        # TODO: implement search against your source
        results = []
        return json.dumps({"results": results, "offset": offset, "total_fetched": len(results)})
    except Exception as ex:
        _log(f"search error: {ex}")
        return json.dumps({"error": str(ex), "results": []})


def stream_info(url: str) -> str:
    """
    Resolve a URL and return track or playlist information.

    Case 1 — Single track:
    {
        "videoId":      "unique_identifier",
        "title":        "Track title",
        "channelName":  "Artist",
        "durationMs":   210000,
        "thumbnailUrl": "https://...",
        "url":          "https://...",
        "description":  "..."
    }

    Case 2 — Playlist / collection:
    {
        "_type":       "playlist",
        "id":          "playlist_identifier",
        "title":       "Playlist name",
        "channelName": "Author",
        "videoCount":  42,
        "results":     [ ... ]   <- same format as search result items
    }

    Playlist vs single track detection is your responsibility.
    Expected JSON return (error): {"error": "message"}
    """
    _check()
    try:
        # TODO: resolve the URL and return track/playlist info
        return json.dumps({"error": "stream_info not implemented"})
    except Exception as ex:
        _log(f"stream_info error: {ex}")
        return json.dumps({"error": str(ex)})


def fetch_audio(url: str, out_dir: str, max_retries: int = 10) -> str:
    """
    Download the audio file for `url` into `out_dir`.
    Inject metadata into the file after downloading.

    Parameters:
        url         : track URL (webpage or direct stream)
        out_dir     : destination folder (create it if missing)
        max_retries : number of attempts on network failure

    Expected JSON return (success):
    {
        "filePath":    "/absolute/path/to/file.m4a",
        "videoId":     "unique_identifier",
        "title":       "Track title",
        "channelName": "Artist",
        "durationMs":  210000,
        "description": "...",
        "ext":         "m4a"
    }

    Expected JSON return (error): {"error": "message"}

    Recommended formats (preference order, no ffmpeg needed):
      m4a > mp4 > mp3 > webm (last resort)
    """
    _check()
    os.makedirs(out_dir, exist_ok=True)
    try:
        # TODO: download the file and return its info
        return json.dumps({"error": "fetch_audio not implemented"})
    except Exception as ex:
        _log(f"fetch_audio error: {ex}")
        return json.dumps({"error": str(ex)})


def playlist_meta(url: str, max_items: int = 2000) -> str:
    """
    Fetch playlist metadata without downloading any audio files.
    Used by OmegaPlayer to display a preview and trigger imports.

    Parameters:
        url       : playlist URL
        max_items : maximum number of tracks to return

    Expected JSON return (success):
    {
        "id":          "playlist_identifier",
        "title":       "Playlist name",
        "channelName": "Author",
        "videoCount":  42,
        "results": [
            {
                "videoId":      "...",
                "title":        "...",
                "channelName":  "...",
                "durationMs":   0,
                "thumbnailUrl": "...",
                "url":          "..."
            },
            ...
        ]
    }

    Expected JSON return (error): {"error": "message"}
    """
    _check()
    try:
        # TODO: fetch playlist metadata from your source
        return json.dumps({"error": "playlist_meta not implemented"})
    except Exception as ex:
        _log(f"playlist_meta error: {ex}")
        return json.dumps({"error": str(ex)})


# =============================================================================
#  OPTIONAL FUNCTIONS
# =============================================================================

def related(source_id: str, max_results: int = 10) -> str:
    """
    [OPTIONAL] Return tracks similar to source_id.
    If not implemented, OmegaPlayer will silently ignore this function.

    Expected JSON return: same format as search -> {"results": [...]}
    """
    return json.dumps({"results": []})


def fetch_playlist(url: str, out_dir: str, max_items: int = 200) -> str:
    """
    [OPTIONAL] Download all tracks in a playlist.
    Default implementation: calls playlist_meta + fetch_audio in a loop.
    Override this if you have a more efficient batch method.

    Expected JSON return:
    {
        "playlistTitle": "...",
        "results": [ ... ],   <- successfully downloaded tracks
        "errors":  [ ... ]    <- {"videoId": "...", "error": "..."}
    }
    """
    meta = json.loads(playlist_meta(url, max_items))
    if "error" in meta:
        return json.dumps({"error": meta["error"], "results": [], "errors": []})

    results, errors = [], []
    for entry in meta.get("results", []):
        vid = entry.get("videoId", "")
        if not vid:
            continue
        r = json.loads(fetch_audio(entry.get("url", vid), out_dir))
        if "error" in r:
            errors.append({"videoId": vid, "error": r["error"]})
        else:
            results.append(r)

    return json.dumps({
        "playlistTitle": meta.get("title", ""),
        "results": results,
        "errors":  errors,
    })


# =============================================================================
#  UTILITIES (copy, adapt or replace based on your data source)
# =============================================================================

def _fmt(seconds) -> str:
    """Format a duration in seconds to 'M:SS' or 'H:MM:SS'."""
    if not seconds:
        return "--:--"
    s = int(seconds)
    m, s = divmod(s, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _to_dict(entry: dict, detail: bool = False) -> dict:
    """
    Normalize a raw dict (from your API / scraper) into an OmegaPlayer dict.
    Adapt the field names to match your data source.
    """
    track_id = entry.get("id", "") or entry.get("videoId", "")
    duration = entry.get("duration") or entry.get("duration_ms", 0) / 1000
    thumb    = entry.get("thumbnail") or entry.get("thumbnailUrl", "")

    return {
        "videoId":      track_id,
        "title":        entry.get("title", ""),
        "channelName":  entry.get("artist") or entry.get("channel") or entry.get("uploader", ""),
        "durationMs":   int(duration * 1000),
        "duration":     _fmt(duration),
        "thumbnailUrl": thumb,
        "url":          entry.get("url") or entry.get("webpage_url", ""),
        "description":  (entry.get("description") or "")[:300],
    }


# =============================================================================
#  OPTIONAL CAPABILITY: "recognize" — identify what is playing in the room
# =============================================================================
#  Define this function and the app's microphone buttons start working. Leave it
#  out and they explain that the active plugin does not do recognition. Nothing
#  else to switch on.
#
#  THE APP DOES NO AUDIO PROCESSING AT ALL. It records ~12 s from the microphone
#  and hands you the raw samples. Everything after that is yours: fingerprint (or
#  not), format, service, network. That is deliberate — it means you can change
#  algorithm or provider by shipping a new plugin, with no app update.
#
#  def recognize(pcm: bytes, sample_rate: int) -> str:
#
#    pcm          raw PCM, mono, signed 16-bit little-endian, no header.
#                 Decode with: np.frombuffer(pcm, dtype='<i2')
#    sample_rate  samples per second, currently 16000. Read it, do not assume it.
#
#  Returns a JSON string. On success, whatever shape your service produces — the
#  app looks for "matches" and "track" {title, subtitle, images}. On failure,
#  json.dumps({"error": "network", "message": "..."}).
#
#  NumPy is available: the app bundles it precisely so that a plugin can do real
#  signal processing. Import it normally. Note that a plugin ZIP can NEVER carry
#  compiled extensions — since Android 10 the app may not load native code from a
#  directory it can write to — so NumPy, requests and beautifulsoup4 are what you
#  get natively. Pure-Python packages you may ship next to this file.
#
#  What you receive is microphone audio. It may contain no music at all: a
#  conversation, a television, silence. Return no match rather than a guess, and
#  keep in mind that it is somebody's room you are sending somewhere.
#
# def recognize(pcm: bytes, sample_rate: int) -> str:
#     import numpy as np
#     samples = np.frombuffer(pcm, dtype='<i2')
#     ...
#     return json.dumps({"matches": [], "track": {}})
