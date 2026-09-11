import asyncio
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

        text = data.strip()

        if text:
            self.text_parts.append(text + " ")

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

        self.timeout = 15

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

            "substack": [
                "substack.com"
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
                preferred.extend(
                    domains
                )

        return list(
            dict.fromkeys(
                preferred
            )
        )

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
                r'href=["\']([^"\']+)["\']',
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

    def _score_candidate_url(self, url: str, title: str, domains: list) -> int:
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
        score = 0

        for domain in domains:
            domain = domain.lower().strip()
            if host == domain or host.endswith("." + domain):
                score += 100
                break

        path_text = (parsed.path + " " + parsed.query).lower()
        words = set(re.findall(r"[a-z0-9]{4,}", title.lower()))

        for word in words:
            if word in path_text:
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

    def find_publisher_article(
        self,
        title: str,
        source: str = "",
        source_url: str = "",
    ) -> str:
        if not title:
            return ""

        title = title.strip()
        source = (source or "").strip()
        source_url = (source_url or "").strip()

        known_url = self.get_known_publisher_url(title, source)
        if known_url:
            return known_url

        domains = self.get_publisher_domains(source)

        # Deterministic title-slug fast path. CFR uses /articles/<slug>.
        for candidate in self._publisher_slug_candidates(title, domains):
            if "/articles/" in candidate:
                return candidate

        # Sitemap discovery is much more stable than SERP HTML scraping.
        sitemap_candidates = self._publisher_sitemap_candidates(
            title,
            domains,
        )
        if sitemap_candidates:
            return sitemap_candidates[0]

        roots = []
        if source_url:
            try:
                parsed = urlparse(source_url)
                if (
                    parsed.scheme in ("http", "https")
                    and not self.is_blocked_host(source_url)
                ):
                    roots.append(
                        parsed.scheme + "://" + parsed.netloc
                    )
            except Exception:
                pass

        for domain in domains:
            root = "https://" + domain
            if root not in roots:
                roots.append(root)

        encoded = quote(title)

        for root in roots[:4]:
            for search_url in (
                root + "/search?q=" + encoded,
                root + "/search?query=" + encoded,
                root + "/search?search=" + encoded,
            ):
                page = self.fetch_search_page(search_url)
                if not page:
                    continue

                raw_links = re.findall(
                    r"(?:href|data-href|data-url)\s*=\s*[\"']([^\"']+)[\"']",
                    page,
                    flags=re.I,
                )

                scored = []

                for raw in raw_links:
                    try:
                        link = urljoin(
                            search_url,
                            html.unescape(raw).strip(),
                        )
                        score = self._score_candidate_url(
                            link,
                            title,
                            domains,
                        )
                        if score > 0:
                            scored.append((score, link))
                    except Exception:
                        continue

                if scored:
                    scored.sort(key=lambda x: (-x[0], len(x[1])))
                    return scored[0][1]

        # Final fallback to existing search-engine extraction.
        if domains:
            domain_query = " OR ".join(
                "site:" + domain for domain in domains
            )
            query = '"' + title + '" (' + domain_query + ")"
        elif source:
            query = '"' + title + '" "' + source + '"'
        else:
            query = '"' + title + '"'

        for engine_url in (
            "https://www.google.com/search?q=" + quote(query),
            "https://www.bing.com/search?q=" + quote(query),
        ):
            page = self.fetch_search_page(engine_url)
            candidates = self.extract_search_candidates(
                page,
                title,
                source,
                domains,
            )
            candidates.sort(key=lambda x: (-x[0], len(x[1])))

            for _, link in candidates:
                host = urlparse(link).netloc.lower()
                if not domains or any(
                    host == domain or host.endswith("." + domain)
                    for domain in domains
                ):
                    return link

        return ""

    # ========================================================
    # RESOLVE SOURCE URL
    # ========================================================

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

                parser = ArticleTextParser()

                parser.feed(
                    decoded
                )

                text = parser.get_text()

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

        Example:
        W3C XHTML namespace content must not be treated as
        an LLM article.
        """

        if not article_text:
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
            any(
                marker in text
                for marker in w3c_markers
            )
            and "large language model" not in text
            and "large language models" not in text
        ):
            return False

        # ----------------------------------------------------
        # LLM-specific validation
        # ----------------------------------------------------

        title_lower = title.lower()

        if (
            "llm" in title_lower
            or "large language model" in title_lower
        ):

            if not (
                "large language model" in text
                or "large language models" in text
                or re.search(
                    r"\bllm\b",
                    text,
                )
            ):
                return False

        # ----------------------------------------------------
        # Title overlap
        # ----------------------------------------------------

        title_words = [
            word
            for word in re.findall(
                r"[a-z0-9]{4,}",
                title_lower,
            )
            if word not in {
                "what",
                "what's",
                "large",
                "language",
                "model",
                "models",
            }
        ]

        if title_words:

            overlap = sum(
                1
                for word in title_words
                if word in text
            )

            if overlap == 0:
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

        sentences = (
            self.split_sentences(
                text
            )
        )

        if not sentences:
            return ""

        query_words = set(
            re.findall(
                r"[a-zA-Z]{4,}",
                query.lower(),
            )
        )

        stop_words = {
            "what",
            "what's",
            "latest",
            "developments",
            "about",
            "with",
            "from",
            "that",
            "this",
            "into",
            "their",
            "there",
            "which",
            "have",
            "been",
            "will",
            "could",
            "would",
            "should",
            "does",
            "doesn't",
            "using",
            "based",
            "explained",
            "definition",
        }

        query_words -= stop_words

        scored = []

        for index, sentence in enumerate(
            sentences
        ):

            sentence_words = set(
                re.findall(
                    r"[a-zA-Z]{4,}",
                    sentence.lower(),
                )
            )

            overlap = (
                query_words
                & sentence_words
            )

            score = (
                len(overlap)
                * 3
            )

            score += max(
                0,
                3 - index,
            )

            if len(sentence) > 350:
                score -= 1

            scored.append(
                (
                    score,
                    index,
                    sentence,
                )
            )

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected = scored[
            :max_sentences
        ]

        selected.sort(
            key=lambda item: item[1]
        )

        return " ".join(
            item[2]
            for item in selected
        )

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

        enriched = []

        for source in sources[:6]:

            title = source.get(
                "title",
                "",
            )

            source_name = source.get(
                "source",
                "",
            )

            original_url = source.get(
                "url",
                "",
            )

            # ------------------------------------------------
            # 1. Resolve Google News
            # ------------------------------------------------

            resolved_url = (
                await asyncio.to_thread(
                    self.resolve_url,
                    original_url,
                )
            )

            # ------------------------------------------------
            # 2. Publisher fallback
            # ------------------------------------------------

            if not resolved_url:

                resolved_url = (
                    await asyncio.to_thread(
                        self.find_publisher_article,
                        title,
                        source_name,
                        source_url,
                    )
                )

            # ------------------------------------------------
            # 3. Fetch
            # ------------------------------------------------

            article_text = ""

            if resolved_url:

                article_text = (
                    await asyncio.to_thread(
                        self.fetch_article,
                        resolved_url,
                    )
                )

            # ------------------------------------------------
            # 4. Validate
            # ------------------------------------------------

            article_valid = (
                self.article_matches_source(
                    article_text,
                    title,
                    source_name,
                )
            )

            if not article_valid:
                article_text = ""

            # ------------------------------------------------
            # 5. Summary
            # ------------------------------------------------

            summary = ""

            if article_text:

                summary = (
                    self.summarize_article(
                        article_text,
                        task,
                    )
                )

            enriched_source = source.copy()

            enriched_source[
                "search_url"
            ] = original_url

            enriched_source[
                "url"
            ] = (
                resolved_url
                if (
                    resolved_url
                    and not self.is_blocked_host(
                        resolved_url
                    )
                )
                else original_url
            )

            enriched_source[
                "article_available"
            ] = bool(
                article_text
            )

            enriched_source[
                "article_valid"
            ] = article_valid

            enriched_source[
                "article_length"
            ] = len(
                article_text
            )

            if summary:

                enriched_source[
                    "summary"
                ] = summary

            else:

                enriched_source[
                    "summary"
                ] = (
                    "Article content could not be "
                    "extracted or validated."
                )

            enriched.append(
                enriched_source
            )

        return enriched

    # ========================================================
    # BUILD RESULT
    # ========================================================

    def build_result(
        self,
        task: str,
        sources: list,
    ) -> dict:

        if not sources:

            return {
                "agent": self.name,
                "task": task,
                "status": "unavailable",
                "research_status": "unavailable",
                "grounding": "unavailable",
                "ai_status": "disabled",
                "result": (
                    "Research could not be completed "
                    "because no web sources were returned."
                ),
                "sources": [],
                "source_count": 0,
                "articles_read": 0,
            }

        unique_sources = []

        seen_urls = set()

        for source in sources:

            url = source.get(
                "url",
                "",
            )

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(
                url
            )

            # Only validated article content is presented as a
            # research finding. Search candidates that could not
            # be fetched or validated are not promoted to findings.
            if not source.get(
                "article_valid",
                False,
            ):
                continue

            unique_sources.append(
                source
            )

        valid_article_count = sum(
            1
            for source in unique_sources
            if (
                source.get(
                    "article_available",
                    False,
                )
                and source.get(
                    "article_valid",
                    False,
                )
            )
        )

        # If search returned candidates but none survived article
        # validation, do not manufacture a research report.
        if not unique_sources:
            return {
                "agent": self.name,
                "task": task,
                "status": "unavailable",
                "research_status": "unavailable",
                "grounding": "available",
                "grounding_method": (
                    "Google News RSS + publisher extraction"
                ),
                "ai_status": "disabled",
                "result": (
                    "Search returned web sources, but none of the "
                    "article pages could be fetched and validated."
                ),
                "sources": [],
                "source_count": 0,
                "articles_read": 0,
                "message": (
                    "Research candidates were found, but no "
                    "validated article content was available."
                ),
            }

        lines = [
            f"Research findings for: {task}",
            "",
        ]

        if valid_article_count:

            lines.append(
                "The Research Agent searched recent "
                "web sources and extracted findings "
                "from validated article content."
            )

        else:

            lines.append(
                "The Research Agent searched recent "
                "web sources, but no article content "
                "could be reliably validated."
            )

        lines.append("")

        for index, source in enumerate(
            unique_sources[:6],
            start=1,
        ):

            title = source.get(
                "title",
                "Untitled",
            )

            source_name = source.get(
                "source",
                "",
            )

            published = source.get(
                "published",
                "",
            )

            summary = source.get(
                "summary",
                "",
            )

            lines.append(
                f"{index}. {title}"
            )

            if source_name:

                lines.append(
                    f"   Source: {source_name}"
                )

            if published:

                lines.append(
                    f"   Published: {published}"
                )

            if summary:

                lines.append(
                    f"   Finding: {summary}"
                )

            lines.append("")

        lines.append(
            "Sources:"
        )

        for index, source in enumerate(
            unique_sources[:6],
            start=1,
        ):

            source_url = source.get(
                "url",
                "",
            )

            lines.append(
                f"{index}. "
                f"{source.get('title', 'Source')} "
                f"- {source_url}"
            )

        return {
            "agent": self.name,
            "task": task,
            "status": "completed",
            "research_status": "available",
            "grounding": "available",
            "grounding_method": (
                "Google News RSS + publisher extraction"
            ),
            "ai_status": "disabled",
            "result": "\n".join(lines),
            "sources": unique_sources[:6],
            "source_count": len(
                unique_sources[:6]
            ),
            "articles_read": valid_article_count,
            "message": (
                "Research completed using web search "
                "and local article extraction without Gemini."
            ),
        }

    # ========================================================
    # MAIN RUN
    # ========================================================

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
            # Result
            # ------------------------------------------------

            return self.build_result(
                task,
                enriched_sources,
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
        