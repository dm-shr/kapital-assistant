import base64
import io
import json
import os
from typing import List
from typing import Optional
from typing import Type

from langchain.prompts import load_prompt
from langchain.pydantic_v1 import BaseModel
from langchain.pydantic_v1 import Field
from langchain.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.tools import BaseTool
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from PIL import Image

from app.common import logger
from app.common import OPENAI_API_KEY
from app.common import PROMPT_PATH
from app.common.knowledge_graphs import company_matcher
from app.common.utils import get_base_64_string
from app.common.utils import load_docs_from_jsonl
from app.common.utils import metadata_filter_callable


faiss_vdb = "faiss_unstructured_pydata_v0.0.2"

emebeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)

db = FAISS.load_local(
    os.path.join("data", "unstructured_vdb", faiss_vdb),
    emebeddings,
    allow_dangerous_deserialization=True,
)

documents = load_docs_from_jsonl(os.path.join("data", "unstructured_vdb", faiss_vdb, "docs.jsonl"))


llm = ChatOpenAI(
    model="gpt-4o",
    api_key=OPENAI_API_KEY,
    model_kwargs={"response_format": {"type": "json_object"}},
)
prompt = load_prompt(os.path.join(PROMPT_PATH, "rephrase.yaml"))
chain = prompt | llm


def context_from_hybrid_retriever(query, query_metadata, chunks, metadata_filter, top_k=20):
    logger.info(f"query metadata: {query_metadata}")
    logger.info(f"doc metadata: {chunks[0].metadata}")
    bm25_relevant_docs = [
        doc
        for doc in chunks
        if all(doc.metadata[key] in query_metadata[key] for key in query_metadata.keys())
    ]
    logger.info(f"len bm25: {len(bm25_relevant_docs)}")

    faiss_similarity_retriever = db.as_retriever(
        search_type="similarity", search_kwargs={"k": top_k, "filter": metadata_filter}
    )

    faiss_mmr_retriever = db.as_retriever(
        search_type="mmr", search_kwargs={"k": top_k, "filter": metadata_filter}
    )

    retrievers = [faiss_similarity_retriever, faiss_mmr_retriever]

    if len(bm25_relevant_docs) > 0:
        bm25_retriever = BM25Retriever.from_documents(bm25_relevant_docs)
        retrievers.append(bm25_retriever)

    ensemble_relevant_docs = EnsembleRetriever(
        retrievers=retrievers,
        # weights=[0.3, 0.2, 0.4],
    ).invoke(query)

    # get docs with unique page numbers, company names and years
    unique_docs = {}
    for doc in ensemble_relevant_docs:
        key = (doc.metadata["page_nr"], doc.metadata["company"], doc.metadata["year"])
        if key not in unique_docs:
            unique_docs[key] = doc
        else:
            continue

    ensemble_relevant_docs = list(unique_docs.values())
    return ensemble_relevant_docs


class UnstructuredToolInput(BaseModel):
    user_query: str = Field(query="User search query directed at structured data")
    company_names: Optional[List[str]] = Field(
        query="""\
        Company names.
            IMPORTANT:
            - Try very hard to find or infer the company names from the query.\
 It can be a single company or multiple companies variants. Be rather generous in this regard.
            - If company name is not provided in the query, leave this field to None"""
    )
    years: Optional[List[int]] = Field(
        query="""\
        Years the user query is related to. If the query is not related to a specific year, \
leave this field None.
        IMPORTANT: Try very hard to find or infer the years from the query. It can be a \
single year or multiple years variants. Be rather generous in this regard."""
    )
    quarters: Optional[List[str]] = Field(
        query="""\
        Quarters the user query is related to. A list which can contain:
        - 'q1': First quarter, in case the user query is related to Q1 or January-March.
        - 'q2': Second quarter, in case the user query is related to Q2 or April-June or\
 January-June or Half-year (H1).
        - 'q3': Third quarter, in case the user query is related to Q3 or July-September or\
 January-September or Nine months (9M).
        - 'q4': Fourth quarter, in case the user query is related to Q4 or October-December or\
 January-December or Whole year (FY).
        - 'annual': Annual data, in case the user query is related to the whole year (also add 'q4' \
to the list in this case).
        If the query is not related to a specific quarter, leave this field None.
        IMPORTANT: Try very hard to find or infer the quarters from the query. Be rather generous \
in this regard."""
    )


