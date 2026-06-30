import arxiv
from datetime import datetime
import re
from models import save_paper, paper_exists

# Keywords weighted by relevance to AI agent research
KEYWORDS_WEIGHTED = [
    (r'\bagent\b', 10),
    (r'\bagents\b', 10),
    (r'\bmulti[- ]?agent\b', 15),
    (r'\bLLM\s+agent\b', 20),
    (r'\btool\s+use\b', 12),
    (r'\btool\s+calling\b', 12),
    (r'\bfunction\s+calling\b', 10),
    (r'\bplanning\b', 8),
    (r'\breasoning\b', 8),
    (r'\bautonomous\b', 10),
    (r'\bMCP\b', 15),
    (r'\bRetrieval[- ]?Augmented\b', 8),
    (r'\bRAG\b', 8),
    (r'\bfine[- ]?tun', 5),
    (r'\bRLHF\b', 5),
    (r'\breinforcement\s+learning\s+from\s+human\s+feedback\b', 5),
    (r'\bLLM\b', 5),
    (r'\blarge\s+language\s+model\b', 5),
    (r'\bGPT\b', 3),
    (r'\bchain[- ]?of[- ]?thought\b', 8),
    (r'\bCoT\b', 8),
    (r'\bReAct\b', 10),
    (r'\btree[- ]?of[- ]?thought\b', 8),
    (r'\bsandbox\b', 7),
    (r'\bgrounding\b', 7),
]

TARGET_CATEGORIES = ['cs.AI', 'cs.MA', 'cs.CL', 'cs.LG', 'cs.RO']

def calc_relevance(title: str, summary: str) -> int:
    text = (title + ' ' + summary).lower()
    score = 0
    for pattern, weight in KEYWORDS_WEIGHTED:
        matches = len(re.findall(pattern, text, re.IGNORECASE))
        score += matches * weight
    return score

def fetch_papers(max_results: int = 80, top_n: int = 10) -> list:
    """Fetch recent AI/agent papers from arXiv and return the top N by relevance."""
    category_query = ' OR '.join(f'cat:{cat}' for cat in TARGET_CATEGORIES)
    query = f'({category_query}) AND (ti:agent OR ti:multi-agent OR ti:LLM OR ti:reasoning OR ti:planning OR ti:tool OR ti:autonomous)'

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    scored_papers = []
    for result in client.results(search):
        title = result.title
        summary = result.summary
        score = calc_relevance(title, summary)

        if score == 0:
            continue

        authors = ', '.join(a.name for a in result.authors[:5])
        if len(result.authors) > 5:
            authors += f' +{len(result.authors) - 5} more'

        paper = {
            'arxiv_id': result.entry_id.split('/')[-1],
            'title': title,
            'authors': authors,
            'summary': summary,
            'categories': ', '.join(result.categories),
            'published': result.published.isoformat(),
            'pdf_url': result.pdf_url,
            'relevance_score': score,
        }
        scored_papers.append(paper)

    # Sort by relevance score descending, take top N
    scored_papers.sort(key=lambda p: p['relevance_score'], reverse=True)
    top_papers = scored_papers[:top_n]

    return top_papers

def fetch_and_save(max_results: int = 80, top_n: int = 10) -> int:
    """Fetch papers and save them to the database. Returns number of new papers saved."""
    papers = fetch_papers(max_results=max_results, top_n=top_n)
    today = datetime.now().strftime('%Y-%m-%d')

    new_count = 0
    for paper in papers:
        if not paper_exists(paper['arxiv_id']):
            new_count += 1
        save_paper(paper, today)

    return new_count
