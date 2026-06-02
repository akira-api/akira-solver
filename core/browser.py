import logging
import time
import os
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions


logger = logging.getLogger(__name__)


def _build_options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.add_argument('--proxy-server=socks5://akira-xray:1080')
    headless_value = os.getenv("BROWSER_HEADLESS", "false").strip().lower()
    options.headless = headless_value in {"1", "true", "yes", "on"}
    chrome_binary = os.getenv("CHROME_BINARY")
    if chrome_binary:
        options.binary_location = chrome_binary
    elif os.path.exists("/usr/bin/chromium"):
        options.binary_location = "/usr/bin/chromium"
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    current_time = int(time.time())
    options.browser_preferences = {
        "profile": {
            "last_engagement_time": str(current_time - (3 * 60 * 60)),
            "exited_cleanly": True,
            "exit_type": "Normal",
        },
        "safebrowsing": {"enabled": True},
    }

    return options


class BrowserManager:
    def __init__(self) -> None:
        self._browser: Chrome | None = None
        self._bootstrap_tab = None

    async def start(self) -> None:
        options = _build_options()
        self._browser = Chrome(options=options)
        logger.info("Starting browser process")
        # Debug: log key options (avoid dumping large prefs)
        try:
            logger.debug("Browser args: %s", getattr(options, "arguments", []))
            logger.debug("Browser headless: %s", getattr(options, "headless", False))
        except Exception:
            pass
        self._bootstrap_tab = await self._browser.start()
        logger.info("Browser process started")

    async def stop(self) -> None:
        if self._browser:
            if self._bootstrap_tab:
                try:
                    await self._bootstrap_tab.close()
                except Exception:
                    pass
                self._bootstrap_tab = None
            await self._browser.__aexit__(None, None, None)
            self._browser = None

    async def new_tab(self):
        if not self._browser:
            raise RuntimeError("Browser is not started")
        logger.debug("Creating new browser tab")
        tab = await self._browser.new_tab()
        logger.debug("New tab created: %s", getattr(tab, "_target_id", "unknown"))
        return tab

    async def close_tab(self, tab) -> None:
        try:
            logger.debug("Closing tab: %s", getattr(tab, "_target_id", "unknown"))
            await tab.close()
        except Exception:
            logger.exception("Error closing tab")


browser_manager = BrowserManager()