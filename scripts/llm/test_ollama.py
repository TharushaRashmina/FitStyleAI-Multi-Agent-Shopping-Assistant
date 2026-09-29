import json

from ollama import chat


# -------------------------------------------------
# Configuration
# -------------------------------------------------

MODEL_NAME = (
    "qwen2.5:3b-instruct"
)


# -------------------------------------------------
# JSON schema
# -------------------------------------------------

OUTPUT_SCHEMA = {

    "type": "object",

    "properties": {

        "intent": {
            "type": "string",
            "enum": [
                "product_search",
                "outfit_recommendation"
            ]
        },

        "category": {
            "type": [
                "string",
                "null"
            ]
        },

        "target_group": {
            "type": [
                "string",
                "null"
            ]
        },

        "material": {
            "type": [
                "string",
                "null"
            ]
        },

        "style": {
            "type": [
                "string",
                "null"
            ]
        },

        "occasion": {
            "type": [
                "string",
                "null"
            ]
        },

        "preferred_colors": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "max_price": {
            "type": [
                "number",
                "null"
            ]
        },

        "sizes": {
            "type": "object",
            "properties": {

                "top": {
                    "type": "string"
                },

                "bottom": {
                    "type": "string"
                },

                "shoes": {
                    "type": "string"
                }
            },

            "additionalProperties": False
        },

        "size": {
            "type": [
                "string",
                "null"
            ]
        }
    },

    "required": [
        "intent",
        "category",
        "target_group",
        "material",
        "style",
        "occasion",
        "preferred_colors",
        "max_price",
        "sizes",
        "size"
    ],

    "additionalProperties": False
}


# -------------------------------------------------
# Query Understanding Test
# -------------------------------------------------

def understand_query(
    query
):

    system_prompt = """
You are the Query Understanding component
of FitStyle AI.

Convert the user's fashion query into the
provided JSON schema.

Rules:

1. Use only these canonical categories when possible:
   tops, bottoms, dresses, footwear,
   innerwear, accessories, bags, ethnic_wear.

2. Separate gender/target group from category.
   Example:
   "women casual top"
   category = "tops"
   target_group = "women"

3. Extract styles such as:
   casual, formal, smart casual,
   business casual, party, activewear.

4. max_price must be a number only.

5. For size:
   - shirts/tops -> sizes.top
   - trousers/jeans/bottoms/waist -> sizes.bottom
   - shoes/heels -> sizes.shoes

6. For a simple single-product query,
   also copy the requested size into "size".

7. For outfit queries with multiple sizes,
   keep "size" as null and use "sizes".

8. preferred_colors must always be an array.

9. Do not invent missing information.
   Use null or an empty array/object.

10. Return only valid JSON matching the schema.
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
                "content": query
            }
        ],

        format=OUTPUT_SCHEMA,

        options={
            "temperature": 0
        }
    )


    content = (
        response.message.content
    )


    result = json.loads(
    content
    )


    # -------------------------------------------------
    # Deterministic post-processing
    # -------------------------------------------------

    if (
        result.get("intent")
        == "product_search"
        and not result.get("size")
    ):

        sizes = result.get(
            "sizes",
            {}
        )

        available_sizes = [
            value
            for value in sizes.values()
            if value
        ]

        if len(available_sizes) == 1:

            result["size"] = (
                available_sizes[0]
            )


    return result


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    query = (
        "women casual cotton top "
        "size M under 5000"
    )


    result = understand_query(
        query
    )


    print(
        "\n--- OLLAMA QUERY UNDERSTANDING TEST ---"
    )

    print(
        "Query:",
        query
    )

    print(
        "\nStructured Output:"
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )