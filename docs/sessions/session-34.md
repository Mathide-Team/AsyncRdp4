# Session 34 — 2026-10-11 : CI étendue, issue #41

## Résultat
Les 5 fichiers exclus du job Qualité tournent dans un nouveau job CI,
« Intégration (GTK4 Xvfb, serveur RDP d'essai) ». Ce job est non bloquant
(`continue-on-error`) et le job Qualité ne change pas. En local (Ubuntu
26.04, Python 3.14, PyGObject 3.58, GTK 4, FreeRDP 3.32) :

| Fichier | Résultat |
|---|---|
| test_gtk4_bridges / clipboard_file_download / demo_viewer | 48 réussis |
| test_gtk4_live.py (Xvfb, `build_gir.py` lancé avant) | 8 réussis, 2 xfail (connus) |
| test_integration_live.py (freerdp-shadow-cli) | 4 réussis, 1 sauté (resize) |

## Deux vrais bogues trouvés en lançant ces tests
1. **gbulb ne s'importe plus sous Python 3.14** :
   `ImportError: AbstractChildWatcher` (retiré d'`asyncio.unix_events`).
   Ce n'est pas qu'un problème de test : `gcm_gtk4_demo_viewer.main()`,
   l'application hôte de référence, était cassée. Nouveau module
   `integrations/gtk4/gcm_gtk4_asyncio.py` : `run_application(app)` utilise
   `gi.events.GLibEventLoopPolicy` (intégré à PyGObject ≥ 3.50) et ne
   revient à gbulb que sur un PyGObject plus ancien. Les deux tests live qui
   utilisaient gbulb et le visualiseur de démonstration passent par ce
   module.
2. **Provider presse-papier natif introuvable avec PyGObject ≥ 3.52** :
   « Namespace AsyncrdpClipboard not available ». PyGObject s'appuie
   désormais sur libgirepository-2.0, dont le dépôt n'est plus un singleton :
   `GIRepository.Repository.prepend_search_path()` n'atteint plus le dépôt
   qu'utilise `gi`. Correctif : `gi.Repository.get_default().prepend_search_path()`
   quand il existe, l'ancien chemin sinon. Sans ce correctif, le pont
   retombait en silence sur `new_for_value()`, donc des images invisibles
   pour un lecteur externe.

## Serveur RDP d'essai
`freerdp-shadow-cli` (paquet freerdp3-shadow-x11) partage un second Xvfb
(:98, 1280×800). L'authentification NLA passe par une base SAM produite par
`winpr-hash -u rdptest -p testpass123 -f sam`. Ce serveur n'ouvre pas le
canal Display Control : `test_resize` est sauté si `ASYNCRDP_TEST_NO_DISP=1`.
Il reste à le vérifier contre xrdp ou Windows.
