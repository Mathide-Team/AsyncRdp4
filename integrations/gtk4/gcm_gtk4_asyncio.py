"""Boucle asyncio intégrée à la boucle GLib d'une Gtk.Application.

Deux intégrateurs possibles, choisis à l'exécution :

1. ``gi.events.GLibEventLoopPolicy`` (PyGObject >= 3.50, intégré) : la
   politique est installée puis ``app.run()`` fait tourner GLib et asyncio
   ensemble ;
2. ``gbulb`` (ancien intégrateur), uniquement si PyGObject est plus ancien.
   gbulb 0.6 ne s'importe plus sous Python 3.14 (``AbstractChildWatcher``
   retiré d'``asyncio.unix_events``), constaté le 2026-10-11 (issue #41).

La politique précédente est restaurée à la sortie.
"""

from __future__ import annotations

import asyncio
import warnings

from loguru import logger

from asyncrdp.tracing import traced


@traced
def run_application(app, argv: list[str] | None = None) -> int:
    """Lance *app* (Gtk.Application) avec asyncio branché sur GLib ; renvoie le code de sortie."""
    argv = [] if argv is None else argv
    with warnings.catch_warnings():
        # asyncio.*_event_loop_policy : dépréciés en 3.14, retirés en 3.16 ;
        # PyGObject n'expose pas encore d'autre point d'entrée.
        warnings.simplefilter("ignore", DeprecationWarning)
        previous = asyncio.get_event_loop_policy()
        try:
            from gi.events import GLibEventLoopPolicy
        except ImportError as exc:
            logger.debug("gbulb absent, politique GLib non chargée : {}", exc)
            GLibEventLoopPolicy = None
        try:
            if GLibEventLoopPolicy is not None:
                asyncio.set_event_loop_policy(GLibEventLoopPolicy())
                return int(app.run(argv) or 0)
            import gbulb

            asyncio.set_event_loop_policy(gbulb.GLibEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_forever(application=app, argv=argv)
            return 0
        finally:
            asyncio.set_event_loop_policy(previous)
