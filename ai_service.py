import requests
import json

API_KEY = "sk-ws-H.RXHMPIH.Td07.MEUCIQCAuz21AiNnonmTrf1FqaFXjsHCMkBMFch2_Ycdf9nEXgIgcZGN42eKDqxv-ykUoSzj5_eSoNnEh_xNCcCL8JgoVhg"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen3-235b-a22b"


def _call_llm(messages: list, temperature: float = 0.3) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 8000,
        "extra_body": {"enable_thinking": False}
    }
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=data,
        timeout=180
    )
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]


def translate_text(paragraphs: list) -> list:
    if not paragraphs:
        return []

    batch_size = 5
    all_pairs = []

    for i in range(0, len(paragraphs), batch_size):
        batch = paragraphs[i:i + batch_size]
        numbered = "\n\n".join(f"[{j+1}] {p}" for j, p in enumerate(batch))

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位专业的学术论文翻译专家。请将以下编号段落从英文翻译为中文。"
                    "保持学术专业性和准确性。每段翻译用相同编号标记，格式为 [编号] 翻译内容。"
                    "不要添加任何解释，只输出翻译。"
                )
            },
            {"role": "user", "content": numbered}
        ]

        try:
            result = _call_llm(messages)
            translations = _parse_numbered(result, len(batch))
            for j, p in enumerate(batch):
                zh = translations[j] if j < len(translations) else p
                all_pairs.append({"en": p, "zh": zh})
        except Exception:
            for p in batch:
                all_pairs.append({"en": p, "zh": "[翻译失败]"})

    return all_pairs


def _parse_numbered(text: str, expected: int) -> list:
    import re
    parts = re.split(r'\[(\d+)\]\s*', text)
    results = {}
    for i in range(1, len(parts) - 1, 2):
        idx = int(parts[i])
        content = parts[i + 1].strip()
        results[idx] = content

    return [results.get(i + 1, "") for i in range(expected)]


def summarize_paper(title: str, text: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "你是一位资深AI研究专家，擅长深入分析和解读学术论文。"
                "请用中文对以下论文进行详细、深入的结构化总结，包含以下部分：\n\n"
                "1. **研究背景与动机**：详细说明这篇论文要解决什么问题，当前领域存在哪些挑战和不足，为什么这个问题重要\n"
                "2. **核心方法与技术框架**：详细描述提出的方法、模型架构或框架设计，包括关键技术细节、算法流程和设计思路\n"
                "3. **主要创新点**：逐条列出与已有工作相比的创新之处，每个创新点展开说明\n"
                "4. **实验设置与结果**：描述实验使用的数据集、基线方法、评估指标，以及主要实验结果和关键数据\n"
                "5. **消融实验与分析**：如果论文包含消融实验或深入分析，总结其发现\n"
                "6. **局限性与未来方向**：论文存在的局限性以及作者提出的未来研究方向\n"
                "7. **核心贡献总结**：用2-3句话概括论文的核心贡献和意义\n\n"
                "请尽可能详细和深入，不要省略重要信息。每个部分都要充分展开，总结应在1500-2000字左右。"
            )
        },
        {"role": "user", "content": f"论文标题：{title}\n\n论文内容：\n{text[:8000]}"}
    ]

    try:
        return _call_llm(messages)
    except Exception as e:
        return f"总结生成失败：{str(e)}"


def recommend_keywords(study_history: list) -> list:
    if not study_history:
        return []

    history_text = "\n".join(
        f"- {r['title']} ({r['categories']})"
        for r in study_history[:20]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "根据用户的论文学习历史，推荐5-8个英文搜索关键词，"
                "用于在arXiv上发现用户可能感兴趣的新论文。"
                "关键词应反映用户的研究兴趣方向，并包含一些拓展方向。"
                "只输出关键词，每行一个，不要编号或解释。"
            )
        },
        {"role": "user", "content": f"我的学习历史：\n{history_text}"}
    ]

    try:
        result = _call_llm(messages, temperature=0.7)
        keywords = [kw.strip().strip('-').strip() for kw in result.strip().split('\n') if kw.strip()]
        return keywords[:8]
    except Exception:
        return []
