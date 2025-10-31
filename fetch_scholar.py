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
from typing import List, Dict, Set
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


def format_author_list(authors, bold_name="Nic Fishman"):
    """
    Format author list with proper comma/and delimiters and bold the specified name.
    
    Rules:
    - <= 3 authors: use "and" between all (e.g., "A and B and C")
    - > 3 authors: use commas with "and" before last (e.g., "A, B, C, and D")
    - Bold the specified name if it appears in the list
    """
    if not authors:
        return ""
    
    # Handle list or string input
    if isinstance(authors, list):
        author_list = [str(a).strip() for a in authors if str(a).strip()]
    elif isinstance(authors, str):
        # Parse string - handle comma and "and" separators
        author_list = []
        # Split by "and" first, then by commas
        parts = re.split(r'\s+and\s+', authors)
        for part in parts:
            sub_parts = [p.strip() for p in part.split(',') if p.strip()]
            author_list.extend(sub_parts)
        author_list = [a.strip() for a in author_list if a.strip()]
    else:
        author_list = [str(authors).strip()] if str(authors).strip() else []
    
    if not author_list:
        return ""
    
    # Format each author, bolding if name matches
    formatted_authors = []
    for author in author_list:
        author_str = str(author).strip()
        # Remove existing HTML tags to check if name matches
        clean_author = re.sub(r'<[^>]+>', '', author_str)
        
        # Check if this author should be bolded (case-insensitive partial match)
        # Only add bold tags if not already present
        if '<b>' in author_str or '<strong>' in author_str:
            # Already has bold tags, keep as is
            formatted_authors.append(author_str)
        elif bold_name.lower() in clean_author.lower():
            formatted_authors.append(f'<b>{author_str}</b>')
        else:
            formatted_authors.append(author_str)
    
    # Join according to rules
    if len(formatted_authors) == 1:
        return formatted_authors[0]
    elif len(formatted_authors) == 2:
        return f"{formatted_authors[0]} and {formatted_authors[1]}"
    elif len(formatted_authors) == 3:
        return f"{formatted_authors[0]} and {formatted_authors[1]} and {formatted_authors[2]}"
    else:
        # > 3 authors: commas with "and" before last
        return ', '.join(formatted_authors[:-1]) + ', and ' + formatted_authors[-1]


