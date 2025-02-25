import os
from typing import Optional
from typing import Tuple

from fuzzywuzzy import fuzz
from rdflib import Graph

from app.common import logger


class CompanyMatcher:
    def __init__(self, graph_path: str):
        self.g = Graph()
        self.g.parse(os.path.join(graph_path, "companies.ttl"), format="ttl")

    def get_company_matches(self, company_name: str) -> Optional[Tuple[str, str, float]]:
        """
        Search for a company name in the graph and return the best match with canonical name.

        Args:
            company_name (str): The company name to search for

        Returns:
            Optional[Tuple[str, str, float]]: Tuple of (canonical name, official name, match ratio) or None if no match found
        """
        # First try exact match
        query = (
            """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX ex: <http://example.com/>
            SELECT ?canonicalName ?label
            WHERE {
                ?company rdfs:label ?label ;
                        ex:canonicalName ?canonicalName .
                BIND(LCASE(str(?label)) AS ?lowerLabel)
                FILTER(?lowerLabel = "%s")
            }
        """
            % company_name.lower()
        )

        results = self.g.query(query)
        for row in results:
            return (str(row.canonicalName), str(row.label), 100.0)

        # If no exact match, try fuzzy matching against all labels
        query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX ex: <http://example.com/>
            SELECT DISTINCT ?canonicalName ?label ?altLabel
            WHERE {
                ?company rdfs:label ?label ;
                        ex:canonicalName ?canonicalName ;
                        ex:altLabel ?altLabel .
            }
        """

        best_match = None
        best_ratio = 0

        results = self.g.query(query)
        company_name_lower = company_name.lower()

        for row in results:
            # Check main label
            ratio = fuzz.ratio(company_name_lower, str(row.label).lower())
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = (str(row.canonicalName), str(row.label), ratio)

            # Check alternative label
            ratio = fuzz.ratio(company_name_lower, str(row.altLabel).lower())
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = (str(row.canonicalName), str(row.label), ratio)

        # Return best match if it meets threshold
        if best_match and best_match[2] >= 75:
            logger.info(
                f"Found fuzzy match for '{company_name}': {best_match[1]} (ratio: {best_match[2]})"
            )
            return best_match

        logger.warning(f"No match found for company name: {company_name}")
        return None

    def get_canonical_name(self, company_name: str) -> Optional[str]:
        """
        Main interface to find a company's canonical name given any variant of its name.

        Args:
            company_name (str): Name to search for

        Returns:
            Optional[str]: Canonical name if found, None otherwise
        """
        match = self.get_company_matches(company_name)
        if match:
            return match[0]  # Return canonical name instead of source doc
        # return None
        return company_name  # Return the original name if no match found


g = Graph()
g.parse(os.path.join("data", "knowledge_graph", "companies.ttl"), format="ttl")


def is_company_match(source, company_name):
    query = """
    PREFIX ex: <http://example.com/>

    SELECT ?altLabel
    WHERE {{
        ?company ex:sourceDoc ?sourceDoc ;
                ex:altLabel ?altLabel .
        FILTER(?sourceDoc = "{}")
    }}
    """.format(
        source
    )

    results = g.query(query)

    logger.info(source)
    for row in results:
        if fuzz.ratio(company_name.lower(), row.altLabel.lower()) > 75:
            return True
    return False


company_matcher = CompanyMatcher(os.path.join("data", "knowledge_graph"))
