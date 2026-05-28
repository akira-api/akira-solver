import asyncio
import time
import logging


async def check_cookie_validity(tab, url: str, timeout: int = 10) -> bool:
    """
    Open url in tab with existing browser cookies and check if
    Turnstile appears. Returns True if cookie is still valid.
    """
    await tab.go_to(url)

    start = time.time()
    loading_titles = {"loading..", "loading...", "please wait", "just a moment", ""}
    logger = logging.getLogger(__name__)
    logger.debug("Validating cookies for URL: %s", url)

    while time.time() - start < timeout:
        try:
            turnstile_present = await tab.execute_script("""
                const frames = document.querySelectorAll('iframe');
                for (const f of frames) {
                    if (f.src && f.src.includes('challenges.cloudflare.com')) {
                        return true;
                    }
                }
                return false;
            """)
            if turnstile_present:
                logger.debug("Turnstile detected on URL: %s", url)
                return False

            ready = await tab.execute_script("""
                return {
                    state: document.readyState,
                    title: document.title
                }
            """)

            if (
                ready["state"] == "complete"
                and ready["title"].lower().strip() not in loading_titles
            ):
                logger.debug("Page ready without turnstile for URL: %s (title=%s)", url, ready["title"])
                return True

        except Exception:
            pass

        await asyncio.sleep(0.5)

    return False