"""
Shared VLC lifecycle helpers.

Centralizes two things that were previously copy-pasted across the app
(SharedPlayerManager, EasyModeScreen and the app-level cleanup):

1. Building the arguments for a VLC ``Instance`` -- notably locating the
   plugins directory on Windows. See :func:`vlc_instance_args`.
2. The Windows-safe teardown sequence for a media player / instance. VLC on
   Windows is prone to access-violation crashes if ``stop()`` then
   ``release()`` is called while the player is still attached to a window. The
   safe order (documented in CLAUDE.md) is:
   pause -> detach from window -> set_media(None) -> release, skipping
   ``stop()`` on Windows entirely. See :func:`safe_release_player`.

Keeping this in one place means the crash-avoidance rules cannot drift between
the modules that own a VLC player.
"""
import logging
import os
import sys

logger = logging.getLogger(__name__)


def _windows_plugin_path() -> "str | None":
    """
    Best-effort location of the VLC ``plugins`` directory on Windows.

    Checks, in order: the ``VLC_PLUGIN_PATH`` environment variable, the
    registry ``InstallDir`` value (both 64- and 32-bit views, plus per-user),
    and the common Program Files locations. Returns the first directory that
    exists, or ``None`` if none do.
    """
    candidates = []

    env_path = os.environ.get("VLC_PLUGIN_PATH")
    if env_path:
        candidates.append(env_path)

    # Registry: HKLM/HKCU \SOFTWARE\VideoLAN\VLC -> InstallDir
    try:
        import winreg

        reg_views = (
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_CURRENT_USER, 0),
        )
        for hive, flags in reg_views:
            try:
                with winreg.OpenKey(
                    hive, r"SOFTWARE\VideoLAN\VLC", 0, winreg.KEY_READ | flags
                ) as key:
                    install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                    if install_dir:
                        candidates.append(os.path.join(install_dir, "plugins"))
            except OSError:
                continue
    except ImportError:
        pass

    candidates.extend(
        [
            r"C:\Program Files\VideoLAN\VLC\plugins",
            r"C:\Program Files (x86)\VideoLAN\VLC\plugins",
        ]
    )

    for path in candidates:
        if path and os.path.isdir(path):
            return path
    return None


def vlc_instance_args() -> list:
    """
    VLC ``Instance`` arguments for the current platform.

    On Windows we disable the plugins cache and point VLC at its plugins
    directory when we can find it. If we cannot, we omit ``--plugin-path``
    rather than pass a bogus path (a wrong path yields a black screen / no
    audio). On other platforms VLC's default discovery is used.
    """
    if sys.platform != "win32":
        return []

    args = ["--no-plugins-cache"]
    plugin_path = _windows_plugin_path()
    if plugin_path:
        args.append(f"--plugin-path={plugin_path}")
        logger.debug(f"Using VLC plugins path: {plugin_path}")
    else:
        logger.warning(
            "VLC plugins directory not found; relying on VLC's default "
            "discovery. Set VLC_PLUGIN_PATH if playback shows no video."
        )
    return args


def _detach_window(player) -> None:
    """Detach the player from its render window (platform-specific)."""
    try:
        if sys.platform == "win32":
            player.set_hwnd(None)
        elif sys.platform.startswith("linux"):
            player.set_xwindow(0)
        elif sys.platform == "darwin":
            player.set_nsobject(0)
    except Exception as e:
        logger.warning(f"Could not detach player from window: {e}")


def safe_release_player(player) -> None:
    """
    Release a VLC media player using the Windows-safe sequence.

    Order: pause (if playing) -> detach from window -> set_media(None) ->
    ``stop()`` only on non-Windows -> ``release()``. Every step is guarded;
    failures are logged, never raised, because this runs during shutdown.

    Passing ``None`` is a no-op, so callers can safely null out their
    reference and call this again without a double-release crash.
    """
    if not player:
        return

    try:
        try:
            if player.is_playing():
                player.set_pause(1)
        except Exception:
            pass

        # Detach before any release to avoid Windows access violations.
        _detach_window(player)

        try:
            player.set_media(None)
        except Exception:
            pass

        # On Windows, stop() can crash VLC; release() handles teardown.
        if sys.platform != "win32":
            try:
                player.stop()
            except Exception as e:
                logger.warning(f"Error stopping player: {e}")

        try:
            player.release()
            logger.debug("VLC player released")
        except Exception as e:
            logger.error(f"Error releasing player: {e}")
    except Exception as e:
        logger.error(f"Error during player cleanup: {e}")


def safe_release_instance(instance) -> None:
    """Release a VLC instance, swallowing and logging any error."""
    if not instance:
        return
    try:
        instance.release()
        logger.debug("VLC instance released")
    except Exception as e:
        logger.error(f"Error releasing VLC instance: {e}")
