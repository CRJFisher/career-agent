

# **Architecting a Systematic Job Application Agent with PocketFlow: A Technical White Paper**

## **Foreword: A Note on "Agentic Coding"**

This document is structured as a high-level design specification, following the "Agentic Coding" philosophy championed by the PocketFlow framework.1 The user has provided an exemplary human-led design (the "Job Application Agent Guideline"). This report serves as the architectural bridge, enabling an AI coding assistant or a human developer to execute the implementation with clarity and precision. The proposed architecture adheres to the recommended project structure:  
docs/design.md, utils/, nodes.py, flow.py, and main.py.  
---

### **Part I: Foundation and Framework Alignment**

#### **1\. Introduction: Disambiguating and Embracing the PocketFlow Paradigm**

##### **1.1 Identifying the Correct "PocketFlow": An Essential Clarification**

The open-source landscape contains multiple, unrelated projects named "PocketFlow." A critical first step is to disambiguate these frameworks to ensure the project is built on the correct foundation. This report exclusively concerns **"The-Pocket/PocketFlow,"** a minimalist Large Language Model (LLM) orchestration framework designed for building agents and workflows.1  
Other frameworks with the same name serve entirely different purposes. For instance, Tencent/PocketFlow is an automatic model compression (AutoMC) framework for making deep learning models smaller and faster, focusing on techniques like channel pruning and weight sparsification.5 Another,  
Saoge123/PocketFlow, is a highly specialized autoregressive flow model for generating drug-like molecules within protein pockets.8 Attempting to use concepts from these other frameworks would lead to project failure. The following table provides a definitive clarification.  
**Table 1: PocketFlow Framework Disambiguation**

| Repository | Core Purpose | Relevance to Job Agent |
| :---- | :---- | :---- |
| The-Pocket/PocketFlow | Minimalist LLM workflow orchestration | **Directly Applicable (Core Focus of this Report)** |
| Tencent/PocketFlow | Deep learning model compression | Not Applicable |
| Saoge123/PocketFlow | Structure-based molecular generation | Not Applicable |

This report will proceed solely based on the architecture and design patterns of The-Pocket/PocketFlow.

##### **1.2 The Core Abstraction: A 100-Line Foundation of Graph \+ Shared Store**

The power of PocketFlow lies in its deliberate minimalism. It is not a monolithic library with extensive dependencies; instead, it provides a core 100-line abstraction that models all LLM applications as a directed graph.1 This design philosophy avoids bloat, dependency issues, and vendor lock-in, granting the developer maximum control and transparency.1 The framework is built on three fundamental concepts, analogous to a well-organized kitchen :

* **Nodes**: These are the discrete units of work, the "cooking stations" where specific tasks are performed. Each Node follows a strict lifecycle:  
  1. **prep**: Gathers necessary data ("ingredients") from the Shared Store.  
  2. **exec**: Executes its core logic, such as calling an LLM, running a calculation, or invoking an external API.  
  3. **post**: Writes the results back to the Shared Store and returns an "action" string, which determines the next step in the flow. This lifecycle is consistent across implementations in Python, TypeScript, C++, and Go.1  
* **Flow**: This is the "recipe" that connects Nodes into a coherent process. A Flow is a directed graph where the edges are labeled with the "action" strings returned by the Nodes. This mechanism enables powerful conditional branching, looping, and the construction of complex, multi-step pipelines.1  
* **Shared Store**: This is the central "countertop," a common data repository accessible to all Nodes within a Flow. In the Python implementation, this is a simple dictionary that is passed by reference, enabling seamless state management and communication between disparate parts of the agent's workflow.1

##### **1.3 Architectural Overview: Mapping Job Application Phases to PocketFlow Patterns**

The user-provided guideline naturally decomposes into a sequence of tasks that align perfectly with the design patterns explicitly supported by PocketFlow.2 By mapping each phase of the job application process to a primary PocketFlow pattern, we can create a clear and robust architectural roadmap.  
A detailed examination of each phase's objective reveals this natural alignment. Phase 1, which involves converting unstructured text into a rigid format, is a canonical use case for the Structured Output pattern. Phase 3, which requires dynamic, multi-step tool use for research, is best modeled as an Agent. The remaining phases, which consist of linear data processing and synthesis steps, are ideal candidates for the Workflow pattern. This mapping provides a high-level blueprint for the entire system.  
**Table 2: Job Application Phases to PocketFlow Patterns**

