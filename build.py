#!/usr/bin/env python3
"""
Static Site Generator for Personal Website
Converts markdown and templates to static HTML files
"""
import os
import markdown
import codecs
import json
import time
import shutil
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Configuration
SOURCE_DIR = Path('njwfish')
OUTPUT_DIR = Path('site')
STATIC_DIR = SOURCE_DIR / 'static'
TEMPLATES_DIR = SOURCE_DIR / 'templates'
POSTS_DIR = STATIC_DIR / 'posts'

# Markdown extensions
MD_EXTENSIONS = ['fenced_code', 'tables', 'toc']

def ensure_dir(path):
    """Create directory if it doesn't exist"""
    path.mkdir(parents=True, exist_ok=True)

def md_to_html(md_path):
    """Convert markdown file to HTML"""
    if not md_path.exists():
        return ""
    with codecs.open(md_path, mode="r", encoding="utf-8") as f:
        text = f.read()
    return markdown.markdown(text, extensions=MD_EXTENSIONS)

def load_post(post_dir):
    """Load post metadata and content"""
    post_name = post_dir.name
    
    # Read title and blurb
    title_file = post_dir / 'title'
    blurb_file = post_dir / 'blurb'
    
    title = title_file.read_text().strip() if title_file.exists() else post_name.replace('_', ' ').title()
    blurb = blurb_file.read_text().strip() if blurb_file.exists() else ""
    
    # Read main content
    main_html = post_dir / 'main.html'
    main_md = post_dir / 'main.md'
    
    if main_html.exists():
        post_content = main_html.read_text()
    elif main_md.exists():
        post_content = md_to_html(main_md)
        # If no title file, try to extract from markdown
        if not title_file.exists():
            lines = main_md.read_text().split('\n')
            for line in lines:
                if line.strip().startswith('# '):
                    title = line.strip()[2:].strip()
                    break
        # Ensure blurb exists - if missing, create a default from markdown
        if not blurb:
            lines = main_md.read_text().split('\n')
            for line in lines[:3]:  # Check first 3 lines
                if line.strip() and not line.strip().startswith('#'):
                    blurb = line.strip()[:150] + "..." if len(line.strip()) > 150 else line.strip()
                    break
            if not blurb:
                blurb = "No description available."
            # Write blurb back to file
            blurb_file.write_text(blurb)
    else:
        post_content = ""
        if not blurb:
            blurb = "No description available."
            blurb_file.write_text(blurb)
    
    # Get modification time
    mtime = os.path.getmtime(post_dir)
    date_str = time.strftime('%B %d, %Y', time.gmtime(mtime))
    date_sort = time.gmtime(mtime)
    
    return {
        'slug': post_name,
        'title': title,
        'blurb': blurb,
        'content': post_content,
        'date': date_str,
        'date_sort': date_sort
    }

def load_posts():
    """Load all posts"""
    posts = []
    if not POSTS_DIR.exists():
        return posts
    
    for post_dir in POSTS_DIR.iterdir():
        if post_dir.is_dir():
            try:
                post = load_post(post_dir)
                posts.append(post)
            except Exception as e:
                print(f"Error loading post {post_dir}: {e}")
    
    # Sort by date (newest first)
    posts.sort(key=lambda x: x['date_sort'], reverse=True)
    return posts

def load_talks():
    """Load talks from talks.json if it exists"""
    talks_file = SOURCE_DIR / 'talks.json'
    if talks_file.exists():
        with open(talks_file, 'r') as f:
            return json.load(f)
    return []

