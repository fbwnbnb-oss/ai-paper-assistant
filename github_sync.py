import subprocess
import os
import json
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'github_config.json')
CWD = os.path.dirname(os.path.abspath(__file__))


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def _git(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['git'] + args,
        cwd=CWD,
        capture_output=True,
        text=True
    )


def sync_to_github() -> dict:
    config = load_config()
    token = config.get('token', '').strip()
    repo = config.get('repo', '').strip()
    branch = config.get('branch', 'main').strip() or 'main'

    if not token:
        return {'success': False, 'error': '请先配置 GitHub Personal Access Token'}
    if not repo:
        return {'success': False, 'error': '请先配置仓库名称（格式：用户名/仓库名）'}

    # Ensure git repo exists
    if not os.path.exists(os.path.join(CWD, '.git')):
        _git(['init'])
        _git(['branch', '-M', branch])

    # Set identity
    _git(['config', 'user.email', 'fbwnbnb@gmail.com'])
    _git(['config', 'user.name', 'AI Paper Assistant'])

    # Ensure .gitignore exists
    gitignore_path = os.path.join(CWD, '.gitignore')
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write('\n'.join([
                'venv/', '__pycache__/', '*.pyc', '*.pyo',
                'papers.db', 'github_config.json', '.env', '.DS_Store'
            ]) + '\n')

    # Set remote
    remote_url = f'https://{token}@github.com/{repo}.git'
    remotes = _git(['remote'])
    if 'origin' in remotes.stdout.splitlines():
        _git(['remote', 'set-url', 'origin', remote_url])
    else:
        _git(['remote', 'add', 'origin', remote_url])

    # Stage all tracked + new files
    _git(['add', '-A'])

    # Check if anything to commit
    status = _git(['status', '--porcelain'])
    if not status.stdout.strip():
        return {'success': True, 'message': '无变更，仓库已是最新 ✓', 'url': f'https://github.com/{repo}'}

    # Commit
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    commit = _git(['commit', '-m', f'sync: {ts}'])
    if commit.returncode != 0:
        return {'success': False, 'error': commit.stderr or commit.stdout}

    # Push
    push = _git(['push', '-u', 'origin', branch, '--force'])
    if push.returncode == 0:
        return {
            'success': True,
            'message': f'已同步到 github.com/{repo}',
            'url': f'https://github.com/{repo}'
        }
    else:
        err = push.stderr or push.stdout
        return {'success': False, 'error': err or '推送失败，请检查 Token 权限（需要 repo 权限）'}
