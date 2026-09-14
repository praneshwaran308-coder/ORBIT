from pathlib import Path

p = Path("backend/agents/research_agent.py")
s = p.read_text(encoding="utf-8")

needle = '''        # SiliconANGLE has a reliable WordPress API resolver.
        if "siliconangle" in source.lower():
'''

insert = '''        # ------------------------------------------------------------------
        # Publisher-specific discovery
        # ------------------------------------------------------------------
        # These publishers do not expose a consistently usable generic
        # /search endpoint, so use their stable public discovery mechanisms.
        
        source_low = source.lower()

        # Nature: search Nature's public site and DOI infrastructure.
        if "nature" in source_low:
            try:
                nature_candidate = self._find_nature_article(title)
                if (
                    nature_candidate
                    and self._is_usable_article_candidate(nature_candidate)
                ):
                    article = self.fetch_article(nature_candidate)
                    if article and self.article_matches_source(
                        article, title, source
                    ):
                        return nature_candidate
            except Exception:
                pass

        # WTTW: their search endpoint redirects to /search/node, while
        # article pages themselves are directly fetchable. Use Google web
        # discovery and validate every resulting publisher URL.
        if "wttw" in source_low:
            try:
                wttw_candidate = self._find_wttw_article(title)
                if (
                    wttw_candidate
                    and self._is_usable_article_candidate(wttw_candidate)
                ):
                    article = self.fetch_article(wttw_candidate)
                    if article and self.article_matches_source(
                        article, title, source
                    ):
                        return wttw_candidate
            except Exception:
                pass

        # Capitol News Illinois: use external web discovery because its
        # public search endpoint is unreliable from automated clients.
        if "capitol news illinois" in source_low:
            try:
                capitol_candidate = self._find_capitol_news_illinois_article(
                    title
                )
                if (
                    capitol_candidate
                    and self._is_usable_article_candidate(capitol_candidate)
                ):
                    article = self.fetch_article(capitol_candidate)
                    if article and self.article_matches_source(
                        article, title, source
                    ):
                        return capitol_candidate
            except Exception:
                pass

        # SiliconANGLE has a reliable WordPress API resolver.
        if "siliconangle" in source.lower():
'''

if needle not in s:
    raise SystemExit("Insertion point not found")

s = s.replace(needle, insert, 1)

# Insert helper methods immediately before find_publisher_article.
marker = "    def find_publisher_article(self, title: str, source: str = \"\", source_url: str = \"\") -> str:\n"

helpers = r'''    def _find_nature_article(self, title: str) -> str:
        """Discover a Nature article using Nature's public search/DOI pages."""
        import requests

        # Nature's article pages are often indexed directly by Google.
        queries = [
            f'"{title}" site:nature.com',
            f'"{title}" site:doi.org nature',
        ]

        for query in queries:
            try:
                response = requests.get(
                    "https://www.google.com/search",
                    params={"q": query, "num": 10},
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 Chrome/142.0 Safari/537.36"
                        )
                    },
                    timeout=8,
                )

                if not response.ok:
                    continue

                links = re.findall(
                    r'href=["\\'](https?://[^"\\']+)["\\']',
                    response.text,
                    flags=re.I,
                )

                for candidate in links:
                    candidate = candidate.replace("&amp;", "&")

                    if not (
                        "nature.com/" in candidate
                        or candidate.startswith("https://doi.org/")
                    ):
                        continue

                    if not self._is_usable_article_candidate(candidate):
                        continue

                    try:
                        article = self.fetch_article(candidate)
                    except Exception:
                        continue

                    if article and self.article_matches_source(
                        article, title, "Nature"
                    ):
                        return candidate

            except Exception:
                continue

        return ""

    def _find_wttw_article(self, title: str) -> str:
        """Discover a WTTW article through indexed publisher URLs."""
        import requests

        query = f'"{title}" site:news.wttw.com'

        try:
            response = requests.get(
                "https://www.google.com/search",
                params={"q": query, "num": 10},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/142.0 Safari/537.36"
                    )
                },
                timeout=8,
            )

            if not response.ok:
                return ""

            links = re.findall(
                r'href=["\\'](https?://[^"\\']+)["\\']',
                response.text,
                flags=re.I,
            )

            seen = set()

            for candidate in links:
                candidate = candidate.replace("&amp;", "&")

                if candidate in seen:
                    continue
                seen.add(candidate)

                parsed = urlparse(candidate)
                host = (parsed.netloc or "").lower().split(":")[0]

                if host.startswith("www."):
                    host = host[4:]

                if host != "news.wttw.com":
                    continue

                if not self._is_usable_article_candidate(candidate):
                    continue

                try:
                    article = self.fetch_article(candidate)
                except Exception:
                    continue

                if article and self.article_matches_source(
                    article, title, "WTTW News"
                ):
                    return candidate

        except Exception:
            pass

        return ""

    def _find_capitol_news_illinois_article(self, title: str) -> str:
        """Discover Capitol News Illinois article URLs via indexed search."""
        import requests

        query = f'"{title}" site:capitolnewsillinois.com'

        try:
            response = requests.get(
                "https://www.google.com/search",
                params={"q": query, "num": 10},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/142.0 Safari/537.36"
                    )
                },
                timeout=8,
            )

            if not response.ok:
                return ""

            links = re.findall(
                r'href=["\\'](https?://[^"\\']+)["\\']',
                response.text,
                flags=re.I,
            )

            seen = set()

            for candidate in links:
                candidate = candidate.replace("&amp;", "&")

                if candidate in seen:
                    continue
                seen.add(candidate)

                parsed = urlparse(candidate)
                host = (parsed.netloc or "").lower().split(":")[0]

                if host.startswith("www."):
                    host = host[4:]

                if host != "capitolnewsillinois.com":
                    continue

                if not self._is_usable_article_candidate(candidate):
                    continue

                try:
                    article = self.fetch_article(candidate)
                except Exception:
                    continue

                if article and self.article_matches_source(
                    article, title, "Capitol News Illinois"
                ):
                    return candidate

        except Exception:
            pass

        return ""

'''

if marker not in s:
    raise SystemExit("Method marker not found")

s = s.replace(marker, helpers + marker, 1)

p.write_text(s, encoding="utf-8")
print("PATCHED:", p)
