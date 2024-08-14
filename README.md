# career-agent

## Design principles

- Human-centric
  - In most cases, AI should augument, not replace the human from tasks
- AI Collaboration
  - The quality of the end result is the product of human-AI collaboration
- Transparency
  - The user should be able to see and edit the data in all it's intermediary forms

## TODO: High Level

- [ ] Prototype the main processing steps (see diagram.excalidraw and Project Description section) in jupyter notebooks
- [ ] Build an evaluation set for each step of processing that uses LLMs
- [ ] Decide which platform to release on

## Setup

- Get an API key from OpenAI. Paste it into a file called .env in the root directory of this repo.
  - Like this: `OPENAI_API_KEY=<the key>`

### Python

- Make sure the python version is 3.8
  - Check with: `python --version`
  - If it's not 3.8, install [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) and then run:
    - `pyenv install 3.8`
  - N.B. don't use the Terminal window in VSCode, it doesn't work well with pyenv. Use the terminal app.
- Create a virtual environment
  - `python -m venv venv`
- Install the requirements
  - `pip install -r requirements.txt`

### Optional

- Readme files will contain wikilinks to other files in the repo. To use these links, use an extension e.g.
  - [Foam](https://foambubble.github.io/foam/) for VSCode
  - ... or [Markdown Links](https://marketplace.visualstudio.com/items?itemName=henriiik.vscode-markdown-links) extension in VSCode.
- View Excalidraw Diagrams
  - If using VSCode, install Excalidraw plugin

## Project Description

1. Parse CVs
   - Create database of all your experiences, skills, deliverables etc.
   - Columns: Company, Experience, Skills, KPIs
2. Parse Job Specs and extract:
   - Technical job requirements
   - Soft skill requirements
   - Industry, culture and values from job spec
3. Match Experience to Job Spec
4. Write CV
   - For each work experience section, write the bullet points for key experiences
   - For profile show it the:
     - Outputs of step 3.1 (the work experiences)
     - The name, values, culture, industry of the company
     - An conceptual outline / structure
5. Cover Letter
   - Body paragraphs with inputs. Reverse chronological order
     - CV work experience
     - Soft skills requirements
   - Intro paragraph summarising journey in chronological order, building a narrative for why the next logical step is in this role.
     - Body paragraphs from 4.1
     - Company details (industry, values, culture etc)
   - Summary paragraph
     - The rest of the cover letter
   - (Style matching)
     - In order to avoid looking like it was AI-generated, it would be good to provide examples of your own prose as part of the prompts.

## Implementation Discussion

### UI

#### Requirements

- Present intermediary data and make it editable before proceeding to next steps

#### Platform options

This is linked to choice of language. We'd prefer to use Python for the better libraries but TS/JS is better for web apps.

- Web app
  - When running locally, run on localhost
  - Could be hosted on the web
- Desktop app
  - Electron
- CLI
  - Could be a CLI tool
- Jupyter Notebook
  - Could develop like this and convert to a another platform later
- Extension to a text editor
  - VSCode
  - Obsidian
- Streamlit
