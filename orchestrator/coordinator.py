from pathlib import Path
import sys


# -------------------------------------------------
# Project path
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# -------------------------------------------------
# Import agents
# -------------------------------------------------

from agents.query_understanding_agent import (
    QueryUnderstandingAgent
)

from agents.product_retrieval_agent import (
    ProductRetrievalAgent
)

from agents.size_fit_agent import (
    SizeFitAgent
)

from agents.outfit_recommendation_agent import (
    OutfitRecommendationAgent
)


# -------------------------------------------------
# Coordinator
# -------------------------------------------------

class Coordinator:

    def __init__(self):

        self.name = "FitStyle AI Coordinator"

        self.query_agent = (
            QueryUnderstandingAgent()
        )

        self.retrieval_agent = (
            ProductRetrievalAgent(
                default_top_k=10
            )
        )

        self.size_fit_agent = (
            SizeFitAgent()
        )

        self.outfit_agent = (
            OutfitRecommendationAgent()
        )


    # -------------------------------------------------
    # Merge Size/Fit results
    # -------------------------------------------------

    def _merge_size_results(
        self,
        retrieved_products,
        size_results
    ):

        size_lookup = {
            item["product_id"]: item
            for item in size_results
        }

        merged_products = []

        for product in retrieved_products:

            product_id = product.get(
                "product_id"
            )

            size_info = size_lookup.get(
                product_id,
                {}
            )

            merged_products.append({
                **product,

                "requested_size":
                    size_info.get(
                        "requested_size"
                    ),

                "size_available":
                    size_info.get(
                        "size_available"
                    ),

                "available_sizes":
                    size_info.get(
                        "available_sizes",
                        []
                    ),

                "matching_variants":
                    size_info.get(
                        "matching_variants",
                        []
                    )
            })

        return merged_products



    # -------------------------------------------------
    # FitStyle AI system information
    # -------------------------------------------------

    def _build_system_info_response(
        self,
        query
    ):

        # Keep this response deterministic so the system
        # never invents capabilities that are not actually
        # implemented in FitStyle AI.
        return {
            "coordinator":
                self.name,

            "status":
                "success",

            "intent":
                "system_info",

            "query":
                query,

            "title":
                "About FitStyle AI",

            "message":
                (
                    "FitStyle AI is a multi-agent fashion "
                    "recommendation system that helps users "
                    "discover fashion products, verify available "
                    "sizes and variants, and build outfit "
                    "recommendations using preferences such as "
                    "style, occasion, budget, color, and size."
                ),

            "capabilities": [
                (
                    "Search for clothing, footwear, bags, "
                    "and fashion accessories."
                ),
                (
                    "Understand natural-language fashion "
                    "requests using a Query Understanding Agent."
                ),
                (
                    "Combine BM25 keyword retrieval and Qdrant "
                    "semantic search using Equal RRF."
                ),
                (
                    "Apply SQL Server hard filters for product "
                    "facts, availability, target group, size, "
                    "and budget constraints."
                ),
                (
                    "Verify requested size availability using "
                    "the Size/Fit Agent."
                ),
                (
                    "Build complete outfit recommendations using "
                    "verified top, bottom, and footwear products."
                ),
                (
                    "Generate grounded outfit explanations while "
                    "using deterministic validation and fallback "
                    "logic for safety."
                )
            ],

            "supported_examples": [
                "women casual cotton top size M",
                "men formal shirt under 5000",
                (
                    "I need a smart casual men's outfit "
                    "for a job interview under 15000."
                )
            ]
        }


    # -------------------------------------------------
    # Unsupported request
    # -------------------------------------------------

    def _build_unsupported_request(
        self,
        query
    ):

        return {
            "coordinator":
                self.name,

            "status":
                "unsupported_request",

            "intent":
                "out_of_domain",

            "query":
                query,

            "message":
                (
                    "FitStyle AI specializes in fashion "
                    "product discovery, size and availability "
                    "checking, and outfit recommendations. "
                    "Please ask about clothing, footwear, "
                    "bags, accessories, sizes, or outfits."
                ),

            "supported_examples": [
                "women casual cotton top size M",
                "men formal shirt under 5000",
                (
                    "I need a smart casual men's outfit "
                    "for a job interview under 15000."
                )
            ]
        }


    # -------------------------------------------------
    # No-match response
    # -------------------------------------------------

    def _build_no_match_response(
        self,
        query,
        intent,
        filters,
        message,
        suggestions=None,
        missing_roles=None
    ):

        # Return a safe response instead of inventing
        # products when the constraints cannot be met.
        response = {
            "coordinator":
                self.name,

            "status":
                "no_match",

            "intent":
                intent,

            "query":
                query,

            "filters":
                filters,

            "message":
                message,

            "suggestions":
                suggestions or []
        }

        if missing_roles:

            response[
                "missing_roles"
            ] = missing_roles

        return response



    # -------------------------------------------------
    # Query-understanding clarification
    # -------------------------------------------------

    def _build_query_clarification(
        self,
        query,
        understanding
    ):

        clarification = (
            understanding.get(
                "clarification",
                {}
            )
        )

        return {
            "coordinator":
                self.name,

            "status":
                "needs_clarification",

            "intent":
                understanding.get(
                    "intent"
                ),

            "query":
                query,

            "filters":
                understanding.get(
                    "filters",
                    {}
                ),

            "clarification_type":
                clarification.get(
                    "type"
                ),

            "question":
                clarification.get(
                    "question"
                ),

            "options":
                clarification.get(
                    "options",
                    []
                ),

            "reason":
                clarification.get(
                    "reason"
                )
        }


    # -------------------------------------------------
    # Product Search
    # -------------------------------------------------

    def _handle_product_search(
        self,
        query,
        understanding
    ):

        filters = understanding.get(
            "filters",
            {}
        )

        retrieval_query = understanding.get(
            "retrieval_query",
            query
        )

        exclusions = understanding.get(
            "exclusions",
            []
        )

        retrieval_response = (
            self.retrieval_agent.run({
                "query":
                    retrieval_query,

                "filters":
                    filters,

                "exclusions":
                    exclusions,

                "top_k":
                    10
            })
        )

        retrieved_products = (
            retrieval_response.get(
                "products",
                []
            )
        )


        # Keep only products with at least one
        # currently available variant.
        retrieved_products = [
            product
            for product in retrieved_products
            if product.get(
                "available_any"
            ) is True
        ]


        requested_size = filters.get(
            "size"
        )

        size_fit_response = None
        final_products = retrieved_products


        # Verify size when the user explicitly
        # requests one.
        if requested_size:

            size_fit_response = (
                self.size_fit_agent.run({
                    "products":
                        retrieved_products,

                    "requested_size":
                        requested_size
                })
            )

            final_products = (
                self._merge_size_results(
                    retrieved_products,
                    size_fit_response.get(
                        "products",
                        []
                    )
                )
            )

            # Do not return a requested size unless
            # that exact size is available.
            final_products = [
                product
                for product in final_products
                if product.get(
                    "size_available"
                ) is True
            ]


        # -----------------------------------------
        # No-match handling
        # -----------------------------------------

        if not final_products:

            return (
                self._build_no_match_response(

                    query=query,

                    intent="product_search",

                    filters=filters,

                    message=(
                        "No available fashion products matched "
                        "all of your requested constraints."
                    ),

                    suggestions=[
                        (
                            "Try increasing your budget or "
                            "removing one preference."
                        ),
                        (
                            "Try another size, color, material, "
                            "style, or product category."
                        )
                    ]
                )
            )


        agents_used = [
            "Query Understanding Agent",
            "Product Retrieval Agent"
        ]

        if requested_size:

            agents_used.append(
                "Size/Fit Agent"
            )


        return {
            "coordinator":
                self.name,

            "status":
                "success",

            "intent":
                understanding.get(
                    "intent"
                ),

            "query":
                query,

            "retrieval_query":
                retrieval_query,

            "filters":
                filters,

            "exclusions":
                exclusions,

            "agents_used":
                agents_used,

            "retrieval_method":
                retrieval_response.get(
                    "retrieval_method"
                ),

            "result_count":
                len(final_products),

            "products":
                final_products,

            "size_fit":
                size_fit_response
        }


    # -------------------------------------------------
    # Outfit clarification
    # -------------------------------------------------

    def _needs_outfit_target_group(
        self,
        filters
    ):

        target_group = filters.get(
            "target_group"
        )

        return not target_group


    def _build_target_group_clarification(
        self,
        query,
        understanding
    ):

        return {
            "coordinator":
                self.name,

            "status":
                "needs_clarification",

            "intent":
                "outfit_recommendation",

            "query":
                query,

            "filters":
                understanding.get(
                    "filters",
                    {}
                ),

            "clarification_type":
                "target_group",

            "question":
                (
                    "Who is this outfit for: "
                    "women, men, or teen?"
                ),

            "options": [
                "women",
                "men",
                "teen"
            ],

            "reason":
                (
                    "FitStyle AI does not infer "
                    "the target group when it is "
                    "not explicitly provided."
                )
        }


    # -------------------------------------------------
    # Outfit hard filters
    # -------------------------------------------------

    def _build_outfit_filters(
        self,
        original_filters,
        category
    ):

        outfit_filters = {
            "category": category
        }


        for key in [
            "target_group",
            "material"
        ]:

            value = original_filters.get(
                key
            )

            if value is not None:

                outfit_filters[
                    key
                ] = value


        budget = original_filters.get(
            "max_price"
        )

        if budget is not None:

            outfit_filters[
                "max_price"
            ] = budget


        return outfit_filters


    # -------------------------------------------------
    # Outfit role query
    # -------------------------------------------------

    def _build_outfit_query(
        self,
        original_query,
        role
    ):

        role_terms = {
            "top":
                "top shirt",

            "bottom":
                "pants trousers",

            "shoes":
                "shoes footwear"
        }

        return (
            f"{original_query} "
            f"{role_terms.get(role, role)}"
        )


    # -------------------------------------------------
    # Outfit Recommendation
    # -------------------------------------------------

    def _handle_outfit_recommendation(
        self,
        query,
        understanding
    ):

        filters = understanding.get(
            "filters",
            {}
        )

        retrieval_query = understanding.get(
            "retrieval_query",
            query
        )

        exclusions = understanding.get(
            "exclusions",
            []
        )


        budget = filters.get(
            "max_price"
        )

        occasion = filters.get(
            "occasion"
        )

        style = filters.get(
            "style"
        )


        preferred_colors = filters.get(
            "preferred_colors",
            []
        )

        if (
            not preferred_colors
            and filters.get("color")
        ):

            preferred_colors = [
                filters["color"]
            ]


        requested_sizes = filters.get(
            "sizes",
            {}
        )


        outfit_roles = {
            "top":
                "tops",

            "bottom":
                "bottoms",

            "shoes":
                "footwear"
        }


        candidate_groups = {}
        retrieval_details = {}


        # -----------------------------------------
        # Retrieve each outfit role
        # -----------------------------------------

        for role, category in (
            outfit_roles.items()
        ):

            role_query = (
                self._build_outfit_query(
                    retrieval_query,
                    role
                )
            )


            role_filters = (
                self._build_outfit_filters(
                    filters,
                    category
                )
            )


            role_size = (
                requested_sizes.get(
                    role
                )
            )

            if role_size:

                role_filters[
                    "size"
                ] = role_size


            retrieval_response = (
                self.retrieval_agent.run({
                    "query":
                        role_query,

                    "filters":
                        role_filters,

                    "exclusions":
                        exclusions,

                    "top_k":
                        20
                })
            )


            retrieved_products = (
                retrieval_response.get(
                    "products",
                    []
                )
            )


            retrieved_products = [
                product
                for product in retrieved_products
                if product.get(
                    "available_any"
                ) is True
            ]


            final_role_products = (
                retrieved_products
            )


            if role_size:

                size_fit_response = (
                    self.size_fit_agent.run({
                        "products":
                            retrieved_products,

                        "requested_size":
                            role_size
                    })
                )


                merged_products = (
                    self._merge_size_results(
                        retrieved_products,
                        size_fit_response.get(
                            "products",
                            []
                        )
                    )
                )


                final_role_products = [
                    product
                    for product in merged_products
                    if product.get(
                        "size_available"
                    ) is True
                ]


            candidate_groups[
                role
            ] = final_role_products


            retrieval_details[
                role
            ] = {
                "query":
                    role_query,

                "filters":
                    role_filters,

                "requested_size":
                    role_size,

                "retrieved_count":
                    len(
                        retrieved_products
                    ),

                "verified_count":
                    len(
                        final_role_products
                    ),

                "size_verified":
                    (
                        role_size is not None
                    )
            }


        # -----------------------------------------
        # Stop if one required role has no products
        # -----------------------------------------

        missing_roles = [
            role
            for role in outfit_roles
            if not candidate_groups.get(
                role
            )
        ]


        if missing_roles:

            readable_roles = ", ".join(
                missing_roles
            )

            return (
                self._build_no_match_response(

                    query=query,

                    intent="outfit_recommendation",

                    filters=filters,

                    message=(
                        "FitStyle AI could not build a complete "
                        "outfit because no valid products were "
                        f"found for: {readable_roles}."
                    ),

                    suggestions=[
                        (
                            "Try increasing the budget or "
                            "removing one preference."
                        ),
                        (
                            "Try another requested size, color, "
                            "material, or style."
                        )
                    ],

                    missing_roles=missing_roles
                )
            )


        # -----------------------------------------
        # Outfit Recommendation Agent
        # -----------------------------------------

        outfit_response = (
            self.outfit_agent.run({
                "candidate_groups":
                    candidate_groups,

                "budget":
                    budget,

                "style":
                    style,

                "occasion":
                    occasion,

                "preferred_colors":
                    preferred_colors,

                "requested_sizes":
                    requested_sizes
            })
        )


        selected_products = (
            outfit_response.get(
                "selected_products",
                []
            )
        )

        item_count = (
            outfit_response.get(
                "item_count",
                len(selected_products)
            )
        )

        within_budget = (
            outfit_response.get(
                "within_budget"
            )
        )


        # -----------------------------------------
        # Protect the complete-outfit constraint
        # -----------------------------------------

        if (
            item_count < 3
            or (
                budget is not None
                and within_budget is not True
            )
        ):

            return (
                self._build_no_match_response(

                    query=query,

                    intent="outfit_recommendation",

                    filters=filters,

                    message=(
                        "FitStyle AI found relevant products, "
                        "but could not create a complete outfit "
                        "that satisfies all required constraints."
                    ),

                    suggestions=[
                        (
                            "Try increasing the total outfit "
                            "budget."
                        ),
                        (
                            "Try relaxing one size, color, "
                            "material, or style preference."
                        )
                    ]
                )
            )


        agents_used = [
            "Query Understanding Agent",
            "Product Retrieval Agent"
        ]


        if requested_sizes:

            agents_used.append(
                "Size/Fit Agent"
            )


        agents_used.append(
            "Outfit Recommendation "
            "& Explanation Agent"
        )


        return {
            "coordinator":
                self.name,

            "status":
                "success",

            "intent":
                "outfit_recommendation",

            "query":
                query,

            "retrieval_query":
                retrieval_query,

            "filters":
                filters,

            "exclusions":
                exclusions,

            "agents_used":
                agents_used,

            "retrieval_method":
                (
                    "BM25 + Qdrant Semantic + "
                    "Equal RRF + SQL Server Hard Filters"
                ),

            "preferred_colors":
                preferred_colors,

            "requested_sizes":
                requested_sizes,

            "retrieval_details":
                retrieval_details,

            "candidate_groups":
                candidate_groups,

            "ranked_groups":
                outfit_response.get(
                    "ranked_groups",
                    {}
                ),

            "selected_products":
                selected_products,

            "item_count":
                item_count,

            "total_price":
                outfit_response.get(
                    "total_price"
                ),

            "budget":
                budget,

            "within_budget":
                within_budget,

            "occasion":
                occasion,

            "style":
                style,

            "combination_score":
                outfit_response.get(
                    "combination_score"
                ),

            "explanation":
                outfit_response.get(
                    "explanation",
                    ""
                ),

            "explanation_source":
                outfit_response.get(
                    "explanation_source"
                ),

            "llm_explanation_valid":
                outfit_response.get(
                    "llm_explanation_valid"
                )
        }


    # -------------------------------------------------
    # Main interface
    # -------------------------------------------------

    def run(
        self,
        input_data
    ):

        if not isinstance(
            input_data,
            dict
        ):

            raise TypeError(
                "Coordinator input must "
                "be a dictionary."
            )


        query = input_data.get(
            "query",
            ""
        )


        if not isinstance(
            query,
            str
        ):

            raise TypeError(
                "Query must be a string."
            )


        query = query.strip()


        if not query:

            raise ValueError(
                "Query cannot be empty."
            )


        understanding = (
            self.query_agent.run({
                "query":
                    query
            })
        )


        intent = understanding.get(
            "intent"
        )


        # -----------------------------------------
        # Answer questions about FitStyle AI itself
        # -----------------------------------------

        if intent == "system_info":

            return (
                self._build_system_info_response(
                    query
                )
            )


        # -----------------------------------------
        # Block out-of-domain requests
        # -----------------------------------------

        if (
            understanding.get("domain")
            == "out_of_domain"
            or intent == "out_of_domain"
        ):

            return (
                self._build_unsupported_request(
                    query
                )
            )


        # -----------------------------------------
        # Clarify explicit conflicting constraints
        # -----------------------------------------

        if (
            understanding.get("status")
            == "needs_clarification"
        ):

            return (
                self._build_query_clarification(
                    query,
                    understanding
                )
            )


        # -----------------------------------------
        # Route product search
        # -----------------------------------------

        if intent == "product_search":

            return (
                self._handle_product_search(
                    query,
                    understanding
                )
            )


        # -----------------------------------------
        # Route outfit recommendation
        # -----------------------------------------

        if intent == "outfit_recommendation":

            filters = understanding.get(
                "filters",
                {}
            )


            if self._needs_outfit_target_group(
                filters
            ):

                return (
                    self._build_target_group_clarification(
                        query,
                        understanding
                    )
                )


            return (
                self._handle_outfit_recommendation(
                    query,
                    understanding
                )
            )


        return {
            "coordinator":
                self.name,

            "status":
                "unsupported_intent",

            "query":
                query,

            "intent":
                intent,

            "message":
                (
                    "FitStyle AI could not determine "
                    "a supported fashion request."
                )
        }
