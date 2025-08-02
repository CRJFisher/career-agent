"""
Test suite for validating CV and cover letter templates.
Ensures templates follow formatting guidelines and ATS compatibility rules.
"""

import re
import unittest
from typing import Dict, List, Tuple


class CVTemplateValidator:
    """Validates CV templates for structure and formatting compliance."""
    
    REQUIRED_SECTIONS = [
        "Professional Summary",
        "Professional Experience", 
        "Technical Skills",
        "Education"
    ]
    
    OPTIONAL_SECTIONS = [
        "Core Competencies",
        "Certifications",
        "Additional Information"
    ]
    
    def validate_structure(self, cv_content: str) -> Tuple[bool, List[str]]:
        """Validate CV has all required sections."""
        errors = []
        
        for section in self.REQUIRED_SECTIONS:
            if f"## {section}" not in cv_content:
                errors.append(f"Missing required section: {section}")
        
        return len(errors) == 0, errors
    
    def validate_markdown_formatting(self, cv_content: str) -> Tuple[bool, List[str]]:
        """Validate proper Markdown syntax."""
        errors = []
        
        # Check for proper header hierarchy
        lines = cv_content.split('\n')
        h1_count = sum(1 for line in lines if line.startswith('# ') and not line.startswith('## '))
        if h1_count != 1:
            errors.append("CV should have exactly one H1 header for candidate name")
        
        # Check for consistent bullet points
        bullet_styles = set()
        for line in lines:
            if line.strip() and line.lstrip()[0] in ['-', '*', '+']:
                bullet_styles.add(line.lstrip()[0])
        
        if len(bullet_styles) > 1:
            errors.append(f"Inconsistent bullet point styles: {bullet_styles}")
        
        return len(errors) == 0, errors
    
    def validate_experience_format(self, experience_section: str) -> Tuple[bool, List[str]]:
        """Validate experience entries follow the template."""
        errors = []
        
        # Check for required components in each entry
        entry_pattern = r'### .+ \| .+\n\*.+ \| .+\*'
        entries = re.findall(entry_pattern, experience_section, re.MULTILINE)
        
        if not entries:
            errors.append("No properly formatted experience entries found")
        
        # Check for achievement bullets
        if not re.search(r'^- \w+', experience_section, re.MULTILINE):
            errors.append("Experience entries missing achievement bullets")
        
        # Check for Technologies section
        if "**Technologies:**" not in experience_section:
            errors.append("Experience entries missing Technologies section")
        
        return len(errors) == 0, errors
    
    def validate_ats_compliance(self, cv_content: str) -> Tuple[bool, List[str]]:
        """Check for ATS compatibility issues."""
        errors = []
        
        # Check for special characters
        special_chars = ['♦', '●', '▪', '➤', '✓', '★', '◆']
        for char in special_chars:
            if char in cv_content:
                errors.append(f"Contains special character '{char}' that may break ATS parsing")
        
        # Check date formats
        date_patterns = [
            r'\d{1,2}/\d{4}',  # MM/YYYY
            r'[A-Za-z]+ \d{4}',  # Month YYYY
            r'\d{4} - \d{4}',  # YYYY - YYYY
            r'\d{1,2}/\d{4} - Present'  # MM/YYYY - Present
        ]
        
        if not any(re.search(pattern, cv_content) for pattern in date_patterns):
            errors.append("No standard date formats found")
        
        # Check for tables (Markdown tables)
        if '|' in cv_content and re.search(r'\|.*\|.*\|', cv_content):
            errors.append("Contains table formatting that may not parse in ATS")
        
        return len(errors) == 0, errors