| Guideline Phase | Primary PocketFlow Pattern | Rationale |
| :---- | :---- | :---- |
| Phase 0: Personal Career Database | Utility Functions & Initial State | Data loading is a prerequisite setup step, handled by a custom utility function to populate the initial Shared Store. |
| Phase 1: Requirements Extraction | Structured Output | Converts an unstructured job description into a precise, parsable YAML format, a core use case for this pattern. |
| Phase 2: Requirements Mapping | Workflow \+ RAG | A sequential process of mapping, assessing, and analyzing gaps. The mapping step uses Retrieval-Augmented Generation (RAG) to find evidence in the career database. |
| Phase 3: Company Research | Agent | Requires dynamic, multi-step tool use (web search, content scraping, synthesis) and iterative decision-making, which is the defining characteristic of the Agent pattern. |
| Phase 4: Suitability Assessment | Workflow | A linear pipeline that takes structured data, applies a scoring logic (via an LLM), and generates a structured assessment. |
| Phase 5: Narrative Strategy | Workflow | A sophisticated, sequential workflow that first prioritizes experiences with a scoring algorithm and then uses an LLM to synthesize a high-level narrative strategy. |
| Phase 6: Material Construction | Workflow | A final generative pipeline that takes the narrative strategy and constructs tailored CV and cover letter documents in Markdown format. |

#### **2\. Phase 0: Personal Career Database Construction and Ingestion**

##### **2.1 Strategy: The Shared Store as the Single Source of Truth**

The user's YAML-based career database is the foundational dataset for the entire agent. It represents the ground truth of the applicant's professional history. The first operational step of the agent, before any Flow is executed, is to load this comprehensive database into the agent's memory. This is not a task for a Node but rather a prerequisite setup action. The parsed data will form the initial state of the shared dictionary, which is then passed as the central context to all subsequent Flows.

##### **2.2 Implementation: The utils/database\_parser.py Module**

PocketFlow's minimalist philosophy intentionally omits built-in functionalities like file parsers to avoid bloat and maintain flexibility.1 The framework's design guide explicitly recommends separating core orchestration logic (  
Nodes, Flows) from external interactions, which should be encapsulated in a utils/ directory. Parsing a local YAML file is a classic example of such an external interaction.  
Therefore, the first component to be developed is a utility module. A file named utils/database\_parser.py will contain a function, for example load\_career\_database(path), which will use a standard Python library like PyYAML to parse the user's career data files into a Python dictionary.  
The main entry point of the application, main.py, will then use this utility to initialize the Shared Store at startup. This ensures that the complete career history is available to the agent from the very beginning of its execution.

Python

\# main.py  
from utils.database\_parser import load\_career\_database  
from flow import create\_full\_application\_flow \# Assuming a master flow orchestrator

def main():  
    \# Initialize the Shared Store with foundational data  
    shared \= {  
        "career\_db": load\_career\_database("./career\_db.yaml"),  
        "job\_spec\_text": None, \# To be populated by user input or file read  
        "job\_requirements\_structured": None, \# Output of Phase 1  
        "requirement\_mapping\_final": None,   \# Output of Phase 2  
        "gaps": None,                        \# Output of Phase 2  
        "company\_research": None,            \# Output of Phase 3  
        "suitability\_assessment": None,      \# Output of Phase 4  
        "narrative\_strategy": None,          \# Output of Phase 5  
        "cv\_markdown": None,                 \# Output of Phase 6  
        "cover\_letter\_text": None,           \# Output of Phase 6  
    }

    \# Example of how the master flow would be run  
    \# full\_application\_flow \= create\_full\_application\_flow()  
    \# final\_state \= full\_application\_flow.run(shared)  
    \# print("CV Generated:\\n", final\_state\["cv\_markdown"\])

if \_\_name\_\_ \== "\_\_main\_\_":  
    main()

---

### **Part II: Analysis and Strategy Generation**

#### **3\. Phase 1: Requirements Extraction via a Structured Output Flow**

##### **3.1 Pattern: Structured Output for Reliable Data Extraction**

The objective of Phase 1 is to transform an unstructured, free-form text job description into the user's specified, highly structured YAML format. This task is a perfect application of the Structured Output design pattern.2 This pattern leverages sophisticated prompting techniques to compel an LLM to generate responses that strictly adhere to a predefined schema, such as JSON or YAML. This approach mitigates the unreliability and parsing difficulties associated with free-form text generation, ensuring consistent and machine-readable output.15  
The official PocketFlow repository explicitly lists a tutorial for "Extracting structured data from resumes by prompting". This use case is conceptually identical to our goal of extracting structured data from a job description, confirming that the framework is well-suited for this type of task.

