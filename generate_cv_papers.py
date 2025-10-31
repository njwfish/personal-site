#!/usr/bin/env python3
"""
Generate CV publications section from papers.json
"""
import json
import re
from pathlib import Path

def escape_latex(text):
    """Escape LaTeX special characters"""
    if not text:
        return ""
    text = str(text)
    # Escape special characters
    special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\^{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}',
    }
    for char, escaped in special_chars.items():
        text = text.replace(char, escaped)
    return text

def format_authors(authors_str, bold_name="Fishman"):
    """Format authors string, bolding the specified name"""
    if not authors_str:
        return ""
    
    # Remove HTML tags but preserve their intent
    # Check if bold tags are already present - if so, mark authors that had tags
    bold_positions = set()
    if '<b>' in authors_str or '<strong>' in authors_str:
        # Find positions where bold tags were
        import re as re2
        for match in re2.finditer(r'<[bB]>(.*?)</[bB]>|<strong>(.*?)</strong>', authors_str):
            bold_text = match.group(1) or match.group(2)
            # Mark any author containing this text as bold
            bold_positions.add(bold_text.lower())
    
    # Remove HTML tags
    authors_str = re.sub(r'<[^>]+>', '', authors_str)
    
    # Split by common separators
    # Handle "and" as separator
    authors = []
    parts = re.split(r'\s+and\s+', authors_str)
    for part in parts:
        # Split by comma
        sub_parts = [p.strip() for p in part.split(',') if p.strip()]
        authors.extend(sub_parts)
    
    # Clean up empty entries
    authors = [a.strip() for a in authors if a.strip()]
    
    formatted = []
    for author in authors:
        if not author:
            continue
        
        # Check if this author should be bolded
        should_bold = False
        author_lower = author.lower()
        
        # Check if name matches
        if bold_name.lower() in author_lower:
            should_bold = True
        
        # Check if it was in bold tags
        for bold_text in bold_positions:
            if bold_text in author_lower:
                should_bold = True
                break
        
        if should_bold:
            formatted.append(r'\textbf{' + escape_latex(author) + '}')
        else:
            formatted.append(escape_latex(author))
    
    # Join with ", " and "and" appropriately
    # <= 3 authors: use "and" between all
    # > 3 authors: use commas with "and" before last
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return formatted[0] + ' and ' + formatted[1]
    elif len(formatted) == 3:
        return formatted[0] + ' and ' + formatted[1] + ' and ' + formatted[2]
    else:
        # > 3 authors: commas with "and" before last
        return ', '.join(formatted[:-1]) + ', and ' + formatted[-1]

def format_venue(venue_str):
    """Format venue string"""
    if not venue_str:
        return ""
    
    venue_str = escape_latex(venue_str)
    
    # Clean up common patterns
    venue_str = re.sub(r'\s+', ' ', venue_str)
    venue_str = venue_str.strip()
    
    return f"\\textit{{{venue_str}}}"

def format_paper(paper, is_working=False):
    """Format a single paper entry"""
    title = escape_latex(paper.get('title', 'Untitled'))
    authors = format_authors(paper.get('authors', ''))
    venue = paper.get('venue', '')
    year = paper.get('year', '')
    
    # Format the entry: Authors, Year. Title. Venue.
    parts = []
    
    if authors:
        parts.append(authors + ",")
    
    if year:
        parts.append(f"{year}.")
    else:
        # If no year, just add period after authors comma
        if authors:
            parts.append(".")
    
    parts.append(title + ".")
    
    if venue:
        venue_formatted = format_venue(venue)
        if venue_formatted:
            parts.append(venue_formatted + ".")
    
    # Join parts with spaces
    entry = " ".join(parts)
    
    return entry

def generate_cv_writing(papers_json_path, output_path):
    """Generate CV writing.tex file from papers.json"""
    
    # Load papers
    with open(papers_json_path, 'r') as f:
        papers_data = json.load(f)
    
    # Extract published and working papers
    if isinstance(papers_data, dict):
        published_papers = papers_data.get('published', [])
        working_papers = papers_data.get('working', [])
    else:
        # Old format - organize
        published_papers = []
        working_papers = []
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
    
    # Sort by year (newest first)
    published_papers.sort(key=lambda p: (p.get('year', '') or '0'), reverse=True)
    working_papers.sort(key=lambda p: (p.get('year', '') or '0'), reverse=True)
    
    # Generate LaTeX
    latex_content = """%-------------------------------------------------------------------------------
%	SECTION TITLE
%-------------------------------------------------------------------------------
\\cvsection{Publications}
\\begin{cvparagraph}

\\honorpositionstyle{Published Papers}

\\begin{addmargin}[2em]{0em}

"""
    
    # Add published papers
    for paper in published_papers:
        entry = format_paper(paper, is_working=False)
        latex_content += entry + "\n\n"
    
    latex_content += """\\end{addmargin}

\\honorpositionstyle{Working Papers}

\\begin{addmargin}[2em]{0em}

"""
    
    # Add working papers
    for paper in working_papers:
        entry = format_paper(paper, is_working=True)
        latex_content += entry + "\n\n"
    
    latex_content += """\\end{addmargin}

\\end{cvparagraph}
"""
    
    # Write output
    with open(output_path, 'w') as f:
        f.write(latex_content)
    
    print(f"Generated CV writing section: {output_path}")
    print(f"  Published papers: {len(published_papers)}")
    print(f"  Working papers: {len(working_papers)}")

if __name__ == '__main__':
    import sys
    
    # Default paths
    papers_json = Path(__file__).parent / 'njwfish' / 'papers.json'
    output_file = Path(__file__).parent / 'latex_cv' / 'resume' / 'writing.tex'
    
    if len(sys.argv) > 1:
        papers_json = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    generate_cv_writing(papers_json, output_file)

