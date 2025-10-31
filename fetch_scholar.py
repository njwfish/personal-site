#!/usr/bin/env python3
"""
Google Scholar Integration
Fetches publications from Google Scholar using scholarly library and merges with manual entries from papers.json.
Intelligently merges duplicates, keeping the entry with the most information.
"""
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Set
from difflib import SequenceMatcher

from scholarly import scholarly


GOOGLE_SCHOLAR_ID = "saYhrnwAAAAJ"


def normalize_title(title: str) -> str:
    """Normalize title for comparison (lowercase, remove special chars)"""
    if not title:
        return ""
    # Remove HTML tags
    title = re.sub(r'<[^>]+>', '', title)
    # Lowercase and strip
    title = title.lower().strip()
    # Remove common punctuation
    title = re.sub(r'[^\w\s]', '', title)
    return title


def title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles (0-1)"""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def count_fields(paper: Dict) -> int:
    """Count how many fields are filled in a paper entry"""
    count = 0
    fields = ['title', 'authors', 'venue', 'year', 'citation', 'pdf_link', 'pub_url', 'eprint_url', 'github_link']
    for field in fields:
        if paper.get(field) and str(paper[field]).strip():
            count += 1
    return count


def merge_paper_entries(paper1: Dict, paper2: Dict) -> Dict:
    """
    Merge two paper entries, keeping the entry with more information.
    Prefers manual entries over auto-fetched, but merges fields intelligently.
    """
    # Determine which is more complete
    count1 = count_fields(paper1)
    count2 = count_fields(paper2)
    
    # Prefer manual entries if equally complete
    if count1 == count2:
        if paper1.get('source') == 'manual' and paper2.get('source') != 'manual':
            base = paper1.copy()
            other = paper2.copy()
        elif paper2.get('source') == 'manual' and paper1.get('source') != 'manual':
            base = paper2.copy()
            other = paper1.copy()
        else:
            base = paper1.copy()
            other = paper2.copy()
    elif count1 > count2:
        base = paper1.copy()
        other = paper2.copy()
    else:
        base = paper2.copy()
        other = paper1.copy()
    
    # Merge fields, preferring non-empty values from base, but filling gaps from other
    merged = base.copy()
    
    # Merge fields that might be missing
    for field in ['authors', 'venue', 'year', 'citation', 'pub_url', 'eprint_url', 'github_link']:
        if not merged.get(field) or not str(merged[field]).strip():
            if other.get(field) and str(other[field]).strip():
                merged[field] = other[field]
    
    # Special handling for PDF links - prefer the one that exists
    if not merged.get('pdf_link') or not merged['pdf_link']:
        if other.get('pdf_link') and other['pdf_link']:
            merged['pdf_link'] = other['pdf_link']
    
    # Track sources
    sources = set()
    if merged.get('source'):
        sources.add(merged['source'])
    if other.get('source'):
        sources.add(other['source'])
    merged['source'] = ','.join(sorted(sources)) if sources else 'merged'
    
    # If either was auto-fetched, mark as potentially auto-fetched
    merged['auto_fetched'] = merged.get('auto_fetched', False) or other.get('auto_fetched', False)
    
    return merged


def fetch_google_scholar_publications() -> List[Dict]:
    """
    Fetch publications from Google Scholar using scholarly library.
    Gets full publication details including authors, venue, year, citations, and links.
    """
    publications = []
    
    try:
        print(f"Fetching publications for Google Scholar ID: {GOOGLE_SCHOLAR_ID}")
        
        # Get author profile
        author = scholarly.search_author_id(GOOGLE_SCHOLAR_ID)
        
        # Fill author profile with publications
        author = scholarly.fill(author)
        
        print(f"Found {len(author.get('publications', []))} publications")
        
        # Process each publication
        for pub in author.get('publications', []):
            try:
                # Fill publication details
                filled_pub = scholarly.fill(pub)
                
                # Extract information
                title = filled_pub.get('bib', {}).get('title', '')
                
                # Handle authors - can be list or string
                author_list = filled_pub.get('bib', {}).get('author', [])
                if isinstance(author_list, list):
                    authors = ', '.join(author_list) if author_list else ''
                elif isinstance(author_list, str):
                    authors = author_list
                else:
                    authors = str(author_list) if author_list else ''
                
                venue = filled_pub.get('bib', {}).get('venue', '') or filled_pub.get('bib', {}).get('journal', '')
                year = filled_pub.get('bib', {}).get('pub_year', '')
                citation = filled_pub.get('bib', {}).get('citation', '')
                
                # Get publication URL
                pub_url = filled_pub.get('pub_url', '')
                eprint_url = filled_pub.get('eprint_url', '')
                
                # Try to get PDF link from pub_url or eprint_url
                pdf_link = None
                if pub_url:
                    pdf_link = pub_url
                elif eprint_url:
                    pdf_link = eprint_url
                
                # Build citation string if not provided
                if not citation and (authors or venue or year):
                    citation_parts = []
                    if authors:
                        citation_parts.append(authors)
                    if title:
                        citation_parts.append(f'"{title}"')
                    if venue:
                        citation_parts.append(venue)
                    if year:
                        citation_parts.append(str(year))
                    citation = ', '.join(citation_parts)
                
                paper = {
                    'title': title,
                    'authors': authors,
                    'venue': venue or '',
                    'year': str(year) if year else '',
                    'citation': citation,
                    'pdf_link': pdf_link,
                    'pub_url': pub_url,
                    'eprint_url': eprint_url,
                    'source': 'google_scholar',
                    'auto_fetched': True
                }
                
                if title:  # Only add if we have a title
                    publications.append(paper)
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing publication: {e}")
                continue
        
        print(f"Successfully fetched {len(publications)} publications from Google Scholar")
        
    except Exception as e:
        print(f"Error fetching from Google Scholar: {e}")
        print("Continuing with existing papers only...")
        import traceback
        traceback.print_exc()
    
    return publications


def load_existing_papers(papers_json: Path) -> List[Dict]:
    """Load existing papers from papers.json, handling both old and new formats"""
    if not papers_json.exists():
        return []
    
    try:
        with open(papers_json, 'r') as f:
            papers_data = json.load(f)
        
        # Handle both formats: dict with published/working or flat list
        if isinstance(papers_data, dict):
            all_papers = papers_data.get('published', []) + papers_data.get('working', [])
        else:
            all_papers = papers_data
        
        return all_papers
    except Exception as e:
        print(f"Error loading existing papers: {e}")
        return []


def organize_papers(papers: List[Dict]) -> Dict:
    """Organize papers into published and working sections"""
    published = []
    working = []
    
    for paper in papers:
        venue = paper.get('venue', '').lower()
        year = paper.get('year', '')
        
        # Determine if published
        is_published = False
        if venue and venue.strip():
            # Check for working paper indicators
            if 'in preparation' in venue.lower() or 'in prep' in venue.lower():
                is_published = False
            # Check if venue looks like a real publication venue
            elif any(journal in venue.lower() for journal in [
                'science', 'nature', 'advances in neural', 'neurips', 'proceedings', 
                'journal', 'conference', 'arxiv', 'transactions', 'icml', 'acl', 'opt',
                'tac', 'ijcai', 'aaai', 'iclr', 'jmlr', 'pami', 'cvpr', 'eccv', 'iccv'
            ]):
                is_published = True
            elif year and year.isdigit() and int(year) >= 2018:
                is_published = True
        
        if is_published:
            published.append(paper)
        else:
            working.append(paper)
    
    # Sort by year (newest first)
    published.sort(key=lambda p: (p.get('year', '') or '0'), reverse=True)
    working.sort(key=lambda p: (p.get('year', '') or '0'), reverse=True)
    
    return {'published': published, 'working': working}


def deduplicate_and_merge_papers(existing_papers: List[Dict], scholar_papers: List[Dict]) -> List[Dict]:
    """
    Intelligently merge papers, deduplicating by title similarity.
    Keeps the entry with the most information.
    """
    # Separate manual papers from existing ones
    manual_papers = [p for p in existing_papers if p.get('source') == 'manual' or not p.get('auto_fetched', False)]
    
    # Start with all papers
    all_papers = manual_papers + scholar_papers
    
    # Group similar papers
    merged_papers = []
    processed_indices: Set[int] = set()
    
    for i, paper1 in enumerate(all_papers):
        if i in processed_indices:
            continue
        
        # Find similar papers
        similar_papers = [paper1]
        
        for j, paper2 in enumerate(all_papers[i+1:], start=i+1):
            if j in processed_indices:
                continue
            
            # Check title similarity
            similarity = title_similarity(paper1.get('title', ''), paper2.get('title', ''))
            
            # Consider similar if similarity > 0.85 (85% match)
            if similarity > 0.85:
                similar_papers.append(paper2)
                processed_indices.add(j)
        
        # Merge all similar papers
        merged = similar_papers[0]
        for similar in similar_papers[1:]:
            merged = merge_paper_entries(merged, similar)
        
        merged_papers.append(merged)
        processed_indices.add(i)
    
    return merged_papers


def update_papers_config(papers: List[Dict], output_file: Path):
    """Save papers to a JSON config file, organized by published/working"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Organize papers
    organized = organize_papers(papers)
    
    with open(output_file, 'w') as f:
        json.dump(organized, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(organized['published'])} published and {len(organized['working'])} working papers to {output_file}")