def extract_venue_from_citation(citation: str) -> str:
    """Extract venue from citation string when venue field is missing"""
    if not citation:
        return ""
    
    citation = citation.strip()
    
    # Common patterns in citations:
    # "OPT 2024: Optimization for Machine Learning, 2024"
    # "Proceedings of the 2022 ACM Conference on Fairness, Accountability, and …, 2022"
    
    # Pattern 1: "Venue Year: Description, Year" - extract everything before the colon
    # Keep the year if it's part of the venue name (e.g., "OPT 2024")
    match = re.match(r'^([^:]+?):', citation)
    if match:
        venue = match.group(1).strip()
        if venue:
            return venue
    
    # Pattern 2: Remove trailing year if present (e.g., ", 2024" or " 2024")
    citation_clean = re.sub(r',\s*\d{4}$', '', citation)
    citation_clean = re.sub(r'\s+\d{4}$', '', citation_clean)
    
    # Pattern 3: If there's a colon, take everything before it
    if ':' in citation_clean:
        venue = citation_clean.split(':')[0].strip()
        if venue:
            return venue
    
    # Pattern 4: Split by comma and take everything except standalone years
    parts = citation_clean.split(',')
    if len(parts) > 1:
        venue_parts = []
        for part in parts:
            part = part.strip()
            # Skip if it's just a year or empty
            if not re.match(r'^\d{4}$', part) and part:
                venue_parts.append(part)
        if venue_parts:
            venue = ', '.join(venue_parts)
            # Clean up trailing commas, "and,", and ellipsis
            venue = venue.rstrip('…').strip()
            venue = re.sub(r',\s*$', '', venue)  # Remove trailing comma
            venue = re.sub(r'\s+and\s*,\s*$', '', venue)  # Remove "and," at end
            venue = re.sub(r'\s+and\s*$', '', venue)  # Remove trailing "and"
            return venue.strip()
    
    # Fallback: return cleaned citation
    venue = citation_clean.rstrip('…').strip()
    venue = re.sub(r',\s*$', '', venue)  # Remove trailing comma
    venue = re.sub(r'\s+and\s*,\s*$', '', venue)  # Remove "and," at end
    return venue.strip()


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
    Merge two paper entries, preferring Google Scholar data (more up-to-date)
    but preserving local-only fields like github_link.
    """
    # Determine which is from Google Scholar and which is local/manual
    paper1_is_scholar = paper1.get('source') == 'google_scholar' or paper1.get('auto_fetched', False)
    paper2_is_scholar = paper2.get('source') == 'google_scholar' or paper2.get('auto_fetched', False)
    
    # Prefer Google Scholar as base (more up-to-date), but fall back to more complete entry
    if paper1_is_scholar and not paper2_is_scholar:
        # paper1 is from Google Scholar, use it as base
        base = paper1.copy()
        local = paper2.copy()
    elif paper2_is_scholar and not paper1_is_scholar:
        # paper2 is from Google Scholar, use it as base
        base = paper2.copy()
        local = paper1.copy()
    else:
        # Both or neither from Google Scholar - use more complete as base
        count1 = count_fields(paper1)
        count2 = count_fields(paper2)
        if count1 >= count2:
            base = paper1.copy()
            local = paper2.copy()
        else:
            base = paper2.copy()
            local = paper1.copy()
    
    # Start with Google Scholar/base entry
    merged = base.copy()
    
    # Fields that Google Scholar provides - prefer base (Google Scholar) but fill gaps from local
    scholar_fields = ['title', 'authors', 'venue', 'year', 'citation', 'pub_url', 'eprint_url', 'pdf_link']
    for field in scholar_fields:
        # If base is missing this field, fill from local
        if not merged.get(field) or not str(merged[field]).strip():
            if local.get(field) and str(local[field]).strip():
                merged[field] = local[field]
    
    # Fields that are typically local-only - always preserve from local if present
    local_only_fields = ['github_link']
    for field in local_only_fields:
        if local.get(field) and str(local[field]).strip():
            merged[field] = local[field]
    
    # If venue is still missing but citation exists, try to extract venue from citation
    if not merged.get('venue') or not str(merged.get('venue', '')).strip():
        citation = merged.get('citation', '')
        if citation:
            extracted_venue = extract_venue_from_citation(citation)
            if extracted_venue:
                merged['venue'] = extracted_venue
    
    # Track sources
    sources = set()
    if merged.get('source'):
        sources.add(merged['source'])
    if local.get('source'):
        sources.add(local['source'])
    merged['source'] = ','.join(sorted(sources)) if sources else 'merged'
    
    # If either was auto-fetched, mark as potentially auto-fetched
    merged['auto_fetched'] = merged.get('auto_fetched', False) or local.get('auto_fetched', False)
    
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
                # Format authors with proper comma/and delimiters and bold Nic Fishman
                authors = format_author_list(author_list, bold_name="Nic Fishman")
                
                venue = filled_pub.get('bib', {}).get('venue', '') or filled_pub.get('bib', {}).get('journal', '')
                year = filled_pub.get('bib', {}).get('pub_year', '')
                citation = filled_pub.get('bib', {}).get('citation', '')
                
                # If venue is missing but citation exists, try to extract venue from citation
                if not venue and citation:
                    venue = extract_venue_from_citation(citation)
                
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
        venue = paper.get('venue', '').strip()
        citation = paper.get('citation', '').strip()
        
        # If venue is empty but citation exists, try to extract venue from citation
        if not venue and citation:
            venue = extract_venue_from_citation(citation)
            paper['venue'] = venue
        
        # Format authors consistently
        authors = paper.get('authors', '')
        if authors and isinstance(authors, str) and authors.strip():
            paper['authors'] = format_author_list(authors, bold_name="Nic Fishman")
        
        venue_lower = venue.lower() if venue else ''
        
        # Check for working paper indicators
        if not venue_lower:
            # No venue = working paper
            working.append(paper)
        elif 'in preparation' in venue_lower or 'in prep' in venue_lower:
            # Explicitly marked as working
            working.append(paper)
        elif 'arxiv' in venue_lower:
            # arXiv-only = working paper
            working.append(paper)
        else:
            # Has venue = published
            published.append(paper)
    
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