def copy_static_files():
    """Copy static files to output directory"""
    static_output = OUTPUT_DIR / 'static'
    
    # Copy CSS, JS, fonts, images
    for item in ['css', 'js', 'fonts', 'img', 'papers', 'slides']:
        src = STATIC_DIR / item
        if src.exists():
            dst = static_output / item
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    
    # Copy PDFs
    for pdf in ['resume.pdf', 'cv.pdf']:
        src = STATIC_DIR / pdf
        if src.exists():
            ensure_dir(static_output)
            shutil.copy2(src, static_output / pdf)
    
    # Copy favicon to root for better browser compatibility
    favicon_src = STATIC_DIR / 'img' / 'favicon.ico'
    if favicon_src.exists():
        shutil.copy2(favicon_src, OUTPUT_DIR / 'favicon.ico')
    
    # Copy post assets (PDFs, images, etc. from post directories)
    posts_static = OUTPUT_DIR / 'static' / 'posts'
    ensure_dir(posts_static)
    if POSTS_DIR.exists():
        for post_dir in POSTS_DIR.iterdir():
            if post_dir.is_dir():
                # Copy all non-content files from post directories
                post_name = post_dir.name
                post_output = posts_static / post_name
                ensure_dir(post_output)
                for item in post_dir.iterdir():
                    if item.is_file() and item.name not in ['title', 'blurb', 'main.md', 'main.html']:
                        shutil.copy2(item, post_output / item.name)

def build_cv():
    """Generate CV publications section and compile PDF"""
    import subprocess
    
    print("Generating CV publications section...")
    
    # Generate writing.tex from papers.json
    papers_json = SOURCE_DIR / 'papers.json'
    writing_tex = Path('latex_cv') / 'resume' / 'writing.tex'
    
    if papers_json.exists():
        subprocess.run([
            'python3', 'generate_cv_papers.py',
            str(papers_json),
            str(writing_tex)
        ], check=False)
    
    # Compile CV PDF
    print("Compiling CV PDF...")
    cv_dir = Path('latex_cv')
    cv_tex = cv_dir / 'cv.tex'
    
    if cv_tex.exists():
        try:
            # Change to latex_cv directory for compilation
            subprocess.run(
                ['xelatex', '-interaction=nonstopmode', 'cv.tex'],
                cwd=str(cv_dir),
                capture_output=True,
                text=True
            )
            
            # Run twice for references
            subprocess.run(
                ['xelatex', '-interaction=nonstopmode', 'cv.tex'],
                cwd=str(cv_dir),
                capture_output=True,
                text=True
            )
            
            # Copy PDF to static directory
            cv_pdf = cv_dir / 'cv.pdf'
            if cv_pdf.exists():
                shutil.copy2(cv_pdf, STATIC_DIR / 'cv.pdf')
                print("CV PDF compiled successfully!")
            else:
                print(f"Warning: CV PDF not found at {cv_pdf}")
                # Try alternative location
                alt_pdf = Path('latex_cv') / 'cv.pdf'
                if alt_pdf.exists():
                    shutil.copy2(alt_pdf, STATIC_DIR / 'cv.pdf')
                    print("CV PDF found and copied from alternative location!")
        except FileNotFoundError:
            print("Warning: xelatex not found. Skipping CV compilation.")
        except Exception as e:
            print(f"Warning: CV compilation failed: {e}")
    else:
        print("Warning: CV LaTeX file not found")

