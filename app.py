from flask import Flask, render_template, jsonify, request
from datetime import datetime, date
from models import init_db, get_papers_by_date, get_all_dates, update_paper_status
from fetcher import fetch_and_save
from apscheduler.schedulers.background import BackgroundScheduler
import threading

app = Flask(__name__)

# Initialize database
init_db()

# Scheduler for daily paper fetching
scheduler = BackgroundScheduler()

def scheduled_fetch():
    """Called by scheduler to fetch papers daily."""
    print(f"[{datetime.now()}] Scheduled fetch started...")
    try:
        count = fetch_and_save()
        print(f"[{datetime.now()}] Fetched {count} new papers")
    except Exception as e:
        print(f"[{datetime.now()}] Fetch error: {e}")

# Schedule daily fetch at 8:00 AM
scheduler.add_job(scheduled_fetch, 'cron', hour=8, minute=0)
scheduler.start()

@app.route('/')
def index():
    """Show papers for a specific date (default: today)."""
    target_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    papers = get_papers_by_date(target_date)
    all_dates = get_all_dates()

    # If no papers for today, try to fetch
    if not papers and target_date == date.today().strftime('%Y-%m-%d'):
        print("No papers found for today, fetching now...")
        fetch_and_save()
        papers = get_papers_by_date(target_date)
        all_dates = get_all_dates()

    return render_template('index.html',
                         papers=papers,
                         current_date=target_date,
                         all_dates=all_dates)

@app.route('/paper/<arxiv_id>')
def paper_detail(arxiv_id):
    """Show detailed view of a single paper."""
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
    """Mark a paper as read/unread."""
    data = request.get_json()
    arxiv_id = data.get('arxiv_id')
    is_read = data.get('is_read', True)

    update_paper_status(arxiv_id, is_read=is_read)
    return jsonify({'success': True})

@app.route('/api/toggle-favorite', methods=['POST'])
def toggle_favorite():
    """Toggle favorite status of a paper."""
    data = request.get_json()
    arxiv_id = data.get('arxiv_id')
    is_favorite = data.get('is_favorite', True)

    update_paper_status(arxiv_id, is_favorite=is_favorite)
    return jsonify({'success': True})

@app.route('/api/fetch-now', methods=['POST'])
def fetch_now():
    """Manually trigger paper fetch."""
    try:
        count = fetch_and_save()
        return jsonify({'success': True, 'message': f'Fetched {count} new papers'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Fetch papers on startup if none exist for today
    today = date.today().strftime('%Y-%m-%d')
    papers = get_papers_by_date(today)
    if not papers:
        print("No papers found for today, fetching...")
        try:
            count = fetch_and_save()
            print(f"Fetched {count} papers")
        except Exception as e:
            print(f"Initial fetch failed: {e}")

    print("\n" + "="*60)
    print("AI Paper Assistant is running!")
    print("Open your browser to: http://localhost:5000")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
