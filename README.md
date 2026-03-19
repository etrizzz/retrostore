# RetroHub Cinema

Application desktop Python autonome orientée retrogaming PC avec interface premium sombre, recherche multi-sources et moteur de téléchargement résilient.

## Fonctionnalités

- Recherche fédérée via **Archive.org**, **MyAbandonware**, **MobyGames** (optionnel via clé API) et import local d'un manifeste **eXoDOS/LaunchBox**.
- Classement automatique des jeux : **MS-DOS**, **ScummVM**, **Windows rétro complexe**.
- Téléchargement robuste avec **retries exponentiels**, fichiers `.part`, validation des archives ZIP, garde-fou contre les chemins d'archive dangereux et extraction silencieuse en arrière-plan.
- Lancement automatique avec **DOSBox** ou **ScummVM** si les exécutables sont disponibles, y compris détection automatique des installateurs classiques dans `Program Files` sous Windows.
- Redirection des jeux complexes (`.iso`, `.cue`, installateurs `.exe`) vers `A_Installer_Manuellement` avec message explicite.
- Bibliothèque locale persistée dans `library_index.json`.
- Journalisation applicative dans `~/RetroHubCinema/logs/retrohub.log`.

## Architecture

```text
app.py                       # point d'entrée Qt
retrohub/
  config.py                  # configuration, chemins, variables d'environnement
  models.py                  # modèles métier
  logging_utils.py           # logs fichier + console
  providers/
    archive_org.py           # API advancedsearch + metadata Archive.org
    myabandonware.py         # annuaire web public orienté abandonware PC
    mobygames.py             # API publique optionnelle pour enrichir les métadonnées
    exodos_manifest.py       # import XML local type LaunchBox/eXoDOS
  services/
    search_service.py        # agrégation multi-providers
    downloader.py            # téléchargement, retry, extraction, routage logistique
    launcher.py              # DOSBox / ScummVM
    library.py               # index local
  ui/
    main_window.py           # interface graphique premium sombre
```

## Installation Windows pas-à-pas

### Installation express

```powershell
.\install_windows.bat
```

ou

