# "Kapital" Assistant
AI-powered interface to chat over the financial reportings. 🤖

This is a slightly polished version of what we have built at [Hack Genesis 2024](https://hackgenesis.com/) which secured as the first place. 🏆

The project is live, [**check it out here.**](https://kapital-assistant.vercel.app/)

Currently, only limited number of reports is available, check the demo page for more details.

## Codebase

```
├── app                           # Backend app
│   ├── api.py                    # FastAPI app
│   ├── common                   # Utilities and Tools
│   │   ├── __init__.py          # Prompts and common params
│   │   ├── knowledge_graphs.py  # Code for matching user query and the correct company DB
│   │   ├── structured_tools.py  # Tools to be called by an agent for tabular data analysis 
│   │   ├── unstructured_tools.py # Tools for textual unstructured data 
│   │   └── utils.py             # common utils
│   └── prompts                  # YAML prompt templates
├── frontend             # Next.js frontend application
├── data                 # Data and vector DBs for the project
├── Dockerfile          # Backend Dockerfile
└── docker-compose.yml  # Docker compose configuration
```

## Getting Started

### Backend Setup

1. Clone the repository:
```bash
git clone git@github.com:dm-shr/kapital-assistant.git
cd kapital-assistant
```

2. Set up environment variables:
```bash
cp .env.example .env
```

Generate a secure API key:
```bash
openssl rand -base64 32
```

Add it to your `.env` file along with other required variables.

**NOTE**: You would need an OpenAI API key for the current project implementation.

3. Download required data:
```bash
chmod +x get-data.sh
./get-data.sh
```

4. Start the backend services:
```bash
docker-compose up -d --build
```

5. (Optional) Set up ngrok for external access:
```bash
ngrok http 8000
```

You would need to install ngrok for that.

### Frontend Setup

1. Development mode:
```bash
cd frontend
cp .env.development.example .env.development
# Add your configuration to .env.development
npm install
npm run dev
```

2. Production deployment:
- Deploy to Vercel:
  1. Connect your GitHub repository
  2. Add environment variables in Vercel project settings:
     - `PROD_API_URL`: Your backend API URL
     - `PROD_API_KEY`: Your API key (must match backend's API_KEYS)


## Architecture Overview

<img src="./resources/img/overview.jpg" alt="System Overview" width="700"/>

----


Key points:
* The assistant engine is developed using LangChain.
* The agent app is using Tools for interacting with the external world.
* Hybrid search (vector similarity + BM25) is used for the RAG.
* Knowledge graphs are used to store company metadata and route user query to the correct company collection.

### Unstructured Data Search (Qualitative Questions)

<img src="./resources/img/unstructured.jpg" alt="Unstructured Data Search (Qualitative Questions)" width="700"/>

Information search on a given topic based on unstructured data (text).

----

### Structured Data Search (Quantitative Questions)

<img src="./resources/img/structured.jpg" alt="Structured Data Search (Quantitative Questions)" width="700"/>

Information search on a given topic based on structured data (tables).

----

### Knowledge Graphs for query routing

<img src="./resources/img/knowledge-graph.jpg" alt="Knowledge Graph Pipeline" width="700"/>

The use of knowledge graph helps quickly map the user-used company name with the correcte knowledge base

----

### Data Ingestion Pipeline

#### Structured Data (Tables)
<img src="./resources/img/structured-ingestion.jpg" alt="Structured Data Ingsestion" width="700"/>

----

#### Untructured Data (Text)
<img src="./resources/img/unstructured-ingestion.jpg" alt="Unstructured Data Ingsestion" width="700"/>

----

## Authors

- [Dmitrii Shiriaev](https://www.linkedin.com/in/dshiriaev/)
- [Aleksandr Perevalov](https://www.linkedin.com/in/aleksandr-perevalov/)
- [Vladislav Raskoshinskii](https://www.linkedin.com/in/vladislav-raskoshinskii/)
- [Ilya Moshonkin](https://www.linkedin.com/in/ilyamoshonkin/)

## Connect With me

[![GitHub](https://img.shields.io/badge/GitHub-dm--shr-black?style=flat&logo=github)](https://github.com/dm-shr)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Dmitrii_Shiriaev-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/dshiriaev/)
