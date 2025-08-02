# ATS Compatibility Guide

## Overview
Applicant Tracking Systems (ATS) are software applications that scan, parse, and rank resumes before human review. 75% of resumes are rejected by ATS before reaching a recruiter. This guide ensures both CV and cover letter templates pass ATS screening.

---

## Universal ATS Rules

### File Formats
✅ **Preferred Formats:**
- .docx (Best compatibility)
- .txt (100% parseable, no formatting)
- .pdf (Only if specifically requested - some ATS can't parse)

❌ **Never Use:**
- .png, .jpg (Images can't be parsed)
- .pages (Mac-specific format)
- .odt (Open source format with limited support)
- .html (Web format, inconsistent parsing)

### Character Encoding
- Use UTF-8 encoding
- Avoid special characters: ♦ ● ▪ ➤ ✓
- Use standard characters: * - + > 

### File Naming
```
Correct: John_Smith_Resume_2024.docx
Correct: JohnSmith_SoftwareEngineer_CV.docx
Incorrect: John's Resume (FINAL).docx
Incorrect: Resume_v2.3_UPDATED!!.docx
```

---

## CV/Resume ATS Optimization

### Structure & Formatting

**Do:**
- Use standard section headers: "Professional Experience", "Education", "Skills"
- Maintain consistent formatting throughout
- Use simple bullet points (-, *, •)
- Include both acronyms and full names: "Amazon Web Services (AWS)"
- Use standard date formats: MM/YYYY or Month YYYY

**Don't:**
- Use tables, columns, or text boxes
- Include headers, footers, or page numbers
- Use images, logos, or graphics
- Employ fancy fonts or formatting
- Create custom section names

### Keyword Optimization

1. **Mirror Job Description Language**
   - Job says "Python" → Use "Python" (not "Python programming")
   - Job says "team lead" → Use "team lead" (not "team leader")

2. **Include Variations**
   ```
   Good: "JavaScript (JS), HTML5/CSS3"
   Good: "Continuous Integration/Continuous Deployment (CI/CD)"
   ```

3. **Skills Section Format**
   ```
   Technical Skills:
   - Programming: Python, JavaScript, TypeScript, Go
   - Cloud: AWS (EC2, S3, Lambda), Google Cloud Platform
   - Databases: PostgreSQL, MongoDB, Redis
   ```

### Common ATS Parsing Errors

**Contact Information:**
```
❌ Wrong: John Smith | john@email.com | 555-1234
✅ Right: 
John Smith
john@email.com
(555) 123-4567
```

**Job Titles:**
```
❌ Wrong: Sr. SWE @ TechCo
✅ Right: Senior Software Engineer at TechCorp
```

**Dates:**
```
❌ Wrong: '20 - Present
✅ Right: 2020 - Present
✅ Right: 01/2020 - Present
```

---

## Cover Letter ATS Optimization

### Format Requirements
- Plain text or simple formatting only
- No columns or tables
- Standard business letter format
- Clear paragraph breaks (double line spacing)
- Left-aligned text

### Keyword Integration
1. Use exact job title from posting
2. Include 5-7 key skills from requirements
3. Mirror company's language and terminology
4. Include industry-specific keywords

### Structure for ATS
```
[Your Name]
[Your Address]
[City, State ZIP]
[Email]
[Phone]
[Date]

[Company Name]
[Hiring Manager Title]
[Company Address]

Dear Hiring Manager,

[Paragraph 1 - Include job title and company name]

[Paragraph 2-4 - Include keywords naturally]

[Closing paragraph]

Sincerely,
[Your Name]
```

---

## ATS Testing Checklist

### Before Submission
- [ ] Saved in .docx or .txt format
- [ ] File name includes your name and position
- [ ] No tables, columns, or special formatting
- [ ] Standard section headers used
- [ ] Keywords from job description included
- [ ] Dates in consistent format
- [ ] Contact information clearly separated
- [ ] No typos or grammatical errors

### Content Verification
- [ ] Job titles match official titles (not internal codes)
- [ ] Companies spelled correctly and completely
- [ ] Skills match job posting terminology
- [ ] Both acronyms and full terms included
- [ ] Action verbs start each bullet point
- [ ] Quantifiable metrics included

### Technical Validation
- [ ] Copy/paste to notepad - still readable?
- [ ] File size under 1MB
- [ ] No embedded images or graphics
- [ ] No hyperlinks (unless specifically requested)
- [ ] Standard fonts (Arial, Calibri, Times New Roman)
- [ ] Font size 10-12pt for body text

---

## Common ATS Systems & Quirks

### Taleo (Oracle)
- Strict about date formats
- Prefers .docx over .pdf
- May truncate long bullet points

### Workday
- Good with standard formats
- Handles .pdf well
- May miss information in headers/footers

### iCIMS
- Parses most formats well
- May struggle with columns
- Prefers chronological order

### Greenhouse
- Modern parser, handles most formats
- Still avoid tables/graphics
- Good with technical keywords

### Lever
- Excellent parsing capability
- Still follow standard practices
- May extract LinkedIn data

---

## Keyword Strategy by Role

### Software Engineering
**Must Include:**
- Programming languages from job posting
- Specific frameworks/libraries mentioned
- Cloud platforms (AWS, GCP, Azure)
- Development methodologies (Agile, Scrum)
- Database technologies
- Version control (Git, GitHub)

### Data Science
**Must Include:**
- Programming: Python, R, SQL
- ML frameworks: TensorFlow, PyTorch, Scikit-learn
- Statistical methods mentioned
- Big data tools: Spark, Hadoop
- Visualization: Tableau, PowerBI
- Cloud ML platforms

### Product Management
**Must Include:**
- Product lifecycle terms
- Agile/Scrum/Kanban
- Metrics: KPIs, OKRs
- Tools: JIRA, Confluence
- Analytics platforms
- Stakeholder management

---

## Testing Your Documents

### Manual Test
1. Copy entire document to plain text editor
2. Check all information is present and readable
3. Verify formatting hasn't created confusion
4. Ensure keywords are intact

### Online ATS Scanners
- JobScan (compares to job description)
- Resume Worded (general ATS score)
- Rezi (ATS optimization suggestions)
- VMock (formatting analysis)

### Red Flags to Fix
- Score below 80% match to job description
- Missing critical keywords from requirements
- Formatting errors in plain text version
- Contact information not detected
- Work experience dates unclear

---

## Final Optimization Tips

1. **One Version Per Application**
   - Customize keywords for each position
   - Match the company's terminology
   - Align with specific requirements

2. **Quality Over Creativity**
   - Simple, clean formatting wins
   - Clear information hierarchy
   - Consistent style throughout

3. **Human Review Ready**
   - ATS-friendly doesn't mean boring
   - Use Markdown formatting for visual appeal
   - Ensure it's pleasant to read after parsing

4. **Update Regularly**
   - ATS algorithms evolve
   - Keep format modern but simple
   - Test with new tools periodically