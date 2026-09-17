<p align="center">
  <img src="icon.png" alt="" width="120">
</p>

<h1 align="center">Omega Player</h1>

<p align="center">
  Lecteur de musique local pour Android — Android Auto, montre Wear OS, audio
  spatial binaural, analyse de tempo, égaliseur, files intelligentes.<br>
  <strong>Rien ne quitte l'appareil.</strong>
</p>

<p align="center">
  <em>A local music player for Android — Android Auto, Wear OS watch app,
  binaural spatial audio, tempo analysis, equalizer, smart queues.<br>
  Nothing leaves your device.</em>
</p>

---

## Ce dépôt / This repository

Ce dépôt ne contient **pas** le code source de l'application. Il sert à trois
choses, et trois seulement :

| | |
|---|---|
| [`PRIVACY_POLICY.md`](PRIVACY_POLICY.md) | la politique de confidentialité, référencée depuis la fiche Play |
| [Releases](../../releases) | les APK signés, pour installer hors Play Store |
| [`plugin-sdk/`](plugin-sdk/) | de quoi écrire un greffon de source en ligne |

*This repository does not contain the app's source code. It holds the privacy
policy, the signed APKs for sideloading, and the plugin SDK.*

## Installer / Install

**Depuis le Play Store** — la voie normale, mises à jour automatiques.

**Depuis un APK** — page [Releases](../../releases). Ils sont signés avec la
même clé que la version publiée sur Play : une installation manuelle se met
ensuite à jour depuis le Store, et inversement, sans désinstaller.

Vérifier l'origine d'un APK avant de l'installer :

```bash
apksigner verify --print-certs OmegaPlayer-<version>.apk
```

L'empreinte SHA-256 du certificat doit être exactement :

```
347bc78c1e1e49fc123befc8a602d759d2c6c0b0a1c970872cf5fbde02ab8caf
```

C'est la même que celle affichée dans Play Console → Intégrité de
l'application : un APK qui n'y répond pas ne vient pas d'ici.

Deux limites de l'installation manuelle, honnêtement :

- **Android Auto** refuse par défaut les applications installées hors Play. Il
  faut activer « Sources inconnues » dans les paramètres développeur d'Android
  Auto, sans quoi l'application n'apparaît pas en voiture.
- **Aucune mise à jour automatique** tant que l'application n'est pas installée
  depuis le Store.

### Montre Wear OS

La page [Releases](../../releases) contient aussi l'application de montre.
Elle **ne fonctionne pas seule** : elle pilote le téléphone par Bluetooth
(RFCOMM direct, sans Play Services). Le téléphone doit avoir Omega Player
installé et le pont activé dans les réglages.

## Greffons / Plugins

**L'application ne fournit, n'héberge, ne distribue et n'indexe aucun contenu
audio.** Elle est livrée sans aucun greffon : telle qu'installée, elle lit les
fichiers déjà présents sur l'appareil, et c'est tout.

Un greffon est un module Python indépendant, installé par l'utilisateur, qui
ajoute une source en ligne. Les greffons ne sont ni écrits, ni relus, ni
approuvés, ni contrôlés par Omega Player. Vous en êtes seul responsable, y
compris de la conformité de leur usage aux lois de votre juridiction.

[`plugin-sdk/`](plugin-sdk/) contient de quoi en écrire un :

| Fichier | Rôle |
|---|---|
| `README.html` | le contrat complet : fonctions attendues, formats de retour, erreurs |
| `media_bridge.py` | le pont réel embarqué dans l'application — à lire plutôt qu'à deviner |
| `media_plugin.py` | le squelette à remplir |
| `manifest.json` | l'identité du greffon (version, capacités) |

Le même dossier s'exporte depuis l'application : **Réglages → Greffons →
Exporter le SDK**.

Quatre fonctions sont attendues (`search`, `stream_info`, `fetch_audio`,
`playlist_meta`) ; `recognize` est optionnelle et active la reconnaissance au
micro. Un greffon ne peut pas embarquer de code natif : Android refuse le
chargement de bibliothèques depuis un répertoire modifiable par l'application.
`numpy`, `requests` et `beautifulsoup4` sont fournis par l'application.

## Vie privée / Privacy

Aucune donnée personnelle collectée, stockée ou transmise par l'application.
Bibliothèque, historique, analyses et réglages restent sur l'appareil. Le micro
ne sert qu'à la reconnaissance, sur action explicite et après consentement, et
l'enregistrement n'est jamais écrit sur le disque.

Détail complet, et ce qui relève des greffons : [`PRIVACY_POLICY.md`](PRIVACY_POLICY.md).

## Contact

mistano.dev@gmail.com