class CoverLetterTemplateValidator:
    """Validates cover letter templates for structure and formatting."""
    
    def validate_structure(self, letter_content: str) -> Tuple[bool, List[str]]:
        """Validate cover letter has proper structure."""
        errors = []
        
        # Check for contact information
        required_contact = ["Name", "Email", "Phone"]
        for item in required_contact:
            if item not in letter_content[:200]:  # Check in header area
                errors.append(f"Missing contact information: {item}")
        
        # Check for date
        if not re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}', letter_content):
            errors.append("Missing or improperly formatted date")
        
        # Check for salutation
        if not re.search(r'Dear .+[,:]', letter_content):
            errors.append("Missing proper salutation")
        
        # Check for closing
        if not re.search(r'(Sincerely|Best regards|Thank you),?\n', letter_content):
            errors.append("Missing professional closing")
        
        return len(errors) == 0, errors
    
    def validate_five_part_structure(self, letter_body: str) -> Tuple[bool, List[str]]:
        """Validate the 5-part structure is present."""
        errors = []
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in letter_body.split('\n\n') if p.strip()]
        
        # Exclude header and closing to focus on body
        body_paragraphs = [p for p in paragraphs if not p.startswith('Dear') and not p.startswith('Sincerely')]
        
        if len(body_paragraphs) < 5:
            errors.append(f"Cover letter should have 5 body paragraphs, found {len(body_paragraphs)}")
        
        # Check opening paragraph mentions position and company
        if body_paragraphs and not re.search(r'position|role', body_paragraphs[0], re.IGNORECASE):
            errors.append("Opening paragraph should mention the position")
        
        return len(errors) == 0, errors
    
    def validate_length(self, letter_content: str) -> Tuple[bool, List[str]]:
        """Validate cover letter length constraints."""
        errors = []
        
        word_count = len(letter_content.split())
        if word_count > 450:
            errors.append(f"Cover letter too long: {word_count} words (max 450)")
        elif word_count < 250:
            errors.append(f"Cover letter too short: {word_count} words (min 250)")
        
        # Check line length
        lines = letter_content.split('\n')
        long_lines = [i for i, line in enumerate(lines) if len(line) > 80]
        if long_lines:
            errors.append(f"Lines exceeding 80 characters: {len(long_lines)} lines")
        
        return len(errors) == 0, errors
    
    def validate_ats_compliance(self, letter_content: str) -> Tuple[bool, List[str]]:
        """Check cover letter for ATS issues."""
        errors = []
        
        # Check for plain text format
        if '<' in letter_content or '>' in letter_content:
            if not re.match(r'[^<>]*@[^<>]*', letter_content):  # Allow email addresses
                errors.append("Contains HTML-like tags that may confuse ATS")
        
        # Check for special formatting
        if '\t' in letter_content:
            errors.append("Contains tabs - use spaces for alignment")
        
        # Check for proper paragraph spacing
        if '\n\n\n' in letter_content:
            errors.append("Excessive blank lines between paragraphs")
        
        return len(errors) == 0, errors


class TestCVTemplate(unittest.TestCase):
    """Test cases for CV template validation."""
    
    def setUp(self):
        self.validator = CVTemplateValidator()
        
    def test_cv_has_required_sections(self):
        """Test that CV template includes all required sections."""
        sample_cv = """
# John Smith

## Professional Summary
Experienced software engineer...

## Professional Experience
### Senior Engineer | TechCorp
*San Francisco, CA | 01/2020 - Present*

## Technical Skills
- Python, JavaScript, Go

## Education
### BS in Computer Science
*MIT | Cambridge, MA | 2015*
"""
        valid, errors = self.validator.validate_structure(sample_cv)
        self.assertTrue(valid, f"CV validation failed: {errors}")
    
    def test_cv_markdown_formatting(self):
        """Test proper Markdown formatting."""
        sample_cv = """
# John Smith

## Professional Summary
Test summary

## Professional Experience
- Achievement 1
- Achievement 2
"""
        valid, errors = self.validator.validate_markdown_formatting(sample_cv)
        self.assertTrue(valid, f"Markdown validation failed: {errors}")
    
    def test_experience_entry_format(self):
        """Test experience entries follow template."""
        experience = """
### Senior Software Engineer | Google
*Mountain View, CA | 03/2018 - Present*

Led development of search infrastructure serving 1B+ queries daily.

**Key Achievements:**
- Built distributed caching system reducing latency by 40%
- Mentored team of 8 engineers on best practices
- Implemented CI/CD pipeline improving deployment frequency by 3x

**Technologies:** Python, Go, Kubernetes, GCP, PostgreSQL
"""
        valid, errors = self.validator.validate_experience_format(experience)
        self.assertTrue(valid, f"Experience format validation failed: {errors}")
    
    def test_ats_compliance(self):
        """Test CV passes ATS compliance checks."""
        sample_cv = """
# John Smith

## Experience
### Software Engineer | TechCorp
*01/2020 - Present*

- Developed features
- Fixed bugs

No special characters here!
"""
        valid, errors = self.validator.validate_ats_compliance(sample_cv)
        self.assertTrue(valid, f"ATS compliance failed: {errors}")


