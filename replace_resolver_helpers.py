from pathlib import Path

p = Path("backend/agents/research_agent.py")
s = p.read_text(encoding="utf-8")

start = s.index("    def _find_nature_article")
end = s.index("    def find_publisher_article", start)

helpers = '''    def _find_nature_article(self, title: str) -> str:
        """Discover a Nature article through Google web search."""
        import requests

        query = f'"{title}" site:nature.com'

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
                r"""href=["'](https?://[^"']+)["']""",
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
            pass

        return ""


    def _find_wttw_article(self, title: str) -> str:
        """Discover a WTTW article through Google web search."""
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
                r"""href=["'](https?://[^"']+)["']""",
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
        """Discover Capitol News Illinois articles through Google."""
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
                r"""href=["'](https?://[^"']+)["']""",
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

s = s[:start] + helpers + s[end:]
p.write_text(s, encoding="utf-8")

print("HELPER SECTION REPLACED CLEANLY")
