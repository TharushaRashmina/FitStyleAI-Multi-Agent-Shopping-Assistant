from pathlib import Path
from itertools import product as cartesian_product
import json
import math
import re
import sys

from ollama import chat
from sentence_transformers import SentenceTransformer


# -------------------------------------------------
# Project root / imports
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from database.sqlserver_repository import (
    SQLServerRepository
)


# -------------------------------------------------
# Paths
# -------------------------------------------------

OUTFIT_RULES_FILE = (
    BASE_DIR
    / "knowledge"
    / "outfit_rules.json"
)

SEMANTIC_MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)

LLM_MODEL_NAME = (
    "qwen2.5:3b-instruct"
)


# -------------------------------------------------
# Load rules
# -------------------------------------------------

with open(
    OUTFIT_RULES_FILE,
    "r",
    encoding="utf-8"
) as f:

    outfit_rules = json.load(f)


# -------------------------------------------------
# Outfit Recommendation Agent
# -------------------------------------------------

class OutfitRecommendationAgent:

    def __init__(self):

        self.name = (
            "Outfit Recommendation "
            "& Explanation Agent"
        )

        self.rules = outfit_rules

        self.weights = (
            self.rules.get(
                "ranking_weights",
                {}
            )
        )

        self.repository = (
            SQLServerRepository()
        )

        self._product_cache = {}
        self._variant_cache = {}

        self.semantic_model = (
            SentenceTransformer(
                SEMANTIC_MODEL_NAME,
                local_files_only=True
            )
        )


    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _safe_text(self, value):

        if value is None:
            return ""

        if isinstance(value, float):

            if math.isnan(value):
                return ""

        return str(value).strip()


    def _normalize(self, value):

        return (
            self._safe_text(value)
            .lower()
            .strip()
        )


    def _contains_phrase(
        self,
        text,
        phrase
    ):

        text = self._normalize(text)
        phrase = self._normalize(phrase)

        if not text or not phrase:
            return False

        pattern = (
            r"\b"
            + re.escape(phrase)
            + r"\b"
        )

        return (
            re.search(
                pattern,
                text
            )
            is not None
        )


    def _get_price(self, product):

        try:

            return float(
                product.get(
                    "base_price",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return 0.0


    # -------------------------------------------------
    # SQL Server product / variant access
    # -------------------------------------------------

    def _get_product_row(
        self,
        product
    ):

        product_id = str(
            product.get(
                "product_id",
                ""
            )
        ).strip()

        if not product_id:
            return None

        if product_id in self._product_cache:

            return self._product_cache[
                product_id
            ]

        row = (
            self.repository
            .get_product_by_id(
                product_id
            )
        )

        if row is not None:

            self._product_cache[
                product_id
            ] = row

        return row


    def _get_variants(
        self,
        product_id
    ):

        product_id = str(
            product_id
        ).strip()

        if not product_id:
            return []

        if product_id in self._variant_cache:

            return self._variant_cache[
                product_id
            ]

        variants = (
            self.repository
            .get_variants_by_product(
                product_id
            )
        )

        self._variant_cache[
            product_id
        ] = variants

        return variants


    # -------------------------------------------------
    # Build product text
    # -------------------------------------------------

    def _build_product_text(
        self,
        product
    ):

        row = self._get_product_row(
            product
        )

        if row is None:

            return " ".join([
                self._safe_text(
                    product.get(
                        "product_name",
                        ""
                    )
                ),
                self._safe_text(
                    product.get(
                        "category",
                        ""
                    )
                ),
                self._safe_text(
                    product.get(
                        "style",
                        ""
                    )
                )
            ])

        fields = [

            row.get(
                "product_name",
                ""
            ),

            row.get(
                "category",
                ""
            ),

            row.get(
                "sub_category",
                ""
            ),

            row.get(
                "target_group",
                ""
            ),

            row.get(
                "material",
                ""
            ),

            row.get(
                "fit_type",
                ""
            ),

            row.get(
                "pattern",
                ""
            ),

            row.get(
                "style",
                ""
            ),

            row.get(
                "occasion",
                ""
            ),

            row.get(
                "color",
                ""
            ),

            row.get(
                "product_type_raw",
                ""
            ),

            row.get(
                "tags",
                ""
            ),

            row.get(
                "description",
                ""
            )
        ]

        clean_fields = []

        for value in fields:

            text = self._safe_text(
                value
            )

            if text:

                clean_fields.append(
                    text
                )

        return " ".join(
            clean_fields
        )


    # -------------------------------------------------
    # Product occasion / color
    # -------------------------------------------------

    def _get_occasion_text(
        self,
        product
    ):

        row = self._get_product_row(
            product
        )

        if row is None:

            return self._normalize(
                product.get(
                    "occasion",
                    ""
                )
            )

        return self._normalize(
            row.get(
                "occasion",
                ""
            )
        )


    def _get_color(
        self,
        product
    ):

        row = self._get_product_row(
            product
        )

        if row is None:

            return self._normalize(
                product.get(
                    "color",
                    ""
                )
            )

        return self._normalize(
            row.get(
                "color",
                ""
            )
        )


    # -------------------------------------------------
    # Availability
    # -------------------------------------------------

    def _is_available_value(
        self,
        value
    ):

        if isinstance(
            value,
            bool
        ):

            return value

        if value is None:
            return False

        return (
            self._normalize(value)
            in {
                "true",
                "1",
                "yes"
            }
        )


    def _has_available_variant(
        self,
        product_id
    ):

        variants = (
            self._get_variants(
                product_id
            )
        )

        for variant in variants:

            if self._is_available_value(
                variant.get(
                    "available",
                    False
                )
            ):

                return True

        return False


    # -------------------------------------------------
    # Size score
    # -------------------------------------------------

    def _size_score(
        self,
        product_id,
        requested_size=None
    ):

        if not requested_size:
            return 1.0

        requested_size = (
            str(requested_size)
            .strip()
            .upper()
        )

        variants = (
            self._get_variants(
                product_id
            )
        )

        for variant in variants:

            variant_size = (
                self._safe_text(
                    variant.get(
                        "size",
                        ""
                    )
                )
                .upper()
            )

            available = (
                self._is_available_value(
                    variant.get(
                        "available",
                        False
                    )
                )
            )

            if (
                variant_size
                == requested_size
                and available
            ):

                return 1.0

        return 0.0


    # -------------------------------------------------
    # Occasion score
    # -------------------------------------------------

    def _occasion_score(
        self,
        product,
        occasion
    ):

        if not occasion:
            return 1.0

        occasion_key = (
            self._normalize(
                occasion
            )
            .replace(
                " ",
                "_"
            )
        )

        rule = (
            self.rules
            .get(
                "occasion_rules",
                {}
            )
            .get(
                occasion_key,
                {}
            )
        )

        if not rule:
            return 0.5

        product_text = (
            self._build_product_text(
                product
            )
        )

        product_occasion = (
            self._get_occasion_text(
                product
            )
        )

        if self._contains_phrase(
            product_occasion,
            occasion
        ):

            return 1.0

        for avoid_style in rule.get(
            "avoid_styles",
            []
        ):

            if self._contains_phrase(
                product_text,
                avoid_style
            ):

                return 0.0

        for preferred_style in (
            rule.get(
                "preferred_styles",
                []
            )
        ):

            if self._contains_phrase(
                product_text,
                preferred_style
            ):

                return 0.85

        return 0.20


    # -------------------------------------------------
    # Style score
    # -------------------------------------------------

    def _style_score(
        self,
        product,
        requested_style,
        occasion
    ):

        product_text = (
            self._build_product_text(
                product
            )
        )

        if requested_style:

            if self._contains_phrase(
                product_text,
                requested_style
            ):

                return 1.0

        occasion_key = (
            self._normalize(
                occasion
            )
            .replace(
                " ",
                "_"
            )
            if occasion
            else ""
        )

        rule = (
            self.rules
            .get(
                "occasion_rules",
                {}
            )
            .get(
                occasion_key,
                {}
            )
        )

        preferred_styles = (
            rule.get(
                "preferred_styles",
                []
            )
        )

        for style in preferred_styles:

            if self._contains_phrase(
                product_text,
                style
            ):

                return 0.85

        return 0.15


    # -------------------------------------------------
    # Semantic score
    # -------------------------------------------------

    def _semantic_scores(
        self,
        role,
        candidate_products,
        style,
        occasion
    ):

        preference_parts = []

        if style:
            preference_parts.append(
                style
            )

        if occasion:
            preference_parts.append(
                occasion
            )

        preference_parts.append(
            role
        )

        preference_text = " ".join(
            preference_parts
        )

        candidate_texts = [
            self._build_product_text(
                product
            )
            for product
            in candidate_products
        ]

        query_embedding = (
            self.semantic_model.encode(
                [preference_text],
                normalize_embeddings=True
            )[0]
        )

        product_embeddings = (
            self.semantic_model.encode(
                candidate_texts,
                normalize_embeddings=True
            )
        )

        return (
            product_embeddings
            @ query_embedding
        )


    # -------------------------------------------------
    # Rerank one candidate group
    # -------------------------------------------------

    def _rerank_group(
        self,
        role,
        candidate_products,
        style=None,
        occasion=None,
        requested_size=None
    ):

        if not candidate_products:
            return []

        semantic_scores = (
            self._semantic_scores(
                role,
                candidate_products,
                style,
                occasion
            )
        )

        reranked = []

        for index, product in enumerate(
            candidate_products
        ):

            product_id = (
                product.get(
                    "product_id"
                )
            )

            occasion_score = (
                self._occasion_score(
                    product,
                    occasion
                )
            )

            style_score = (
                self._style_score(
                    product,
                    style,
                    occasion
                )
            )

            size_score = (
                self._size_score(
                    product_id,
                    requested_size
                )
            )

            availability_score = (
                1.0
                if self._has_available_variant(
                    product_id
                )
                else 0.0
            )

            rule_score = (

                self.weights.get(
                    "occasion_match",
                    0.30
                )
                * occasion_score

                +

                self.weights.get(
                    "style_match",
                    0.20
                )
                * style_score

                +

                self.weights.get(
                    "size_available",
                    0.15
                )
                * size_score

                +

                self.weights.get(
                    "availability",
                    0.05
                )
                * availability_score
            )

            scored_product = {

                **product,

                "outfit_role":
                    role,

                "retrieval_rank":
                    index + 1,

                "occasion_match_score":
                    occasion_score,

                "style_match_score":
                    style_score,

                "size_available_score":
                    size_score,

                "availability_score":
                    availability_score,

                "semantic_match_score":
                    float(
                        semantic_scores[
                            index
                        ]
                    ),

                "outfit_score":
                    float(
                        rule_score
                    )
            }

            reranked.append(
                scored_product
            )

        reranked.sort(

            key=lambda item: (

                item[
                    "outfit_score"
                ],

                item[
                    "semantic_match_score"
                ],

                -item[
                    "retrieval_rank"
                ]
            ),

            reverse=True
        )

        return reranked


    # -------------------------------------------------
    # Color compatibility
    # -------------------------------------------------

    def _pair_color_score(
        self,
        color_a,
        color_b
    ):

        color_a = self._normalize(
            color_a
        )

        color_b = self._normalize(
            color_b
        )

        if (
            not color_a
            or not color_b
        ):

            return 0.5

        if color_a == color_b:
            return 1.0

        compatibility = (
            self.rules.get(
                "color_compatibility",
                {}
            )
        )

        if color_b in compatibility.get(
            color_a,
            []
        ):

            return 1.0

        if color_a in compatibility.get(
            color_b,
            []
        ):

            return 1.0

        return 0.0


    def _combination_color_score(
        self,
        products
    ):

        colors = [
            self._get_color(
                product
            )
            for product
            in products
        ]

        pair_scores = []

        for i in range(
            len(colors)
        ):

            for j in range(
                i + 1,
                len(colors)
            ):

                pair_scores.append(
                    self._pair_color_score(
                        colors[i],
                        colors[j]
                    )
                )

        if not pair_scores:
            return 0.5

        return (
            sum(pair_scores)
            / len(pair_scores)
        )


    # -------------------------------------------------
    # User preferred-color score
    # -------------------------------------------------

    def _preferred_color_score(
        self,
        products,
        preferred_colors
    ):

        if not preferred_colors:
            return 1.0

        preferred_colors = [
            self._normalize(
                color
            )
            for color
            in preferred_colors
        ]

        matches = 0

        for product in products:

            product_color = (
                self._get_color(
                    product
                )
            )

            if (
                product_color
                in preferred_colors
            ):

                matches += 1

        if not products:
            return 0.0

        return (
            matches
            / len(products)
        )


    # -------------------------------------------------
    # Select best complete outfit
    # -------------------------------------------------

    def _select_best_combination(
        self,
        ranked_groups,
        budget=None,
        preferred_colors=None
    ):

        preferred_colors = (
            preferred_colors or []
        )

        usable_groups = {
            role: products
            for role, products
            in ranked_groups.items()
            if products
        }

        if not usable_groups:
            return [], 0.0

        candidate_lists = list(
            usable_groups.values()
        )

        best_products = None

        best_score = float(
            "-inf"
        )

        best_semantic = float(
            "-inf"
        )

        for combination in (
            cartesian_product(
                *candidate_lists
            )
        ):

            selected = list(
                combination
            )

            total_price = sum(
                self._get_price(
                    item
                )
                for item
                in selected
            )

            if (
                budget is not None
                and total_price > budget
            ):

                continue

            average_item_score = (
                sum(
                    item[
                        "outfit_score"
                    ]
                    for item
                    in selected
                )
                / len(selected)
            )

            compatibility_score = (
                self._combination_color_score(
                    selected
                )
            )

            preference_score = (
                self._preferred_color_score(
                    selected,
                    preferred_colors
                )
            )

            if preferred_colors:

                color_score = (
                    0.5
                    * compatibility_score

                    +

                    0.5
                    * preference_score
                )

            else:

                color_score = (
                    compatibility_score
                )

            if budget is None:
                budget_score = 1.0

            elif total_price <= budget:
                budget_score = 1.0

            else:
                budget_score = 0.0

            combination_score = (

                average_item_score

                +

                self.weights.get(
                    "budget_match",
                    0.20
                )
                * budget_score

                +

                self.weights.get(
                    "color_compatibility",
                    0.10
                )
                * color_score
            )

            average_semantic = (
                sum(
                    item[
                        "semantic_match_score"
                    ]
                    for item
                    in selected
                )
                / len(selected)
            )

            if (
                combination_score
                > best_score
            ):

                best_score = (
                    combination_score
                )

                best_semantic = (
                    average_semantic
                )

                best_products = (
                    selected
                )

            elif (
                combination_score
                == best_score
                and average_semantic
                > best_semantic
            ):

                best_semantic = (
                    average_semantic
                )

                best_products = (
                    selected
                )

        return (
            best_products or [],
            best_score
            if best_products
            else 0.0
        )


    # -------------------------------------------------
    # Deterministic fallback explanation
    # -------------------------------------------------

    def _build_deterministic_explanation(
        self,
        selected_products,
        style,
        occasion,
        preferred_colors,
        budget,
        total_price,
        within_budget,
        requested_sizes
    ):

        parts = []

        if style and occasion:

            parts.append(
                f"The selected outfit was evaluated "
                f"for a {style} style and the "
                f"{occasion} occasion."
            )

        elif style:

            parts.append(
                f"The requested style was {style}."
            )

        elif occasion:

            parts.append(
                f"The outfit was evaluated for the "
                f"{occasion} occasion."
            )

        if preferred_colors:

            parts.append(
                "The preferred colors considered were "
                + ", ".join(
                    preferred_colors
                )
                + "."
            )

        if selected_products:

            names = [
                product.get(
                    "product_name",
                    ""
                )
                for product
                in selected_products
                if product.get(
                    "product_name"
                )
            ]

            if names:

                parts.append(
                    "Selected pieces: "
                    + ", ".join(
                        names
                    )
                    + "."
                )

        size_notes = []

        for product in selected_products:

            role = product.get(
                "outfit_role",
                "item"
            )

            requested_size = (
                requested_sizes.get(
                    role
                )
            )

            if requested_size is None:
                continue

            size_available = (
                self._size_score(
                    product.get(
                        "product_id"
                    ),
                    requested_size
                )
                == 1.0
            )

            if size_available:

                size_notes.append(
                    f"{role} size "
                    f"{requested_size} is available"
                )

            else:

                size_notes.append(
                    f"{role} size "
                    f"{requested_size} is not available"
                )

        if size_notes:

            parts.append(
                "Size availability: "
                + "; ".join(
                    size_notes
                )
                + "."
            )

        parts.append(
            f"The total price is "
            f"Rs. {float(total_price):.2f}."
        )

        if (
            budget is not None
            and within_budget is True
        ):

            parts.append(
                f"This is within the "
                f"Rs. {float(budget):.2f} budget."
            )

        elif (
            budget is not None
            and within_budget is False
        ):

            parts.append(
                f"This exceeds the "
                f"Rs. {float(budget):.2f} budget."
            )

        parts.append(
            "Verified size availability only confirms "
            "that the requested variant is available; "
            "it does not guarantee physical fit."
        )

        return " ".join(
            parts
        )


    # -------------------------------------------------
    # Build grounded facts for LLM
    # -------------------------------------------------

    def _build_explanation_facts(
        self,
        selected_products,
        style,
        occasion,
        preferred_colors,
        budget,
        total_price,
        within_budget,
        requested_sizes
    ):

        fact_products = []

        for product in selected_products:

            role = product.get(
                "outfit_role"
            )

            requested_size = (
                requested_sizes.get(
                    role
                )
            )

            size_available = None

            if requested_size is not None:

                size_available = (
                    self._size_score(
                        product.get(
                            "product_id"
                        ),
                        requested_size
                    )
                    == 1.0
                )

            item = {
                "role":
                    role,

                "product_name":
                    product.get(
                        "product_name",
                        ""
                    ),

                "price":
                    self._get_price(
                        product
                    ),

                "requested_size":
                    requested_size,

                "size_available":
                    size_available
            }

            verified_color = (
                self._get_color(
                    product
                )
            )

            if verified_color:

                item[
                    "product_color"
                ] = verified_color

            fact_products.append(
                item
            )

        return {
            "currency":
                "Rs.",

            "requested_style":
                style,

            "occasion":
                occasion,

            "preferred_colors":
                preferred_colors,

            "budget":
                budget,

            "selected_products":
                fact_products,

            "total_price":
                total_price,

            "within_budget":
                within_budget
        }


    # -------------------------------------------------
    # LLM explanation
    # -------------------------------------------------

    def _generate_llm_explanation(
        self,
        facts
    ):

        system_prompt = """
You are the explanation component of FitStyle AI.

Your job is ONLY to explain an outfit that has already
been selected and verified by the system.

STRICT GROUNDING RULES:

1. Use ONLY facts explicitly provided in the JSON input.

2. Never invent or infer product colors, materials, sizes,
   prices, availability, target group, fit quality, or
   other product properties.

3. A user's preferred color is NOT a verified product color.
   Mention it only as a preference unless product_color is
   explicitly provided for that exact product.

4. Mention ALL selected products using their exact
   product_name values.

5. Never shorten, rename, replace, or omit a selected product.

6. Currency is Sri Lankan Rupees.
   Always use "Rs." and never use "$", USD, or dollars.

7. A verified size means only that the requested variant
   is available. Never guarantee physical fit.

8. Use the exact requested style and occasion provided.
   Do not infer a different dress code.

9. If a fact is missing, do not guess it.

10. Return one short natural plain-text explanation only.
"""

        response = chat(

            model=LLM_MODEL_NAME,

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": json.dumps(
                        facts,
                        indent=2
                    )
                }
            ],

            options={
                "temperature": 0
            }
        )

        return (
            response.message.content
            .strip()
        )


    # -------------------------------------------------
    # Validate LLM explanation
    # -------------------------------------------------

    def _validate_llm_explanation(
        self,
        explanation,
        facts
    ):

        if not explanation:
            return False

        explanation_lower = (
            explanation.lower()
        )

        # Every selected product name must appear exactly.
        for product in facts.get(
            "selected_products",
            []
        ):

            product_name = (
                product.get(
                    "product_name",
                    ""
                )
            )

            if (
                product_name
                and product_name
                not in explanation
            ):

                return False

        # Wrong currency is not allowed.
        for value in [
            "$",
            "usd",
            "dollar",
            "dollars"
        ]:

            if value in explanation_lower:
                return False

        if (
            facts.get("total_price") is not None
            or facts.get("budget") is not None
        ):

            if "rs." not in explanation_lower:
                return False

        # Unsupported product-color claims.
        preferred_colors = [
            str(color).strip().lower()
            for color in facts.get(
                "preferred_colors",
                []
            )
            if str(color).strip()
        ]

        for product in facts.get(
            "selected_products",
            []
        ):

            product_name = (
                product.get(
                    "product_name",
                    ""
                )
            )

            verified_color = (
                product.get(
                    "product_color"
                )
            )

            if (
                product_name
                and not verified_color
            ):

                product_name_lower = (
                    product_name.lower()
                )

                for color in preferred_colors:

                    suspicious_phrase = (
                        product_name_lower
                        + " in "
                        + color
                    )

                    if (
                        suspicious_phrase
                        in explanation_lower
                    ):

                        return False

        # No physical-fit guarantee.
        for phrase in [
            "perfect fit",
            "fits perfectly",
            "will fit you",
            "guaranteed fit",
            "guaranteed to fit"
        ]:

            if phrase in explanation_lower:
                return False

        return True


    # -------------------------------------------------
    # Safe explanation wrapper
    # -------------------------------------------------

    def _generate_safe_explanation(
        self,
        selected_products,
        style,
        occasion,
        preferred_colors,
        budget,
        total_price,
        within_budget,
        requested_sizes
    ):

        deterministic = (
            self._build_deterministic_explanation(
                selected_products=
                    selected_products,

                style=
                    style,

                occasion=
                    occasion,

                preferred_colors=
                    preferred_colors,

                budget=
                    budget,

                total_price=
                    total_price,

                within_budget=
                    within_budget,

                requested_sizes=
                    requested_sizes
            )
        )

        facts = (
            self._build_explanation_facts(
                selected_products=
                    selected_products,

                style=
                    style,

                occasion=
                    occasion,

                preferred_colors=
                    preferred_colors,

                budget=
                    budget,

                total_price=
                    total_price,

                within_budget=
                    within_budget,

                requested_sizes=
                    requested_sizes
            )
        )

        try:

            llm_explanation = (
                self._generate_llm_explanation(
                    facts
                )
            )

            valid = (
                self._validate_llm_explanation(
                    llm_explanation,
                    facts
                )
            )

            if valid:

                return {
                    "explanation":
                        llm_explanation,

                    "explanation_source":
                        "Qwen2.5 grounded explanation",

                    "llm_explanation_valid":
                        True,

                    "llm_candidate_explanation":
                        llm_explanation
                }

            return {
                "explanation":
                    deterministic,

                "explanation_source":
                    "deterministic fallback",

                "llm_explanation_valid":
                    False,

                "llm_candidate_explanation":
                    llm_explanation
            }

        except Exception as error:

            return {
                "explanation":
                    deterministic,

                "explanation_source":
                    "deterministic fallback",

                "llm_explanation_valid":
                    False,

                "llm_candidate_explanation":
                    None,

                "llm_explanation_error":
                    str(error)
            }


    # -------------------------------------------------
    # Recommend outfit
    # -------------------------------------------------

    def recommend(
        self,
        candidate_groups,
        budget=None,
        style=None,
        occasion=None,
        preferred_colors=None,
        requested_sizes=None
    ):

        preferred_colors = (
            preferred_colors or []
        )

        requested_sizes = (
            requested_sizes or {}
        )

        ranked_groups = {}

        for role, candidates in (
            candidate_groups.items()
        ):

            ranked_groups[
                role
            ] = self._rerank_group(

                role=role,

                candidate_products=
                    candidates,

                style=style,

                occasion=occasion,

                requested_size=
                    requested_sizes.get(
                        role
                    )
            )

        (
            selected_products,
            combination_score
        ) = (
            self._select_best_combination(

                ranked_groups=
                    ranked_groups,

                budget=
                    budget,

                preferred_colors=
                    preferred_colors
            )
        )

        total_price = sum(
            self._get_price(
                item
            )
            for item
            in selected_products
        )

        within_budget = None

        if budget is not None:

            within_budget = (
                bool(
                    selected_products
                )
                and total_price <= budget
            )

        explanation_result = (
            self._generate_safe_explanation(

                selected_products=
                    selected_products,

                style=
                    style,

                occasion=
                    occasion,

                preferred_colors=
                    preferred_colors,

                budget=
                    budget,

                total_price=
                    total_price,

                within_budget=
                    within_budget,

                requested_sizes=
                    requested_sizes
            )
        )

        response = {

            "agent":
                self.name,

            "status":
                "success",

            "data_source":
                "SQL Server",

            "style":
                style,

            "occasion":
                occasion,

            "preferred_colors":
                preferred_colors,

            "budget":
                budget,

            "ranked_groups":
                ranked_groups,

            "selected_products":
                selected_products,

            "item_count":
                len(
                    selected_products
                ),

            "total_price":
                total_price,

            "within_budget":
                within_budget,

            "combination_score":
                combination_score,

            "explanation":
                explanation_result[
                    "explanation"
                ],

            "explanation_source":
                explanation_result[
                    "explanation_source"
                ],

            "llm_explanation_valid":
                explanation_result[
                    "llm_explanation_valid"
                ]
        }

        if (
            explanation_result.get(
                "llm_candidate_explanation"
            )
            is not None
        ):

            response[
                "llm_candidate_explanation"
            ] = explanation_result[
                "llm_candidate_explanation"
            ]

        if explanation_result.get(
            "llm_explanation_error"
        ):

            response[
                "llm_explanation_error"
            ] = explanation_result[
                "llm_explanation_error"
            ]

        return response


    # -------------------------------------------------
    # Standard Agent Interface
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
                "Agent input must be "
                "a dictionary."
            )

        candidate_groups = (
            input_data.get(
                "candidate_groups",
                {}
            )
        )

        if not isinstance(
            candidate_groups,
            dict
        ):

            raise TypeError(
                "candidate_groups must "
                "be a dictionary."
            )

        return self.recommend(

            candidate_groups=
                candidate_groups,

            budget=input_data.get(
                "budget"
            ),

            style=input_data.get(
                "style"
            ),

            occasion=input_data.get(
                "occasion"
            ),

            preferred_colors=
                input_data.get(
                    "preferred_colors",
                    []
                ),

            requested_sizes=
                input_data.get(
                    "requested_sizes",
                    {}
                )
        )