class UnstructuredTool(BaseTool):
    name = "unstructured_tool"
    description: str = """
    Searches for an answer to the user's question in an unstructured database of financial reports.
    Unsctructured data relates to the text of financial reports, without the focus on numbers, \
tables, metrics. It can be used to answer questions that require understanding of the context,\
 definitions, explanations, etc. It is especially useful when the user is looking for the risks, \
opportunities, trends, and other qualitative aspects of the financial data.
    Examples of such questions:
    - What types of events does the group consider as signs of default?
    - What do rent payments consist of?
    - In what cases does the group revalue the lease liability?
    - What is "LTIP"?
    - What is amortized cost?
    - When does the recognition of financial liabilities cease?
    And other questions...
    """
    args_schema: Type[BaseModel] = UnstructuredToolInput
    return_direct: bool = True

    def __init__(self, **data):
        super().__init__(**data)

    def _run(
        self,
        user_query: str = "",
        company_names: Optional[List[str]] = None,
        years: Optional[List[str]] = None,
        quarters: Optional[List[str]] = None,
        run_manager=None,
    ) -> str:
        years = years if years is not None else [2023]
        quarters = quarters if quarters is not None else ["q4", "annual"]
        quarters = [quarter.lower() for quarter in quarters]
        input_ = {
            "user_query": user_query,
            "company_names": company_names,
            "years": years,
            "quarters": quarters,
        }
        logger.info(f"Metadata: {user_query} {input_}")
        canonical_company_names = [
            company_matcher.get_canonical_name(company_name) for company_name in company_names
        ]
        logger.info(f"Canonical company names: {canonical_company_names}")
        query_metadata = {
            "company": canonical_company_names,
            "year": years,
            "quarter": quarters,
        }

        metadata_filter = metadata_filter_callable(
            companies=canonical_company_names, years=years, quarters=quarters
        )
        docs = context_from_hybrid_retriever(
            user_query, query_metadata, documents, metadata_filter, top_k=20
        )
        logger.info(f"Found {len(docs)} documents")
        # page_func = lambda x: docs[x].metadata["source"].split("/")[-1].split("_")[-1].split(".")[0]

        file_name_func = lambda x: docs[x].metadata["source"].split("/")[-2] + ".pdf"
        source_data = [
            {"index": index, "file_name": file_name_func(index), "context": doc.page_content}
            for index, doc in enumerate(docs)
        ]
        output = chain.invoke({"user_query": user_query, "source_data": str(source_data)})
        result = output.content
        try:
            logger.info(f"tokens sent: {output.response_metadata['token_usage']['prompt_tokens']}")
        except Exception as e:
            print(str(e))

        # try to convert into dict
        company_dict = {
            "hm": "H&M",
            "volvo": "Volvo",
            "ikea": "IKEA",
        }
        quarter_dict = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4", "annual": "FY"}
        try:
            result = json.loads(result)
            context_sources_indices = result.get("context_sources_indices", [])
            selected_docs = [docs[index] for index in context_sources_indices]
            companies = [
                company_dict.get(doc.metadata["company"], doc.metadata["company"])
                for doc in selected_docs
            ]
            quarters = [
                quarter_dict.get(doc.metadata["quarter"], doc.metadata["quarter"])
                for doc in selected_docs
            ]
            years = [doc.metadata["year"] for doc in selected_docs]
            pages = [doc.metadata["page_nr"] for doc in selected_docs]
            file_names = [
                company + "_" + str(year) + "_" + quarter
                for company, year, quarter in zip(companies, years, quarters)
            ]
            file_names_metadata = [file_name_func(index) for index in context_sources_indices]
            images = []
            for page, file_name in zip(pages, file_names_metadata):
                base64_string = get_base_64_string(
                    os.path.join(
                        "data",
                        "for_pydata",
                        "pdf_png_base64",
                        file_name.split(".")[0],
                        file_name.split(".")[0] + "_page_" f"{page}.txt",
                    )
                )
                images.append(base64_string)

        except IndexError as e:  # in case index starts from 1
            logger.error(f"Index error: {e}")
            context_sources_indices = [index - 1 for index in context_sources_indices]
            selected_docs = [docs[index] for index in context_sources_indices]
            companies = [
                company_dict.get(doc.metadata["company"], doc.metadata["company"])
                for doc in selected_docs
            ]
            quarters = [
                quarter_dict.get(doc.metadata["quarter"], doc.metadata["quarter"])
                for doc in selected_docs
            ]
            years = [doc.metadata["year"] for doc in selected_docs]
            pages = [doc.metadata["page_nr"] for doc in selected_docs]
            file_names = [
                company + "_" + str(year) + "_" + quarter
                for company, year, quarter in zip(companies, years, quarters)
            ]
            file_names_metadata = [file_name_func(index) for index in context_sources_indices]
            images = []
            for page, file_name in zip(pages, file_names_metadata):
                base64_string = get_base_64_string(
                    os.path.join(
                        "data",
                        "for_pydata",
                        "pdf_png_base64",
                        file_name.split(".")[0],
                        file_name.split(".")[0] + "_page_" f"{page}.txt",
                    )
                )
                images.append(base64_string)

        except Exception as e:
            logger.error(f"Error converting result to dict: {e}")
            file_names = []
            pages = []
            images = []
        logger.info(f"File names retrieved: {file_names}")
        images = [Image.open(io.BytesIO(base64.b64decode(image))) for image in images]

        for image, file_name, page in zip(images, file_names_metadata, pages):
            company = company_dict[file_name.split("_")[0]]
            quarter = quarter_dict[file_name.split("_")[1]]
            year = file_name.split("_")[2].split(".")[0]

            # image.info['file_name'] = file_name
            image.info["file_name"] = f"{company} {quarter} {year}"
            image.info["page"] = page

        used_sources = {}
        for file, page_nr in zip(file_names, pages):
            if file in used_sources:
                used_sources[file].append(page_nr)
            else:
                used_sources[file] = [page_nr]
        for source in used_sources:
            used_sources[source] = [str(page_nr) for page_nr in sorted(used_sources[source])]

        logger.info(f"Used sources: {used_sources}")

        result_markdown = f"{result['response']}"

        def format_file_name(file_name: str) -> str:
            company, year, report_type = file_name.replace(".pdf", "").split("_")
            company_mapping = {"ikea": "IKEA", "volvo": "Volvo", "hm": "H&M", "h&m": "H&M"}
            report_mapping = {
                "q1": "Q1",
                "q2": "Q2",
                "q3": "Q3",
                "q4": "Q4",
                "annual": "annual",
                "fy": "annual",
            }
            report_type = report_mapping[report_type.lower()]
            company = company_mapping[company.lower()]
            return f"{company} {report_type} report, year {year}"

        if len(used_sources) > 0:
            result_markdown += "\n\n**Sources:**\n\n"
            result_markdown += "\n".join(
                [
                    f"- {format_file_name(file_name)}\n  - Pages: {', '.join(used_sources[file_name])}"
                    for file_name in used_sources
                ]
            )

        logger.info(f"Output: {result}")

        return {
            "result": result_markdown,  # docs[0].page_content,
            "metadata": {"file_name": file_names, "page": pages},
            "image": images,
        }
