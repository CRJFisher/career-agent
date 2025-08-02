---
id: task-39
title: Implement ExtractExperienceNode
status: pending
priority: high
assignee: unassigned
created: 2024-01-01
updated: 2025-08-02
tags: [node, extraction, llm, experience-database, pocketflow]
dependencies: [task-37, task-38]
estimated_hours: 8
actual_hours: 0
---

# Task: Implement ExtractExperienceNode

## Description

Implement the ExtractExperienceNode that processes discovered documents and extracts work experience information using LLM-powered analysis.

## Acceptance Criteria

- [ ] Node processes document list from ScanDocumentsNode
- [ ] Uses document parsing utilities to extract text
- [ ] Employs LLM to identify and extract work experience
- [ ] Handles different document formats (resumes, project docs, etc.)
- [ ] Extracts all fields from enhanced career database schema
- [ ] Identifies nested projects within work experiences
- [ ] Batches LLM calls for efficiency

## Technical Details

- Extends base Node class or BatchNode for parallel processing
- Uses document parsing utilities from task-37
- Uses LLM wrapper for experience extraction
- Implements smart prompting to extract:
  - Job titles, companies, dates
  - Responsibilities and achievements
  - Projects with full details
  - Technologies and skills
  - Cultural fit information
- Stores raw extractions in shared["extracted_experiences"]

## Implementation Plan

### Node Structure

```python
class ExtractExperienceNode(BatchNode):
    """Extracts work experience from parsed documents using LLM analysis."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare documents for processing."""
        documents = shared.get("document_sources", [])
        return {
            "documents": documents,
            "batch_size": 5,  # Process 5 documents at a time
            "career_schema": shared.get("career_database_schema")
        }
    
    def exec_batch(self, batch: List[dict], prep_res: dict) -> List[dict]:
        """Process a batch of documents."""
        extracted = []
        for doc in batch:
            # Parse document
            parsed = parse_document(doc)
            # Extract experience via LLM
            experience = self.extract_experience(parsed, prep_res["career_schema"])
            extracted.append(experience)
        return extracted
    
    def post(self, shared: dict, prep_res: dict, exec_res: List[dict]) -> str:
        """Store extracted experiences."""
        shared["extracted_experiences"] = exec_res
        return "continue"
```

### LLM Prompt Template

```yaml
system_prompt: |
  You are an expert career analyst extracting work experience from documents.
  Extract structured information matching this schema:
  {career_schema}
  
  Focus on:
  1. Complete work history with dates
  2. Detailed project information
  3. Technologies and skills used
  4. Quantifiable achievements
  5. Leadership and team experiences

user_prompt: |
  Extract all work experience from this document:
  
  Document Type: {doc_type}
  Document Name: {doc_name}
  
  Content:
  {content}
  
  Return as structured YAML matching the career database schema.
```

### Extraction Strategy

1. **Document Classification**
   - Identify document type (resume, portfolio, project doc)
   - Apply appropriate extraction strategy

2. **Hierarchical Extraction**
   - First pass: Identify major sections
   - Second pass: Extract detailed information
   - Third pass: Link projects to experiences

3. **Data Enrichment**
   - Cross-reference skills across experiences
   - Infer missing dates from context
   - Standardize job titles and company names

### Output Schema

```yaml
extracted_experiences:
  - document_source: "path/to/resume.pdf"
    extraction_confidence: 0.95
    experiences:
      - company: "Tech Corp"
        title: "Senior Engineer"
        start_date: "2020-01"
        end_date: "2023-12"
        responsibilities:
          - "Led team of 5 engineers"
        achievements:
          - description: "Reduced latency by 40%"
            metrics: ["40% improvement", "100ms to 60ms"]
        projects:
          - name: "API Redesign"
            role: "Tech Lead"
            description: "Complete API overhaul"
            technologies: ["Python", "FastAPI"]
            outcomes:
              - "Improved performance"
              - "Better developer experience"
```

## Dependencies

- Document parsing utilities (task-37)
- LLM wrapper
- Enhanced career database schema

## Testing Requirements

- Test with various document types
- Test extraction accuracy with known documents
- Test handling of non-work documents
- Test batching and error recovery
- Verify all schema fields are extracted

## Error Handling

1. **Parsing Failures**
   - Log error and skip document
   - Mark as failed in output

2. **LLM Errors**
   - Implement retry with backoff
   - Fallback to simpler prompts

3. **Schema Validation**
   - Validate extracted data
   - Fix common formatting issues

## Performance Optimization

- Batch similar documents together
- Cache parsed documents
- Use smaller model for classification
- Parallelize LLM calls where possible

## Quality Assurance

- Confidence scoring for extractions
- Duplicate detection across documents
- Consistency checks for dates
- Validation against career schema