import base64
import io
import json
import os
from typing import List
from typing import Optional
from typing import Type

from langchain.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.tools import BaseTool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from PIL import Image
from pydantic import BaseModel
from pydantic import Field

from app.common import logger
from app.common import MODEL
from app.common import OPENAI_API_KEY
from app.common import TOP_K
from app.common.knowledge_graphs import company_matcher
from app.common.utils import get_base_64_string
from app.common.utils import load_docs_from_jsonl
from app.common.utils import metadata_filter_callable
from app.common.utils import process_chat_completion


faiss_vdb = "faiss_structured_pydata_v0.0.1_full_size_score_above_50"


db = FAISS.load_local(
    os.path.join("data", "structured_vdb", faiss_vdb),
    OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY),
    allow_dangerous_deserialization=True,
)

documents = load_docs_from_jsonl(os.path.join("data", "structured_vdb", faiss_vdb, "docs.jsonl"))


def context_from_hybrid_retriever(query, query_metadata, chunks, metadata_filter, top_k=TOP_K):
    bm25_relevant_docs = [
        doc
        for doc in chunks
        if all(doc.metadata[key] in query_metadata[key] for key in query_metadata.keys())
    ]

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


class StructuredToolInput(BaseModel):
    user_query: str = Field(
        query="User search query directed at structured data. It can be an original\
 query re-written in a way that it can be used to search for the data in the financial reports."
    )
    company_names: Optional[List[str]] = Field(
        query="""\
        Company names.
            IMPORTANT:
            - Try very hard to find or infer the company names from the query. \
It can be a single company or multiple companies variants. Be rather generous in this regard.
            - If company name is not provided in the query, leave this field to None"""
    )
    years: Optional[List[int]] = Field(
        query="""\
        Years the user query is related to. If the query is not related to a specific year,\
 leave this field None. If the query is about the next year, consider it to be None.
        IMPORTANT: Try very hard to find or infer the years from the query. It can be a \
single year or multiple years variants. Be rather generous in this regard."""
    )
    quarters: Optional[List[str]] = Field(
        query="""\
        Quarters the user query is related to. A list which can contain:
        - 'q1': First quarter, in case the user query is related to Q1 or January-March.
        - 'q2': Second quarter, in case the user query is related to Q2 or April-June or \
January-June or Half-year (H1).
        - 'q3': Third quarter, in case the user query is related to Q3 or July-September or \
January-September or Nine months (9M).
        - 'q4': Fourth quarter, in case the user query is related to Q4 or October-December or\
 January-December or Whole year (FY).
        - 'annual': Annual data, in case the user query is related to the whole year (also add \
'q4' to the list in this case).
        If the query is not related to a specific quarter, leave this field None.
        IMPORTANT: Try very hard to find or infer the quarters from the query. Be rather \
generous in this regard."""
    )