def fetch_papers():
    """Fetch papers from Google Scholar and update papers.json"""
    print("Fetching papers from Google Scholar...")
    fetch_script = Path('fetch_scholar.py')
    
    if fetch_script.exists():
        try:
            result = subprocess.run(
                ['python3', str(fetch_script)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            if result.returncode == 0:
                print("Papers fetched successfully from Google Scholar")
            else:
                print(f"Warning: Google Scholar fetch had issues: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print("Warning: Google Scholar fetch timed out")
        except Exception as e:
            print(f"Warning: Failed to fetch papers: {e}")
    else:
        print("Warning: fetch_scholar.py not found. Skipping paper fetch.")

def build_site():
    """Build the entire static site"""
    print("Building static site...")
    
    # Setup
    ensure_dir(OUTPUT_DIR)
    
    # Fetch papers from Google Scholar first
    fetch_papers()
    
    # Build CV first (updates publications section)
    build_cv()
    
    # Load data
    posts = load_posts()
    talks = load_talks()
    
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    # Copy static files
    copy_static_files()
    
    # Build index/about page
    print("Building index page...")
    about_md = STATIC_DIR / 'about.md'
    about_content = md_to_html(about_md) if about_md.exists() else ""
    
    about_template = env.get_template('about.html')
    index_html = about_template.render(
        active_page='index',
        title='Nic Fishman',
        description='PhD student in Statistics at Harvard University',
        content=about_content
    )
    (OUTPUT_DIR / 'index.html').write_text(index_html)
    
    # Build posts listing page
    print("Building posts page...")
    posts_template = env.get_template('posts.html')
    posts_html = posts_template.render(
        active_page='words',
        title='Posts - Nic Fishman',
        description='Blog posts and writings',
        posts=posts
    )
    ensure_dir(OUTPUT_DIR / 'posts')
    (OUTPUT_DIR / 'posts' / 'index.html').write_text(posts_html)
    
    # Build individual post pages
    print("Building post pages...")
    post_template = env.get_template('post.html')
    for post in posts:
        post_html = post_template.render(
            active_page='words',
            title=f"{post['title']} - Nic Fishman",
            description=post['blurb'],
            post=post
        )
        ensure_dir(OUTPUT_DIR / 'posts' / post['slug'])
        (OUTPUT_DIR / 'posts' / post['slug'] / 'index.html').write_text(post_html)
    
    # Build papers page
    print("Building papers page...")
    papers_json_file = SOURCE_DIR / 'papers.json'
    published_papers = []
    working_papers = []
    
    if papers_json_file.exists():
        with open(papers_json_file, 'r') as f:
            papers_data = json.load(f)
            # Handle both old format (list) and new format (dict with published/working)
            if isinstance(papers_data, dict):
                published_papers = papers_data.get('published', [])
                working_papers = papers_data.get('working', [])
            else:
                # Old format - organize on the fly
                for paper in papers_data:
                    venue = paper.get('venue', '').lower()
                    year = paper.get('year', '')
                    if venue and venue.strip() and 'in preparation' not in venue.lower():
                        if any(journal in venue.lower() for journal in ['science', 'nature', 'advances in neural', 'neurips', 'proceedings', 'journal', 'conference', 'arxiv', 'transactions', 'icml', 'opt']):
                            published_papers.append(paper)
                        elif year and year.isdigit() and int(year) >= 2018:
                            published_papers.append(paper)
                        else:
                            working_papers.append(paper)
                    else:
                        working_papers.append(paper)
    
    # Sort by year
    published_papers.sort(key=lambda p: (p.get('year', '') or '0'), reverse=True)
    working_papers.sort(key=lambda p: (p.get('year', '') or '0'), reverse=True)
    
    papers_template = env.get_template('papers.html')
    papers_html = papers_template.render(
        active_page='papers',
        title='Papers - Nic Fishman',
        description='Research publications',
        published_papers=published_papers,
        working_papers=working_papers
    )
    ensure_dir(OUTPUT_DIR / 'papers')
    (OUTPUT_DIR / 'papers' / 'index.html').write_text(papers_html)
    
    # Build talks page
    print("Building talks page...")
    talks_template = env.get_template('talks.html')
    # Sort talks by date (newest first)
    talks_sorted = sorted(talks, key=lambda t: t.get('date', ''), reverse=True) if talks else []
    talks_html = talks_template.render(
        active_page='talks',
        title='Talks - Nic Fishman',
        description='Presentations and invited talks',
        talks=talks_sorted
    )
    ensure_dir(OUTPUT_DIR / 'talks')
    (OUTPUT_DIR / 'talks' / 'index.html').write_text(talks_html)
    
    print(f"Site built successfully! Output in {OUTPUT_DIR}/")
    print(f"Total posts: {len(posts)}")
    print(f"Total talks: {len(talks)}")

def deploy_to_gh_pages():
    """Deploy built site to gh-pages branch"""
    print("\n" + "="*60)
    print("Deploying to gh-pages branch...")
    print("="*60)
    
    # Check if we're in a git repository
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        print("Warning: Not in a git repository. Skipping deployment.")
        return
    
    # Get current branch
    result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                          capture_output=True, text=True, check=True)
    current_branch = result.stdout.strip()
    
    # Verify site was built before deploying
    if not OUTPUT_DIR.exists():
        print(f"Error: {OUTPUT_DIR} directory does not exist!")
        print("Please run build_site() first. Build automatically runs before deploy.")
        return
    
    index_file = OUTPUT_DIR / 'index.html'
    if not index_file.exists():
        print(f"Error: {index_file} does not exist!")
        print("Site build may have failed. Please check build output.")
        return
    
    # Get absolute path to site directory (before switching branches)
    site_path = OUTPUT_DIR.resolve()
    print(f"✓ Found built site at {site_path}")
    
    # Stash any uncommitted changes
    subprocess.run(['git', 'stash'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Check if gh-pages branch exists
        result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', 'refs/heads/gh-pages'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            # Create orphan branch if it doesn't exist
            print("Creating gh-pages branch...")
            subprocess.run(['git', 'checkout', '--orphan', 'gh-pages'], check=True)
        else:
            # Switch to gh-pages branch
            print("Switching to gh-pages branch...")
            subprocess.run(['git', 'checkout', 'gh-pages'], check=True)
        
        # Remove only tracked files (not untracked like site/)
        print("Cleaning gh-pages branch...")
        result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
        if result.stdout.strip():
            subprocess.run(['git', 'rm', '-rf', '--quiet', '.'], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Copy built site files (using absolute path from master branch)
        # Copy contents of site_path to current directory root
        print("Copying built site files...")
        files_copied = 0
        for item in site_path.iterdir():
            if item.name != '.git':
                dest = Path(item.name)
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                    files_copied += 1
                else:
                    shutil.copy2(item, dest)
                    files_copied += 1
        
        if files_copied == 0:
            print("Warning: No files to copy. Site may not have been built correctly.")
            return
        
        # Verify index.html was copied
        if not Path('index.html').exists():
            print("Error: index.html was not copied! Deployment aborted.")
            return
        
        print(f"✓ Copied {files_copied} files/directories")
        
        # Add all files
        subprocess.run(['git', 'add', '-A'], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True)
        if result.stdout.strip():
            # Commit changes
            print("Committing changes...")
            subprocess.run(['git', 'commit', '-m', 'Update site'],
                         check=True)
            
            # Push to remote
            print("Pushing to origin/gh-pages...")
            # Check if upstream exists
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            push_cmd = ['git', '-c', 'http.version=HTTP/1.1', 
                       '-c', 'http.postBuffer=524288000',
                       'push']
            if result.returncode != 0:
                # First push, set upstream
                push_cmd.extend(['-u', 'origin', 'gh-pages'])
            else:
                push_cmd.extend(['origin', 'gh-pages'])
            subprocess.run(push_cmd, check=True)
            print("✓ Successfully deployed to gh-pages!")
        else:
            print("No changes to deploy.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during deployment: {e}")
        print("Switching back to original branch...")
    finally:
        # Switch back to original branch
        print(f"Switching back to {current_branch} branch...")
        subprocess.run(['git', 'checkout', current_branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Restore stashed changes if any
        subprocess.run(['git', 'stash', 'pop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    import sys
    
    build_site()
    
    # Deploy to gh-pages if requested
    if '--deploy' in sys.argv or '-d' in sys.argv:
        deploy_to_gh_pages()
    else:
        print("\nTip: Run with --deploy to automatically deploy to gh-pages")