##### **3.2 Implementation: The RequirementExtractionFlow**

This phase can be implemented as a simple, single-node Flow designed for one specific task: extraction.

* **nodes.py \- ExtractRequirementsNode:**  
  * **prep**: This method will read the raw job description, which should be loaded into shared\["job\_spec\_text"\].  
  * **exec**: The core of this node is a call to an LLM utility function. This call will pass the job description along with a meticulously engineered prompt designed to elicit a structured YAML response.  
  * **post**: This method will receive the LLM's raw string output, parse it using a YAML library, and save the resulting dictionary to shared\["job\_requirements\_structured"\].  
* Prompt Engineering for ExtractRequirementsNode:  
  The reliability of structured output is directly proportional to the quality of the prompt. While modern LLM APIs offer features like json\_schema response formats to enforce structure 16, a well-crafted prompt remains essential for ensuring semantic accuracy. The prompt must clearly communicate the desired schema, the context of the task, and the expected output format.  
  The most effective approach is to use one-shot prompting, where a perfect example of the desired output is provided directly in the prompt. This leverages the LLM's in-context learning capabilities and dramatically improves adherence to the specified format.18 The user's own guideline provides the ideal example for this purpose.  
  The prompt should be constructed with the following components:  
  1. **Role Definition (System Prompt)**: "You are an expert HR analyst and a senior technical recruiter. Your task is to meticulously parse a job description and extract all salient requirements into a structured YAML format."  
  2. **Task Instruction**: "Analyze the following job description. Your goal is to identify and categorize all requirements. Distinguish between 'must-haves,' which are explicitly required, and 'nice-to-haves,' which are advantageous but not mandatory. Categorize requirements into 'hard\_skills' (e.g., specific technologies, languages), 'soft\_skills' (e.g., communication, teamwork), and 'experiences' (e.g., 'built production systems')."  
  3. **Format Specification**: "You MUST provide the output ONLY in valid YAML format. Do not include any introductory text, concluding summaries, or any other content outside of the YAML block."  
  4. **One-Shot Example**:  
     Here is an example of the required output format:

     \`\`\`yaml  
     job\_requirements:  
       role: Software Engineer, Org Tech  
       company: DeepMind

       must\_haves:  
         hard\_skills:  
           \- Full-stack web development  
           \- Algorithm design understanding  
         soft\_skills:  
           \- Technical communication  
           \- Stakeholder interaction  
         experiences:  
           \- Building internal tools  
           \- End-to-end solution delivery

       nice\_to\_haves:  
         technologies:  
           \- TypeScript  
           \- Angular  
           \- Java  
         interests:  
           \- AI applications  
           \- User experience design

     Now, analyze the following job description and generate the corresponding YAML output.  
     \[Insert raw text of job description here\]

#### **4\. Phase 2: Requirements Mapping and Gap Analysis via a Workflow**

##### **4.1 Pattern: A Multi-Node Workflow for Sequential Analysis**

This phase entails a logical sequence of distinct analytical steps: first mapping requirements to personal experiences, then assessing the strength of those mappings, and finally identifying any gaps. This linear, multi-step process is a canonical use case for a PocketFlow Workflow, which excels at chaining multiple nodes together to form a processing pipeline.2  
Furthermore, the initial mapping step requires searching through the personal career database to find relevant evidence for each job requirement. This sub-task is a form of Retrieval-Augmented Generation (RAG), where a retrieval system (searching the database) provides context to a generation system (the LLM or logic that creates the mapping).2

##### **4.2 Implementation: The AnalysisFlow**

The AnalysisFlow will be composed of three nodes that execute sequentially, with the output of each node serving as the input for the next.

* **nodes.py \- RequirementMappingNode:**  
  * **prep**: Reads the structured requirements from shared\["job\_requirements\_structured"\] and the full career database from shared\["career\_db"\].  
  * **exec**: This node will iterate through each requirement extracted in Phase 1\. For each requirement (e.g., "full\_stack\_development"), it will perform a retrieval operation against the career\_db. This can be a combination of keyword matching and semantic search (if using embeddings) across the professional\_experience and projects sections to find all potentially relevant pieces of evidence. This internal RAG process generates a list of candidate evidence for each requirement.  
  * **post**: Saves this initial, unprocessed mapping of requirements to evidence into a new key in the shared store, shared\["requirement\_mapping\_raw"\].  
* **nodes.py \- StrengthAssessmentNode:**  
  * **prep**: Reads the raw mapping from shared\["requirement\_mapping\_raw"\].  
  * **exec**: This node iterates through each requirement and its associated list of evidence. It uses an LLM to perform a qualitative synthesis. The prompt for the LLM would be: "Given the job requirement '{requirement}' and the following evidence from my career history: {evidence\_list}, assess the strength of the match as HIGH, MEDIUM, or LOW. A HIGH match means the evidence directly and powerfully demonstrates the required skill. A MEDIUM match shows related experience. A LOW match is a weak or indirect link."  
  * **post**: Updates the mapping data structure with the LLM-assigned strength score for each requirement and saves it to shared\["requirement\_mapping\_assessed"\].  
* **nodes.py \- GapAnalysisNode:**  
  * **prep**: Reads the strength-assessed mapping from shared\["requirement\_mapping\_assessed"\] and the original requirements from shared\["job\_requirements\_structured"\].  
  * **exec**: This node's logic compares the "must-have" requirements against the assessed mappings. Any "must-have" requirement with a LOW strength or no evidence is flagged as a gap. For each identified gap, the node uses another LLM call to brainstorm a mitigation strategy, as specified in the user's guideline. The prompt would be: "I have a gap in my experience for the requirement '{requirement}'. My current state is '{current\_state}'. Brainstorm a concise, strategic way to mitigate this weakness in a cover letter or interview."  
  * **post**: Saves the final, fully annotated mapping to shared\["requirement\_mapping\_final"\] and the list of identified gaps and their mitigation strategies to shared\["gaps"\].

#### **5\. Phase 3: Company Research via an Autonomous Agent**

##### **5.1 Pattern: The Agent for Dynamic, Multi-Step Research**

Phase 3 deviates from a linear pipeline. The task of researching a company is inherently dynamic and exploratory. The system must be able to formulate search queries, execute them, parse the results, decide if the information is sufficient, and potentially refine its search or explore new avenues. This iterative, decision-driven process is the quintessential use case for the PocketFlow Agent pattern.1  
An agent in PocketFlow is typically implemented as a looping Flow that can dynamically choose which "tool" to use at each step based on the current context and its overall goal. The intelligence of the agent emerges from its ability to select the right tool for the job and to iterate until its objective is complete.

##### **5.2 Implementation: The CompanyResearchAgent**

The agent's primary goal is to populate the company\_research data structure defined in the user's guideline. To achieve this, it needs to interact with the external world (the internet) through a set of predefined tools.  
The architecture will be based on the canonical agentic loop demonstrated in the PocketFlow documentation: a central DecideActionNode that directs traffic to various tool-using nodes and then loops back to itself for re-evaluation.22 The tools themselves will be implemented as simple functions in the  
utils/ directory, such as utils/web\_search.py and utils/web\_scraper.py. The Action Space defined in the agent's prompt is what exposes these capabilities to the LLM, allowing it to "use" the tools.

* **The Flow Structure:**  
  * **DecideActionNode**: The cognitive core of the agent. It assesses the current state of the research and decides the next action.  
  * **WebSearchNode**: A simple node that calls the utils/web\_search.py utility with a query provided by the DecideActionNode.  
  * **ReadContentNode**: A node that calls a utils/web\_scraper.py utility to extract clean, readable text from a specific URL.  
  * **SynthesizeInfoNode**: A node that takes a block of raw text (e.g., an "About Us" page) and uses an LLM to extract and synthesize the specific piece of information needed to fill one field of the company\_research template (e.g., 'mission').  
  * The Flow will be a loop. DecideActionNode will return an action string (e.g., "search", "read", "synthesize", "finish"). This action directs the flow to the corresponding node. After the tool node executes, the flow loops back to DecideActionNode for the next decision. This continues until the DecideActionNode determines the research is complete and returns the "finish" action.

* ### **nodes.py \- DecideActionNode Prompt:**   **The prompt for the decision-making node is the most critical part of the agent's design. It must provide clear context, a well-defined set of actions, and instructions for how to reason. It will be structured based on the official documentation's best practices.22**   **\#\#\# CONTEXT**   **Your goal is to conduct research on the company "{company\_name}" for the role of "{role\_title}" and complete the following research template.**    **Template to fill:**   **\`\`\`yaml**   **company\_research:**     **{company\_name}:**       **mission: null**       **team\_scope: null**       **strategic\_importance: null**       **culture: null**    **Current state of research:**   **YAML**   **{current\_state\_of\_template}**     **ACTION SPACE**    **You have the following tools available:**   **web\_search**   **Description: Use a web search engine to find relevant URLs (e.g., company website, news articles, blog posts).**   **Parameters:**   **\- query (str): The search query.**   **read\_content**   **Description: Read the full text content from a given URL.**   **Parameters:**   **\- url (str): The URL to scrape.**   **synthesize**   **Description: Analyze a block of text to fill a specific field in the research template.**   **Parameters:**   **\- field\_to\_fill (str): The name of the field to populate (e.g., "mission", "team\_scope").**   **\- content\_to\_analyze (str): The text content to analyze.**   **finish**   **Description: Use this action when all fields in the research template are complete.**   **Parameters: None**    **NEXT ACTION**    **Based on the context and the current state of the research template, decide the next single action to take. Provide your step-by-step reasoning process. Return your response ONLY in the following YAML format:**   **YAML**   **thinking: |**     **\<your step-by-step reasoning process for choosing the next action\>**   **action: \<action\_name\>**   **parameters:**     **\<parameter\_name\>: \<parameter\_value\>**  

---

### **Part III: Synthesis and Material Generation**

#### **6\. Phase 4 & 5: Suitability Assessment and Narrative Strategy**

##### **6.1. Pattern: Advanced Synthesis Workflows**

These phases transition from data gathering and analysis to high-level synthesis. The goal is to take all the structured information generated in the preceding phases and distill it into two key outputs: a quantitative suitability\_assessment and a qualitative narrative\_strategy. These tasks, while complex, are fundamentally sequential. They involve taking structured inputs, applying a series of transformations and logical steps, and producing structured outputs. Therefore, they are best implemented as two distinct, sequential Workflows.

##### **6.2. Implementation: AssessmentFlow and NarrativeFlow**

* **AssessmentFlow:** This workflow is responsible for generating the suitability\_assessment object.  
  * **SuitabilityScoringNode**: This single, powerful node takes shared\["requirement\_mapping\_final"\] and shared\["gaps"\] as its primary inputs. Its exec method will use an LLM to perform a holistic evaluation. The prompt will instruct the LLM to act as a senior hiring manager and perform several tasks in one call:  
    1. Calculate a technical\_fit score out of 100 based on the number of "must-have" and "nice-to-have" skills met, weighted by their assessed strength.  
    2. Calculate a cultural\_fit score based on the company research and the applicant's stated goals.  
    3. Synthesize the applicant's most compelling strengths from the mapping.  
    4. Identify the most significant gaps.  
    5. Most importantly, formulate the unique\_value\_proposition by identifying the rare and powerful intersections of skills and experiences (e.g., "A full-stack engineer with patented ML experience and a proven track record of building user-loved developer tools").  
       The output of this node will be the complete suitability\_assessment dictionary, which is then saved to the Shared Store.  
* **NarrativeFlow:** This workflow develops the strategic blueprint for the application materials.  
  * **ExperiencePrioritizationNode**: This node implements the user's weighted scoring framework. Critically, this can be a pure Python node that does not require an LLM. Its exec method will iterate through every item in the career\_db (experiences and projects), score each against the job requirements using the user's explicit weights (relevance\_to\_role: 40%, recency: 20%, etc.), and produce a ranked list of all career experiences. This list is saved to the Shared Store.  
  * **NarrativeStrategyNode**: This is a highly sophisticated LLM-driven node that performs the final strategic synthesis. It takes the ranked list of experiences from the previous node and the suitability\_assessment as input. Its prompt will be a master instruction for a "career storyteller": "You are an expert career coach. Your task is to create a narrative strategy for a job application. Use the provided ranked list of experiences and suitability assessment to: 1\. Select the top 2-3 'must-tell' experiences that directly address the core job requirements. 2\. Select 1-2 'differentiator' experiences that make the candidate unique. 3\. Formulate a compelling career arc (past, present, future) that positions this role as the logical and aspirational next step. 4\. Define three concise, powerful key messages to be woven throughout the application. 5\. Draft 1-2 detailed evidence stories in the 'Challenge, Action, Result' (CAR) format using the top-ranked experiences." The structured output of this node will be the complete narrative\_strategy object.

#### **7\. Phase 6: Material Construction in Markdown**

##### **7.1. Pattern: Generative Workflows**

This final phase is purely creative and generative. It uses the high-level strategic outputs from Phase 5 to construct the tangible application materials: the CV and cover letter. This is best implemented as a Workflow designed to produce formatted text, specifically Markdown. The existence of a Batch tutorial in the PocketFlow repository that involves translating markdown indicates the framework is well-suited for this kind of text and markup manipulation.

##### **7.2. Implementation: The GenerationFlow**

* **CVGenerationNode:**  
  * **prep**: Reads the final shared\["narrative\_strategy"\] and the original shared\["career\_db"\].  
  * **exec**: This node uses an LLM with a prompt that delegates the task of resume writing. The prompt will be: "You are a professional resume writer creating a tailored CV in GitHub-flavored Markdown. Use the following narrative strategy: {strategy}. The CV must prominently feature these prioritized experiences: {list\_of\_experiences\_to\_emphasize}. Experiences to minimize or summarize briefly are: {list\_to\_minimize}. Structure the CV to mirror the language of the job spec and quantify impact wherever possible, drawing data from the full career database provided here: {career\_db}. The final output must be only the Markdown content for the CV."  
  * **post**: Saves the generated Markdown string to shared\["cv\_markdown"\].  
* **CoverLetterNode:**  
  * **prep**: Reads shared\["narrative\_strategy"\], shared\["company\_research"\], and shared\["suitability\_assessment"\].  
  * **exec**: This node uses an LLM with a highly detailed prompt that directly implements the user's specified 5-part cover letter structure. The prompt will be a template that the agent fills in: "Write a compelling and authentic cover letter based on the following structure and information. 1\. **Hook**: Start by directly addressing a need or goal mentioned in the company research: {company\_mission\_or\_goal}. 2\. **Value Proposition**: Clearly state the unique value you bring, using this summary: {unique\_value\_proposition}. 3\. **Evidence**: Provide concrete proof by weaving in these 2-3 evidence stories: {evidence\_stories}. 4\. **Company Fit**: Explain your specific attraction to the company, referencing their values and your research: {company\_research}. 5\. **Call to Action**: Conclude with a confident and clear call to action."  
  * **post**: Saves the generated cover letter text to shared\["cover\_letter\_text"\].

---

### **Part IV: Orchestration and Final Architecture**

#### **8\. The Unified Agent: Final Assembly and Data Contracts**

##### **8.1 The main.py Orchestrator**

The top-level main.py script serves as the master orchestrator for the entire agent. Its responsibilities are to:

1. Perform initial setup: Load the career database from YAML files and read the target job specification text.  
2. Initialize the Shared Store dictionary with this foundational data.  
3. Create instances of each Flow (RequirementExtractionFlow, AnalysisFlow, CompanyResearchAgent, etc.).  
4. Chain these flows together or run them sequentially, passing the shared dictionary from one to the next. This ensures a continuous data pipeline where the output of one phase becomes the input for the next.  
5. Handle the final output by taking the generated cv\_markdown and cover\_letter\_text from the Shared Store and writing them to .md and .txt files.

##### **8.2 The Shared Store Data Contract**

The Shared Store is the central nervous system of the agent. Its structure defines the data dependencies and the "API contract" between every phase. A well-designed, explicit data contract is the most critical element for ensuring the system is modular, debuggable, and maintainable. It provides a single source of truth for the data that flows through the agent's entire lifecycle. The following table defines this contract.  
**Table 3: The Shared Store Data Contract**

| Key | Data Type | Produced By | Consumed By |
| :---- | :---- | :---- | :---- |
| career\_db | dict | Initial Setup | AnalysisFlow, NarrativeFlow, GenerationFlow |
| job\_spec\_text | str | Initial Setup | RequirementExtractionFlow |
| job\_requirements\_structured | dict | RequirementExtractionFlow | AnalysisFlow |
| requirement\_mapping\_final | dict | AnalysisFlow | AssessmentFlow |
| gaps | list\[dict\] | AnalysisFlow | AssessmentFlow |
| company\_research | dict | CompanyResearchAgent | AssessmentFlow, GenerationFlow |
| suitability\_assessment | dict | AssessmentFlow | NarrativeFlow, GenerationFlow |
| narrative\_strategy | dict | NarrativeFlow | GenerationFlow |
| cv\_markdown | str | GenerationFlow | Final Output |
| cover\_letter\_text | str | GenerationFlow | Final Output |

##### **8.3 Final System Diagram**

To provide a complete visual representation of the agent's architecture, the following diagram illustrates the sequence of Flows and their interaction via the Shared Store. Each major phase from the user's guideline is represented as a distinct Flow (subgraph), demonstrating the system's modularity. The arrows indicate the overall orchestration managed by main.py.

Code snippet

flowchart TD  
    subgraph "Setup"  
        A\[Load career\_db.yaml\] \--\> S;  
        B\[Load job\_spec.txt\] \--\> S;  
    end

    subgraph "Phase 1: Extraction"  
        F1  
    end

    subgraph "Phase 2: Analysis"  
        F2\[AnalysisFlow\]  
    end

    subgraph "Phase 3: Research"  
        F3  
    end

    subgraph "Phase 4: Assessment"  
        F4\[AssessmentFlow\]  
    end

    subgraph "Phase 5: Strategy"  
        F5\[NarrativeFlow\]  
    end

    subgraph "Phase 6: Generation"  
        F6\[GenerationFlow\]  
    end

    subgraph "Output"  
        O1  
        O2  
    end  
      
    S(Shared Store) \--\> F1;  
    F1 \--\> S;  
    S \--\> F2;  
    F2 \--\> S;  
    S \--\> F3;  
    F3 \--\> S;  
    S \--\> F4;  
    F4 \--\> S;  
    S \--\> F5;  
    F5 \--\> S;  
    S \--\> F6;  
    F6 \--\> S;  
    S \--\> O1;  
    S \--\> O2;

### **Conclusion and Recommendations**

This report has detailed a comprehensive architectural blueprint for implementing the user's "Job Application Agent Guideline" using the The-Pocket/PocketFlow framework. By systematically mapping each phase of the user's specification to a corresponding PocketFlow design pattern—Structured Output, Workflow, and Agent—we have designed a system that is modular, robust, and aligned with the framework's core philosophy of "Agentic Coding."  
The key architectural decisions include:

1. **Strict Separation of Concerns**: Isolating external interactions (file parsing, web scraping) into utils modules, keeping Nodes and Flows focused purely on orchestration logic.  
2. **Pattern-Based Design**: Leveraging the appropriate PocketFlow pattern for each task, using simple Workflows for linear processes and a dynamic Agent for complex, iterative research.  
3. **Prompt Engineering as a Core Component**: Designing detailed, example-driven prompts for all LLM-driven nodes to ensure high-quality, reliable outputs for tasks like structured data extraction, synthesis, and creative generation.  
4. **The Shared Store as a Central Contract**: Defining a clear and explicit data schema for the Shared Store to ensure seamless integration and state management between all phases of the agent's operation.

To proceed with implementation, the following steps are recommended:

* **Iterative Development**: Build and test each Flow independently. Start with the RequirementExtractionFlow and validate its output before moving to the AnalysisFlow. This modular approach, enabled by the PocketFlow design, simplifies debugging.  
* **Utility-First Implementation**: Implement and unit-test all necessary utility functions (database\_parser, web\_search, web\_scraper, LLM wrappers) before constructing the Nodes that depend on them.  
* **Focus on Prompt Refinement**: The quality of the final output will be highly dependent on the performance of the LLM-driven nodes. Expect to iterate on the prompts for ExtractRequirementsNode, SuitabilityScoringNode, and NarrativeStrategyNode to achieve the desired level of nuance and accuracy.

By following this architectural guide, a developer or an AI coding assistant can systematically construct a powerful, automated agent that transforms the manual, time-consuming process of job application into a strategic, data-driven workflow.

#### **Works cited**

1. I Built Pocket Flow, an LLM Framework in just 100 Lines — Here is Why | by Zachary Huang, accessed on July 31, 2025, [https://medium.com/@zh2408/i-built-an-llm-framework-in-just-100-lines-83ff1968014b](https://medium.com/@zh2408/i-built-an-llm-framework-in-just-100-lines-83ff1968014b)  
2. The-Pocket/PocketFlow: Pocket Flow: 100-line LLM framework. Let Agents build Agents\! \- GitHub, accessed on July 31, 2025, [https://github.com/The-Pocket/PocketFlow](https://github.com/The-Pocket/PocketFlow)  
3. Agentic Coding | Pocket Flow, accessed on July 31, 2025, [https://the-pocket.github.io/PocketFlow/guide.html](https://the-pocket.github.io/PocketFlow/guide.html)  
4. Home | Pocket Flow, accessed on July 31, 2025, [https://the-pocket.github.io/PocketFlow/](https://the-pocket.github.io/PocketFlow/)  
5. PocketFlow Docs: Home, accessed on July 31, 2025, [https://pocketflow.github.io/](https://pocketflow.github.io/)  
6. Tencent/PocketFlow: An Automatic Model Compression (AutoMC) framework for developing smaller and faster AI applications. \- GitHub, accessed on July 31, 2025, [https://github.com/Tencent/PocketFlow](https://github.com/Tencent/PocketFlow)  
7. Tutorial \- PocketFlow Docs, accessed on July 31, 2025, [https://pocketflow.github.io/tutorial/](https://pocketflow.github.io/tutorial/)  
8. Saoge123/PocketFlow: an autoregressive flow model incorporated with chemical acknowledge for generating drug-like molecules inside protein pockets \- GitHub, accessed on July 31, 2025, [https://github.com/Saoge123/PocketFlow](https://github.com/Saoge123/PocketFlow)  
9. (PDF) PocketFlow is a data-and-knowledge-driven structure-based molecular generative model \- ResearchGate, accessed on July 31, 2025, [https://www.researchgate.net/publication/378874436\_PocketFlow\_is\_a\_data-and-knowledge-driven\_structure-based\_molecular\_generative\_model](https://www.researchgate.net/publication/378874436_PocketFlow_is_a_data-and-knowledge-driven_structure-based_molecular_generative_model)  
10. I Built an Agent Framework in just 100 Lines\!\! : r/AI\_Agents \- Reddit, accessed on July 31, 2025, [https://www.reddit.com/r/AI\_Agents/comments/1i5tjd0/i\_built\_an\_agent\_framework\_in\_just\_100\_lines/](https://www.reddit.com/r/AI_Agents/comments/1i5tjd0/i_built_an_agent_framework_in_just_100_lines/)  
11. The-Pocket/PocketFlow-CPP: Pocket Flow: A minimalist LLM framework. Let Agents build Agents\! \- GitHub, accessed on July 31, 2025, [https://github.com/The-Pocket/PocketFlow-CPP](https://github.com/The-Pocket/PocketFlow-CPP)  
12. The-Pocket/PocketFlow-Go: Pocket Flow: A minimalist LLM framework. Let Agents build Agents\! \- GitHub, accessed on July 31, 2025, [https://github.com/The-Pocket/PocketFlow-Go](https://github.com/The-Pocket/PocketFlow-Go)  
13. The-Pocket/PocketFlow-Typescript: Pocket Flow: A minimalist LLM framework. Let Agents build Agents\! \- GitHub, accessed on July 31, 2025, [https://github.com/The-Pocket/PocketFlow-Typescript](https://github.com/The-Pocket/PocketFlow-Typescript)  
14. PocketFlow/.cursorrules at main \- GitHub, accessed on July 31, 2025, [https://github.com/the-pocket/PocketFlow/blob/main/.cursorrules](https://github.com/the-pocket/PocketFlow/blob/main/.cursorrules)  
15. Structured Outputs: Everything You Should Know \- Humanloop, accessed on July 31, 2025, [https://humanloop.com/blog/structured-outputs](https://humanloop.com/blog/structured-outputs)  
16. Structured Outputs \- OpenAI API, accessed on July 31, 2025, [https://platform.openai.com/docs/guides/structured-outputs](https://platform.openai.com/docs/guides/structured-outputs)  
17. Structured Outputs \- Build with Cerebras Inference, accessed on July 31, 2025, [https://inference-docs.cerebras.ai/capabilities/structured-outputs](https://inference-docs.cerebras.ai/capabilities/structured-outputs)  
18. Introduction to Prompt Engineering for Data Professionals \- Dataquest, accessed on July 31, 2025, [https://www.dataquest.io/blog/introduction-to-prompt-engineering-for-data-professionals/](https://www.dataquest.io/blog/introduction-to-prompt-engineering-for-data-professionals/)  
19. A Data Professional's Guide to Prompt Engineering with Synthetic Survey Data \- Medium, accessed on July 31, 2025, [https://medium.com/@dataquestio/a-data-professionals-guide-to-prompt-engineering-with-synthetic-survey-data-e074d7d5f69d](https://medium.com/@dataquestio/a-data-professionals-guide-to-prompt-engineering-with-synthetic-survey-data-e074d7d5f69d)  
20. Building SQL Extractor using PocketFlow, Gemini & Streamlit | by Sreedharlal B Naick, accessed on July 31, 2025, [https://medium.com/@sreedharlal.b.naick/building-sql-extractor-using-pocketflow-gemini-streamlit-60fd6fedfbeb](https://medium.com/@sreedharlal.b.naick/building-sql-extractor-using-pocketflow-gemini-streamlit-60fd6fedfbeb)  
21. Archive \- Pocket Flow, accessed on July 31, 2025, [https://pocketflow.substack.com/archive](https://pocketflow.substack.com/archive)  
22. Agent | Pocket Flow \- GitHub Pages, accessed on July 31, 2025, [https://the-pocket.github.io/PocketFlow/design\_pattern/agent.html](https://the-pocket.github.io/PocketFlow/design_pattern/agent.html)