class StructuredTool(BaseTool):
    name: str = "structured_tool"
    description: str = """
    Searches for an answer to the user's question in a structured database of financial reports.
    Structured data relates to the numbers, metrics, comparisons of these two.
    Use this tool to find the answer to the user's question in a structured database of financial reports.
    Examples of such questions:
    - The amount of retained earnings of the Company as of 12/31/2022
    - Total liabilities of the company as of December 31, 2022?
    - Total deficit of the company's capital as of December 31, 2022
    - What are the other non-financial assets as of December 31, 2022?
    - Total profit for 2020?
    - How much has the economy decreased?
    - Total loans issued as of December 31, 2021
    And other questions...
    """
    args_schema: Type[BaseModel] = StructuredToolInput
    return_direct: bool = True

    def __init__(self, **data):
        super().__init__(**data)

    def _run(
        self,
        user_query: str = "",
        # company_name: str="",
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

        # logger.info(f"Metadata: {user_query}")
        canonical_company_names = [
            company_matcher.get_canonical_name(company_name) for company_name in company_names
        ]
        logger.info(f"Metadata: {str(input_)}, ")

        metadata_filter = metadata_filter_callable(canonical_company_names, years, quarters)
        query_metadata = {
            # "user_query": user_query,
            "company": canonical_company_names,
            "year": years,
            "quarter": quarters,
        }
        docs = context_from_hybrid_retriever(
            user_query, query_metadata, documents, metadata_filter, top_k=TOP_K
        )

        docs = docs[:TOP_K]

        source_data = []
        for index, doc in enumerate(docs):
            company_name = doc.metadata["company"]
            quarter = doc.metadata["quarter"]
            year = doc.metadata["year"]
            page = int(doc.metadata["page_nr"])
            file_name = f"{company_name}_{quarter}_{year}.pdf"
            logger.info(f"File name: {file_name}, Page: {page}")
            try:
                base64_string = get_base_64_string(
                    os.path.join(
                        "data",
                        "for_pydata",
                        "pdf_png_base64",
                        file_name.split(".")[0],
                        file_name.split(".")[0] + "_page_" f"{page}.txt",
                    )
                )

                context = base64_string
                summary = doc.page_content.split("## Summary of the table:\n")[1].strip()
            except Exception as e:
                logger.error(str(e))
                logger.info(os.path.join("data", "pdf", file_name))
                summary = doc.page_content.split("## Summary of the table:\n")[1].strip()
                context = None

            source_data.append(
                {
                    "index": index,
                    "file_name": file_name,
                    "summary": summary,
                    "context": context,
                    "page_nr": page,
                }
            )

        result = process_chat_completion(source_data, user_query, model=MODEL)

        # try to convert into dict
        try:
            result = json.loads(result)
            context_sources_indices = result.get("context_sources_indices", [])
            logger.info(f"Context sources indices: {len(context_sources_indices)}")
            file_names = [source_data[index]["file_name"] for index in context_sources_indices]
            pages = [source_data[index]["page_nr"] for index in context_sources_indices]
            images = [
                source_data[index]["context"] for index in context_sources_indices
            ]  # this is a list of base64 strings
            # convert to png with pillow without saving to disk
            images = [Image.open(io.BytesIO(base64.b64decode(image))) for image in images]
        # list index out of range error
        except IndexError as e:
            logger.error(f"Index error: {e}")
            context_sources_indices = [index - 1 for index in context_sources_indices]
            file_names = [source_data[index]["file_name"] for index in context_sources_indices]
            pages = [source_data[index]["page_nr"] for index in context_sources_indices]
            images = [
                source_data[index]["context"] for index in context_sources_indices
            ]  # this is a list of base64 strings
            images = [Image.open(io.BytesIO(base64.b64decode(image))) for image in images]
        except Exception as e:
            logger.error(f"Error converting result to dict: {e}")
            file_names = []
            pages = []
            images = []

        company_dict = {
            "hm": "H&M",
            "volvo": "Volvo",
            "ikea": "IKEA",
        }
        quarter_dict = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4", "annual": "FY"}
        for image, file_name, page in zip(images, file_names, pages):
            company = company_dict[file_name.split("_")[0]]
            quarter = quarter_dict[file_name.split("_")[1]]
            year = file_name.split("_")[2].split(".")[0]

            image.info["file_name"] = f"{company} {quarter} {year}"
            image.info["page"] = page

        used_sources = {}
        for file, page_nr in zip(file_names, pages):
            if file in used_sources:
                # used_sources[file].append(str(page_nr))
                used_sources[file].append(page_nr)
            else:
                # used_sources[file] = [str(page_nr)]
                used_sources[file] = [page_nr]

        for source in used_sources:
            used_sources[source] = [str(page_nr) for page_nr in sorted(used_sources[source])]

        logger.info(f"Output: {result}")
        logger.info(f"Used sources: {str(used_sources)}")
        result_markdown = f"{result['response']}"

        def format_file_name(file_name: str) -> str:
            company, report_type, year = file_name.replace(".pdf", "").split("_")
            company_mapping = {"ikea": "IKEA", "volvo": "Volvo", "hm": "H&M"}
            report_mapping = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4", "annual": "annual"}
            report_type = report_mapping[report_type]
            return f"{company_mapping[company]} {report_type} report, year {year}"

        if len(used_sources) > 0:
            result_markdown += "\n\n**Sources:**\n\n"
            result_markdown += "\n".join(
                [
                    f"- {format_file_name(file_name)}\n  - Pages: {', '.join(used_sources[file_name])}"
                    for file_name in used_sources
                ]
            )

        return {
            "result": result_markdown,
            "metadata": {"file_name": file_names, "page": pages},
            "image": images,
        }
