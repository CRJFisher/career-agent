# CV and Cover Letter Templates

This directory contains professional templates and formatting guidelines for generating CVs and cover letters that are both ATS-friendly and visually appealing.

## Template Files

### CV Templates
- **cv_template.md** - Main CV structure with all sections and placeholders
- **experience_entry_template.md** - Detailed formatting for experience entries with examples
- **skills_section_template.md** - Technical skills categorization and formatting
- **education_certification_template.md** - Education and certification section formatting

### Cover Letter Templates
- **cover_letter_template.txt** - Plain text cover letter template with proper business format
- **cover_letter_5part_structure.md** - Detailed guide for the 5-part cover letter structure

### Guidelines
- **ats_compatibility_guide.md** - Comprehensive ATS optimization rules and testing
- **formatting_guidelines.md** - Document formatting standards and best practices

## Usage

The generation nodes (CVGenerationNode and CoverLetterNode) use these templates to:

1. Load the appropriate template structure
2. Populate with candidate data from the narrative strategy
3. Validate formatting and ATS compliance
4. Export in the requested format

## Key Features

### CV Templates
- GitHub-flavored Markdown for rich formatting
- ATS-optimized section headers
- Flexible structure supporting various career levels
- Professional formatting with visual appeal

### Cover Letter Templates  
- Plain text format for maximum compatibility
- 5-part narrative structure
- Business letter formatting
- Dynamic content adaptation

### Validation
- Built-in template validation tests
- ATS compliance checking
- Length and formatting constraints
- Markdown syntax validation

## Template Utilities

The `utils/template_utils.py` module provides:
- `TemplateLoader` - Loads templates from files
- `CVBuilder` - Builds CV from template and data
- `CoverLetterBuilder` - Builds cover letter from template  
- `TemplateValidator` - Validates output against rules

## Testing

Run template validation tests:
```bash
python -m pytest tests/test_template_validation.py -v
```

This ensures:
- All required sections are present
- Formatting follows guidelines
- ATS compatibility rules are met
- Output matches expected structure