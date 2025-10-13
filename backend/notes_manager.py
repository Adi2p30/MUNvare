"""
Enhanced notes manager with folders and templates
"""
import os
import json
from datetime import datetime
from typing import List, Dict

class NotesManager:
    """Manages hierarchical notes with folders and templates"""

    def __init__(self, notes_dir="./data/notes_v2"):
        self.notes_dir = notes_dir
        self.folders_file = os.path.join(notes_dir, "folders.json")
        os.makedirs(notes_dir, exist_ok=True)
        self.folders = self.load_folders()

    def load_folders(self) -> List[Dict]:
        """Load folder structure"""
        if os.path.exists(self.folders_file):
            with open(self.folders_file, 'r') as f:
                return json.load(f)
        return self.create_default_folders()

    def create_default_folders(self) -> List[Dict]:
        """Create default folder structure"""
        folders = [
            {'id': 'research', 'name': 'Research', 'icon': '🔍'},
            {'id': 'speeches', 'name': 'Speeches', 'icon': '🎤'},
            {'id': 'poi', 'name': 'POI Questions', 'icon': '❓'},
            {'id': 'lobbying', 'name': 'Lobbying Strategy', 'icon': '🤝'},
            {'id': 'documentation', 'name': 'Documentation', 'icon': '📄'},
            {'id': 'general', 'name': 'General Notes', 'icon': '📝'}
        ]
        self.save_folders(folders)
        return folders

    def save_folders(self, folders: List[Dict]):
        """Save folder structure"""
        with open(self.folders_file, 'w') as f:
            json.dump(folders, f, indent=2)
        self.folders = folders

    def create_folder(self, name: str, icon: str = "📁") -> Dict:
        """Create a new folder"""
        folder_id = f"folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        folder = {'id': folder_id, 'name': name, 'icon': icon}
        self.folders.append(folder)
        self.save_folders(self.folders)
        return folder

    def get_templates(self) -> List[Dict]:
        """Get note templates"""
        return [
            {
                'id': 'country_research',
                'name': 'Country Research',
                'folder': 'research',
                'content': """# Country Research: [Country Name]

## Basic Information
- **Official Name:**
- **Capital:**
- **Population:**
- **Government Type:**
- **GDP:**
- **Major Allies:**

## Position on Agenda
### Current Stance
[Describe the country's official position]

### Historical Context
[Past actions and policies]

### Key Statements
-

## Domestic Factors
### Economic Interests
-

### Political Climate
-

### Public Opinion
-

## International Relations
### Alliances
-

### Conflicts/Tensions
-

## Likely Position in Committee
[Predict how they'll vote and argue]

## Sources
1.
"""
            },
            {
                'id': 'speech_draft',
                'name': 'Speech Draft',
                'folder': 'speeches',
                'content': """# Speech Draft: [Topic]

**Type:** GSL / Moderated Caucus / Opening / Closing
**Time:** 90 seconds
**Date:** [Date]

## Opening Statement
[Hook or greeting]

## Main Points

### Point 1: [Title]
[Content with facts and statistics]

### Point 2: [Title]
[Content with facts and statistics]

### Point 3: [Title]
[Content with facts and statistics]

## Call to Action / Closing
[What you want the committee to do]

## Delivery Notes
-
-

## Key Stats to Mention
-
"""
            },
            {
                'id': 'poi_prep',
                'name': 'POI Preparation',
                'folder': 'poi',
                'content': """# POI Questions Preparation

## Target Countries

### [Country 1]
**Weaknesses to Exploit:**
-

**Questions:**
1.
2.
3.

### [Country 2]
**Weaknesses to Exploit:**
-

**Questions:**
1.
2.
3.

## Defensive POIs (Expected Questions Against Me)

### Question 1: [Predicted question]
**Answer:**

### Question 2: [Predicted question]
**Answer:**

## Follow-up Strategy
[How to press further if they give weak answers]
"""
            },
            {
                'id': 'lobbying_plan',
                'name': 'Lobbying Strategy',
                'folder': 'lobbying',
                'content': """# Lobbying Strategy

## My Position
[Clear statement of what I want to achieve]

## Target Allies
### High Priority
- **[Country 1]:** Why they'll support us / What we offer them
- **[Country 2]:** Why they'll support us / What we offer them

### Medium Priority
-

### Swing Votes
-

## Opposition Analysis
**Main Opponents:**
-

**Their Likely Arguments:**
-

**Counter-Strategies:**
-

## Moderated Caucus Topics to Propose
1.
2.
3.

## Unmod Caucus Plan
**First 5 minutes:**
-

**Next 10 minutes:**
-

**Final push:**
-

## Documentation Strategy
[What clauses I want, who to co-sponsor with]
"""
            },
            {
                'id': 'resolution_draft',
                'name': 'Resolution Draft',
                'folder': 'documentation',
                'content': """# Draft Resolution

**Committee:** [Committee name]
**Topic:** [Agenda]
**Sponsors:** [Countries]
**Signatories:** [Countries]

## Preambulatory Clauses

*Recalling* [past UN resolution or action],

*Noting with concern* [problem statement],

*Emphasizing* [importance of the issue],

*Recognizing* [positive efforts or frameworks],

## Operative Clauses

1. *Calls upon* member states to [action];

2. *Requests* the Secretary-General to [action];

3. *Encourages* [specific groups] to [action];

4. *Recommends* that states [action];

5. *Decides* to establish [mechanism/program];

## Implementation Notes
[How this will actually work]

## Expected Opposition
[Which countries might oppose and why]
"""
            },
            {
                'id': 'committee_notes',
                'name': 'Committee Session Notes',
                'folder': 'general',
                'content': """# Committee Session Notes

**Date:** [Date]
**Session:** Day [X] / Session [Y]

## Key Speeches
### [Country Name]
- Main points:
- Notable quotes:
- Stance:

### [Country Name]
- Main points:
- Notable quotes:
- Stance:

## Moderated Caucuses
### Topic: [Topic]
**Key takeaways:**
-

**Emerging consensus:**
-

**Divisions:**
-

## Lobbying Progress
**Successfully lobbied:**
-

**Need to follow up:**
-

**Lost causes:**
-

## Action Items
- [ ]
- [ ]
- [ ]

## Strategy Adjustments
[What I need to change based on today]
"""
            }
        ]

    def create_note_from_template(self, template_id: str, title: str = None) -> Dict:
        """Create a note from a template"""
        templates = self.get_templates()
        template = next((t for t in templates if t['id'] == template_id), None)

        if not template:
            return None

        note_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        note = {
            'id': note_id,
            'title': title or template['name'],
            'folder': template['folder'],
            'content': template['content'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'analysis': None
        }

        note_file = os.path.join(self.notes_dir, f"{note_id}.json")
        with open(note_file, 'w') as f:
            json.dump(note, f, indent=2)

        return note

    def get_all_notes_context(self) -> str:
        """Get all notes content as context for LLM"""
        context_parts = []

        for filename in os.listdir(self.notes_dir):
            if filename.endswith('.json') and filename != 'folders.json':
                note_file = os.path.join(self.notes_dir, filename)
                with open(note_file, 'r') as f:
                    note = json.load(f)
                    context_parts.append(f"### {note['title']}\n{note['content']}\n")

        if not context_parts:
            return ""

        return "USER'S NOTES:\n\n" + "\n---\n".join(context_parts)
