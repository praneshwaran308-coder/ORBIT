from pathlib import Path

p = Path("backend/agents/research_agent.py")
s = p.read_text(encoding="utf-8")

start = s.index("    def _find_nature_article")
end = s.index("    def _find_wttw_article", start)

helper = '''    def _find_nature_article(self, title: str) -> str:
        """Discover a Nature article through Crossref DOI metadata."""
        import requests

        try:
            response = requests.get(
                "https://api.crossref.org/works",
                params={
                    "query.title": title,
                    "rows": 10,
                    "select": "DOI,title,type",
                },
                headers={
                    "User-Agent": "ORBIT research resolver/1.0"
                },
                timeout=8,
            )

            if not response.ok:
                return ""

            items = response.json().get("message", {}).get("items", [])

            target = self.clean_text(title).lower()

            for item in items:
                doi = self.clean_text(item.get("DOI", ""))
                titles = item.get("title") or []

                if not doi or not titles:
                    continue

                candidate_title = self.clean_text(titles[0])

                # Require strong title overlap before accepting the DOI.
                target_words = {
                    w for w in re.findall(r"[a-z0-9]+", target)
                    if len(w) > 2
                }
                candidate_words = {
                    w for w in re.findall(
                        r"[a-z0-9]+",
                        candidate_title.lower()
                    )
                    if len(w) > 2
                }

                if not target_words:
                    continue

                overlap = len(target_words & candidate_words) / len(target_words)

                if overlap < 0.75:
                    continue

                url = "https://doi.org/" + doi

                if not self._is_usable_article_candidate(url):
                    continue

                try:
                    article = self.fetch_article(url)
                except Exception:
                    continue

                if article and self.article_matches_source(
                    article,
                    title,
                    "Nature",
                ):
                    return url

        except Exception:
            pass

        return ""


'''

s = s[:start] + helper + s[end:]

p.write_text(s, encoding="utf-8")
print("NATURE RESOLVER UPDATED: Crossref DOI discovery")
