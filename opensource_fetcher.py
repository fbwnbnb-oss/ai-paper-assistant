import requests
from datetime import datetime, timedelta

GITHUB_ORGS = {
    "OpenAI": ["openai"],
    "Google": ["google-deepmind", "google-research", "google"],
    "Anthropic": ["anthropics"],
}

AI_TOPIC_KEYWORDS = [
    "llm", "language-model", "gpt", "transformer", "agent", "reasoning",
    "rlhf", "diffusion", "multimodal", "vision", "embedding", "tokenizer",
    "fine-tuning", "alignment", "safety", "benchmark", "eval", "inference",
    "training", "model", "ai", "machine-learning", "deep-learning", "neural",
    "claude", "gemini", "palm", "bard", "whisper", "codex", "sora",
]


def _is_ai_related(repo: dict) -> bool:
    name = (repo.get("name") or "").lower()
    desc = (repo.get("description") or "").lower()
    topics = [t.lower() for t in (repo.get("topics") or [])]
    text = f"{name} {desc} {' '.join(topics)}"
    return any(kw in text for kw in AI_TOPIC_KEYWORDS)


def fetch_github_repos(org: str, since_days: int = 90, max_results: int = 30) -> list:
    since_date = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d")
    url = f"https://api.github.com/orgs/{org}/repos"
    params = {
        "sort": "pushed",
        "direction": "desc",
        "per_page": 100,
        "type": "public",
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        if resp.status_code != 200:
            return []
        repos = resp.json()
    except Exception:
        return []

    results = []
    for repo in repos:
        pushed_at = repo.get("pushed_at", "")[:10]
        if pushed_at < since_date:
            continue
        if repo.get("fork"):
            continue
        if not _is_ai_related(repo):
            continue

        results.append({
            "repo_id": repo["full_name"],
            "name": repo["name"],
            "org": org,
            "description": repo.get("description") or "",
            "url": repo["html_url"],
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language") or "",
            "topics": ", ".join(repo.get("topics") or []),
            "created_at": (repo.get("created_at") or "")[:10],
            "updated_at": pushed_at,
        })

    results.sort(key=lambda x: x["stars"], reverse=True)
    return results[:max_results]


def fetch_all_opensource() -> list:
    all_repos = []
    for company, orgs in GITHUB_ORGS.items():
        for org in orgs:
            repos = fetch_github_repos(org)
            for r in repos:
                r["company"] = company
            all_repos.extend(repos)

    all_repos.sort(key=lambda x: x["updated_at"], reverse=True)
    return all_repos
