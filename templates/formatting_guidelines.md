# Document Formatting Guidelines

## CV Formatting Guidelines

### GitHub-Flavored Markdown Features

**Headers:**
```markdown
# Name (H1 - Only for candidate name)
## Section Headers (H2 - Major sections)
### Subsection Headers (H3 - Job titles, degrees)
```

**Text Emphasis:**
```markdown
**Bold** - For emphasis (company names, key achievements)
*Italics* - For secondary info (locations, dates)
`Code` - For technical terms, commands
```

**Lists:**
```markdown
- Unordered lists for bullet points
1. Ordered lists for sequential items
   - Nested items with proper indentation
```

**Links:**
```markdown
[LinkedIn](https://linkedin.com/in/username)
[GitHub](https://github.com/username)
[Portfolio](https://portfolio.com)
```

**Blockquotes:**
```markdown
> Professional summary or key highlights
```

**Horizontal Rules:**
```markdown
--- 
(To separate major sections)
```

### CV Style Guide

**Professional Summary:**
- 3-4 lines maximum
- Use blockquote format for visual distinction
- Include years of experience, specialization, and value proposition
- Write in first person implied (no "I" statements)

**Section Ordering:**
1. Professional Summary
2. Core Competencies (optional, for senior roles)
3. Professional Experience
4. Technical Skills
5. Education
6. Certifications
7. Additional Information (optional)

**Experience Entries:**
- Role title in H3 header with company name
- Location and dates in italics
- Brief role description (1-2 sentences)
- 3-6 achievement bullets based on seniority
- Technologies list at end of each role

**Consistency Rules:**
- Date format: MM/YYYY throughout
- Location format: City, State/Country
- Tense: Past tense for previous roles, present for current
- Numbers: Spell out one through nine, use digits for 10+
- Abbreviations: Define on first use, then abbreviate

### Typography Guidelines

**Font Hierarchy (when exported):**
- Name: 18-20pt bold
- Section Headers: 14-16pt bold
- Job Titles: 12-14pt bold
- Body Text: 10-12pt regular
- Dates/Location: 10-12pt italic

**Spacing:**
- Single space within sections
- Double space between sections
- No extra space before bullets
- Consistent indent for nested items

**Line Length:**
- Aim for 80-100 characters per line
- Shorter for better readability
- Avoid orphan words

---

## Cover Letter Formatting Guidelines

### Plain Text Format

**Structure:**
```
Contact Information Block
[blank line]
Date
[blank line]
Recipient Information Block
[blank line]
Salutation
[blank line]
Opening Paragraph
[blank line]
Body Paragraph 1
[blank line]
Body Paragraph 2
[blank line]
Body Paragraph 3
[blank line]
Closing Paragraph
[blank line]
Sign-off
Name
```

**Paragraph Guidelines:**
- No indentation (block style)
- Single space within paragraphs
- Double space between paragraphs
- Left-aligned throughout
- No justification

**Line Breaks:**
- Natural breaks at 70-80 characters
- Break at logical points (commas, conjunctions)
- Avoid breaking numbers or technical terms

### Writing Style

**Voice & Tone:**
- Professional but personable
- Confident without arrogance
- Enthusiastic but not overeager
- Specific rather than generic

**Sentence Structure:**
- Vary sentence length for rhythm
- Lead with strong action verbs
- Average 15-20 words per sentence
- Mix simple and complex sentences

**Word Choice:**
- Use company's terminology
- Avoid jargon unless industry-standard
- Choose precise over flowery language
- Mirror formality level of job posting

---

## File Export Guidelines

### CV Export Options

**Primary: Markdown to PDF**
```bash
# Using pandoc
pandoc cv.md -o cv.pdf --pdf-engine=xelatex

# With custom styling
pandoc cv.md -o cv.pdf --css=cv-style.css
```

**Secondary: Markdown to DOCX**
```bash
pandoc cv.md -o cv.docx
```

**Fallback: Markdown to HTML to PDF**
- Better control over styling
- Consistent rendering across systems
- Allows CSS customization

### Cover Letter Export

**Primary: Plain Text**
- Already in correct format
- No conversion needed
- Maximum compatibility

**Alternative: TXT to DOCX**
- Only if specifically requested
- Maintains plain text simplicity
- Allows basic formatting if needed

### File Naming Conventions

**CV:**
```
FirstName_LastName_CV_2024.pdf
FirstName_LastName_Resume_CompanyName.pdf
FirstName_LastName_SeniorEngineer_CV.pdf
```

**Cover Letter:**
```
FirstName_LastName_CoverLetter_CompanyName.txt
FirstName_LastName_CoverLetter_Position.docx
```

---

## Quality Checklist

### Before Generation

**Content Verification:**
- [ ] All required sections included
- [ ] Keywords from job description incorporated
- [ ] Achievements quantified where possible
- [ ] Technical skills match requirements
- [ ] No spelling or grammar errors

**Format Verification:**
- [ ] Consistent date formats
- [ ] Proper Markdown syntax
- [ ] Appropriate section headers
- [ ] Correct bullet point style
- [ ] No special characters that break parsing

### After Generation

**CV Checks:**
- [ ] All sections properly formatted
- [ ] Links are clickable (if PDF)
- [ ] No formatting artifacts
- [ ] Fits on appropriate number of pages
- [ ] Visually balanced and readable

**Cover Letter Checks:**
- [ ] Proper business letter format
- [ ] All 5 parts clearly present
- [ ] Under 400 words
- [ ] Natural keyword integration
- [ ] Strong opening and closing

### Final Review

**ATS Compliance:**
- [ ] Passes plain text test
- [ ] Keywords properly distributed
- [ ] No parsing errors
- [ ] Contact info extractable
- [ ] Standard section headers used

**Human Readability:**
- [ ] Visually appealing
- [ ] Easy to scan
- [ ] Logical flow
- [ ] Professional appearance
- [ ] Consistent style

---

## Common Formatting Errors to Avoid

### CV Errors
1. **Inconsistent Formatting**
   - Mixed date formats
   - Varying bullet styles
   - Inconsistent capitalization

2. **Over-Formatting**
   - Too many bold/italic elements
   - Excessive use of separators
   - Multiple font styles

3. **Poor Structure**
   - Unclear hierarchy
   - Missing section breaks
   - Illogical ordering

### Cover Letter Errors
1. **Wall of Text**
   - No paragraph breaks
   - Too long paragraphs
   - No visual breathing room

2. **Incorrect Format**
   - Missing contact information
   - Wrong date format
   - Improper salutation

3. **Style Mismatches**
   - Too casual for company
   - Generic templated feel
   - Inconsistent voice

---

## Accessibility Considerations

### For Screen Readers
- Use semantic headers correctly
- Include alt text for any images (though avoid images)
- Ensure logical reading order
- Don't rely on formatting alone for meaning

### For Color Blindness
- Don't use color as only differentiator
- Ensure sufficient contrast
- Use bold/italic for emphasis instead

### For Dyslexia
- Use clear, simple fonts
- Adequate line spacing
- Short paragraphs
- Left-aligned text