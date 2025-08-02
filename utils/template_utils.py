"""
Utilities for working with CV and cover letter templates.
Provides functions for loading, parsing, and populating templates.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class TemplateLoader:
    """Loads and manages document templates."""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
    
    def load_cv_template(self) -> str:
        """Load the CV template structure."""
        cv_template_path = self.template_dir / "cv_template.md"
        if cv_template_path.exists():
            return cv_template_path.read_text()
        else:
            raise FileNotFoundError(f"CV template not found at {cv_template_path}")
    
    def load_cover_letter_template(self) -> str:
        """Load the cover letter template."""
        cover_letter_path = self.template_dir / "cover_letter_template.txt"
        if cover_letter_path.exists():
            return cover_letter_path.read_text()
        else:
            raise FileNotFoundError(f"Cover letter template not found at {cover_letter_path}")
    
    def load_section_template(self, section_name: str) -> str:
        """Load a specific section template."""
        section_templates = {
            "experience": "experience_entry_template.md",
            "skills": "skills_section_template.md",
            "education": "education_certification_template.md"
        }
        
        if section_name in section_templates:
            template_path = self.template_dir / section_templates[section_name]
            if template_path.exists():
                return template_path.read_text()
        
        raise ValueError(f"Unknown section template: {section_name}")


class CVBuilder:
    """Builds CV from template and data."""
    
    def __init__(self, template: str):
        self.template = template
        self.sections = self._parse_template_sections()
    
    def _parse_template_sections(self) -> Dict[str, str]:
        """Parse template into sections."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in self.template.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def build_professional_summary(self, summary_data: Dict) -> str:
        """Build professional summary section."""
        summary = summary_data.get('summary', '')
        return f"> {summary}"
    
    def build_experience_entry(self, experience: Dict) -> str:
        """Build a single experience entry."""
        entry_parts = []
        
        # Header
        title = experience.get('title', 'Position')
        company = experience.get('company', 'Company')
        entry_parts.append(f"### {title} | {company}")
        
        # Location and dates
        location = experience.get('location', 'Location')
        start_date = experience.get('start_date', 'Start')
        end_date = experience.get('end_date', 'Present')
        entry_parts.append(f"*{location} | {start_date} - {end_date}*")
        entry_parts.append("")
        
        # Description
        description = experience.get('description', '')
        if description:
            entry_parts.append(description)
            entry_parts.append("")
        
        # Achievements
        entry_parts.append("**Key Achievements:**")
        achievements = experience.get('achievements', [])
        for achievement in achievements:
            entry_parts.append(f"- {achievement}")
        entry_parts.append("")
        
        # Technologies
        technologies = experience.get('technologies', [])
        if technologies:
            tech_list = ", ".join(technologies)
            entry_parts.append(f"**Technologies:** {tech_list}")
        
        return '\n'.join(entry_parts)
    
    def build_skills_section(self, skills_data: Dict) -> str:
        """Build technical skills section."""
        section_parts = []
        
        for category, skills in skills_data.items():
            section_parts.append(f"### {category}")
            
            if isinstance(skills, dict):
                # Skills with proficiency levels
                for level, skill_list in skills.items():
                    if skill_list:
                        skills_str = ", ".join(skill_list)
                        section_parts.append(f"- **{level}**: {skills_str}")
            else:
                # Simple skill list
                for skill in skills:
                    section_parts.append(f"- {skill}")
            
            section_parts.append("")
        
        return '\n'.join(section_parts)
    
    def build_education_entry(self, education: Dict) -> str:
        """Build education entry."""
        entry_parts = []
        
        degree = education.get('degree', 'Degree')
        field = education.get('field', 'Field of Study')
        entry_parts.append(f"### {degree} in {field}")
        
        institution = education.get('institution', 'University')
        location = education.get('location', 'Location')
        year = education.get('graduation_year', 'Year')
        entry_parts.append(f"*{institution} | {location} | {year}*")
        
        # Optional details
        details = education.get('details', [])
        if details:
            for detail in details:
                entry_parts.append(f"- {detail}")
        
        return '\n'.join(entry_parts)
    
    def populate_cv(self, cv_data: Dict) -> str:
        """Populate CV template with data."""
        cv_content = []
        
        # Name header
        name = cv_data.get('name', 'Your Name')
        cv_content.append(f"# {name}")
        cv_content.append("")
        
        # Professional Summary
        cv_content.append("## Professional Summary")
        cv_content.append(self.build_professional_summary(cv_data))
        cv_content.append("")
        
        # Core Competencies (if provided)
        if 'core_competencies' in cv_data:
            cv_content.append("## Core Competencies")
            for competency in cv_data['core_competencies']:
                cv_content.append(f"- {competency}")
            cv_content.append("")
        
        # Professional Experience
        cv_content.append("## Professional Experience")
        cv_content.append("")
        for experience in cv_data.get('experiences', []):
            cv_content.append(self.build_experience_entry(experience))
            cv_content.append("")
        
        # Technical Skills
        cv_content.append("## Technical Skills")
        cv_content.append("")
        cv_content.append(self.build_skills_section(cv_data.get('skills', {})))
        
        # Education
        cv_content.append("## Education")
        cv_content.append("")
        for education in cv_data.get('education', []):
            cv_content.append(self.build_education_entry(education))
            cv_content.append("")
        
        # Certifications (if any)
        if 'certifications' in cv_data and cv_data['certifications']:
            cv_content.append("## Certifications & Professional Development")
            cv_content.append("")
            for cert in cv_data['certifications']:
                cv_content.append(f"- {cert}")
            cv_content.append("")
        
        # Additional Information (if any)
        if 'additional_info' in cv_data:
            cv_content.append("## Additional Information")
            cv_content.append("")
            cv_content.append(cv_data['additional_info'])
        
        return '\n'.join(cv_content)


