# Personal Website - Static Site Generator

A modern, static site generator for your personal website. This replaces the Flask-based server with a simple Python build script that generates static HTML files.

## Features

- ✅ **Static Site Generation** - No server needed, just HTML files
- ✅ **Modern Design** - Clean, responsive design with improved typography
- ✅ **Blog Support** - Easy markdown-based blog posts
- ✅ **Projects Page** - Showcase your work with a beautiful grid layout
- ✅ **Papers Page** - Improved styling for your publications
- ✅ **Cheap Hosting** - Deploy to GitHub Pages, Netlify, or Vercel for free

## Structure

```
njwfish/
├── static/              # Source files
│   ├── about.md         # About page content
│   ├── posts/           # Blog posts (each in its own folder)
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript
│   └── ...
├── templates/           # Jinja2 templates
├── talks.json           # Talks metadata
└── ...

site/                    # Generated static site (output)
```

## Usage

### Building the Site

**With conda environment:**
```bash
conda activate website-build
python3 build.py
```

**Or use the helper script:**
```bash
./build.sh
```

**Without conda:**
```bash
python3 build.py
```

This will:
1. Read all markdown files and templates
2. Convert markdown to HTML
3. Generate static HTML files in the `site/` directory
4. Copy static assets (CSS, JS, images, etc.)

### Adding a New Blog Post

1. Create a new folder in `njwfish/static/posts/` (e.g., `my-new-post/`)
2. Create three files:
   - `title` - The post title
   - `blurb` - A short description
   - `main.md` or `main.html` - The post content

Example:
```
njwfish/static/posts/my-new-post/
├── title
├── blurb
└── main.md
```

### Updating Papers

Papers are automatically fetched from Google Scholar when you run `build.py`. To manually update:

```bash
python3 fetch_scholar.py
```

Or edit `njwfish/papers.json` directly. The CV will automatically update with all papers from `papers.json`.

### Adding a Talk

Edit `njwfish/talks.json`:

```json
[
    {
        "title": "My Talk Title",
        "venue": "Conference Name",
        "location": "City, Country",
        "date": "2024",
        "slides": "/static/slides/my-slides.pdf",
        "video": "https://...",
        "links": []
    }
]
```

### Deploying

#### Option 1: GitHub Pages (Free)

1. Push the `site/` directory to a `gh-pages` branch
2. Enable GitHub Pages in your repo settings

Or use GitHub Actions to auto-build on push.

#### Option 2: Netlify (Free)

1. Install Netlify CLI: `npm install -g netlify-cli`
2. Build command: `python3 build.py`
3. Publish directory: `site`
4. Deploy: `netlify deploy --prod`

#### Option 3: Vercel (Free)

1. Install Vercel CLI: `npm install -g vercel`
2. Build command: `python3 build.py`
3. Output directory: `site`
4. Deploy: `vercel --prod`

## Development

### Local Testing

After building, you can serve the site locally:

```bash
# Using Python
cd site
python3 -m http.server 8000

# Or using Node.js
npx serve site
```

Then visit `http://localhost:8000`

## Requirements

- Python 3.6+ (Python 3.9 recommended)
- `markdown` package
- `jinja2` package

### Installation Options

**Conda (Recommended):**
```bash
conda env create -f environment.yml
conda activate website-build
```

**pip:**
```bash
pip install markdown jinja2
```

## Migrating from Flask

The old Flask app is still in `njwfish/njwfish.py` and `njwfish/core.py`. You can:

1. Keep it for reference
2. Delete it once you've migrated
3. Run both in parallel during transition

The new system uses the same content structure, so your posts will work immediately.

## Customization

- **Colors**: Edit CSS variables in `njwfish/static/css/main.css`
- **Layout**: Modify templates in `njwfish/templates/`
- **Styling**: Update CSS in `njwfish/static/css/main.css`

## Notes

- Posts are sorted by modification date (newest first)
- The build script preserves your existing post structure
- All static assets are copied to the `site/` directory
- The site is fully static - no server-side code needed