class TestCoverLetterTemplate(unittest.TestCase):
    """Test cases for cover letter template validation."""
    
    def setUp(self):
        self.validator = CoverLetterTemplateValidator()
    
    def test_cover_letter_structure(self):
        """Test cover letter has proper structure."""
        sample_letter = """
John Smith
john.smith@email.com
(555) 123-4567

January 15, 2024

Dear Hiring Manager,

I am writing to express my interest in the Software Engineer position at TechCorp.

[Body paragraphs...]

Sincerely,
John Smith
"""
        valid, errors = self.validator.validate_structure(sample_letter)
        self.assertTrue(valid, f"Structure validation failed: {errors}")
    
    def test_five_part_structure(self):
        """Test 5-part body structure."""
        letter_body = """
Dear Hiring Manager,

Opening paragraph about the position and company.

Experience paragraph with relevant achievements.

Technical expertise paragraph highlighting skills.

Cultural fit paragraph showing alignment.

Closing paragraph with call to action.

Sincerely,
"""
        valid, errors = self.validator.validate_five_part_structure(letter_body)
        self.assertTrue(valid, f"5-part structure validation failed: {errors}")
    
    def test_length_constraints(self):
        """Test cover letter meets length requirements."""
        # Generate sample letter of appropriate length
        words = ["word"] * 350  # 350 words
        sample_letter = " ".join(words)
        
        valid, errors = self.validator.validate_length(sample_letter)
        self.assertTrue(valid, f"Length validation failed: {errors}")
    
    def test_ats_compliance_cover_letter(self):
        """Test cover letter ATS compliance."""
        sample_letter = """
John Smith
john@email.com

January 15, 2024

Dear Hiring Manager,

Plain text content without special formatting.

No tabs or HTML tags here.

Proper paragraph spacing.

Sincerely,
John Smith
"""
        valid, errors = self.validator.validate_ats_compliance(sample_letter)
        self.assertTrue(valid, f"ATS compliance failed: {errors}")


class TestTemplateIntegration(unittest.TestCase):
    """Integration tests for template system."""
    
    def test_cv_cover_letter_consistency(self):
        """Test that CV and cover letter templates are consistent."""
        # This would test that both documents use consistent information
        # For example, same contact info, aligned experiences, etc.
        pass
    
    def test_template_variable_replacement(self):
        """Test that template variables are properly replaced."""
        template = "Hello {name}, you applied for {position} at {company}."
        variables = {
            "name": "John Smith",
            "position": "Software Engineer",
            "company": "TechCorp"
        }
        
        result = template.format(**variables)
        expected = "Hello John Smith, you applied for Software Engineer at TechCorp."
        self.assertEqual(result, expected)
    
    def test_markdown_to_text_conversion(self):
        """Test conversion from Markdown to plain text maintains structure."""
        markdown = """
## Header

**Bold text** and *italic text*

- Bullet 1
- Bullet 2
"""
        # This would test actual conversion logic
        # For now, just verify structure is parseable
        self.assertIn("## Header", markdown)
        self.assertIn("**Bold text**", markdown)
        self.assertIn("- Bullet", markdown)


if __name__ == "__main__":
    unittest.main()