```powershell
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

Ce script crée le venv, installe les dépendances Python, tente d'installer DOSBox et ScummVM via `winget` si disponible, puis génère `Run-RetroHub.ps1` pour démarrer l'application plus facilement.

### 1) Installer Python

- Recommande : **Python 3.11 x64** ou **Python 3.12 x64**.
- Télécharge Python depuis le site officiel puis lance l'installateur Windows.
- **Très important** : coche la case **Add Python to PATH** avant de cliquer sur **Install Now**.

### 2) Vérifier Python dans le terminal

Ouvre **PowerShell** puis tape :

```powershell
python --version
pip --version
```

Si la version s'affiche correctement, l'environnement de base est prêt.

### 3) Préparer le projet

Dans PowerShell, place-toi dans le dossier du projet :

```powershell
cd C:\Chemin\Vers\retrostore
```

Crée ensuite un environnement virtuel :

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 4) Installer les bibliothèques Python

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Le fichier `requirements.txt` installe :
- `PySide6` pour l'interface graphique
- `requests` pour les requêtes HTTP
- `beautifulsoup4` + `lxml` pour lire certains annuaires HTML
- `py7zr` pour extraire les archives `.7z`

### 5) Installer les moteurs externes

Pour un fonctionnement automatique confortable, installe :

- **DOSBox** ou **DOSBox Staging**
- **ScummVM**

Le programme essaie de les trouver automatiquement dans :
- le `PATH`
- `C:\Program Files\DOSBox-0.74-3\DOSBox.exe`
- `C:\Program Files\DOSBox Staging\dosbox.exe`
- `C:\Program Files\ScummVM\scummvm.exe`

Si tu préfères contrôler toi-même les chemins, définis ces variables dans PowerShell avant de lancer l'app :

```powershell
$env:DOSBOX_PATH="C:\Program Files\DOSBox-0.74-3\DOSBox.exe"
$env:SCUMMVM_PATH="C:\Program Files\ScummVM\scummvm.exe"
python app.py
```

### 6) Lancer l'application

```powershell
python app.py
```

## Mode d'emploi — comme une salle de cinéma automatisée

Imagine l'application comme un **projectionniste automatique** :

1. **Tu choisis le film** → ici, tu tapes le nom du jeu dans la barre de recherche.
2. **Le projectionniste consulte plusieurs catalogues** → Archive.org, MyAbandonware, MobyGames (si clé API) et eXoDOS local.
3. **Il sélectionne la meilleure bobine** → le moteur privilégie les archives simples (`.zip`, `.7z`) avant les formats d'installation lourds (`.iso`, `.exe`).
4. **Il prépare la salle** :
   - pour un jeu DOS / ScummVM simple : téléchargement, extraction et lancement
   - pour un jeu Windows rétro complexe : copie propre dans `A_Installer_Manuellement`
5. **Il te laisse profiter** → l'app reste ouverte même si une source web échoue ou si un téléchargement plante.

## Recherche et téléchargement d'un jeu MS-DOS depuis Archive.org

### Étape 1 — Rechercher

- Lance l'application.
- Dans la barre du haut, tape par exemple `Doom`, `Prince of Persia` ou `Monkey Island`.
- Clique sur **Rechercher**.

### Étape 2 — Lire les résultats

Chaque ligne affiche :
- la source (`Archive.org`, `MyAbandonware`, etc.)
- le type détecté (`dos`, `scummvm`, `windows`, `unknown`)
- le titre

Quand tu cliques sur un résultat, le panneau de droite affiche :
- le titre
- la source
- le type détecté
- l'année
- l'URL source
- le nombre d'assets trouvés
- un résumé

### Étape 3 — Télécharger / lancer

- Sélectionne de préférence un résultat **Archive.org** marqué **[dos]**.
- Clique sur **Télécharger / Lancer**.

Le moteur fait alors automatiquement :

1. téléchargement dans `~/RetroHubCinema/downloads/`
2. création d'un fichier temporaire `.part`
3. plusieurs tentatives en cas d'erreur réseau
4. vérification de l'archive
5. extraction dans `~/RetroHubCinema/library/<Nom du jeu>/`
6. génération d'un petit fichier de config DOSBox
7. lancement de DOSBox si trouvé

### Étape 4 — Si le jeu est plus complexe

Si l'asset détecté est un :
- `.iso`
- `.cue`
- installateur `.exe`

alors le hub le place dans :

```text
~/RetroHubCinema/A_Installer_Manuellement/
```

Tu n'as plus qu'à :
- double-cliquer sur l'installateur, ou
- monter l'ISO avec Windows, puis lancer l'installation.

## Où placer DOSBox et ScummVM ?

Tu as **trois options**, par ordre de simplicité :

### Option A — Installation standard

Installe simplement DOSBox et ScummVM avec leurs installateurs Windows classiques dans `Program Files`.
Le hub essaiera de les détecter automatiquement.

### Option B — Ajouter les programmes au PATH

Si leurs dossiers sont dans le `PATH`, l'application les trouvera aussi automatiquement.

### Option C — Forcer les chemins via variables d'environnement

Dans PowerShell :

```powershell
$env:DOSBOX_PATH="D:\Emulateurs\DOSBox\DOSBox.exe"
$env:SCUMMVM_PATH="D:\Emulateurs\ScummVM\scummvm.exe"
python app.py
```

## Dépendances externes conseillées

- `dosbox` dans le `PATH`, ou variable `DOSBOX_PATH`.
- `scummvm` dans le `PATH`, ou variable `SCUMMVM_PATH`.
- Optionnel : `MOBYGAMES_API_KEY` pour enrichissement MobyGames.
- Optionnel : déposer un export LaunchBox/eXoDOS dans `~/RetroHubCinema/manifests/exodos.xml`.

## Lancement

```bash
python app.py
```

## Flux de traitement

1. L'utilisateur recherche un jeu.
2. Le hub interroge les providers disponibles.
3. Le moteur choisit le meilleur asset détecté.
4. Si archive simple `zip/7z` + type `dos/scummvm`:
   - téléchargement dans `downloads/`
   - extraction dans `library/<jeu>/`
   - génération de config DOSBox si nécessaire
   - lancement automatique si binaire trouvé
5. Si package complexe `iso/cue/exe` ou type Windows:
   - copie dans `A_Installer_Manuellement/`
   - notification claire à l'écran

## Limites actuelles / pistes d'évolution

- Certains annuaires publics changent fréquemment leur HTML : prévoir des tests d'intégration ou une couche d'adaptateurs versionnés.
- Le routage ScummVM peut être enrichi avec une détection d'engine plus précise (via présence de fichiers `*.000`, `resource.map`, etc.).
- Les jeux Windows rétro complexes pourraient être préparés davantage via profils PCem/86Box ou wrappers Wine/OTVDM selon OS.
