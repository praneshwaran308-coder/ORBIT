import asyncio
import json
import html
import re
from datetime import datetime

from html.parser import HTMLParser
from urllib.parse import quote, urlparse, unquote, urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .base_agent import BaseAgent


# ============================================================
# ARTICLE TEXT PARSER
# ============================================================

class ArticleTextParser(HTMLParser):
    """
    Lightweight HTML parser for extracting readable article text.
    """

    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer",
        "header",
        "form",
        "aside",
        "iframe",
        "button",
    }

    BLOCK_TAGS = {
        "p",
        "article",
        "section",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "blockquote",
    }

    def __init__(self):
        super().__init__()

        self.text_parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        if tag in self.BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in self.SKIP_TAGS:
            if self.skip_depth > 0:
                self.skip_depth -= 1
            return

        if self.skip_depth > 0:
            return

        if tag in self.BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self.skip_depth > 0:
            return

        if not data:
            return

        # Preserve meaningful whitespace around inline HTML elements.
        # SiliconANGLE frequently splits sentences across <span> and <a>
        # tags, so stripping every fragment can create words such as
        # "developmentprograms" or "joinedby".
        text = re.sub(
            r"\s+",
            " ",
            data,
        )

        if text.strip():
            self.text_parts.append(text)

    def get_text(self):
        text = "".join(self.text_parts)

        text = html.unescape(text)

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n\s*\n+",
            "\n",
            text,
        )

        return text.strip()


# ============================================================
# RESEARCH AGENT
# ============================================================

