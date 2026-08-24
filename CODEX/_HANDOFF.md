# ORBIT — Codex Project Handoff

> **Scope note:** This is a project-history and technical handoff, not a byte-for-byte copy of every file in the ORBIT directory. It reflects the available project history and the current uploaded Research Agent's confirmed implementation state. Inspect the actual repository before making changes.

## 1. Project

**Project name:** ORBIT

ORBIT is a multi-agent AI/research system.

Current development environment:

- OS: Windows
- Project directory: `C:\Users\LENOVO\ORBIT`
- Python virtual environment: `C:\Users\LENOVO\ORBIT\.venv`
- Python: 3.14.7
- Python executable: `C:\Users\LENOVO\ORBIT\.venv\Scripts\python.exe`

## 2. Known project structure

```text
ORBIT/
├── .venv/
├── backend/
│   └── agents/
│       ├── base_agent.py
│       ├── research_agent.py
│       ├── research_agent_backup.py
│       └── research_agent_backup2.py
└── ...
```

Do not delete existing project files unless verified first.

## 3. Safe change procedure

Before changing code:

1. Inspect the existing implementation.
2. Make a backup.
3. Make one logical change at a time.
4. Compile the changed Python file.
5. Run a focused test.
6. Only then proceed to the next change.

Do not blindly replace files with files that supposedly exist in Downloads.

## 4. Python environment

Verify the environment:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
```

Expected executable:

```text
C:\Users\LENOVO\ORBIT\.venv\Scripts\python.exe
```

Verified packages:

- `scikit-learn` 1.9.0
- `python-dotenv`

```python
from dotenv import load_dotenv
import dotenv
print(dotenv.__file__)
```

## 5. Research Agent

File: `backend\agents\research_agent.py`

`ResearchAgent` inherits from `BaseAgent` and currently contains:

- `ArticleTextParser`
- `clean_text()`
- `is_explanatory_query()`
- `search_web()`
- `is_google_news_url()`
- `is_blocked_host()`
- `get_known_publisher_url()`
- `get_publisher_domains()`
- `fetch_search_page()`
- `extract_search_candidates()`
- `find_publisher_article()`
- `resolve_url()`
- `fetch_article()`
- `article_matches_source()`
- `split_sentences()`
- `summarize_article()`
- `build_queries()`
- `enrich_sources()`
- `build_result()`
- `run()`

### Intended pipeline

```text
User query
  → build_queries()
  → Google News RSS
  → Search results
  → Google News URL resolution
  → Publisher URL fallback
  → Direct article fetching
  → HTML parsing
  → Article validation
  → Local extractive summary
  → Validated research result
```

The basic research pipeline does not require Gemini.

## 6. Databricks discovery and fix

For **“What are Large Language Models (LLM)?”**, `find_publisher_article()` returns:

```text
https://www.databricks.com/glossary/large-language-models-llm
```

That URL returns HTTP 200 but redirects to:

```text
https://www.databricks.com/blog/what-are-large-language-models
```

The redirected page contains the actual article. It was manually verified as HTML, with a 200 response and approximately 742,778 bytes. `fetch_article()` must therefore support redirects and known alternate publisher URLs.

Known Databricks candidates:

- `https://www.databricks.com/blog/what-are-large-language-models`
- `https://www.databricks.com/glossary/large-language-models-llm`

Successful observed behavior:

```text
URL: https://www.databricks.com/glossary/large-language-models-llm
ARTICLE LENGTH: 12000
VALID: True
```

The extracted text begins with the Databricks LLM article title and substantive LLM content.

## 7. Article parsing and fetching

`ArticleTextParser` uses Python's `HTMLParser`. It ignores:

- `script`, `style`, `noscript`, `svg`, `nav`, `footer`, `header`, `form`, `aside`, `iframe`, `button`

It considers the following block tags:

- `p`, `article`, `section`, `h1`–`h6`, `li`, `blockquote`

`fetch_article()` should:

1. Reject empty URLs.
2. Try direct publisher URLs.
3. Resolve Google News URLs.
4. Try resolved URLs and the original URL where appropriate.
5. Try known publisher alternatives.
6. Send a realistic User-Agent.
7. Accept HTML/XHTML and read enough bytes for modern publisher pages.
8. Parse and clean article text, with raw-HTML fallback if needed.
9. Return text only when enough content is extracted.

Current configuration:

```text
timeout = 15
max_article_chars = 12000
max_download_bytes = 1500000
```

## 8. Search-result filtering

Never scan all search-engine HTML for arbitrary `https://` strings. That previously produced junk such as `storage.live.com` profile-image URLs.

Extract links only from actual `href` attributes:

```python
re.findall(r'href=["\']([^"\']+)["\']', page, flags=re.I)
```

Blocked hosts include Google infrastructure, major search/social services, W3C, and Microsoft asset hosts:

```text
google.com, google.co, googleusercontent.com, gstatic.com, googleapis.com,
news.google.com, youtube.com, youtube-nocookie.com, bing.com, bingj.com,
microsoftonline.com, facebook.com, twitter.com, x.com, w3.org, www.w3.org,
storage.live.com, live.com, onedrive.live.com
```

Known publisher domains:

