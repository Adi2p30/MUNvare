"""
Create static study guides from the MUN book without AI
"""
import os
import json
from datetime import datetime

def create_static_guides():
    """Create basic study guides from MUN book sections"""

    premade_notes_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'premade_notes')
    os.makedirs(premade_notes_dir, exist_ok=True)

    # Read the MUN book
    book_path = os.path.join(os.path.dirname(__file__), '..', 'MUN Book .txt')
    with open(book_path, 'r', encoding='utf-8') as f:
        book_content = f.read()

    # Define sections to extract
    guides = [
        {
            'id': 'introduction',
            'title': 'Introduction to MUN',
            'keywords': ['What is MUN', 'Model United Nations', 'Introduction']
        },
        {
            'id': 'committees',
            'title': 'MUN Committees',
            'keywords': ['ECOSOC', 'UNSC', 'UNHRC', 'DISEC', 'Committee']
        },
        {
            'id': 'rules_of_procedure',
            'title': 'Rules of Procedure',
            'keywords': ['Rules of Procedure', 'GSL', 'Moderated Caucus', 'Unmoderated']
        },
        {
            'id': 'research',
            'title': 'Research Guide',
            'keywords': ['Research', 'Background Guide', 'Preparation']
        },
        {
            'id': 'speeches',
            'title': 'Making Speeches',
            'keywords': ['speeches', 'Speaking', 'GSL speech', 'Opening statement']
        },
        {
            'id': 'poi',
            'title': 'Points of Information',
            'keywords': ['Point of Information', 'POI', 'Questions']
        },
        {
            'id': 'lobbying',
            'title': 'Lobbying',
            'keywords': ['Lobbying', 'Bloc', 'Allies', 'Negotiation']
        },
        {
            'id': 'foreign_policy',
            'title': 'Foreign Policy',
            'keywords': ['Foreign Policy', 'Country position', 'National interest']
        },
        {
            'id': 'documentation',
            'title': 'Documentation',
            'keywords': ['Resolution', 'Working Paper', 'Draft Resolution', 'Clauses']
        },
        {
            'id': 'voting',
            'title': 'Voting Procedure',
            'keywords': ['Voting', 'Vote', 'Consensus', 'Roll call']
        }
    ]

    print("Creating static study guides from MUN book...\n")

    for guide in guides:
        print(f"Creating: {guide['title']}")

        # Extract relevant section
        content_parts = []
        lines = book_content.split('\n')

        # Find sections matching keywords
        in_relevant_section = False
        section_content = []

        for i, line in enumerate(lines):
            line = line.strip()

            # Check if line matches any keyword
            if any(keyword.lower() in line.lower() for keyword in guide['keywords']):
                in_relevant_section = True
                section_content = [line]
                continue

            # If in relevant section, collect lines until we hit a new major section
            if in_relevant_section:
                if line and (line.isupper() or line.startswith('##')):
                    # New major section, stop
                    in_relevant_section = False
                    content_parts.append('\n'.join(section_content))
                    section_content = []
                else:
                    section_content.append(line)

        # Add any remaining content
        if section_content:
            content_parts.append('\n'.join(section_content))

        # Combine and format
        content = '\n\n'.join(content_parts)

        if not content:
            content = f"# {guide['title']}\n\nPlease refer to the MUN guidebook for detailed information on {guide['title'].lower()}.\n\nKey topics to study:\n" + '\n'.join([f"- {kw}" for kw in guide['keywords']])

        # Create note
        note_data = {
            'id': guide['id'],
            'title': guide['title'],
            'content': content,
            'category': 'premade',
            'source': 'MUN Book',
            'created_at': datetime.now().isoformat()
        }

        # Save
        note_file = os.path.join(premade_notes_dir, f"{guide['id']}.json")
        with open(note_file, 'w') as f:
            json.dump(note_data, f, indent=2)

        print(f"  ✓ Saved: {note_file}")

    print(f"\n{'='*60}")
    print(f"✅ Created {len(guides)} study guides!")
    print(f"📁 Location: {premade_notes_dir}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    create_static_guides()
