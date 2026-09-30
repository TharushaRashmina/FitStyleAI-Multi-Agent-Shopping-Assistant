import json
import re

from ollama import chat


class QueryUnderstandingAgent:

    def __init__(self):

        self.name = "Query Understanding Agent"
        self.model_name = "qwen2.5:3b-instruct"

        self.category_aliases = {
            "tops": [
                "top", "tops", "shirt", "shirts",
                "t shirt", "t-shirt", "tshirt", "blouse"
            ],
            "dresses": ["dress", "dresses"],
            "bottoms": [
                "pants", "pant", "trousers", "trouser",
                "jeans", "jean", "skirts", "skirt",
                "shorts", "short"
            ],
            "footwear": [
                "shoe", "shoes", "heel", "heels",
                "sandal", "sandals", "footwear"
            ],
            "innerwear": [
                "innerwear", "bra", "brief", "underwear"
            ],
            "accessories": [
                "accessory", "accessories"
            ],
            "bags": [
                "bag", "bags", "handbag"
            ],
            "ethnic_wear": [
                "ethnic wear", "ethnic", "saree"
            ]
        }

        self.target_groups = {
            "men": [
                "men", "mens", "men's", "male"
            ],
            "women": [
                "women", "womens", "women's", "female"
            ],
            "teen": [
                "teen", "teens", "teenage",
                "teenager", "teenagers"
            ],
            "kids": [
                "kid", "kids", "child", "children"
            ]
        }

        self.materials = [
            "cotton", "linen", "denim", "polyester",
            "silk", "rayon", "viscose", "leather"
        ]

        self.styles = [
            "business casual", "smart casual",
            "formal", "casual", "party",
            "sport", "sports"
        ]

        self.occasions = [
            "job interview", "casual outing",
            "interview", "wedding", "office",
            "work", "party", "university",
            "date", "daily"
        ]

        self.colors = [
            "black", "white", "blue", "red",
            "green", "yellow", "pink", "purple",
            "brown", "grey", "gray", "beige",
            "navy", "orange", "maroon", "olive",
            "cream"
        ]

        # Clear non-fashion signals used by the
        # deterministic fallback. The list is
        # intentionally conservative.
        self.non_fashion_patterns = [
            r"\blaptop\b",
            r"\bcomputer\b",
            r"\bsmartphone\b",
            r"\bphone\b",
            r"\bmobile phone\b",
            r"\bweather\b",
            r"\btemperature\b",
            r"\bpython\b",
            r"\bjavascript\b",
            r"\bcode\b",
            r"\bcoding\b",
            r"\bprogramming\b",
            r"\brestaurant\b",
            r"\bhotel\b",
            r"\bflight\b",
            r"\bairline\b",
            r"\bcar\b",
            r"\bvehicle\b",
            r"\bmedicine\b",
            r"\bdoctor\b",
            r"\bstock market\b",
            r"\bstocks\b",
            r"\bcrypto\b",
            r"\brecipe\b",
            r"\bmovie\b",
            r"\bmusic\b",
            r"\bvideo game\b",
            r"\bcamera\b",
            r"\btelevision\b",
            r"\bheadphones\b",
            r"\bkeyboard\b",
            r"\bprinter\b"
        ]


        # Questions about FitStyle AI itself should not be
        # rejected as out-of-domain. These are handled as a
        # deterministic system-information intent.
        self.system_info_patterns = [
            # Direct questions about this AI / system
            r"\bwhat is (?:this )?(?:ai )?system(?: about)?\b",
            r"\bwhat is this ai(?: about)?\b",
            r"\bwhat(?:'s| is) this ai(?: about)?\b",
            r"\btell me about (?:this ai|this system|fitstyle ai)\b",

            # Direct questions about FitStyle AI
            r"\bwhat is fitstyle ai\b",
            r"\bwhat(?:'s| is) fitstyle ai\b",
            r"\bwhat does (?:this ai|this system|fitstyle ai) do\b",
            r"\bwhat can (?:you|this ai|this system|fitstyle ai) do\b",
            r"\bhow does (?:this ai|this system|fitstyle ai) work\b",

            # Natural conversational help questions
            r"\bwho are you\b",
            r"\bwhat are you\b",
            r"\bwhat do you do\b",
            r"\bwhat is your purpose\b",
            r"\bwhat(?:'s| is) your purpose\b",
            r"\bhow can you help me\b",
            r"\bwhat can you help me with\b",

            # Usage / capability questions
            r"\bhow do i use (?:this ai|this system|fitstyle ai)\b",
            r"\bhow can i use (?:this ai|this system|fitstyle ai)\b",
            r"\bhelp me use (?:this ai|this system|fitstyle ai)\b",
            r"\bwhat are (?:your|its) (?:features|capabilities)\b",
            (
                r"\bwhat kind of (?:fashion )?recommendations "
                r"can (?:you|this ai|this system|fitstyle ai) "
                r"(?:give|make)\b"
            ),
            (
                r"\bcan (?:you|this ai|this system|fitstyle ai) "
                r"(?:check|verify) sizes?\b"
            ),
            (
                r"\bcan (?:you|this ai|this system|fitstyle ai) "
                r"recommend outfits?\b"
            )
        ]

        self.output_schema = {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": [
                        "fashion",
                        "out_of_domain"
                    ]
                },
                "intent": {
                    "type": "string",
                    "enum": [
                        "product_search",
                        "outfit_recommendation",
                        "out_of_domain"
                    ]
                },
                "category": {
                    "type": ["string", "null"]
                },
                "target_group": {
                    "type": ["string", "null"]
                },
                "material": {
                    "type": ["string", "null"]
                },
                "style": {
                    "type": ["string", "null"]
                },
                "occasion": {
                    "type": ["string", "null"]
                },
                "preferred_colors": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "max_price": {
                    "type": ["number", "null"]
                },
                "sizes": {
                    "type": "object",
                    "properties": {
                        "top": {"type": "string"},
                        "bottom": {"type": "string"},
                        "shoes": {"type": "string"}
                    },
                    "additionalProperties": False
                },
                "size": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "domain",
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
    # Basic normalization
    # -------------------------------------------------

    def _normalize_query(self, query):

        query = query.lower().strip()

        return re.sub(
            r"\s+",
            " ",
            query
        )



    # -------------------------------------------------
    # FitStyle AI system/help questions
    # -------------------------------------------------

    def is_system_info_query(
        self,
        query
    ):

        query = self._normalize_query(
            query
        )

        for pattern in self.system_info_patterns:

            if re.search(
                pattern,
                query,
                re.IGNORECASE
            ):
                return True

        return False


    # -------------------------------------------------
    # Deterministic domain detection
    # -------------------------------------------------

    def _has_fashion_signal(self, query):

        # Direct product/category words.
        for aliases in self.category_aliases.values():

            for alias in aliases:

                pattern = (
                    r"\b"
                    + re.escape(alias)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    query
                ):

                    return True


        # General fashion / styling language.
        fashion_patterns = [
            r"\boutfit\b",
            r"\bclothing\b",
            r"\bclothes\b",
            r"\bfashion\b",
            r"\bapparel\b",
            r"\bwhat should i wear\b",
            r"\bwhat to wear\b",
            r"\bcomplete look\b",
            r"\bcomplete outfit\b",
            r"\bfull outfit\b",
            r"\bmatching outfit\b",
            r"\bdress me\b",
            r"\bstyle me\b"
        ]

        for pattern in fashion_patterns:

            if re.search(
                pattern,
                query
            ):

                return True


        # Keep broad occasion requests inside the
        # fashion flow so the system can clarify
        # instead of rejecting them too early.
        contextual_patterns = [
            (
                r"\b(?:need|want|looking for|find|recommend)"
                r"\b.*\b(?:interview|wedding|office|work|"
                r"party|university|date|casual outing)\b"
            )
        ]

        for pattern in contextual_patterns:

            if re.search(
                pattern,
                query
            ):

                return True

        return False


    def detect_domain(self, query):

        query = self._normalize_query(
            query
        )

        # Fashion evidence wins. For example,
        # "what should I wear for rainy weather?"
        # remains a fashion request.
        if self._has_fashion_signal(
            query
        ):

            return "fashion"


        for pattern in self.non_fashion_patterns:

            if re.search(
                pattern,
                query
            ):

                return "out_of_domain"


        # None means deterministic rules are unsure.
        # The LLM can classify the request.
        return None



    # -------------------------------------------------
    # Positive query + exclusion handling
    # -------------------------------------------------

    def _split_positive_and_negative(
        self,
        query
    ):

        """
        Split a query into the positive request and one
        explicit negative / exclusion clause.

        Example:
        "I want a red dress, but do not show blue jeans"
        ->
        positive_query = "i want a red dress"
        negative_text = "blue jeans"
        """

        normalized = self._normalize_query(
            query
        )

        # Keep these patterns conservative so words such
        # as "not" are treated as exclusions only when
        # they introduce a trailing negative constraint.
        patterns = [
            (
                r"(?:,\s*)?\bbut\s+"
                r"(?:absolutely\s+)?"
                r"(?:do\s+not|don't|dont|not|never|no)\s+"
                r"(?:show\s+me\s+|show\s+|include\s+|"
                r"give\s+me\s+)?"
                r"(?P<negative>.+)$"
            ),
            (
                r"(?:,\s*)?\b"
                r"(?:do\s+not|don't|dont|never|except|"
                r"excluding|exclude|without|not|no)\s+"
                r"(?:show\s+me\s+|show\s+|include\s+|"
                r"give\s+me\s+)?"
                r"(?P<negative>.+)$"
            )
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized,
                re.IGNORECASE
            )

            if match:

                positive_query = (
                    normalized[
                        :match.start()
                    ]
                    .strip(" ,.;")
                )

                negative_text = (
                    match.group(
                        "negative"
                    )
                    .strip(" ,.;")
                )

                # If the query begins directly with an
                # exclusion, keep the original query for
                # retrieval instead of producing an empty
                # search string.
                if not positive_query:
                    positive_query = normalized

                return (
                    positive_query,
                    negative_text
                )

        return (
            normalized,
            ""
        )


    def _get_positive_query(
        self,
        query
    ):

        positive_query, _ = (
            self._split_positive_and_negative(
                query
            )
        )

        return positive_query


    def _extract_exclusion(
        self,
        negative_text
    ):

        if not negative_text:
            return None

        text = self._normalize_query(
            negative_text
        )

        exclusion = {
            "raw":
                text
        }

        colors = self._extract_colors(
            text
        )

        if colors:
            # One compound exclusion can contain more
            # than one color. SQL handling treats these
            # as alternatives inside the same field.
            exclusion["colors"] = colors


        category = self._extract_category(
            text
        )

        if category:
            exclusion["category"] = category


        target_group = (
            self._extract_target_group(
                text
            )
        )

        if target_group:
            exclusion[
                "target_group"
            ] = target_group


        material = (
            self._extract_from_list(
                text,
                self.materials
            )
        )

        if material:
            exclusion[
                "material"
            ] = material


        style = (
            self._extract_from_list(
                text,
                self.styles
            )
        )

        if style:

            if style == "sports":
                style = "sport"

            exclusion["style"] = style


        # Keep product-specific words so a compound
        # exclusion such as "blue jeans" does not
        # become a global "exclude blue" rule.
        specific_terms = [
            ("crop tops", "crop"),
            ("crop top", "crop"),
            ("jeans", "jean"),
            ("jean", "jean"),
            ("heels", "heel"),
            ("heel", "heel"),
            ("sneakers", "sneaker"),
            ("sneaker", "sneaker"),
            ("trousers", "trouser"),
            ("trouser", "trouser"),
            ("pants", "pant"),
            ("pant", "pant"),
            ("skirts", "skirt"),
            ("skirt", "skirt"),
            ("shorts", "short"),
            ("short", "short"),
            ("blouses", "blouse"),
            ("blouse", "blouse"),
            ("sandals", "sandal"),
            ("sandal", "sandal"),
            ("floral", "floral"),
            ("printed", "print")
        ]

        for phrase, term in specific_terms:

            if re.search(
                r"\b"
                + re.escape(phrase)
                + r"\b",
                text
            ):

                exclusion["term"] = term
                break


        # Ignore an exclusion that contains no
        # structured fashion information.
        if len(exclusion) == 1:
            return None

        return exclusion


    def extract_exclusions(
        self,
        query
    ):

        _, negative_text = (
            self._split_positive_and_negative(
                query
            )
        )

        exclusion = self._extract_exclusion(
            negative_text
        )

        if exclusion:
            return [exclusion]

        return []



    # -------------------------------------------------
    # Deterministic extraction helpers
    # -------------------------------------------------

    def _extract_category(self, query):

        for category, aliases in (
            self.category_aliases.items()
        ):

            for alias in aliases:

                pattern = (
                    r"\b"
                    + re.escape(alias)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    query
                ):

                    return category

        return None


    def _extract_target_group(self, query):

        for group, aliases in (
            self.target_groups.items()
        ):

            for alias in aliases:

                pattern = (
                    r"\b"
                    + re.escape(alias)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    query
                ):

                    return group

        return None



    def _extract_all_target_groups(
        self,
        query
    ):

        query = self._normalize_query(
            query
        )

        found_groups = []

        for group, aliases in (
            self.target_groups.items()
        ):

            for alias in aliases:

                pattern = (
                    r"\b"
                    + re.escape(alias)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    query
                ):

                    if group not in found_groups:

                        found_groups.append(
                            group
                        )

                    break

        return found_groups


    def _extract_all_role_sizes(
        self,
        query
    ):

        query = self._normalize_query(
            query
        )

        role_patterns = {
            "top": [
                (
                    r"\b(?:shirt|top|t[\s-]?shirt|blouse)"
                    r"\s+size\s+(?:is\s+)?"
                    r"(xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)\b"
                )
            ],

            "bottom": [
                (
                    r"\b(?:trouser|trousers|pant|pants|jean|jeans)"
                    r"\s+size\s+(?:is\s+)?"
                    r"(xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)\b"
                ),
                (
                    r"\b(?:trouser|trousers|pant|pants|jean|jeans)"
                    r"\s+waist\s+(?:is\s+)?"
                    r"(\d+(?:\.\d+)?)\b"
                )
            ],

            "shoes": [
                (
                    r"\b(?:shoe|shoes|heel|heels|sandal|sandals)"
                    r"\s+size\s+(?:is\s+)?"
                    r"(\d+(?:\.\d+)?)\b"
                )
            ]
        }

        found_sizes = {
            "top": [],
            "bottom": [],
            "shoes": []
        }

        for role, patterns in (
            role_patterns.items()
        ):

            for pattern in patterns:

                matches = re.findall(
                    pattern,
                    query,
                    re.IGNORECASE
                )

                for value in matches:

                    normalized_value = (
                        str(value)
                        .strip()
                        .upper()
                    )

                    if (
                        normalized_value
                        not in found_sizes[role]
                    ):

                        found_sizes[
                            role
                        ].append(
                            normalized_value
                        )

        return found_sizes


    def detect_conflict(
        self,
        query
    ):

        # Negative constraints should not be treated
        # as positive conflicts.
        query = self._get_positive_query(
            query
        )

        # -----------------------------------------
        # Conflicting target groups
        # -----------------------------------------

        target_groups = (
            self._extract_all_target_groups(
                query
            )
        )

        if len(target_groups) > 1:

            return {
                "type":
                    "target_group_conflict",

                "question":
                    (
                        "You mentioned more than one "
                        "target group. Which one should "
                        "FitStyle AI use?"
                    ),

                "options":
                    target_groups,

                "reason":
                    (
                        "FitStyle AI does not choose "
                        "between conflicting target groups "
                        "without asking you first."
                    )
            }


        # -----------------------------------------
        # Conflicting role-specific sizes
        # -----------------------------------------

        role_sizes = (
            self._extract_all_role_sizes(
                query
            )
        )

        role_labels = {
            "top": "top",
            "bottom": "bottom",
            "shoes": "shoe"
        }

        for role, sizes in (
            role_sizes.items()
        ):

            if len(sizes) > 1:

                label = role_labels[
                    role
                ]

                return {
                    "type":
                        f"{role}_size_conflict",

                    "question":
                        (
                            f"You provided more than one "
                            f"{label} size. Which size "
                            f"should FitStyle AI use?"
                        ),

                    "options":
                        sizes,

                    "reason":
                        (
                            "FitStyle AI does not guess "
                            "between conflicting size "
                            "constraints."
                        )
                }

        return None


    def _extract_from_list(
        self,
        query,
        values
    ):

        values = sorted(
            values,
            key=len,
            reverse=True
        )

        for value in values:

            pattern = (
                r"\b"
                + re.escape(value)
                + r"\b"
            )

            if re.search(
                pattern,
                query
            ):

                return value

        return None


    def _extract_colors(self, query):

        found_colors = []

        for color in self.colors:

            pattern = (
                r"\b"
                + re.escape(color)
                + r"\b"
            )

            if re.search(
                pattern,
                query
            ):

                normalized_color = (
                    "grey"
                    if color == "gray"
                    else color
                )

                if (
                    normalized_color
                    not in found_colors
                ):

                    found_colors.append(
                        normalized_color
                    )

        return found_colors


    def _extract_max_price(self, query):

        patterns = [
            r"\bunder\s+(?:rs\.?\s*)?([\d,]+)",
            r"\bbelow\s+(?:rs\.?\s*)?([\d,]+)",
            r"\bless\s+than\s+(?:rs\.?\s*)?([\d,]+)",
            r"\bmaximum\s+(?:rs\.?\s*)?([\d,]+)",
            r"\bmax\s+(?:rs\.?\s*)?([\d,]+)",
            r"\bbudget\s+(?:of\s+)?(?:rs\.?\s*)?([\d,]+)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                query
            )

            if match:

                value = (
                    match.group(1)
                    .replace(",", "")
                )

                try:
                    return float(value)

                except ValueError:
                    return None

        return None


    def _extract_size(self, query):

        size_match = re.search(
            r"\bsize\s+(?:is\s+)?"
            r"(xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)\b",
            query,
            re.IGNORECASE
        )

        if size_match:

            return (
                size_match
                .group(1)
                .upper()
            )


        waist_match = re.search(
            r"\bwaist\s+(?:is\s+)?"
            r"(\d+(?:\.\d+)?)\b",
            query,
            re.IGNORECASE
        )

        if waist_match:
            return waist_match.group(1)

        return None


    def _extract_role_sizes(self, query):

        sizes = {}

        top_patterns = [
            (
                r"\b(?:shirt|top|t[\s-]?shirt|blouse)"
                r"\s+size\s+(?:is\s+)?"
                r"(xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)\b"
            )
        ]

        for pattern in top_patterns:

            match = re.search(
                pattern,
                query,
                re.IGNORECASE
            )

            if match:

                sizes["top"] = (
                    match.group(1)
                    .upper()
                )

                break


        bottom_patterns = [
            (
                r"\b(?:trouser|trousers|pant|pants|jean|jeans)"
                r"\s+size\s+(?:is\s+)?"
                r"(xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)\b"
            ),
            (
                r"\b(?:trouser|trousers|pant|pants|jean|jeans)"
                r"\s+waist\s+(?:is\s+)?"
                r"(\d+(?:\.\d+)?)\b"
            ),
            (
                r"\bwaist\s+size\s+(?:is\s+)?"
                r"(\d+(?:\.\d+)?)\b"
            )
        ]

        for pattern in bottom_patterns:

            match = re.search(
                pattern,
                query,
                re.IGNORECASE
            )

            if match:

                sizes["bottom"] = (
                    match.group(1)
                    .upper()
                )

                break


        shoe_patterns = [
            (
                r"\b(?:shoe|shoes|heel|heels|sandal|sandals)"
                r"\s+size\s+(?:is\s+)?"
                r"(\d+(?:\.\d+)?)\b"
            )
        ]

        for pattern in shoe_patterns:

            match = re.search(
                pattern,
                query,
                re.IGNORECASE
            )

            if match:

                sizes["shoes"] = (
                    match.group(1)
                    .upper()
                )

                break

        return sizes


    # -------------------------------------------------
    # Deterministic extraction
    # -------------------------------------------------

    def extract_filters(self, query):

        # Negative clauses must not become positive
        # filters. Example: "not blue jeans" should
        # not add blue to preferred_colors.
        query = self._get_positive_query(
            query
        )

        query = self._normalize_query(
            query
        )

        filters = {}


        category = self._extract_category(
            query
        )

        if category:
            filters["category"] = category


        target_group = (
            self._extract_target_group(
                query
            )
        )

        if target_group:
            filters["target_group"] = (
                target_group
            )


        material = (
            self._extract_from_list(
                query,
                self.materials
            )
        )

        if material:
            filters["material"] = material


        style = (
            self._extract_from_list(
                query,
                self.styles
            )
        )

        if style:

            if style == "sports":
                style = "sport"

            filters["style"] = style


        occasion = (
            self._extract_from_list(
                query,
                self.occasions
            )
        )

        if occasion:

            if occasion == "job interview":
                occasion = "interview"

            filters["occasion"] = occasion


        colors = self._extract_colors(
            query
        )

        if colors:

            filters[
                "preferred_colors"
            ] = colors

            if len(colors) == 1:
                filters["color"] = colors[0]


        max_price = (
            self._extract_max_price(
                query
            )
        )

        if max_price is not None:
            filters["max_price"] = max_price


        role_sizes = (
            self._extract_role_sizes(
                query
            )
        )

        if role_sizes:
            filters["sizes"] = role_sizes


        if not role_sizes:

            size = self._extract_size(
                query
            )

            if size:
                filters["size"] = size


        return filters


    def detect_intent(self, query):

        # Determine intent from the positive request,
        # not from words inside an exclusion clause.
        query = self._get_positive_query(
            query
        )

        query = self._normalize_query(
            query
        )

        outfit_patterns = [
            r"\boutfit\b",
            r"\blook\b",
            r"\bwhat should i wear\b",
            r"\bwhat to wear\b",
            r"\bcomplete outfit\b",
            r"\bfull outfit\b",
            r"\bmatching outfit\b"
        ]

        for pattern in outfit_patterns:

            if re.search(
                pattern,
                query
            ):

                return (
                    "outfit_recommendation"
                )

        return "product_search"


    # -------------------------------------------------
    # LLM extraction
    # -------------------------------------------------

    def _understand_with_llm(
        self,
        query
    ):

        system_prompt = """
You are the Query Understanding component of FitStyle AI.

First classify whether the request belongs to FitStyle AI's
supported fashion domain.

Supported fashion domain:
- clothing and apparel
- footwear
- bags and fashion accessories
- product discovery
- size and variant availability
- styling and outfit recommendations
- what-to-wear requests for occasions

Examples that ARE fashion:
- "women casual cotton top size M"
- "I need an outfit for an interview"
- "I need something for a job interview"
- "what should I wear for a wedding?"
- "find black shoes"

Examples that are OUT OF DOMAIN:
- "recommend me a laptop"
- "what is the weather today?"
- "write Python code"
- "find a restaurant"
- "recommend a phone"

If the query is out of domain:
- domain must be "out_of_domain"
- intent must be "out_of_domain"
- all fashion fields must be null, empty array, or empty object

If the query is fashion-related:
- domain must be "fashion"
- choose product_search or outfit_recommendation

Fashion extraction rules:

1. Use canonical categories only when identifiable:
   tops, bottoms, dresses, footwear, innerwear,
   accessories, bags, ethnic_wear.

2. Separate target group from category.
   Valid target groups: men, women, teen, kids.

3. Extract only information supported by the user's query.
   Do not invent missing information.

4. Normalize:
   job interview -> occasion "interview"
   gray -> "grey"
   sports -> style "sport"

5. Size roles:
   shirts/tops -> sizes.top
   trousers/jeans/bottoms/waist -> sizes.bottom
   shoes/heels/sandals -> sizes.shoes

6. For a simple single-product query, copy the one requested
   size into "size".

7. For an outfit query with multiple role-specific sizes,
   keep "size" as null and use "sizes".

8. preferred_colors must always be an array.

9. max_price must be a number only.

10. A request for a complete outfit/look or what to wear has
    intent "outfit_recommendation".
    Otherwise use "product_search".

11. Use null or an empty array/object when information is absent.

12. Return only valid JSON matching the schema.

13. Never infer a target group or gender from the garment,
    occasion, style, or context. Only extract it when the
    user explicitly states men, women, teen, kids, male,
    female, etc.

14. Never invent or assume a size. Only return a size when
    the user explicitly provides one.
"""

        response = chat(
            model=self.model_name,
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
            format=self.output_schema,
            options={
                "temperature": 0
            }
        )

        return json.loads(
            response.message.content
        )


    # -------------------------------------------------
    # Convert LLM output to project filters
    # -------------------------------------------------

    def _llm_to_filters(
        self,
        llm_result
    ):

        filters = {}

        canonical_categories = set(
            self.category_aliases.keys()
        )

        canonical_targets = set(
            self.target_groups.keys()
        )


        category = llm_result.get(
            "category"
        )

        if category:

            category = (
                str(category)
                .strip()
                .lower()
            )

            if category in canonical_categories:
                filters["category"] = category


        target_group = llm_result.get(
            "target_group"
        )

        if target_group:

            target_group = (
                str(target_group)
                .strip()
                .lower()
            )

            if target_group in canonical_targets:
                filters[
                    "target_group"
                ] = target_group


        for key in [
            "material",
            "style",
            "occasion"
        ]:

            value = llm_result.get(
                key
            )

            if value:

                filters[key] = (
                    str(value)
                    .strip()
                    .lower()
                )


        if filters.get("style") == "sports":
            filters["style"] = "sport"


        if (
            filters.get("occasion")
            == "job interview"
        ):

            filters["occasion"] = (
                "interview"
            )


        raw_colors = (
            llm_result.get(
                "preferred_colors"
            )
            or []
        )

        colors = []

        for color in raw_colors:

            color = (
                str(color)
                .strip()
                .lower()
            )

            if color in {
                "",
                "null",
                "none",
                "n/a"
            }:
                continue

            if color == "gray":
                color = "grey"

            if (
                color
                and color not in colors
            ):

                colors.append(
                    color
                )


        if colors:

            filters[
                "preferred_colors"
            ] = colors

            if len(colors) == 1:
                filters["color"] = colors[0]


        max_price = llm_result.get(
            "max_price"
        )

        if max_price is not None:

            try:

                filters["max_price"] = float(
                    max_price
                )

            except (
                TypeError,
                ValueError
            ):

                pass


        raw_sizes = (
            llm_result.get(
                "sizes"
            )
            or {}
        )

        sizes = {}

        for role in [
            "top",
            "bottom",
            "shoes"
        ]:

            value = raw_sizes.get(
                role
            )

            if value:

                sizes[role] = (
                    str(value)
                    .strip()
                    .upper()
                )


        if sizes:
            filters["sizes"] = sizes


        size = llm_result.get(
            "size"
        )

        if size:

            filters["size"] = (
                str(size)
                .strip()
                .upper()
            )


        return filters


    # -------------------------------------------------
    # Final normalization
    # -------------------------------------------------

    def _finalize_filters(
        self,
        intent,
        filters
    ):

        filters = dict(
            filters
        )


        if intent == (
            "outfit_recommendation"
        ):

            # Outfit requests span multiple categories.
            filters.pop(
                "category",
                None
            )

            # Preferred colors should influence the
            # whole outfit instead of hard-filtering
            # every piece to one color.
            filters.pop(
                "color",
                None
            )

                # Outfit sizes must remain role-specific:
    # top / bottom / shoes.
            filters.pop(
                "size",
                None
            )


        else:

            role_sizes = filters.get(
                "sizes",
                {}
            )

            if (
                role_sizes
                and "size" not in filters
                and len(role_sizes) == 1
            ):

                filters["size"] = next(
                    iter(
                        role_sizes.values()
                    )
                )


            if (
                filters.get("occasion")
                == filters.get("style")
            ):

                filters.pop(
                    "occasion",
                    None
                )


        return filters


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
                "Agent input must be a dictionary."
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


        # Build a clean positive retrieval query and
        # keep explicit negative constraints separately.
        retrieval_query = self._get_positive_query(
            query
        )

        exclusions = self.extract_exclusions(
            query
        )


        # -----------------------------------------
        # Questions about FitStyle AI itself
        # -----------------------------------------

        # These questions do not need product retrieval
        # or an LLM call. A deterministic response keeps
        # the system description accurate and grounded.
        if self.is_system_info_query(
            query
        ):

            return {
                "agent":
                    self.name,

                "status":
                    "success",

                "original_query":
                    query,

                "domain":
                    "fashion",

                "intent":
                    "system_info",

                "filters":
                    {},

                "understanding_method":
                    "deterministic system-info routing"
            }


        # Deterministic parsing always runs so it can
        # validate explicit constraints and act as a
        # fallback if Ollama is unavailable.
        deterministic_domain = (
            self.detect_domain(
                query
            )
        )

        deterministic_intent = (
            self.detect_intent(
                query
            )
        )

        deterministic_filters = (
            self.extract_filters(
                query
            )
        )

        deterministic_conflict = (
            self.detect_conflict(
                query
            )
        )


        llm_used = False
        llm_error = None
        llm_result = None


        try:

            llm_result = (
                self._understand_with_llm(
                    retrieval_query
                )
            )

            llm_used = True


        except Exception as error:

            llm_error = str(
                error
            )


        # -----------------------------------------
        # Decide final domain
        # -----------------------------------------

        if deterministic_domain == "fashion":

            # Explicit fashion language should not
            # be overridden by the LLM.
            domain = "fashion"


        elif deterministic_domain == "out_of_domain":

            # Clear non-fashion requests stay out
            # of the recommendation pipeline.
            domain = "out_of_domain"


        elif llm_result:

            llm_domain = llm_result.get(
                "domain"
            )

            if llm_domain in {
                "fashion",
                "out_of_domain"
            }:

                domain = llm_domain

            else:

                # Do not reject an unclear query
                # without evidence.
                domain = "fashion"


        else:

            # When Ollama is unavailable and the
            # deterministic rules are unsure, keep
            # the request in the fashion flow rather
            # than falsely rejecting it.
            domain = "fashion"


        # -----------------------------------------
        # Out-of-domain response
        # -----------------------------------------

        if domain == "out_of_domain":

            response = {
                "agent":
                    self.name,

                "status":
                    "unsupported_request",

                "original_query":
                    query,

                "domain":
                    "out_of_domain",

                "intent":
                    "out_of_domain",

                "filters":
                    {},

                "understanding_method":
                    (
                        "Qwen2.5 3B + deterministic validation"
                        if llm_used
                        else
                        "deterministic fallback"
                    )
            }


            if llm_error:

                response[
                    "llm_fallback_reason"
                ] = llm_error


            return response


        # -----------------------------------------
        # Explicit conflicting constraints
        # -----------------------------------------

        if deterministic_conflict:

            response = {
                "agent":
                    self.name,

                "status":
                    "needs_clarification",

                "original_query":
                    query,

                "domain":
                    "fashion",

                "intent":
                    deterministic_intent,

                "filters":
                    {},

                "clarification":
                    deterministic_conflict,

                "understanding_method":
                    (
                        "Qwen2.5 3B + deterministic validation"
                        if llm_used
                        else
                        "deterministic fallback"
                    )
            }


            if llm_error:

                response[
                    "llm_fallback_reason"
                ] = llm_error


            return response


        # -----------------------------------------
        # Fashion request understanding
        # -----------------------------------------

        if llm_result:

            llm_intent = llm_result.get(
                "intent"
            )

            if llm_intent not in {
                "product_search",
                "outfit_recommendation"
            }:

                llm_intent = (
                    deterministic_intent
                )


            llm_filters = (
                self._llm_to_filters(
                    llm_result
                )
            )


            # LLM handles broader language
            # understanding. Deterministic values
            # override explicitly detected fields.
            filters = {
                **llm_filters,
                **deterministic_filters
            }


            # -------------------------------------
            # Prevent LLM from inventing hard facts
            # -------------------------------------

            # Target group must be explicitly
            # detected from the user's query.
            if (
                "target_group"
                not in deterministic_filters
            ):

                filters.pop(
                    "target_group",
                    None
                )


            # Sizes must be explicitly present
            # in the user's query.
            if (
                "sizes" not in deterministic_filters
                and "size" not in deterministic_filters
            ):

                filters.pop(
                    "sizes",
                    None
                )

                filters.pop(
                    "size",
                    None
                )


            # If deterministic parser found role
            # sizes, do not trust a different
            # global LLM size.
            if (
                "sizes" in deterministic_filters
                and "size" not in deterministic_filters
            ):

                filters.pop(
                    "size",
                    None
                )


            if (
                deterministic_intent
                == "outfit_recommendation"
            ):

                # Explicit outfit language always wins.
                intent = (
                    "outfit_recommendation"
                )

            elif deterministic_filters.get(
                "category"
            ):

                # An explicit single-product category
                # such as "red dress", "black shoes"
                # or "women jeans" must stay a product
                # search even if the LLM over-generalizes
                # it as an outfit request.
                intent = "product_search"

            else:

                # For broader fashion language without
                # an explicit product category, allow
                # the LLM to help classify the intent.
                intent = llm_intent


        else:

            intent = (
                deterministic_intent
            )

            filters = (
                deterministic_filters
            )


        filters = (
            self._finalize_filters(
                intent,
                filters
            )
        )


        response = {
            "agent":
                self.name,

            "status":
                "success",

            "original_query":
                query,

            "domain":
                "fashion",

            "intent":
                intent,

            "filters":
                filters,

            "retrieval_query":
                retrieval_query,

            "exclusions":
                exclusions,

            "understanding_method":
                (
                    "Qwen2.5 3B + deterministic validation"
                    if llm_used
                    else
                    "deterministic fallback"
                )
        }


        if llm_error:

            response[
                "llm_fallback_reason"
            ] = llm_error


        return response


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    agent = QueryUnderstandingAgent()

    test_queries = [
        "women casual cotton top size M",
        "I need an outfit for an interview",
        "I need something for a job interview",
        "recommend black shoes",
        "recommend me a laptop",
        "what is the weather today?",
        "write Python code",
        "women's jeans for men",
        "men shirt size M and shirt size L",
        "what is this ai system about",
        "what can FitStyle AI do?",
        "how does this system work?",
        "what is this ai about",
        "what do you do?",
        "how can you help me?",
        "tell me about FitStyle AI",
        "I want a red dress for women",
        (
            "I want a red dress, but absolutely "
            "DO NOT show me blue jeans."
        ),
        "Show me blue shirts, but not blue jeans",
        "Show me black shoes but not heels",
        "I want a cotton shirt, no red ones",
        "Find dresses except floral dresses",
        "Show trousers, not jeans",
        "I need an interview outfit but no heels"
    ]

    print(
        "\n--- QUERY UNDERSTANDING AGENT ---"
    )

    for query in test_queries:

        response = agent.run({
            "query":
                query
        })

        print(
            "\nQuery:",
            query
        )

        print(
            "Status:",
            response.get(
                "status"
            )
        )

        print(
            "Domain:",
            response.get(
                "domain"
            )
        )

        print(
            "Intent:",
            response.get(
                "intent"
            )
        )

        print(
            "Filters:",
            response.get(
                "filters"
            )
        )