```text
Databricks: databricks.com       IBM: ibm.com
Microsoft: microsoft.com         OpenAI: openai.com
Anthropic: anthropic.com         Salesforce: salesforce.com
Lookout: lookout.com             KDnuggets: kdnuggets.com
InfoWorld: infoworld.com         Towards Data Science: towardsdatascience.com
Diginomica: diginomica.com       Times of India: timesofindia.indiatimes.com
Indian Express: indianexpress.com  OfficeChai: officechai.com
FoneArena: fonearena.com         NewsBytes: newsbytesapp.com
Substack: substack.com
```

`find_publisher_article()` preference order:

1. Known publisher fallback.
2. Google source-restricted search.
3. Bing source-restricted search.

For known publishers, prefer a query such as `site:databricks.com`.

`search_web()` uses Google News RSS at `https://news.google.com/rss/search` with `hl=en-US`, `gl=US`, and `ceid=US:en`. Google News URLs are not final article URLs; `resolve_url()` must follow them to the publisher.

## 9. Validation and result rules

A search result is **not** evidence. Only successfully fetched and validated article content becomes a research finding.

`article_matches_source()` checks that:

- the article exists and is sufficiently long;
- it is not W3C/XHTML junk;
- LLM queries include relevant terminology such as `large language model`, `large language models`, or `llm`;
- title/content overlap is appropriate.

Reject W3C namespace pages with markers such as `xhtml namespace`, `the namespace name`, `xhtml 1.0`, and `xhtml modularization` unless substantive LLM terminology is also present.

`build_result()` must exclude sources where `article_valid == False`. If no sources survive validation, return `status: unavailable`; never manufacture research findings from RSS metadata.

Expected good behavior for “What is an LLM?” is a completed, grounded result showing only validated Databricks (or other validated) article findings—not failed candidates.

## 10. Backups and regressions

Existing backups:

- `backend\agents\research_agent_backup.py`
- `backend\agents\research_agent_backup2.py`

Before major changes, create a new backup:

```powershell
Copy-Item ".\backend\agents\research_agent.py" ".\backend\agents\research_agent_backup3.py" -Force
```

Compile after every modification:

```powershell
.\.venv\Scripts\python.exe -m py_compile ".\backend\agents\research_agent.py"
```

No output means compilation succeeded.

`ResearchAgent.run()` must be a concrete implementation, not decorated with `@abstractmethod`; otherwise `ResearchAgent()` cannot be instantiated.

Verify its status:

```powershell
.\.venv\Scripts\python.exe -c "from backend.agents.research_agent import ResearchAgent; import inspect; print('RUN:', hasattr(ResearchAgent,'run')); print('ABSTRACT:',getattr(ResearchAgent.run,'__isabstractmethod__',False)); a=ResearchAgent(); print('INSTANTIATION: OK')"
```

Expected:

```text
RUN: True
ABSTRACT: False
INSTANTIATION: OK
```

Verify key methods:

```powershell
.\.venv\Scripts\python.exe -c "from backend.agents.research_agent import ResearchAgent; a=ResearchAgent(); print('publisher:',hasattr(a,'find_publisher_article')); print('known:',hasattr(a,'get_known_publisher_url')); print('validation:',hasattr(a,'article_matches_source')); print('fetch:',hasattr(a,'fetch_article')); print('search:',hasattr(a,'search_web'))"
```

Run the Databricks regression test:

```powershell
.\.venv\Scripts\python.exe -c "from backend.agents.research_agent import ResearchAgent; a=ResearchAgent(); u=a.find_publisher_article('What are Large Language Models (LLM)?','Databricks'); x=a.fetch_article(u); print('URL:',u); print('ARTICLE LENGTH:',len(x)); print('VALID:',a.article_matches_source(x,'What are Large Language Models (LLM)?','Databricks')); print(x[:500])"
```

Expect a nonempty article (normally 12,000 characters) and `VALID: True`.

## 11. First steps for the next Codex session

1. Inspect the complete repository; do not assume this document describes every file.
2. Run `git status` if this is a Git repository.
3. Inspect `backend/`, `backend/agents/`, `backend/agents/base_agent.py`, and `backend/agents/research_agent.py`.
4. Do not overwrite the Research Agent immediately; compare repository state to this handoff.
5. Compile `research_agent.py`.
6. Run the instantiation test and Databricks regression test.
7. Inspect `BaseAgent.run()` to confirm the inheritance contract.
8. Only then propose additional changes.

## 12. Current status and development goal

The Databricks extraction issue has been substantially fixed. Known successful behavior includes publisher lookup, redirect handling, article extraction, validation, junk-URL filtering, invalid-candidate filtering, and a concrete `ResearchAgent.run()` requirement.

Continue development step by step, prioritizing:

- reliable web search and publisher resolution;
- article extraction and source validation;
- no junk URLs or false findings;
- useful summaries and structured results;
- robust errors and BaseAgent compatibility;
- no unnecessary Gemini dependency for basic research.

Avoid inventing a Downloads file such as `research_agent_orbit_fixed_complete.py`; do not instruct anyone to copy it unless it genuinely exists. Keep separate PowerShell commands separate (for example, do not concatenate `-Force` with `Copy-Item`).
