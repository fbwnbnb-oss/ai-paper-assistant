from flask import Flask, render_template, jsonify, request
from datetime import datetime, date
from models import (init_db, get_papers_by_date, get_all_dates, update_paper_status,
                    get_study_record, save_study_record, get_study_history)
from fetcher import fetch_and_save
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

init_db()

scheduler = BackgroundScheduler()

def scheduled_fetch():
    print(f"[{datetime.now()}] Scheduled fetch started...")
    try:
        count = fetch_and_save()
        print(f"[{datetime.now()}] Fetched {count} new papers")
    except Exception as e:
        print(f"[{datetime.now()}] Fetch error: {e}")

scheduler.add_job(scheduled_fetch, 'cron', hour=8, minute=0)
scheduler.start()


@app.route('/')
def index():
    target_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    papers = get_papers_by_date(target_date)
    all_dates = get_all_dates()

    if not papers and target_date == date.today().strftime('%Y-%m-%d'):
        fetch_and_save()
        papers = get_papers_by_date(target_date)
        all_dates = get_all_dates()

    return render_template('index.html',
                           papers=papers,
                           current_date=target_date,
                           all_dates=all_dates)


@app.route('/paper/<arxiv_id>')
def paper_detail(arxiv_id):
    from models import get_db
    with get_db() as conn:
        paper = conn.execute("""
            SELECT p.*,
                   COALESCE(ps.is_read, 0) as is_read,
                   COALESCE(ps.is_favorite, 0) as is_favorite
            FROM papers p
            LEFT JOIN paper_status ps ON p.arxiv_id = ps.arxiv_id
            WHERE p.arxiv_id = ?
        """, (arxiv_id,)).fetchone()

    if not paper:
        return "Paper not found", 404

    return render_template('paper.html', paper=dict(paper))


@app.route('/api/mark-read', methods=['POST'])
def mark_read():
    data = request.get_json()
    update_paper_status(data.get('arxiv_id'), is_read=data.get('is_read', True))
    return jsonify({'success': True})


@app.route('/api/toggle-favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json()
    update_paper_status(data.get('arxiv_id'), is_favorite=data.get('is_favorite', True))
    return jsonify({'success': True})


@app.route('/api/fetch-now', methods=['POST'])
def fetch_now():
    try:
        data = request.get_json() or {}
        keywords = data.get('keywords', None)
        if isinstance(keywords, str):
            keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        count = fetch_and_save(custom_keywords=keywords if keywords else None)
        kw_msg = f" (关键词: {', '.join(keywords)})" if keywords else ""
        return jsonify({'success': True, 'message': f'抓取到 {count} 篇新论文{kw_msg}', 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/github-config', methods=['GET', 'POST'])
def github_config():
    from github_sync import load_config, save_config
    if request.method == 'GET':
        config = load_config()
        return jsonify({
            'repo': config.get('repo', ''),
            'branch': config.get('branch', 'main'),
            'has_token': bool(config.get('token', ''))
        })
    data = request.get_json() or {}
    config = load_config()
    if data.get('token'):
        config['token'] = data['token']
    if data.get('repo') is not None:
        config['repo'] = data['repo']
    if data.get('branch') is not None:
        config['branch'] = data['branch'] or 'main'
    save_config(config)
    return jsonify({'success': True})


@app.route('/api/github-sync', methods=['POST'])
def github_sync():
    from github_sync import sync_to_github
    result = sync_to_github()
    return jsonify(result)


@app.route('/study/<arxiv_id>')
def study_page(arxiv_id):
    from models import get_db
    with get_db() as conn:
        paper = conn.execute(
            "SELECT * FROM papers WHERE arxiv_id = ?", (arxiv_id,)
        ).fetchone()

    if not paper:
        return "Paper not found", 404

    record = get_study_record(arxiv_id)
    return render_template('study.html', paper=dict(paper), record=record)


@app.route('/api/study/start', methods=['POST'])
def study_start():
    import json
    from pdf_extractor import extract_text_from_url
    from ai_service import translate_text, summarize_paper

    data = request.get_json()
    arxiv_id = data.get('arxiv_id')
    pdf_url = data.get('pdf_url')

    if not arxiv_id or not pdf_url:
        return jsonify({'success': False, 'error': '缺少参数'}), 400

    existing = get_study_record(arxiv_id)
    if existing and existing.get('translated_text'):
        return jsonify({
            'success': True,
            'cached': True,
            'paragraphs': json.loads(existing['translated_text']),
            'summary': existing['summary']
        })

    try:
        from models import get_db
        with get_db() as conn:
            paper = conn.execute(
                "SELECT title FROM papers WHERE arxiv_id = ?", (arxiv_id,)
            ).fetchone()
        title = paper['title'] if paper else ''

        paragraphs = extract_text_from_url(pdf_url)
        translated = translate_text(paragraphs)
        full_text = '\n\n'.join(paragraphs)
        summary = summarize_paper(title, full_text)

        save_study_record(arxiv_id, full_text, json.dumps(translated, ensure_ascii=False), summary)

        return jsonify({
            'success': True,
            'cached': False,
            'paragraphs': translated,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/study/recommend-keywords', methods=['GET'])
def study_recommend():
    from ai_service import recommend_keywords
    history = get_study_history()
    if not history:
        return jsonify({'success': True, 'keywords': []})
    keywords = recommend_keywords(history)
    return jsonify({'success': True, 'keywords': keywords})


if __name__ == '__main__':
    today = date.today().strftime('%Y-%m-%d')
    if not get_papers_by_date(today):
        print("No papers for today, fetching...")
        try:
            count = fetch_and_save()
            print(f"Fetched {count} papers")
        except Exception as e:
            print(f"Initial fetch failed: {e}")

    print("\n" + "=" * 60)
    print("AI Paper Assistant is running!")
    print("Open your browser to: http://localhost:5000")
    print("=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
