import json

from ollama import chat


# -------------------------------------------------
# Configuration
# -------------------------------------------------

MODEL_NAME = (
    "qwen2.5:3b-instruct"
)


# -------------------------------------------------
# LLM grounded explanation
# -------------------------------------------------

def generate_outfit_explanation(
    facts
):

    system_prompt = """
You are the explanation component of FitStyle AI.

Your job is ONLY to explain an outfit that has already
been selected and verified by the system.

STRICT GROUNDING RULES:

1. Use ONLY facts explicitly provided in the JSON input.

2. Never invent or infer:
   - product colors
   - product materials
   - sizes
   - prices
   - availability
   - target group / gender
   - fit quality
   - product properties

3. A user's preferred color is NOT the same as a verified
   product color.
   You may say:
   "The preferred colors considered were black and blue."
   You must NOT say a product is black or blue unless a
   verified product_color field explicitly says so.

4. Never change, shorten, rename, or replace selected products.
   Use the exact product_name values provided.

5. Currency is Sri Lankan Rupees.
   Always write prices using "Rs.".
   Never use "$", USD, dollars, or another currency.

6. A verified size means only that the requested product
   variant is available.
   Never claim guaranteed physical fit.

7. Do not infer that an interview is formal unless the
   provided requested_style explicitly says formal.
   Use the exact requested style and occasion.

8. If a fact is missing, simply do not mention it.

9. Mention ALL selected products using their exact names.

10. Explain briefly using only:
    - requested style
    - occasion
    - preferred colors
    - selected products
    - verified size availability
    - total price and budget

11. Return plain text only.
"""


    response = chat(

        model=MODEL_NAME,

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
# Grounding validator
# -------------------------------------------------

def validate_explanation(
    explanation,
    facts
):

    if not explanation:
        return False


    explanation_lower = (
        explanation.lower()
    )


    # ---------------------------------------------
    # 1. Every selected product must appear exactly
    # ---------------------------------------------

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


    # ---------------------------------------------
    # 2. Reject wrong currency
    # ---------------------------------------------

    forbidden_currency = [
        "$",
        "usd",
        "dollar",
        "dollars"
    ]


    for value in forbidden_currency:

        if value in explanation_lower:
            return False


    # ---------------------------------------------
    # 3. Require Rs. when prices/budget are mentioned
    # ---------------------------------------------

    if (
        facts.get("total_price") is not None
        or facts.get("budget") is not None
    ):

        if "rs." not in explanation_lower:
            return False


    # ---------------------------------------------
    # 4. Reject unsupported product-color claims
    # ---------------------------------------------

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


        # If the product has no verified color,
        # reject phrases that directly attach a
        # preferred color to the exact product name.
        if (
            product_name
            and not verified_color
        ):

            product_name_lower = (
                product_name.lower()
            )

            for color in preferred_colors:

                suspicious_phrases = [

                    (
                        product_name_lower
                        + " in "
                        + color
                    ),

                    (
                        product_name_lower
                        + " - "
                        + color
                    )
                ]


                for phrase in suspicious_phrases:

                    if phrase in explanation_lower:
                        return False


    # ---------------------------------------------
    # 5. Reject unsupported physical-fit claims
    # ---------------------------------------------

    forbidden_fit_claims = [
        "perfect fit",
        "fits perfectly",
        "will fit you",
        "guaranteed fit",
        "guaranteed to fit"
    ]


    for phrase in forbidden_fit_claims:

        if phrase in explanation_lower:
            return False


    return True


# -------------------------------------------------
# Deterministic safe fallback explanation
# -------------------------------------------------

def build_fallback_explanation(
    facts
):

    parts = []


    style = facts.get(
        "requested_style"
    )

    occasion = facts.get(
        "occasion"
    )

    preferred_colors = (
        facts.get(
            "preferred_colors"
        )
        or []
    )

    selected_products = (
        facts.get(
            "selected_products"
        )
        or []
    )

    total_price = facts.get(
        "total_price"
    )

    budget = facts.get(
        "budget"
    )

    within_budget = facts.get(
        "within_budget"
    )


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

            for product in selected_products

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

        requested_size = (
            product.get(
                "requested_size"
            )
        )

        size_available = (
            product.get(
                "size_available"
            )
        )

        role = (
            product.get(
                "role",
                "item"
            )
        )


        if (
            requested_size is not None
            and size_available is True
        ):

            size_notes.append(
                f"{role} size "
                f"{requested_size} is available"
            )


        elif (
            requested_size is not None
            and size_available is False
        ):

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


    if total_price is not None:

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
# Safe explanation wrapper
# -------------------------------------------------

def generate_safe_outfit_explanation(
    facts
):

    try:

        llm_explanation = (
            generate_outfit_explanation(
                facts
            )
        )


        is_valid = (
            validate_explanation(
                llm_explanation,
                facts
            )
        )


        if is_valid:

            return {
                "source":
                    "Qwen2.5 grounded explanation",

                "valid":
                    True,

                "llm_explanation":
                    llm_explanation,

                "final_explanation":
                    llm_explanation
            }


        fallback = (
            build_fallback_explanation(
                facts
            )
        )


        return {
            "source":
                "deterministic fallback",

            "valid":
                False,

            "llm_explanation":
                llm_explanation,

            "final_explanation":
                fallback
        }


    except Exception as error:

        fallback = (
            build_fallback_explanation(
                facts
            )
        )


        return {
            "source":
                "deterministic fallback",

            "valid":
                False,

            "llm_explanation":
                None,

            "llm_error":
                str(error),

            "final_explanation":
                fallback
        }


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    facts = {

        "currency":
            "Rs.",

        "requested_style":
            "smart casual",

        "occasion":
            "interview",

        "preferred_colors": [
            "black",
            "blue"
        ],

        "budget":
            15000,

        "selected_products": [

            {
                "role":
                    "top",

                "product_name":
                    "Tendenza V Neck Smocked Peplum Top",

                "price":
                    1295,

                "requested_size":
                    "M",

                "size_available":
                    True
            },

            {
                "role":
                    "bottom",

                "product_name":
                    "Vantage Ultra Slim Fit Formal Trouser - Black",

                "price":
                    4495,

                "requested_size":
                    "32",

                "size_available":
                    True
            },

            {
                "role":
                    "shoes",

                "product_name":
                    "Caliber Executive Textured Loafer Leather Shoe",

                "price":
                    7990,

                "requested_size":
                    None,

                "size_available":
                    None
            }
        ],

        "total_price":
            13780,

        "within_budget":
            True
    }


    result = (
        generate_safe_outfit_explanation(
            facts
        )
    )


    print(
        "\n--- LLM OUTFIT EXPLANATION TEST ---"
    )


    print(
        "\nGrounded Facts:"
    )

    print(
        json.dumps(
            facts,
            indent=2
        )
    )


    print(
        "\nLLM Candidate Explanation:"
    )

    print(
        result.get(
            "llm_explanation"
        )
    )


    print(
        "\nGrounding Valid:",
        result[
            "valid"
        ]
    )


    print(
        "Explanation Source:",
        result[
            "source"
        ]
    )


    print(
        "\nFinal Explanation:"
    )

    print(
        result[
            "final_explanation"
        ]
    )


    if result.get(
        "llm_error"
    ):

        print(
            "\nLLM Error:",
            result[
                "llm_error"
            ]
        )
