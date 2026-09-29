from pathlib import Path
import sys

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request
)

from fastapi.exceptions import (
    RequestValidationError
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from fastapi.responses import (
    JSONResponse
)

from pydantic import (
    BaseModel,
    Field
)


# -------------------------------------------------
# Add project root to Python path
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# -------------------------------------------------
# Project imports
# -------------------------------------------------

from api.auth_routes import (
    router as auth_router
)

from auth.dependencies import (
    get_authenticated_user
)

from orchestrator.coordinator import (
    Coordinator
)


# -------------------------------------------------
# Create FastAPI application
# -------------------------------------------------

app = FastAPI(
    title="FitStyle AI API",

    description=(
        "Backend API for the FitStyle AI "
        "multi-agent fashion recommendation system."
    ),

    version="1.0.0"
)


# -------------------------------------------------
# Authentication Routes
# -------------------------------------------------

app.include_router(
    auth_router
)


# -------------------------------------------------
# CORS Configuration
# -------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173"
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# -------------------------------------------------
# API Error Handlers
# -------------------------------------------------

@app.exception_handler(
    RequestValidationError
)
async def validation_error_handler(
    request: Request,
    error: RequestValidationError
):

    return JSONResponse(
        status_code=422,

        content={
            "status":
                "error",

            "error": {
                "type":
                    "validation_error",

                "message":
                    "The request data is invalid."
            }
        }
    )


@app.exception_handler(
    HTTPException
)
async def http_error_handler(
    request: Request,
    error: HTTPException
):

    return JSONResponse(
        status_code=error.status_code,

        content={
            "status":
                "error",

            "error": {
                "type":
                    "http_error",

                "message":
                    str(error.detail)
            }
        }
    )


# -------------------------------------------------
# Create Coordinator once
# -------------------------------------------------

coordinator = Coordinator()


# -------------------------------------------------
# Request Model
# -------------------------------------------------

class RecommendationRequest(
    BaseModel
):

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description=(
            "Natural-language fashion request "
            "or FitStyle AI help question"
        ),
        examples=[
            "women casual cotton top size M",
            "what is this AI system about"
        ]
    )


# -------------------------------------------------
# Clean one product for frontend
# -------------------------------------------------

def clean_product(
    product
):

    return {
        "product_id":
            product.get(
                "product_id"
            ),

        "product_name":
            product.get(
                "product_name"
            ),

        "category":
            product.get(
                "category"
            ),

        "sub_category":
            product.get(
                "sub_category"
            ),

        "target_group":
            product.get(
                "target_group"
            ),

        "material":
            product.get(
                "material"
            ),

        "style":
            product.get(
                "style"
            ),

        "occasion":
            product.get(
                "occasion"
            ),

        "color":
            product.get(
                "color"
            ),

        "price":
            product.get(
                "base_price"
            ),

        "available":
            product.get(
                "available_any"
            ),

        "image_url":
            product.get(
                "image_url"
            ),

        "product_url":
            product.get(
                "product_url"
            ),

        "outfit_role":
            product.get(
                "outfit_role"
            ),

        "requested_size":
            product.get(
                "requested_size"
            ),

        "size_available":
            product.get(
                "size_available"
            ),

        "available_sizes":
            product.get(
                "available_sizes",
                []
            )
    }


# -------------------------------------------------
# Build clean frontend response
# -------------------------------------------------

def clean_response(
    result
):

    status = result.get(
        "status"
    )

    intent = result.get(
        "intent"
    )


    # ---------------------------------------------
    # FitStyle AI system/help information
    # ---------------------------------------------

    if (
        status == "success"
        and intent == "system_info"
    ):

        return {
            "status":
                "success",

            "intent":
                "system_info",

            "query":
                result.get(
                    "query"
                ),

            "title":
                result.get(
                    "title",
                    "About FitStyle AI"
                ),

            "message":
                result.get(
                    "message"
                ),

            "capabilities":
                result.get(
                    "capabilities",
                    []
                ),

            "supported_examples":
                result.get(
                    "supported_examples",
                    []
                )
        }


    # ---------------------------------------------
    # Unsupported request
    # ---------------------------------------------

    if status == "unsupported_request":

        return {
            "status":
                status,

            "intent":
                intent,

            "query":
                result.get(
                    "query"
                ),

            "message":
                result.get(
                    "message"
                ),

            "supported_examples":
                result.get(
                    "supported_examples",
                    []
                )
        }


    # ---------------------------------------------
    # No-match response
    # ---------------------------------------------

    if status == "no_match":

        return {
            "status":
                status,

            "intent":
                intent,

            "query":
                result.get(
                    "query"
                ),

            "filters":
                result.get(
                    "filters",
                    {}
                ),

            "message":
                result.get(
                    "message"
                ),

            "suggestions":
                result.get(
                    "suggestions",
                    []
                ),

            "missing_roles":
                result.get(
                    "missing_roles",
                    []
                )
        }


    # ---------------------------------------------
    # Clarification response
    # ---------------------------------------------

    if status == "needs_clarification":

        return {
            "status":
                status,

            "intent":
                intent,

            "query":
                result.get(
                    "query"
                ),

            "filters":
                result.get(
                    "filters",
                    {}
                ),

            "clarification": {
                "type":
                    result.get(
                        "clarification_type"
                    ),

                "question":
                    result.get(
                        "question"
                    ),

                "options":
                    result.get(
                        "options",
                        []
                    ),

                "reason":
                    result.get(
                        "reason"
                    )
            }
        }


    # ---------------------------------------------
    # Product-search response
    # ---------------------------------------------

    if intent == "product_search":

        products = [
            clean_product(
                product
            )
            for product in result.get(
                "products",
                []
            )
        ]


        size_fit = (
            result.get(
                "size_fit"
            )
            or {}
        )


        return {
            "status":
                status,

            "intent":
                intent,

            "query":
                result.get(
                    "query"
                ),

            "filters":
                result.get(
                    "filters",
                    {}
                ),

            "result_count":
                len(products),

            "products":
                products,

            "fit_note":
                size_fit.get(
                    "fit_note"
                ),

            "system_info": {
                "agents_used":
                    result.get(
                        "agents_used",
                        []
                    ),

                "retrieval_method":
                    result.get(
                        "retrieval_method"
                    )
            }
        }


    # ---------------------------------------------
    # Outfit-recommendation response
    # ---------------------------------------------

    if intent == "outfit_recommendation":

        selected_products = [
            clean_product(
                product
            )
            for product in result.get(
                "selected_products",
                []
            )
        ]


        return {
            "status":
                status,

            "intent":
                intent,

            "query":
                result.get(
                    "query"
                ),

            "filters":
                result.get(
                    "filters",
                    {}
                ),

            "preferred_colors":
                result.get(
                    "preferred_colors",
                    []
                ),

            "requested_sizes":
                result.get(
                    "requested_sizes",
                    {}
                ),

            "selected_products":
                selected_products,

            "item_count":
                len(
                    selected_products
                ),

            "total_price":
                result.get(
                    "total_price"
                ),

            "budget":
                result.get(
                    "budget"
                ),

            "within_budget":
                result.get(
                    "within_budget"
                ),

            "explanation":
                result.get(
                    "explanation"
                ),

            "system_info": {
                "agents_used":
                    result.get(
                        "agents_used",
                        []
                    ),

                "retrieval_method":
                    result.get(
                        "retrieval_method"
                    ),

                "explanation_source":
                    result.get(
                        "explanation_source"
                    ),

                "llm_explanation_valid":
                    result.get(
                        "llm_explanation_valid"
                    )
            }
        }


    return result


# -------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------

@app.get(
    "/health"
)
def health_check():

    return {
        "status":
            "healthy",

        "service":
            "FitStyle AI API"
    }


# -------------------------------------------------
# Recommendation Endpoint
# -------------------------------------------------

@app.post(
    "/recommend"
)
def recommend(
    request: RecommendationRequest,

    current_user: dict = Depends(
        get_authenticated_user
    )
):

    query = (
        request.query
        .strip()
    )


    if not query:

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty."
        )


    try:

        result = coordinator.run({
            "query":
                query
        })

        return clean_response(
            result
        )


    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


    except HTTPException:
        raise


    except Exception:

        raise HTTPException(
            status_code=500,
            detail=(
                "An internal server error occurred."
            )
        )
