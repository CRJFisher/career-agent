# Job Requirements YAML Schema

This document defines the structured YAML schema for extracted job requirements used by the ExtractRequirementsNode.

## Overview

The job requirements schema provides a standardized format for representing parsed job descriptions. It clearly separates mandatory requirements from nice-to-haves and categorizes different types of requirements for effective candidate matching.

## Schema Structure

### Root Level

```yaml
role_summary:          # Basic information about the role
hard_requirements:     # Mandatory requirements (must-haves)
soft_requirements:     # Soft skills and personal traits
nice_to_have:         # Optional/preferred qualifications
responsibilities:      # Job duties and expectations
compensation_benefits: # Salary and benefits information
```

### role_summary

Basic metadata about the position.

```yaml
role_summary:
  title: string         # Required: Job title
  company: string       # Required: Company name
  location: string      # Required: Job location
  type: string          # Required: Employment type (Full-time, Part-time, Contract)
  level: string         # Required: Seniority level (Entry, Mid, Senior, Lead, Principal)
  department: string    # Optional: Department or team
  reports_to: string    # Optional: Reporting structure
```

### hard_requirements (Must-Haves)

Mandatory qualifications and requirements.

```yaml
hard_requirements:
  education:            # Educational requirements
    - string           # List of degree requirements
    
  experience:
    years_required: number  # Minimum years of experience
    specific_experience:    # Specific experience requirements
      - string
      
  technical_skills:
    programming_languages:  # Required programming languages
      - string
    technologies:          # Required technologies/tools
      - string
    concepts:             # Required technical concepts
      - string
    
  certifications:         # Required certifications
    - string
    
  clearances:            # Security clearances if required
    - string
```

### soft_requirements

Interpersonal skills and personal attributes.

```yaml
soft_requirements:
  skills:               # Soft skills
    - string           # e.g., "Communication", "Leadership"
    
  traits:              # Personal characteristics
    - string           # e.g., "Self-motivated", "Detail-oriented"
    
  cultural_fit:        # Company culture alignment
    - string           # e.g., "Collaborative", "Fast-paced environment"
```

### nice_to_have

Preferred but not mandatory qualifications.

```yaml
nice_to_have:
  certifications:      # Preferred certifications
    - string
    
  experience:          # Preferred experience
    - string
    
  skills:             # Preferred additional skills
    - string
    
  education:          # Preferred education
    - string
    
  technologies:       # Preferred technology experience
    - string
    
  domain_knowledge:   # Preferred industry/domain expertise
    - string
```

### responsibilities

Job duties and expectations.

```yaml
responsibilities:
  primary:            # Core responsibilities
    - string
    
  secondary:          # Additional responsibilities
    - string
    
  leadership:         # Leadership/mentoring duties
    - string
    
  collaboration:      # Cross-functional responsibilities
    - string
```

### compensation_benefits

Compensation and benefits information.

```yaml
compensation_benefits:
  salary_range: string        # Salary range or "Competitive"
  
  benefits:                   # Standard benefits
    - string
    
  perks:                     # Additional perks
    - string
    
  equity:                    # Stock/equity information
    - string
    
  bonus_structure: string    # Bonus information
```

## Validation Rules

1. **Required Sections**: `role_summary`, `hard_requirements`, `responsibilities`
2. **Required Fields in role_summary**: `title`, `company`, `location`, `type`, `level`
3. **At least one requirement type**: `hard_requirements` must contain at least one of:
   - `education`
   - `experience`
   - `technical_skills`
4. **Non-empty lists**: All list fields must contain at least one item if present
5. **Experience years**: If specified, `years_required` must be a positive number

## Example

```yaml
role_summary:
  title: "Senior Software Engineer"
  company: "TechCorp"
  location: "San Francisco, CA"
  type: "Full-time"
  level: "Senior"
  department: "Machine Learning Infrastructure"

hard_requirements:
  education:
    - "Bachelor's degree in Computer Science or related field"
    - "Master's degree preferred"
  experience:
    years_required: 5
    specific_experience:
      - "5+ years of software engineering experience"
      - "3+ years with distributed systems"
      - "Experience with ML infrastructure at scale"
  technical_skills:
    programming_languages:
      - "Python"
      - "Go"
      - "Java"
    technologies:
      - "Kubernetes"
      - "Docker"
      - "AWS or GCP"
      - "TensorFlow or PyTorch"
    concepts:
      - "Distributed systems"
      - "Machine learning"
      - "System design"
      - "Performance optimization"

soft_requirements:
  skills:
    - "Strong communication skills"
    - "Team collaboration"
    - "Problem-solving ability"
    - "Technical leadership"
  traits:
    - "Self-motivated"
    - "Detail-oriented"
    - "Adaptable to changing priorities"
    - "Continuous learner"

nice_to_have:
  certifications:
    - "AWS Solutions Architect"
    - "Kubernetes Administrator"
  experience:
    - "Contributing to open source projects"
    - "Publishing technical papers"
    - "Speaking at conferences"
  skills:
    - "Experience with JAX"
    - "Knowledge of reinforcement learning"
    - "MLOps best practices"

responsibilities:
  primary:
    - "Design and implement scalable ML training pipelines"
    - "Optimize model serving infrastructure for low latency"
    - "Lead technical design reviews and architecture decisions"
    - "Mentor junior engineers and interns"
  secondary:
    - "Participate in on-call rotation"
    - "Contribute to technical documentation"
    - "Interview engineering candidates"

compensation_benefits:
  salary_range: "$180,000 - $250,000"
  benefits:
    - "Comprehensive health insurance"
    - "401(k) with company match"
    - "Unlimited PTO"
    - "Parental leave"
  perks:
    - "Stock options"
    - "Annual learning budget ($5,000)"
    - "Home office stipend"
    - "Flexible work arrangements"
  equity: "0.05% - 0.1% equity stake"
```

## Usage Notes

1. **Flexibility**: Not all sections are required for every job. Adapt based on available information.
2. **Clarity**: Use clear, concise language avoiding company-specific jargon
3. **Specificity**: Be specific about requirements (e.g., "5+ years" not "several years")
4. **Categorization**: Properly categorize between hard requirements and nice-to-haves
5. **Completeness**: Extract all relevant information from the job description