def main():
    """Main function to fetch and merge publications"""
    base_dir = Path(__file__).parent
    papers_json = base_dir / 'njwfish' / 'papers.json'
    
    print("=" * 60)
    print("Google Scholar Publication Fetcher")
    print("=" * 60)
    
    # Load existing papers.json
    print("\nLoading existing papers...")
    existing_papers = load_existing_papers(papers_json)
    print(f"Found {len(existing_papers)} existing papers")
    
    # Extract manual papers (those not auto-fetched)
    manual_papers = [p for p in existing_papers if not p.get('auto_fetched', False) or p.get('source') == 'manual']
    print(f"  - {len(manual_papers)} manual entries")
    print(f"  - {len(existing_papers) - len(manual_papers)} previously auto-fetched")
    
    print("\nFetching publications from Google Scholar...")
    scholar_papers = fetch_google_scholar_publications()
    
    print("\nMerging and deduplicating publications...")
    merged = deduplicate_and_merge_papers(manual_papers, scholar_papers)
    
    print(f"\nTotal after merging: {len(merged)} unique publications")
    
    # Show merge statistics
    manual_count = sum(1 for p in merged if p.get('source') == 'manual' or not p.get('auto_fetched', False))
    scholar_count = sum(1 for p in merged if p.get('source') == 'google_scholar' and p.get('auto_fetched', False))
    merged_count = sum(1 for p in merged if ',' in p.get('source', ''))
    print(f"  - Manual only: {manual_count}")
    print(f"  - Google Scholar only: {scholar_count}")
    print(f"  - Merged (both sources): {merged_count}")
    
    # Save merged list
    update_papers_config(merged, papers_json)
    
    print("\n" + "=" * 60)
    print("Done! Check papers.json for the merged results.")
    print("=" * 60)


if __name__ == '__main__':
    main()