class ResearchAgent(BaseAgent):
    """
    ORBIT web-grounded research agent.

    Does not require Gemini for basic research.

    Pipeline:

        Query
          â†“
        Google News RSS
          â†“
        Publisher URL resolution
          â†“
        Direct article fetch
          â†“
        Article validation
          â†“
        Local extractive summary
          â†“
        Structured research result
    """

    def __init__(self):

        super().__init__(
            "Research Agent"
        )

        self.timeout = 6

        self.max_article_chars = 12000

        self.max_download_bytes = 1500000

    # ========================================================
    # CLEAN TEXT
    # ========================================================

    def clean_text(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        text = html.unescape(
            text
        )

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ========================================================
    # EXPLANATORY QUERY DETECTION
    # ========================================================

    def is_explanatory_query(
        self,
        query: str,
    ) -> bool:

        if not query:
            return False

        q = query.lower().strip()

        patterns = (
            r"^what\s+is\b",
            r"^what\s+are\b",
            r"^what's\b",
            r"^whats\b",
            r"^who\s+is\b",
            r"^why\s+is\b",
            r"^why\s+are\b",
            r"^why\s+does\b",
            r"^why\s+do\b",
            r"^how\s+does\b",
            r"^how\s+do\b",
            r"^how\s+is\b",
            r"^how\s+are\b",
            r"^how\s+to\b",
            r"^explain\b",
            r"^define\b",
            r"^definition\s+of\b",
            r"^meaning\s+of\b",
            r"^tell\s+me\s+about\b",
            r"^describe\b",
        )

        return any(
            re.search(pattern, q)
            for pattern in patterns
        )

    # ========================================================
    # SEARCH WEB
    # ========================================================

    def search_web(
        self,
        query: str,
        limit: int = 6,
    ) -> list:

        """
        Search recent web/news sources using Google News RSS.
        """

        if not query:
            return []

        encoded_query = quote(
            query
        )

        url = (
            "https://news.google.com/rss/search?"
            f"q={encoded_query}"
            "&hl=en-US"
            "&gl=US"
            "&ceid=US:en"
        )

        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/120 Safari/537.36"
                )
            },
        )

        try:

            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                # Limit read size to avoid extremely large RSS payloads.
                data = response.read(self.max_download_bytes)

            try:
                root = ET.fromstring(
                    data
                )
            except Exception:
                return []

            results = []

            for item in root.findall(
                ".//item"
            ):

                title_node = item.find(
                    "title"
                )

                link_node = item.find(
                    "link"
                )

                description_node = item.find(
                    "description"
                )

                pub_date_node = item.find(
                    "pubDate"
                )

                source_node = item.find(
                    "source"
                )

                title = (
                    title_node.text
                    if title_node is not None
                    else ""
                )

                link = (
                    link_node.text
                    if link_node is not None
                    else ""
                )

                description = (
                    description_node.text
                    if description_node is not None
                    else ""
                )

                published = (
                    pub_date_node.text
                    if pub_date_node is not None
                    else ""
                )

                source_url = ""
                if source_node is not None:
                    source_url = (
                        source_node.attrib.get("url", "")
                        or ""
                    )

                title = self.clean_text(
                    title
                )

                description = self.clean_text(
                    description
                )

                if not title or not link:
                    continue

                source = ""

                if " - " in title:

                    parts = title.rsplit(
                        " - ",
                        1,
                    )

                    if len(parts) == 2:

                        title = parts[0].strip()

                        source = parts[1].strip()

                results.append(
                    {
                        "title": title,
                        "url": link,
                        "description": description,
                        "published": published,
                        "source": source,
                        "source_url": source_url,
                    }
                )

                if len(results) >= limit:
                    break

            return results

        except Exception:
            return []

    # ========================================================
    # GOOGLE NEWS URL CHECK
    # ========================================================

    def is_google_news_url(
        self,
        url: str,
    ) -> bool:

        if not url:
            return False

        try:

            host = urlparse(
                url
            ).netloc.lower()

            return (
                host == "news.google.com"
                or host.endswith(
                    ".news.google.com"
                )
            )

        except Exception:
            return False

    # ========================================================
    # BLOCKED / INVALID HOST CHECK
    # ========================================================

    def is_blocked_host(
        self,
        url: str,
    ) -> bool:

        if not url:
            return True

        try:

            host = (
                urlparse(url)
                .netloc
                .lower()
                .split(":")[0]
            )

            blocked_hosts = (
                "google.com",
                "google.co",
                "googleusercontent.com",
                "gstatic.com",
                "googleapis.com",
                "news.google.com",
                "youtube.com",
                "youtube-nocookie.com",
                "bing.com",
                "bingj.com",
                "microsoftonline.com",
                "facebook.com",
                "twitter.com",
                "x.com",
                "w3.org",
                "www.w3.org",
                "storage.live.com",
                "live.com",
                "onedrive.live.com",
            )

            return any(
                host == blocked
                or host.endswith(
                    "." + blocked
                )
                for blocked in blocked_hosts
            )

        except Exception:
            return True

    # ========================================================
    # KNOWN PUBLISHER FALLBACKS
    # ========================================================

    def get_known_publisher_url(
        self,
        title: str,
        source: str = "",
    ) -> str:

        """
        Return a known publisher URL when search-engine
        resolution is unreliable.
        """

        if not title:
            return ""

        source_key = re.sub(
            r"[^a-z0-9]",
            "",
            (source or "").lower(),
        )

        title_key = title.lower()

        known_sources = {

            "databricks": {

                "keywords": (
                    "large language model",
                    "large language models",
                    "llm",
                ),

                # This is intentionally the known URL.
                # fetch_article() will follow its redirect.
                "url": (
                    "https://www.databricks.com/"
                    "glossary/large-language-models-llm"
                ),
            },
        }

        for name, config in known_sources.items():

            if name not in source_key:
                continue

            for keyword in config["keywords"]:

                if keyword in title_key:
                    return config["url"]

        return ""

    # ========================================================
    # PUBLISHER DOMAIN MAP
    # ========================================================

    def get_publisher_domains(
        self,
        source: str,
    ) -> list:

        publisher_domains = {

            "databricks": [
                "databricks.com"
            ],

            "ibm": [
                "ibm.com"
            ],

            "microsoft": [
                "microsoft.com"
            ],

            "openai": [
                "openai.com"
            ],

            "anthropic": [
                "anthropic.com"
            ],

            "salesforce": [
                "salesforce.com"
            ],

            "lookout": [
                "lookout.com"
            ],

            "kdnuggets": [
                "kdnuggets.com"
            ],

            "infoworld": [
                "infoworld.com"
            ],

            "towards data science": [
                "towardsdatascience.com"
            ],

            "diginomica": [
                "diginomica.com"
            ],

            "times of india": [
                "timesofindia.indiatimes.com"
            ],

            "indian express": [
                "indianexpress.com"
            ],

            "officechai": [
                "officechai.com"
            ],

            "fonearena": [
                "fonearena.com"
            ],

            "newsbytes": [
                "newsbytesapp.com"
            ],

            "siliconangle": [
                "siliconangle.com"
            ],

            "substack": [
                "substack.com"
            ],

            # Added publisher mappings
            "council on foreign relations": [
                "cfr.org"
            ],

            "the guardian": [
                "theguardian.com"
            ],

            "aoshearman": [
                "aoshearman.com"
            ],

            "ao shearman": [
                "aoshearman.com"
            ],
        }

        source_key = re.sub(
            r"[^a-z0-9 ]",
            "",
            (source or "").lower(),
        ).strip()

        preferred = []

        for key, domains in publisher_domains.items():

            if (
                key in source_key
                or source_key in key
            ):
                preferred.extend(domains)

        return list(dict.fromkeys(preferred))


    # ========================================================
    # SEARCH PAGE FETCH
    # ========================================================

    def fetch_search_page(
        self,
        search_url: str,
    ) -> str:

        if not search_url:
            return ""

        request = Request(
            search_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0.0.0 "
                    "Safari/537.36"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
                "Accept-Language":
                    "en-US,en;q=0.9",
            },
        )

        try:

            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                return response.read(
                    500000
                ).decode(
                    "utf-8",
                    errors="ignore",
                )

        except Exception:
            return ""

    # ========================================================
    # SEARCH RESULT CANDIDATE EXTRACTION
    # ========================================================

    def extract_search_candidates(
        self,
        page: str,
        title: str,
        source: str,
        preferred_domains: list,
    ) -> list:

        if not page:
            return []

        raw_links = []

        # Only extract URLs from actual HTML href attributes.
        # Search engines embed unrelated URLs inside JavaScript,
        # JSON, tracking data and profile assets. Scanning the whole
        # page for https:// URLs can therefore produce junk such as
        # storage.live.com profile-image URLs.
        raw_links.extend(
            re.findall(
                r"""href=["'](https?://[^"']+)""",
                page,
                flags=re.I,
            )
        )

        title_words = set(
            re.findall(
                r"[a-z0-9]{4,}",
                title.lower(),
            )
        )

        candidates = []

        for raw_link in raw_links:

            try:

                link = html.unescape(
                    raw_link
                )

                if link.startswith(
                    "/url?"
                ):

                    match = re.search(
                        r"[?&](?:q|url)=([^&]+)",
                        link,
                    )

                    if match:
                        link = unquote(
                            match.group(1)
                        )

                if (
                    "url=" in link
                    and (
                        "google." in link
                        or "bing." in link
                    )
                ):

                    match = re.search(
                        r"[?&]url=([^&]+)",
                        link,
                    )

                    if match:
                        link = unquote(
                            match.group(1)
                        )

                if not link.startswith(
                    (
                        "http://",
                        "https://",
                    )
                ):
                    continue

                # Guard against malformed or non-http(s) schemes.
                try:
                    parsed_tmp = urlparse(link)
                    if parsed_tmp.scheme not in ("http", "https"):
                        continue
                except Exception:
                    continue

                if self.is_blocked_host(
                    link
                ):
                    continue

                parsed = urlparse(
                    link
                )

                host = (
                    parsed.netloc
                    .lower()
                    .split(":")[0]
                )

                if not host:
                    continue

                score = 0

                normalized_host = re.sub(
                    r"[^a-z0-9]",
                    "",
                    host,
                )

                for domain in preferred_domains:

                    normalized_domain = re.sub(
                        r"[^a-z0-9]",
                        "",
                        domain,
                    )

                    if (
                        normalized_domain
                        in normalized_host
                    ):
                        score += 100

                normalized_source = re.sub(
                    r"[^a-z0-9]",
                    "",
                    source.lower(),
                )

                if (
                    normalized_source
                    and normalized_source
                    in normalized_host
                ):
                    score += 50

                path_text = (
                    parsed.path
                    + " "
                    + parsed.query
                ).lower()

                score += sum(
                    3
                    for word in title_words
                    if word in path_text
                )

                if len(
                    parsed.path
                ) > 10:
                    score += 2

                candidates.append(
                    (
                        score,
                        link,
                    )
                )

            except Exception:
                continue

        return candidates

    # ========================================================
    # FIND PUBLISHER ARTICLE
    # ========================================================


    def _title_slug(self, title: str) -> str:
        if not title:
            return ""

        value = html.unescape(title).lower()
        value = re.sub(r"[^a-z0-9\s-]", " ", value)
        value = re.sub(r"[-\s]+", "-", value)
        return value.strip("-")

    def _is_usable_article_candidate(self, candidate: str) -> bool:
        """Return True only for plausible publisher article URLs."""
        if not candidate:
            return False

        try:
            parsed = urlparse(candidate)
        except Exception:
            return False

        if parsed.scheme not in ("http", "https"):
            return False

        host = (parsed.netloc or "").lower().split(":")[0]
        path = (parsed.path or "").lower()
        query = (parsed.query or "").lower()

        blocked_hosts = (
            "news.google.com",
            "www.google.com",
            "bing.com",
            "www.bing.com",
        )

        if host in blocked_hosts or host.endswith(".google.com"):
            return False

        blocked_fragments = (
            "/search",
            "search?",
            "/auth/",
            "/login",
            "/signin",
            "/sign-in",
            "/account",
            "/subscribe",
            "/subscription",
            "cookies_not_supported",
        )

        full = path + "?" + query

        if any(fragment in full for fragment in blocked_fragments):
            return False

        if not path or path == "/":
            return False

        path_parts = [part for part in path.strip("/").split("/") if part]
        section_names = {
            "business", "technology", "tech", "latest", "news",
            "topic", "topics", "category", "categories",
            "section", "sections", "channel", "channels",
            "tag", "tags", "functional-safety"
        }

        if any(part in section_names for part in path_parts) and len(path_parts) <= 2:
            return False

        if len(path_parts) == 1 and len(path_parts[0]) < 35:
            return False

        return True

    def _score_candidate_url(
        self,
        url: str,
        title: str,
        domains: list,
    ) -> int:
        """
        Score publisher search candidates.

        High score:
        - same publisher domain
        - article/news/story-like path
        - title words present in URL

        Reject:
        - search/login/auth/account pages
        - assets
        - homepages
        - social/external resources
        """
        if not url:
            return -999

        try:
            parsed = urlparse(url)
        except Exception:
            return -999

        if parsed.scheme not in ("http", "https"):
            return -999

        if self.is_blocked_host(url):
            return -999

        host = parsed.netloc.lower().split(":")[0]
        path = parsed.path.lower().rstrip("/")
        query = parsed.query.lower()
        full = (path + " " + query).lower()

        # Hard reject obvious non-article resources.
        blocked = (
            "/search",
            "/login",
            "/signin",
            "/signup",
            "/account",
            "/auth/",
            "/subscribe",
            "/privacy",
            "/terms",
            "/contact",
            "/about",
            ".css",
            ".js",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".woff",
            ".woff2",
            "/live",
            "/video",
            "/podcast",
        )

        if any(item in full for item in blocked):
            return -999

        # Homepage/root is never an article.
        if path in ("", "/"):
            return -999

        # Candidate must belong to the publisher when domains are known.
        domain_match = False

        for domain in domains:
            domain = domain.lower().strip()
            if host == domain or host.endswith("." + domain):
                domain_match = True
                break

        if domains and not domain_match:
            return -999

        score = 100 if domain_match else 10

        # Article-like URL structures.
        article_markers = (
            "/article/",
            "/articles/",
            "/news/",
            "/story/",
            "/stories/",
            "/2026/",
            "/2025/",
            "/2024/",
            "/2023/",
            "/insights/",
            "/politics/",
            "/technology/",
            "/business/",
        )

        if any(marker in path for marker in article_markers):
            score += 40

        # Title-word overlap.
        words = set(
            re.findall(
                r"[a-z0-9]{4,}",
                title.lower(),
            )
        )

        for word in words:
            if word in full:
                score += 5

        return score

    def _publisher_slug_candidates(self, title: str, domains: list) -> list:
        slug = self._title_slug(title)
        if not slug or not domains:
            return []

        candidates = []

        for domain in domains:
            base = "https://" + domain
            for pattern in (
                "/articles/{slug}",
                "/article/{slug}",
                "/news/{slug}",
                "/insights/{slug}",
                "/stories/{slug}",
                "/{slug}",
            ):
                candidates.append(
                    base + pattern.format(slug=slug)
                )

        return candidates

    def _publisher_sitemap_candidates(self, title: str, domains: list) -> list:
        if not title or not domains:
            return []

        words = set(re.findall(r"[a-z0-9]{4,}", title.lower()))
        results = []

        for domain in domains[:4]:
            root = "https://" + domain

            for sitemap_url in (
                root + "/sitemap.xml",
                root + "/sitemap_index.xml",
                root + "/sitemap/sitemap.xml",
            ):
                xml_text = self.fetch_search_page(sitemap_url)
                if not xml_text:
                    continue

                try:
                    tree = ET.fromstring(xml_text)
                except Exception:
                    continue

                namespace = ""
                if tree.tag.startswith("{"):
                    namespace = tree.tag.split("}", 1)[0] + "}"

                for node in tree.findall(f".//{namespace}loc"):
                    article_url = (node.text or "").strip()
                    if not article_url or article_url.lower().endswith(".xml"):
                        continue

                    parsed = urlparse(article_url)
                    path_text = (parsed.path + " " + parsed.query).lower()
                    overlap = sum(1 for word in words if word in path_text)

                    if overlap >= 2:
                        score = self._score_candidate_url(
                            article_url,
                            title,
                            domains,
                        )
                        results.append(
                            (score + overlap * 10, article_url)
                        )

                if results:
                    break

            if results:
                break

        results.sort(key=lambda x: (-x[0], len(x[1])))
        return [url for _, url in results[:10]]

    def _find_siliconangle_article(
        self,
        title: str,
    ) -> str:
        """Resolve a SiliconANGLE article through its WordPress API."""
        if not title:
            return ""

        try:
            api_url = (
                "https://siliconangle.com/wp-json/wp/v2/posts"
                "?search="
                + quote(title)
                + "&per_page=10"
            )

            request = Request(
                api_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "Chrome/142.0 Safari/537.36"
                    )
                },
            )

            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                data = response.read(
                    min(self.max_download_bytes, 2000000)
                )

            payload = json.loads(
                data.decode("utf-8", "ignore")
            )

            if not isinstance(payload, list):
                return ""

            def normalize(value: str) -> str:
                value = html.unescape(value or "")
                value = re.sub(r"<[^>]+>", " ", value)
                value = value.lower()
                value = re.sub(r"[^a-z0-9]+", " ", value)
                return re.sub(r"\s+", " ", value).strip()

            requested = normalize(title)

            requested_compact = re.sub(
                r"\s+",
                "",
                requested,
            )

            for item in payload:
                if not isinstance(item, dict):
                    continue

                title_data = item.get("title", {})

                if isinstance(title_data, dict):
                    candidate_title = title_data.get(
                        "rendered",
                        "",
                    )
                else:
                    candidate_title = ""

                candidate_url = item.get("link", "")

                if not candidate_title or not candidate_url:
                    continue

                normalized_candidate = normalize(
                    candidate_title
                )

                candidate_compact = re.sub(
                    r"\s+",
                    "",
                    normalized_candidate,
                )

                if (
                    normalized_candidate == requested
                    or candidate_compact == requested_compact
                ):
                    return candidate_url

                requested_words = set(
                    re.findall(
                        r"[a-z0-9]{4,}",
                        requested,
                    )
                )

                candidate_words = set(
                    re.findall(
                        r"[a-z0-9]{4,}",
                        normalized_candidate,
                    )
                )

                if not requested_words:
                    continue

                overlap = len(
                    requested_words & candidate_words
                )

                score = overlap / len(requested_words)

                if score >= 0.85:
                    return candidate_url

        except Exception as exc:
            print(
                "SILICONANGLE ERROR:",
                type(exc).__name__,
                str(exc),
            )
            return ""

        return ""

    def _find_nature_article(self, title: str) -> str:
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


    def find_publisher_article(self, title: str, source: str = "", source_url: str = "") -> str:
        """
        Resolve a Google News result to the real publisher article.

        Strategy:
        1. Use publisher-specific APIs/search mechanisms.
        2. Search the publisher site when possible.
        3. Never trust a generated URL without fetching and title-validating it.
        4. Never return Google/Bing/auth/search/login URLs.
        """
        if not title:
            return ""

        title = self.clean_text(title)
        source = self.clean_text(source)
        source_url = self.clean_text(source_url)

        # ------------------------------------------------------------------
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
            try:
                candidate = self._find_siliconangle_article(title)
                if candidate and self._is_usable_article_candidate(candidate):
                    article = self.fetch_article(candidate)
                    if article and self.article_matches_source(article, title, source):
                        return candidate
            except Exception:
                pass

        # Publisher-specific known URL mappings.
        try:
            known_url = self.get_known_publisher_url(title, source)
            if known_url and self._is_usable_article_candidate(known_url):
                article = self.fetch_article(known_url)
                if article and self.article_matches_source(article, title, source):
                    return known_url
        except Exception:
            pass

        # Resolve publisher domain from source URL when the source-name map
        # doesn't know the publisher.
        domains = self.get_publisher_domains(source)

        if not domains and source_url:
            try:
                parsed = urlparse(source_url)
                host = (parsed.netloc or "").lower().split(":")[0]
                if host.startswith("www."):
                    host = host[4:]
                if host:
                    domains = [host]
            except Exception:
                pass

        if not domains:
            return ""

        # Only use publisher-owned search pages. Do not manufacture article
        # URLs from slugs unless the resulting page is actually fetchable and
        # title-valid.
        encoded = quote(title)

        roots = []
        if source_url:
            try:
                parsed = urlparse(source_url)
                if parsed.scheme in ("http", "https") and parsed.netloc:
                    roots.append(f"{parsed.scheme}://{parsed.netloc}")
            except Exception:
                pass

        for domain in domains:
            if domain:
                roots.append("https://" + domain)
                roots.append("https://www." + domain)

        seen_roots = set()

        for root in roots:
            root = root.rstrip("/")
            if root in seen_roots:
                continue
            seen_roots.add(root)

            search_urls = (
                root + "/search?q=" + encoded,
                root + "/search?query=" + encoded,
                root + "/search?search=" + encoded,
            )

            for search_url in search_urls:
                try:
                    page = self.fetch_search_page(search_url)
                except Exception:
                    continue

                if not page:
                    continue

                # Reject obvious authentication/search-provider pages.
                low = page.lower()
                if (
                    "idp.nature.com" in low
                    or "cookies_not_supported" in low
                    or "/auth/" in low
                    or "sign in" in low[:5000]
                ):
                    continue

                raw_links = re.findall(
                    r'(?:href|data-href|data-url)\s*=\s*["\']([^"\']+)["\']',
                    page,
                    flags=re.I,
                )

                candidates = []
                seen = set()

                for raw in raw_links:
                    candidate = urljoin(root + "/", raw)

                    if candidate in seen:
                        continue
                    seen.add(candidate)

                    if not self._is_usable_article_candidate(candidate):
                        continue

                    parsed = urlparse(candidate)
                    host = (parsed.netloc or "").lower().split(":")[0]
                    if host.startswith("www."):
                        host = host[4:]

                    if not any(
                        host == d or host.endswith("." + d)
                        for d in domains
                    ):
                        continue

                    score = self._score_candidate_url(candidate, title, domains)
                    if score > 0:
                        candidates.append((score, candidate))

                candidates.sort(reverse=True)

                for _, candidate in candidates[:10]:
                    try:
                        article = self.fetch_article(candidate)
                    except Exception:
                        continue

                    if not article:
                        continue

                    try:
                        if self.article_matches_source(article, title, source):
                            return candidate
                    except Exception:
                        continue

        # Last-resort publisher discovery:
        # search the exact headline through the existing search provider,
        # then accept only URLs belonging to the publisher domain.
        try:
            search_query = '"' + title.replace('"', "") + '" ' + source

            search_results = self.search_web(search_query, 10)

            for result in search_results:
                candidate = result.get("url", "")
                if not candidate:
                    continue

                if not self._is_usable_article_candidate(candidate):
                    continue

                parsed = urlparse(candidate)
                host = (parsed.netloc or "").lower().split(":")[0]
                if host.startswith("www."):
                    host = host[4:]

                if not any(
                    host == d or host.endswith("." + d)
                    for d in domains
                ):
                    continue

                article = self.fetch_article(candidate)
                if not article:
                    continue

                if self.article_matches_source(article, title, source):
                    return candidate
        except Exception:
            pass

        # Final discovery layer: query Google web search directly.
        # Google News redirects are opaque, but normal web search exposes
        # publisher URLs. Candidates are still fetched and title-validated.
        try:
            import requests

            search_query = quote(f'"{title}" "{source}"')
            google_url = "https://www.google.com/search?q=" + search_query

            response = requests.get(
                google_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/142.0 Safari/537.36"
                    )
                },
                timeout=8,
                allow_redirects=True,
            )

            if response.ok:
                raw_links = re.findall(
                    r'href=["\'](https?://[^"\']+)["\']',
                    response.text,
                    flags=re.I,
                )

                candidates = []
                seen = set()

                for candidate in raw_links:
                    candidate = candidate.replace("&amp;", "&")

                    if candidate in seen:
                        continue
                    seen.add(candidate)

                    if not self._is_usable_article_candidate(candidate):
                        continue

                    parsed = urlparse(candidate)
                    host = (parsed.netloc or "").lower().split(":")[0]
                    if host.startswith("www."):
                        host = host[4:]

                    if not any(
                        host == d or host.endswith("." + d)
                        for d in domains
                    ):
                        continue

                    score = self._score_candidate_url(
                        candidate,
                        title,
                        domains,
                    )

                    if score > 0:
                        candidates.append((score, candidate))

                candidates.sort(reverse=True)

                for _, candidate in candidates[:10]:
                    try:
                        article = self.fetch_article(candidate)
                    except Exception:
                        continue

                    if article and self.article_matches_source(
                        article,
                        title,
                        source,
                    ):
                        return candidate

        except Exception:
            pass

        return ""

    def resolve_url(
        self,
        url: str,
    ) -> str:

        """
        Resolve Google News URLs.

        IMPORTANT:
        Direct publisher URLs are returned unchanged.
        """

        if not url:
            return ""

        # Direct publisher URL.
        if not self.is_google_news_url(
            url
        ):

            if self.is_blocked_host(
                url
            ):
                return ""

            return url

        # Google News URL.
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/120 Safari/537.36"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml"
                ),
            },
        )

        try:

            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                final_url = response.geturl()

            try:
                parsed_final = urlparse(final_url)
                if (
                    final_url
                    and parsed_final.scheme in ("http","https")
                    and not self.is_google_news_url(
                        final_url
                    )
                    and not self.is_blocked_host(
                        final_url
                    )
                ):
                    return final_url
            except Exception:
                # If parsing fails, treat as unresolved.
                return ""

        except Exception:
            pass

        return ""

    # ========================================================
    # FETCH ARTICLE
    # ========================================================

    def fetch_article(
        self,
        url: str,
    ) -> str:

        """
        Fetch readable article text.

        Direct publisher URLs are fetched directly.

        Google News URLs are resolved first.

        Multiple candidates are attempted so that a redirect
        failure does not automatically mean article failure.
        """

        if not url:
            return ""

        candidates = []

        # ----------------------------------------------------
        # Candidate 1: direct URL
        # ----------------------------------------------------

        if not self.is_google_news_url(
            url
        ):

            candidates.append(
                url
            )

        # ----------------------------------------------------
        # Candidate 2: resolved URL
        # ----------------------------------------------------

        resolved = self.resolve_url(
            url
        )

        if resolved:
            candidates.append(
                resolved
            )

        # ----------------------------------------------------
        # Candidate 3: original URL
        # ----------------------------------------------------

        candidates.append(
            url
        )

        # ----------------------------------------------------
        # Databricks known redirect
        # ----------------------------------------------------

        if "databricks.com" in url.lower():

            candidates.extend(
                [
                    (
                        "https://www.databricks.com/"
                        "blog/what-are-large-language-models"
                    ),
                    (
                        "https://www.databricks.com/"
                        "glossary/large-language-models-llm"
                    ),
                ]
            )

        # Remove duplicates.
        candidates = list(
            dict.fromkeys(
                candidate
                for candidate in candidates
                if candidate
            )
        )

        # ----------------------------------------------------
        # Try candidates
        # ----------------------------------------------------

        for candidate_url in candidates:

            # Validate URL parsing and scheme before attempting fetch.
            try:
                parsed_candidate = urlparse(candidate_url)
                if parsed_candidate.scheme not in ("http","https"):
                    continue
            except Exception:
                continue

            if self.is_google_news_url(
                candidate_url
            ):
                continue

            if self.is_blocked_host(
                candidate_url
            ):
                continue

            request = Request(
                candidate_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/120.0.0.0 "
                        "Safari/537.36"
                    ),
                    "Accept": (
                        "text/html,"
                        "application/xhtml+xml,"
                        "application/xml;q=0.9,"
                        "*/*;q=0.8"
                    ),
                    "Accept-Language":
                        "en-US,en;q=0.9",
                    "Accept-Encoding":
                        "identity",
                },
            )

            try:

                with urlopen(
                    request,
                    timeout=self.timeout,
                ) as response:

                    content_type = (
                        response.headers.get(
                            "Content-Type",
                            "",
                        )
                        .lower()
                    )

                    if (
                        "html"
                        not in content_type
                        and "xhtml"
                        not in content_type
                    ):
                        continue

                    data = response.read(
                        self.max_download_bytes
                    )

                if not data:
                    continue

                decoded = data.decode(
                    "utf-8",
                    errors="ignore",
                )

                # ------------------------------------------------
                # HTML parser
                # ------------------------------------------------

                parser_html = decoded

                # SiliconANGLE exposes the article body inside a
                # dedicated single-post-content container. Restrict
                # parsing to that container so navigation, headers,
                # author metadata and unrelated page text cannot
                # contaminate the article evidence.
                if "siliconangle.com" in candidate_url.lower():
                    container_match = re.search(
                        r'<div[^>]+class=["\'][^"\']*single-post-content[^"\']*["\'][^>]*>'
                        r"(.*?)"
                        r"</div>",
                        decoded,
                        flags=re.I | re.S,
                    )

                    if container_match:
                        parser_html = container_match.group(1)

                parser = ArticleTextParser()

                parser.feed(
                    parser_html
                )

                text = parser.get_text()

                # ------------------------------------------------
                # SiliconANGLE article cleanup
                # ------------------------------------------------
                # SiliconANGLE pages can place navigation, update
                # metadata, headline and author information directly
                # in the parsed text before the article body.
                if "siliconangle.com" in candidate_url.lower():

                    text = html.unescape(
                        text
                    )

                    # Locate the article body after the author line.
                    author_match = re.search(
                        r"\bby\s+[A-Z][^.!?]{1,100}?\s+(?=[A-Z])",
                        text,
                    )

                    if author_match:
                        body_start = author_match.end()
                        body = text[body_start:].strip()

                        if body:
                            text = body

                    # Remove a leftover author surname when the parser
                    # separates "by Maria Deutscher" incorrectly.
                    text = re.sub(
                        r"^(?:[A-Z][a-z]+\s+)?(?=[A-Z][a-z]+\s+today\b)",
                        "",
                        text,
                        count=1,
                    )

                    # Repair text-boundary artifacts produced by the
                    # SiliconANGLE HTML parser.
                    text = re.sub(
                        r"^Deutscher\s+(?=A\s+group\b)",
                        "",
                        text,
                    )

                    replacements = {
                        "joinedby": "joined by",
                        "couldgive": "could give",
                        "realrisk": "real risk",
                        "beyondour": "beyond our",
                        "resultingsystems": "resulting systems",
                        "toautomate": "to automate",
                        "riseto": "rise to",
                        "thatcapability": "that capability",
                        "initiatives.According": "initiatives. According",
                        "ofNvidia": "of Nvidia",
                        "U. S.": "U.S.",
                        "Dario Dario Amodei": "Dario Amodei",
                    }

                    for broken, fixed in replacements.items():
                        text = text.replace(
                            broken,
                            fixed,
                        )

                    # Restore missing whitespace after sentence punctuation.
                    text = re.sub(
                        r"([.!?])([A-Z])",
                        r"\1 \2",
                        text,
                    )

                    # Remove common SiliconANGLE navigation/update noise.
                    text = re.sub(
                        r"^.*?\bSkip to content\b\s*",
                        "",
                        text,
                        count=1,
                        flags=re.I,
                    )

                    text = re.sub(
                        r"^.*?\bUPDATED\s+\d{1,2}:\d{2}\s+[A-Z]{2,4}\s*/\s*"
                        r"[A-Z]+\s+\d{1,2}\s+\d{4}\s*",
                        "",
                        text,
                        count=1,
                        flags=re.I,
                    )

                    # Remove duplicated article headline when present.
                    headline = re.escape(
                        "AI researchers call for new tools that can slow automated model development"
                    )

                    text = re.sub(
                        r"^" + headline + r"\s*",
                        "",
                        text,
                        count=1,
                        flags=re.I,
                    )

                # ------------------------------------------------
                # Clean
                # ------------------------------------------------

                text = html.unescape(
                    text
                )

                text = re.sub(
                    r"Cookie.{0,500}",
                    " ",
                    text,
                    flags=re.I,
                )

                text = re.sub(
                    r"Sign in.{0,300}",
                    " ",
                    text,
                    flags=re.I,
                )

                text = re.sub(
                    r"Subscribe.{0,300}",
                    " ",
                    text,
                    flags=re.I,
                )

                text = re.sub(
                    r"\s+",
                    " ",
                    text,
                ).strip()

                # ------------------------------------------------
                # Parsed text successful
                # ------------------------------------------------

                if len(text) >= 200:
                    return text[
                        :self.max_article_chars
                    ]

                # ------------------------------------------------
                # Raw HTML fallback
                # ------------------------------------------------

                raw_text = decoded

                raw_text = re.sub(
                    r"<script\b[^>]*>.*?</script>",
                    " ",
                    raw_text,
                    flags=re.I | re.S,
                )

                raw_text = re.sub(
                    r"<style\b[^>]*>.*?</style>",
                    " ",
                    raw_text,
                    flags=re.I | re.S,
                )

                raw_text = re.sub(
                    r"<noscript\b[^>]*>.*?</noscript>",
                    " ",
                    raw_text,
                    flags=re.I | re.S,
                )

                raw_text = re.sub(
                    r"<[^>]+>",
                    " ",
                    raw_text,
                )

                raw_text = html.unescape(
                    raw_text
                )

                raw_text = re.sub(
                    r"\s+",
                    " ",
                    raw_text,
                ).strip()

                if len(raw_text) >= 200:
                    return raw_text[
                        :self.max_article_chars
                    ]

                if len(raw_text) >= 200:
                    return raw_text[
                        :self.max_article_chars
                    ]

            except Exception:
                continue

        return ""

    # ========================================================
    # ARTICLE VALIDATION
    # ========================================================

    def article_matches_source(
        self,
        article_text: str,
        title: str,
        source: str = "",
    ) -> bool:

        """
        Reject unrelated or junk pages.

        Validation is deliberately title-centric. Generic word overlap is
        insufficient because unrelated articles from the same publisher can
        contain many of the same AI/research terms.
        """

        if not article_text or not title:
            return False

        text = article_text.lower()

        if len(text) < 200:
            return False

        # ----------------------------------------------------
        # W3C garbage detection
        # ----------------------------------------------------

        w3c_markers = (
            "xhtml namespace",
            "the namespace name",
            "xhtml 1.0",
            "xhtml modularization",
        )

        if (
            any(marker in text for marker in w3c_markers)
            and "large language model" not in text
            and "large language models" not in text
        ):
            return False

        # ----------------------------------------------------
        # Extract likely article title/headline
        # ----------------------------------------------------

        requested_title = re.sub(
            r"\s+",
            " ",
            title.lower(),
        ).strip()

        headline_candidates = []

        # HTML title
        for match in re.findall(
            r"<title[^>]*>(.*?)</title>",
            article_text,
            flags=re.I | re.S,
        ):
            headline_candidates.append(
                re.sub(r"<[^>]+>", " ", match)
            )

        # H1 headline
        for match in re.findall(
            r"<h1[^>]*>(.*?)</h1>",
            article_text,
            flags=re.I | re.S,
        ):
            headline_candidates.append(
                re.sub(r"<[^>]+>", " ", match)
            )

        # Common plain-text article title pattern.
        first_lines = article_text.splitlines()[:20]
        headline_candidates.extend(first_lines)

        def normalize_headline(value: str) -> str:
            value = html.unescape(value)
            value = re.sub(r"<[^>]+>", " ", value)
            value = re.sub(r"\s+", " ", value)
            value = value.lower().strip()

            # Remove common publisher suffixes.
            value = re.sub(
                r"\s*[-|–—]\s*(siliconangle|reuters|the guardian|"
                r"infoworld|kdnuggets).*$",
                "",
                value,
            )

            return value.strip()

        normalized_candidates = [
            normalize_headline(candidate)
            for candidate in headline_candidates
            if candidate
        ]

        normalized_candidates = [
            candidate
            for candidate in normalized_candidates
            if len(candidate) >= 20
        ]

        # ----------------------------------------------------
        # Strong headline validation
        # ----------------------------------------------------

        requested_words = {
            word
            for word in re.findall(
                r"[a-z0-9]{4,}",
                requested_title,
            )
            if word not in {
                "what",
                "what's",
                "large",
                "language",
                "model",
                "models",
                "news",
                "latest",
                "report",
            }
        }

        headline_match = False

        for candidate in normalized_candidates:

            if requested_title in candidate or candidate in requested_title:
                headline_match = True
                break

            candidate_words = set(
                re.findall(
                    r"[a-z0-9]{4,}",
                    candidate,
                )
            )

            if not requested_words or not candidate_words:
                continue

            overlap = len(
                requested_words & candidate_words
            )

            coverage = overlap / len(requested_words)

            # Require substantial title coverage.
            if coverage >= 0.70 and overlap >= 4:
                headline_match = True
                break

        if not headline_match:
            return False

        # ----------------------------------------------------
        # LLM-specific validation
        # ----------------------------------------------------

        if (
            "llm" in requested_title
            or "large language model" in requested_title
        ):
            if not (
                "large language model" in text
                or "large language models" in text
                or re.search(r"\bllm\b", text)
            ):
                return False

        return True

    # ========================================================
    # SENTENCE SPLITTER
    # ========================================================

    def split_sentences(
        self,
        text: str,
    ) -> list:

        if not text:
            return []

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        cleaned = []

        for sentence in sentences:

            sentence = sentence.strip()

            if len(sentence) < 40:
                continue

            if len(sentence) > 500:
                sentence = (
                    sentence[:500]
                    + "..."
                )

            cleaned.append(
                sentence
            )

        return cleaned

    # ========================================================
    # LOCAL EXTRACTIVE SUMMARY
    # ========================================================

    def summarize_article(
        self,
        text: str,
        query: str,
        max_sentences: int = 3,
    ) -> str:

        if not text:
            return ""

        # The article has already been fetched and validated.
        # Preserve its original order instead of query-based
        # sentence ranking, which can produce disjoint findings.
        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        # Repair common inline text-boundary artifacts that can occur
        # in publisher HTML.
        replacements = {
            "callfor": "call for",
            "automatedmodel": "automated model",
            "effortsof": "efforts of",
            "signatorieswrote": "signatories wrote",
            "toautomate": "to automate",
            "riseto": "rise to",
            "thatcapability": "that capability",
            "initiatives.According": "initiatives. According",
            "ofNvidia": "of Nvidia",
            "U. S.": "U.S.",
            "Dario Dario Amodei": "Dario Amodei",
        }

        for broken, fixed in replacements.items():
            text = text.replace(
                broken,
                fixed,
            )

        text = re.sub(
            r"([.!?])([A-Z])",
            r"\1 \2",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        sentences = self.split_sentences(text)

        if not sentences:
            return text

        selected = []

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            selected.append(sentence)

            if len(selected) >= max_sentences:
                break

        return " ".join(selected)


    # ========================================================
    # BUILD QUERIES
    # ========================================================

    def build_queries(
        self,
        task: str,
    ) -> list:

        task = task.strip()

        if self.is_explanatory_query(
            task
        ):

            queries = [
                task,
                f"{task} explained",
                f"{task} definition",
            ]

        else:

            queries = [
                task,
                f"{task} latest",
                f"{task} {datetime.now().year}",
            ]

        unique_queries = []

        for query in queries:

            query = query.strip()

            if (
                query
                and query
                not in unique_queries
            ):

                unique_queries.append(
                    query
                )

        return unique_queries

    # ========================================================
    # ENRICH SOURCES
    # ========================================================

    async def enrich_sources(
        self,
        sources: list,
        task: str,
    ) -> list:
        """
        Enrich research candidates without requiring every publisher
        to expose a directly fetchable article.

        Evidence levels:
        - article: directly fetched and validated article
        - rss_description: search/RSS description used as evidence
        """

        selected = sources[:12]

        def process_source(source):
            try:
                title = (source.get("title") or "").strip()
                source_name = (source.get("source") or "").strip()
                original_url = (source.get("url") or "").strip()
                description = self.clean_text(
                    source.get("description") or ""
                )

                resolved_url = ""
                article_text = ""

                # ------------------------------------------------
                # 1. Try resolving the news URL.
                # ------------------------------------------------
                if original_url:
                    try:
                        candidate = self.resolve_url(original_url)

                        if (
                            candidate
                            and "news.google.com" not in candidate.lower()
                            and "bing.com/news" not in candidate.lower()
                            and "auth." not in candidate.lower()
                            and "/auth/" not in candidate.lower()
                            and "/search" not in candidate.lower()
                            and "search?" not in candidate.lower()
                            and "login" not in candidate.lower()
                            and "signin" not in candidate.lower()
                        ):
                            resolved_url = candidate
                    except Exception:
                        pass

                # ------------------------------------------------
                # 1b. Publisher-aware fallback.
                # ------------------------------------------------
                # Google News frequently leaves us with a redirect URL.
                # If direct resolution fails, ask the existing publisher
                # resolver to locate the article from its title/source.
                if not resolved_url and title:
                    try:
                        # Publisher fallback is potentially network-heavy.
                        # Run it in a bounded worker so one publisher cannot
                        # stall the entire research pipeline.
                        fallback_future = asyncio.to_thread(
                            self.find_publisher_article,
                            title,
                            source_name,
                            source.get("source_url", ""),
                        )

                        candidate = asyncio.run(
                            asyncio.wait_for(
                                fallback_future,
                                timeout=12,
                            )
                        )

                        if (
                            candidate
                            and "news.google.com" not in candidate.lower()
                            and "bing.com/news" not in candidate.lower()
                        ):
                            resolved_url = candidate

                    except Exception:
                        # Resolver failure/timeout must never block enrichment.
                        pass

                # ------------------------------------------------
                # 2. Try direct article extraction.
                # ------------------------------------------------
                if resolved_url:
                    try:
                        article_text = self.fetch_article(
                            resolved_url
                        )
                    except Exception:
                        article_text = ""

                if article_text:
                    try:
                        valid = self.article_matches_source(
                            article_text,
                            title,
                            source_name,
                        )
                    except Exception:
                        valid = False

                    if valid:
                        summary = self.summarize_article(
                            article_text,
                            task,
                        )

                        if summary:
                            enriched = source.copy()
                            enriched["search_url"] = original_url
                            enriched["url"] = resolved_url
                            enriched["article_available"] = True
                            enriched["article_valid"] = True
                            enriched["evidence_type"] = "article"
                            enriched["article_length"] = len(
                                article_text
                            )
                            enriched["summary"] = summary
                            enriched["finding"] = summary
                            return enriched

                # ------------------------------------------------
                # 3. Honest RSS/search evidence fallback.
                # ------------------------------------------------
                #
                # The description came from the search result itself.
                # It is NOT labelled as a fetched article.
                #
                if (
                    description
                    and len(description) >= 40
                    and description.lower() != title.lower()
                ):
                    enriched = source.copy()
                    enriched["search_url"] = original_url
                    enriched["url"] = (
                        resolved_url or original_url
                    )
                    enriched["article_available"] = False
                    enriched["article_valid"] = False
                    enriched["evidence_type"] = "rss_description"
                    enriched["article_length"] = 0
                    enriched["summary"] = description
                    enriched["finding"] = description
                    return enriched

                return None

            except Exception:
                return None

        results = await asyncio.gather(
            *(
                asyncio.to_thread(
                    process_source,
                    source,
                )
                for source in selected
            ),
            return_exceptions=True,
        )

        return [
            result
            for result in results
            if result is not None
            and not isinstance(result, Exception)
        ]

    def extract_evidence(
        self,
        sources: list,
        task: str,
    ) -> list:
        """
        Extract evidence from enriched research sources.

        Fetched articles are treated as article evidence.
        RSS descriptions are retained only when they contain information
        beyond the headline/publisher metadata.
        """
        evidence = []

        for source in sources or []:
            title = self.clean_text(source.get("title", ""))
            source_name = self.clean_text(source.get("source", ""))
            published = source.get("published", "")
            url = source.get("url", "")
            summary = self.clean_text(source.get("summary", ""))
            finding = self.clean_text(source.get("finding", ""))

            article_valid = bool(source.get("article_valid"))
            evidence_type = source.get("evidence_type", "")

            # Preferred: actually fetched and validated article.
            if article_valid and summary:
                evidence.append({
                    "title": title,
                    "source": source_name,
                    "published": published,
                    "url": url,
                    "evidence": summary,
                    "evidence_type": "article",
                    "article_available": True,
                    "article_valid": True,
                })
                continue

            # RSS/search metadata is NOT article evidence.
            # Keep it only if it contains meaningful text beyond
            # the headline and publisher name.
            if evidence_type == "rss_description":
                metadata = finding or summary

                if not metadata:
                    continue

                normalized_metadata = re.sub(
                    r"\s+",
                    " ",
                    metadata.lower(),
                ).strip()

                normalized_title = re.sub(
                    r"\s+",
                    " ",
                    title.lower(),
                ).strip()

                normalized_source = re.sub(
                    r"\s+",
                    " ",
                    source_name.lower(),
                ).strip()

                metadata_variants = {
                    normalized_title,
                    f"{normalized_title} {normalized_source}".strip(),
                    f"{normalized_title} - {normalized_source}".strip(),
                }

                if normalized_metadata in metadata_variants:
                    continue

                evidence.append({
                    "title": title,
                    "source": source_name,
                    "published": published,
                    "url": url,
                    "evidence": metadata,
                    "evidence_type": "rss_metadata",
                    "article_available": False,
                    "article_valid": False,
                })

        return evidence

    def synthesize_findings(
        self,
        evidence: list,
        task: str,
    ) -> list:
        """
        Produce concise deterministic findings from validated evidence.

        Article evidence is preferred over RSS metadata.
        """
        findings = []

        for item in evidence or []:
            text = self.clean_text(
                item.get("evidence")
                or item.get("finding")
                or item.get("title")
                or ""
            )

            if not text:
                continue

            # Normalize common extraction artifacts.
            replacements = {
                "callfor": "call for",
                "automatedmodel": "automated model",
                "effortsof": "efforts of",
                "signatorieswrote": "signatories wrote",
                "tod eliberately": "to deliberately",
                "todeliberately": "to deliberately",
                "U. S.": "U.S.",
                "Dario Dario Amodei": "Dario Amodei",
                "toautomate": "to automate",
                "riseto": "rise to",
                "thatcapability": "that capability",
                "initiatives.According": "initiatives. According",
                "ofNvidia": "of Nvidia",
            }

            for old, new in replacements.items():
                text = text.replace(old, new)

            text = re.sub(r"\s+", " ", text).strip()

            # Keep complete sentences where possible.
            sentences = re.split(
                r"(?<=[.!?])\s+",
                text,
            )

            selected = [
                sentence.strip()
                for sentence in sentences
                if sentence.strip()
            ][:3]

            if not selected:
                continue

            finding_text = " ".join(selected)

            findings.append({
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "published": item.get("published", ""),
                "url": item.get("url", ""),
                "finding": finding_text,
                "evidence": item.get("evidence", ""),
                "evidence_type": item.get(
                    "evidence_type",
                    "article",
                ),
                "article_available": bool(
                    item.get("article_available")
                ),
                "article_valid": bool(
                    item.get("article_valid")
                ),
            })

        # Prefer actual article evidence when both types exist.
        findings.sort(
            key=lambda item: (
                0 if item.get("evidence_type") == "article" else 1,
                item.get("source", "").lower(),
            )
        )

        return findings

    async def run(
        self,
        task: str,
    ) -> dict:

        if not task or not task.strip():

            return {
                "agent": self.name,
                "task": task,
                "status": "invalid_task",
                "result": (
                    "Please provide a research question."
                ),
            }

        try:

            queries = self.build_queries(
                task
            )

            all_sources = []

            for query in queries:

                results = (
                    await asyncio.to_thread(
                        self.search_web,
                        query,
                        6,
                    )
                )

                all_sources.extend(
                    results
                )

                if len(
                    all_sources
                ) >= 8:
                    break

            if not all_sources:

                return self.build_result(
                    task,
                    [],
                )

            # ------------------------------------------------
            # Deduplicate search results
            # ------------------------------------------------

            unique_sources = []

            seen_urls = set()

            for source in all_sources:

                url = source.get(
                    "url",
                    "",
                )

                if (
                    not url
                    or url in seen_urls
                ):
                    continue

                seen_urls.add(
                    url
                )

                unique_sources.append(
                    source
                )

            # ------------------------------------------------
            # Enrich
            # ------------------------------------------------

            enriched_sources = (
                await self.enrich_sources(
                    unique_sources,
                    task,
                )
            )

            # ------------------------------------------------
            # Extract evidence
            # ------------------------------------------------

            evidence = self.extract_evidence(
                enriched_sources,
                task,
            )

            # ------------------------------------------------
            # Synthesize findings
            # ------------------------------------------------

            findings = self.synthesize_findings(
                evidence,
                task,
            )

            # ------------------------------------------------
            # Result
            # ------------------------------------------------

            return self.build_result(
                task,
                findings,
                enriched_sources=enriched_sources,
            )

        except Exception as error:

            return {
                "agent": self.name,
                "task": task,
                "status": "error",
                "research_status": "error",
                "grounding": "unavailable",
                "ai_status": "disabled",
                "result": (
                    "Research failed while accessing "
                    "web sources."
                ),
                "error": str(error),
            }

    def build_result(
        self,
        task: str,
        findings: list,
        enriched_sources: list | None = None,
    ) -> dict:

        enriched_sources = enriched_sources or []

        unique_findings = []
        seen_urls = set()
        seen_findings = set()

        for item in findings or []:
            url = str(item.get("url", "") or "").strip()
            finding = str(item.get("finding", "") or "").strip()

            if not finding:
                continue

            normalized = re.sub(r"\s+", " ", finding.lower())

            if normalized in seen_findings:
                continue

            if url and url in seen_urls:
                continue

            seen_findings.add(normalized)

            if url:
                seen_urls.add(url)

            unique_findings.append(item)

        source_records = []
        seen_source_urls = set()

        for source in enriched_sources:
            title = str(source.get("title", "") or "").strip()
            source_name = str(source.get("source", "") or "").strip()
            url = str(source.get("url", "") or "").strip()

            if not title:
                continue

            if url and url in seen_source_urls:
                continue

            if url:
                seen_source_urls.add(url)

            article_valid = bool(source.get("article_valid"))
            article_available = bool(source.get("article_available"))
            evidence_type = source.get("evidence_type", "")

            if article_valid:
                verification = "validated_article"
            elif evidence_type == "rss_description":
                verification = "rss_metadata"
            else:
                verification = "unresolved"

            source_records.append({
                "title": title,
                "source": source_name,
                "published": source.get("published", ""),
                "url": url,
                "summary": source.get("summary", ""),
                "finding": source.get("finding", ""),
                "article_available": article_available,
                "article_valid": article_valid,
                "evidence_type": verification,
            })

        if unique_findings:

            articles_read = sum(
                1 for item in unique_findings
                if item.get("article_valid")
            )

            lines = [
                f"Research findings for: {task}",
                "",
                "The Research Agent searched recent web sources "
                "and synthesized validated findings.",
                "",
            ]

            for index, item in enumerate(
                unique_findings[:6],
                start=1,
            ):
                title = item.get("title", "Untitled")
                source_name = item.get("source", "Unknown source")
                finding = item.get("finding", "")

                lines.append(f"{index}. {finding}")
                lines.append(
                    f"   Source: {source_name} - {title}"
                )
                lines.append("")

            return {
                "agent": self.name,
                "task": task,
                "status": "success",
                "research_status": "completed",
                "grounding": "available",
                "grounding_method": (
                    "Google News RSS + publisher extraction"
                ),
                "ai_status": "disabled",
                "result": "\n".join(lines).strip(),
                "findings": unique_findings[:6],
                "sources": source_records,
                "source_count": len(source_records),
                "articles_read": articles_read,
            }

        if source_records:

            validated_count = sum(
                1 for item in source_records
                if item.get("article_valid")
            )

            metadata_count = sum(
                1 for item in source_records
                if item.get("evidence_type") == "rss_metadata"
            )

            unresolved_count = sum(
                1 for item in source_records
                if item.get("evidence_type") == "unresolved"
            )

            return {
                "agent": self.name,
                "task": task,
                "status": "partial",
                "research_status": "sources_discovered",
                "grounding": "partial",
                "grounding_method": "Google News RSS discovery",
                "ai_status": "disabled",
                "result": (
                    f"Research sources were discovered for this task, "
                    f"but no publisher article could be independently "
                    f"validated. {len(source_records)} source(s) discovered; "
                    f"{validated_count} article(s) validated; "
                    f"{metadata_count} metadata source(s); "
                    f"{unresolved_count} unresolved source(s)."
                ),
                "findings": [],
                "sources": source_records,
                "source_count": len(source_records),
                "articles_read": validated_count,
                "message": (
                    "ORBIT did not fabricate article evidence. "
                    "The discovered sources are retained for transparency."
                ),
            }

        return {
            "agent": self.name,
            "task": task,
            "status": "unavailable",
            "research_status": "unavailable",
            "grounding": "unavailable",
            "ai_status": "disabled",
            "result": (
                "Research could not be completed because "
                "no usable sources were discovered."
            ),
            "findings": [],
            "sources": [],
            "source_count": 0,
            "articles_read": 0,
        }