class CoverLetterBuilder:
    """Builds cover letter from template and data."""
    
    def __init__(self, template: str):
        self.template = template
    
    def build_header(self, contact_info: Dict) -> str:
        """Build cover letter header."""
        header_parts = []
        
        # Sender info
        header_parts.append(contact_info.get('name', 'Your Name'))
        if 'address' in contact_info:
            header_parts.append(contact_info['address'])
        if 'city_state_zip' in contact_info:
            header_parts.append(contact_info['city_state_zip'])
        header_parts.append(contact_info.get('email', 'your.email@example.com'))
        header_parts.append(contact_info.get('phone', '(555) 123-4567'))
        header_parts.append(contact_info.get('date', 'Date'))
        header_parts.append("")
        
        # Recipient info
        if 'recipient' in contact_info:
            recipient = contact_info['recipient']
            if 'name' in recipient:
                header_parts.append(recipient['name'])
            if 'title' in recipient:
                header_parts.append(recipient['title'])
            header_parts.append(recipient.get('company', 'Company Name'))
            if 'address' in recipient:
                header_parts.append(recipient['address'])
            if 'city_state_zip' in recipient:
                header_parts.append(recipient['city_state_zip'])
        
        return '\n'.join(header_parts)
    
    def build_salutation(self, recipient_name: Optional[str] = None) -> str:
        """Build appropriate salutation."""
        if recipient_name:
            return f"Dear {recipient_name},"
        else:
            return "Dear Hiring Manager,"
    
    def populate_cover_letter(self, letter_data: Dict) -> str:
        """Populate cover letter template with data."""
        letter_parts = []
        
        # Header
        letter_parts.append(self.build_header(letter_data.get('contact_info', {})))
        letter_parts.append("")
        
        # Salutation
        recipient_name = letter_data.get('contact_info', {}).get('recipient', {}).get('name')
        letter_parts.append(self.build_salutation(recipient_name))
        letter_parts.append("")
        
        # 5-part body
        body_sections = letter_data.get('body_sections', {})
        
        # Part 1: Hook
        letter_parts.append(body_sections.get('hook', 'Opening paragraph...'))
        letter_parts.append("")
        
        # Part 2: Experience
        letter_parts.append(body_sections.get('experience', 'Experience paragraph...'))
        letter_parts.append("")
        
        # Part 3: Expertise
        letter_parts.append(body_sections.get('expertise', 'Expertise paragraph...'))
        letter_parts.append("")
        
        # Part 4: Cultural Fit
        letter_parts.append(body_sections.get('cultural_fit', 'Cultural fit paragraph...'))
        letter_parts.append("")
        
        # Part 5: Call to Action
        letter_parts.append(body_sections.get('call_to_action', 'Closing paragraph...'))
        letter_parts.append("")
        
        # Closing
        letter_parts.append("Sincerely,")
        letter_parts.append(letter_data.get('contact_info', {}).get('name', 'Your Name'))
        
        return '\n'.join(letter_parts)


class TemplateValidator:
    """Validates populated templates against formatting rules."""
    
    @staticmethod
    def validate_markdown_syntax(content: str) -> List[str]:
        """Check for valid Markdown syntax."""
        errors = []
        
        # Check for unclosed formatting
        if content.count('**') % 2 != 0:
            errors.append("Unclosed bold formatting (**)")
        if content.count('*') % 2 != 0 and (content.count('*') - content.count('**') * 2) % 2 != 0:
            errors.append("Unclosed italic formatting (*)")
        
        # Check for proper header spacing
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#') and i > 0 and lines[i-1].strip() != '':
                errors.append(f"Missing blank line before header at line {i+1}")
        
        return errors
    
    @staticmethod
    def validate_ats_compatibility(content: str) -> List[str]:
        """Check for ATS compatibility issues."""
        errors = []
        
        # Special characters check
        special_chars = ['♦', '●', '▪', '➤', '✓', '★', '◆', '☎', '✉']
        for char in special_chars:
            if char in content:
                errors.append(f"Contains special character '{char}' that may not parse in ATS")
        
        # Check for consistent formatting
        if '\t' in content:
            errors.append("Contains tab characters - use spaces instead")
        
        return errors
    
    @staticmethod
    def validate_length_constraints(content: str, doc_type: str) -> List[str]:
        """Check document length constraints."""
        errors = []
        
        word_count = len(content.split())
        
        if doc_type == "cover_letter":
            if word_count > 450:
                errors.append(f"Cover letter too long: {word_count} words (max 450)")
            elif word_count < 250:
                errors.append(f"Cover letter too short: {word_count} words (min 250)")
        
        elif doc_type == "cv":
            # CV can be 1-3 pages, roughly 300-900 words
            if word_count > 900:
                errors.append(f"CV may be too long: {word_count} words")
        
        return errors


# Helper functions for template processing

def extract_keywords_from_template(template: str) -> List[str]:
    """Extract placeholder keywords from template."""
    # Find all {placeholder} patterns
    placeholders = re.findall(r'\{(\w+)\}', template)
    return list(set(placeholders))


def format_date(date_str: str, format_type: str = "default") -> str:
    """Format date string according to template standards."""
    # This is a simplified version - would need proper date parsing in production
    if format_type == "default":
        return date_str  # MM/YYYY format
    elif format_type == "full":
        # Convert to "Month DD, YYYY" format
        return date_str
    return date_str


def sanitize_for_ats(content: str) -> str:
    """Remove or replace ATS-problematic elements."""
    # Replace special characters
    replacements = {
        '•': '-',
        '→': '-',
        '®': '(R)',
        '™': '(TM)',
        '—': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'"
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    return content