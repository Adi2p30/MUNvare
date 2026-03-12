"""
Generate pre-made notes from the MUN book for quick reference
"""
import os
import json
from core.vectordb import initialize_vector_db
from core.ai_service import AIService


def generate_premade_notes():
    """Generate structured notes from each section of the MUN book"""

    print("Initializing services...")
    vectordb = initialize_vector_db()
    ai_service = AIService(vectordb)

    sections = [
        {"id": "introduction", "title": "Introduction to MUN", "query": "What is MUN and why should I participate?"},
        {"id": "un_structure", "title": "UN Structure", "query": "Explain the structure of the UN and its committees"},
        {"id": "committees", "title": "MUN Committees", "query": "What are the different MUN committees like ECOSOC, UNSC, UNHRC, DISEC, etc?"},
        {"id": "rules_of_procedure", "title": "Rules of Procedure", "query": "Explain MUN rules of procedure including GSL, motions, caucuses"},
        {"id": "research", "title": "Research Guide", "query": "How to research effectively for MUN?"},
        {"id": "speeches", "title": "Making Speeches", "query": "How to write and deliver effective MUN speeches?"},
        {"id": "poi", "title": "Points of Information", "query": "What are Points of Information and how to use them effectively?"},
        {"id": "lobbying", "title": "Lobbying", "query": "Explain lobbying in MUN and how to build blocs"},
        {"id": "foreign_policy", "title": "Foreign Policy", "query": "How to understand and represent a country's foreign policy?"},
        {"id": "documentation", "title": "Documentation", "query": "Explain MUN documentation including resolutions, working papers"},
        {"id": "voting", "title": "Voting Procedure", "query": "What is the voting procedure in MUN?"},
        {"id": "impact", "title": "Making an Impact", "query": "How to make an impact in MUN committee and win awards?"},
        {"id": "tips", "title": "Tips and Tricks", "query": "What are essential tips for success in MUN?"},
    ]

    premade_notes_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'premade_notes')
    os.makedirs(premade_notes_dir, exist_ok=True)

    for i, section in enumerate(sections):
        print(f"\n[{i+1}/{len(sections)}] Generating notes for: {section['title']}")

        # Get context from vector database
        context = vectordb.get_context_for_query(section['query'], max_context_length=4000)

        # Generate structured notes
        prompt = f"""Based on the following content from the MUN guidebook, create comprehensive, well-structured notes on: {section['title']}

CONTENT:
{context}

Create notes that include:
1. **Overview** - Brief introduction to the topic
2. **Key Points** - Main concepts and important information (use bullet points)
3. **Practical Tips** - Actionable advice for delegates
4. **Examples** - Concrete examples where relevant
5. **Common Mistakes** - What to avoid

Format the notes in markdown for easy reading. Be thorough but concise."""

        notes_content = ai_service.chat_with_context(prompt)

        # Save notes
        note_data = {
            'id': section['id'],
            'title': section['title'],
            'content': notes_content,
            'category': 'premade',
            'source': 'MUN Book Analysis'
        }

        note_file = os.path.join(premade_notes_dir, f"{section['id']}.json")
        with open(note_file, 'w') as f:
            json.dump(note_data, f, indent=2)

        print(f"✓ Saved: {note_file}")

    print("\n" + "="*50)
    print(f"Successfully generated {len(sections)} premade notes!")
    print(f"Location: {premade_notes_dir}")
    print("="*50)


if __name__ == "__main__":
    generate_premade_notes()
