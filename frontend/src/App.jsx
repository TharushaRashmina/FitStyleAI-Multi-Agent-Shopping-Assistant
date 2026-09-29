import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "motion/react"

import {
  AlertTriangle,
  CheckCircle2,
  Info,
  LogOut,
  Search,
  SearchX,
  Shirt,
  Sparkles,
  UserRound,
  WandSparkles,
} from "lucide-react"

import {
  getApiErrorMessage,
  getCurrentUser,
  getRecommendation,
  logoutUser,
} from "./services/api"
import ProductCard from "./components/ProductCard"
import OutfitRecommendation from "./components/OutfitRecommendation"
import ClarificationCard from "./components/ClarificationCard"
import AgentProcessing from "./components/AgentProcessing"
import AuthPage from "./components/AuthPage"


function App() {
  // User's search text.
  const [query, setQuery] = useState("")

  // Stores the response returned by FastAPI.
  const [result, setResult] = useState(null)

  // Shows loading state while the multi-agent system is processing.
  const [loading, setLoading] = useState(false)

  // Stores frontend/API error messages.
  const [error, setError] = useState("")

  // Tracks whether the user has submitted at least
  // one request during the current page session.
  const [hasSearched, setHasSearched] = useState(false)

  // Authentication state.
  const [user, setUser] = useState(null)
  const [authChecking, setAuthChecking] = useState(true)
  const [logoutLoading, setLogoutLoading] = useState(false)
  const [authMessage, setAuthMessage] = useState("")


  // -------------------------------------------------
  // Restore login when the page is refreshed
  // -------------------------------------------------

  useEffect(() => {
    let cancelled = false


    const restoreSession = async () => {

      try {
        const data =
          await getCurrentUser()


        if (!cancelled) {
          setUser(
            data.user
          )
        }

      } catch (err) {

        // A 401 simply means there is no valid
        // login session yet.
        if (
          !cancelled &&
          err?.response?.status !== 401
        ) {
          setAuthMessage(
            "We could not verify your login session. Please sign in again."
          )
        }


        if (!cancelled) {
          setUser(null)
        }

      } finally {

        if (!cancelled) {
          setAuthChecking(false)
        }
      }
    }


    restoreSession()


    return () => {
      cancelled = true
    }

  }, [])


  // -------------------------------------------------
  // Called after successful login / registration
  // -------------------------------------------------

  const handleAuthenticated = (
    authenticatedUser
  ) => {
    setUser(
      authenticatedUser
    )

    setAuthMessage("")
    setError("")
  }


  // -------------------------------------------------
  // Logout
  // -------------------------------------------------

  const handleLogout = async () => {

    try {
      setLogoutLoading(true)

      await logoutUser()


      // Clear private UI state after logout.
      setUser(null)
      setQuery("")
      setResult(null)
      setError("")
      setHasSearched(false)
      setAuthMessage("")

    } catch (err) {

      setError(
        getApiErrorMessage(
          err,
          "Logout failed. Please try again."
        )
      )

    } finally {
      setLogoutLoading(false)
    }
  }


  // -------------------------------------------------
  // Send any query to the FitStyle AI backend
  // -------------------------------------------------

  const submitQuery = async (searchQuery) => {
    const cleanedQuery = searchQuery.trim()

    // Prevent empty searches.
    if (!cleanedQuery) {
      setError(
        "Please describe what you're looking for."
      )
      return
    }

    try {
      // Keep the search box synchronized with
      // the actual query sent to the backend.
      setQuery(cleanedQuery)

      setHasSearched(true)
      setLoading(true)
      setError("")
      setResult(null)

      // Call POST /recommend through api.js.
      const data = await getRecommendation(
        cleanedQuery
      )

      setResult(data)
    } catch (err) {

      // If the JWT expires while the user is
      // using the app, return safely to login.
      if (
        err?.response?.status === 401
      ) {
        setUser(null)
        setResult(null)
        setError("")
        setAuthMessage(
          "Your session expired. Please sign in again."
        )

        return
      }


      setError(
        getApiErrorMessage(
          err,
          "Something went wrong. Please try again."
        )
      )

    } finally {
      setLoading(false)
    }
  }


  // -------------------------------------------------
  // Normal search button / Enter key
  // -------------------------------------------------

  const handleSearch = async () => {
    await submitQuery(query)
  }


  // -------------------------------------------------
  // Build a follow-up query from clarification
  // -------------------------------------------------

  const buildClarifiedQuery = (
    originalQuery,
    clarificationType,
    option
  ) => {
    const baseQuery = originalQuery.trim()


    // ---------------------------------------------
    // Missing target group
    // ---------------------------------------------

    if (clarificationType === "target_group") {
      return `${baseQuery} for ${option}`
    }


    // ---------------------------------------------
    // Conflicting target groups
    // ---------------------------------------------

    if (
      clarificationType ===
      "target_group_conflict"
    ) {
      // Remove all explicit target-group words
      // before adding the user's selected answer.
      const targetGroupPattern =
        /\b(?:men(?:['’]s|s)?|male|women(?:['’]s|s)?|female|teens?|teenage(?:r|rs)?|kids?|child|children)\b/gi

      const cleanedQuery = baseQuery
        .replace(
          targetGroupPattern,
          " "
        )
        .replace(
          /\s+/g,
          " "
        )
        .trim()
        .replace(
          /\bfor\s*$/i,
          ""
        )
        .trim()

      return `${cleanedQuery} for ${option}`
    }


    // ---------------------------------------------
    // Conflicting top sizes
    // ---------------------------------------------

    if (
      clarificationType ===
      "top_size_conflict"
    ) {
      const cleanedQuery = baseQuery
        .replace(
          /\b(?:shirt|top|t[\s-]?shirt|blouse)\s+size\s+(?:is\s+)?(?:xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)\b/gi,
          " "
        )
        .replace(
          /\s+/g,
          " "
        )
        .trim()
        .replace(
          /\b(?:and|or)\s*$/i,
          ""
        )
        .trim()

      return `${cleanedQuery} shirt size ${option}`
    }


    // ---------------------------------------------
    // Conflicting bottom sizes
    // ---------------------------------------------

    if (
      clarificationType ===
      "bottom_size_conflict"
    ) {
      const cleanedQuery = baseQuery
        .replace(
          /\b(?:trouser|trousers|pant|pants|jean|jeans)\s+(?:size|waist)\s+(?:is\s+)?(?:xxs|xs|s|m|l|xl|xxl|xxxl|\d+(?:\.\d+)?)\b/gi,
          " "
        )
        .replace(
          /\s+/g,
          " "
        )
        .trim()
        .replace(
          /\b(?:and|or)\s*$/i,
          ""
        )
        .trim()

      return `${cleanedQuery} trouser size ${option}`
    }


    // ---------------------------------------------
    // Conflicting shoe sizes
    // ---------------------------------------------

    if (
      clarificationType ===
      "shoes_size_conflict"
    ) {
      const cleanedQuery = baseQuery
        .replace(
          /\b(?:shoe|shoes|heel|heels|sandal|sandals)\s+size\s+(?:is\s+)?(?:\d+(?:\.\d+)?)\b/gi,
          " "
        )
        .replace(
          /\s+/g,
          " "
        )
        .trim()
        .replace(
          /\b(?:and|or)\s*$/i,
          ""
        )
        .trim()

      return `${cleanedQuery} shoe size ${option}`
    }


    // ---------------------------------------------
    // Other future clarification types
    // ---------------------------------------------

    if (clarificationType === "size") {
      return `${baseQuery} size ${option}`
    }

    if (clarificationType === "category") {
      return `${baseQuery} ${option}`
    }

    return `${baseQuery} ${option}`
  }


  // -------------------------------------------------
  // Handle clarification option selection
  // -------------------------------------------------

  const handleClarificationSelect = async (
    option
  ) => {
    const clarification =
      result?.clarification

    if (!clarification) {
      return
    }

    const originalQuery =
      result?.query || query

    const followUpQuery =
      buildClarifiedQuery(
        originalQuery,
        clarification.type,
        option
      )

    // Re-send the completed request automatically.
    await submitQuery(
      followUpQuery
    )
  }


  // -------------------------------------------------
  // Initial authentication check
  // -------------------------------------------------

  if (authChecking) {
    return (
      <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0b0c12] text-white">

        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="blob blob-one" />
          <div className="blob blob-two" />
        </div>

        <motion.div
          initial={{
            opacity: 0,
            y: 8,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          className="relative z-10 flex flex-col items-center"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-black">
            <Shirt size={22} />
          </div>

          <p className="mt-4 text-sm font-medium text-white/82">
            FitStyle AI
          </p>

          <div className="mt-4 flex items-center gap-2 text-xs text-white/65">
            <span className="loading-spinner" />
            Checking your session...
          </div>
        </motion.div>

      </main>
    )
  }


  // -------------------------------------------------
  // User must authenticate before accessing the app
  // -------------------------------------------------

  if (!user) {
    return (
      <AuthPage
        onAuthenticated={
          handleAuthenticated
        }
        initialMessage={
          authMessage
        }
      />
    )
  }


  return (
    <main className="min-h-screen overflow-hidden bg-[#0b0c12] text-white">

      {/* Soft animated background */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="blob blob-one" />
        <div className="blob blob-two" />
      </div>


      {/* Navbar */}
      <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-4 py-5 sm:px-6 sm:py-6 lg:px-10">

        <div className="flex items-center gap-3">

          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-black sm:h-10 sm:w-10">
            <Shirt size={20} />
          </div>

          <div>
            <h1 className="text-base font-semibold tracking-tight sm:text-lg">
              FitStyle AI
            </h1>

            <p className="hidden text-xs text-white/55 sm:block">
              Intelligent Fashion Discovery
            </p>
          </div>

        </div>


        <div className="flex items-center gap-2">

          <div className="hidden items-center gap-2 rounded-full border border-white/15 bg-white/[0.075] px-4 py-2 text-sm text-white/72 backdrop-blur-md lg:flex">
            <Sparkles size={15} />
            Multi-Agent Fashion AI
          </div>


          {/* Logged-in user */}
          <div className="flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.065] p-1.5 pl-2 backdrop-blur-md">

            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-400/15 text-violet-200">
              <UserRound size={15} />
            </div>

            <div className="hidden min-w-0 pr-1 text-left sm:block">

              <p className="max-w-28 truncate text-xs font-medium text-white/82">
                {user.name}
              </p>

              <p className="max-w-28 truncate text-[10px] text-white/72">
                {user.email}
              </p>

            </div>


            <button
              type="button"
              onClick={handleLogout}
              disabled={logoutLoading}
              aria-label="Log out"
              title="Log out"
              className="flex h-8 w-8 items-center justify-center rounded-full text-white/65 transition hover:bg-white/[0.07] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              <LogOut size={15} />
            </button>

          </div>

        </div>

      </nav>


      {/* Hero */}
      <section className="relative z-10 mx-auto flex max-w-6xl flex-col items-center px-4 pb-16 pt-12 text-center sm:px-6 sm:pb-24 sm:pt-16 lg:pt-24">

        <motion.div
          initial={{
            opacity: 0,
            y: 15,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.6,
          }}
          className="mb-6 flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.075] px-3.5 py-2 text-xs text-white/72 backdrop-blur-xl sm:mb-7 sm:px-4 sm:text-sm"
        >
          <WandSparkles size={15} />
          AI-powered fashion recommendations
        </motion.div>


        <motion.h2
          initial={{
            opacity: 0,
            y: 25,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.7,
            delay: 0.1,
          }}
          className="max-w-4xl text-4xl font-semibold leading-[1.08] tracking-[-0.045em] sm:text-6xl sm:leading-[1.05] lg:text-7xl"
        >
          Discover your next
          <span className="gradient-text">
            {" "}perfect look.
          </span>
        </motion.h2>


        <motion.p
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            duration: 0.8,
            delay: 0.3,
          }}
          className="mt-5 max-w-2xl text-sm leading-6 text-white/65 sm:mt-6 sm:text-lg sm:leading-7"
        >
          Describe what you're looking for and let our intelligent
          agents discover products, verify sizes, and create
          complete outfits for you.
        </motion.p>


        {/* Search */}
        <motion.div
          initial={{
            opacity: 0,
            y: 25,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.7,
            delay: 0.4,
          }}
          className="mt-9 w-full max-w-3xl sm:mt-12"
        >

          <div className="search-shell">

            <Search
              size={21}
              className="shrink-0 text-white/65"
            />

            <input
              value={query}
              onChange={(event) =>
                setQuery(
                  event.target.value
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter"
                  && !loading
                ) {
                  handleSearch()
                }
              }}
              placeholder="Try: women casual cotton top size M"
              aria-label="Fashion search query"
              className="min-w-0 flex-1 bg-transparent text-base text-white outline-none placeholder:text-white/55"
            />

            <button
              type="button"
              onClick={handleSearch}
              disabled={loading}
              aria-label="Find fashion recommendations"
              className="search-button disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <>
                  <span className="loading-spinner" />
                  Finding...
                </>
              ) : (
                <>
                  <Sparkles size={17} />
                  Find My Style
                </>
              )}
            </button>

          </div>


          {/* Loading, error and result-status transitions */}
          <AnimatePresence mode="wait">

            {loading && (
              <motion.div
                key="loading-state"
                initial={{
                  opacity: 0,
                  y: 10,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                exit={{
                  opacity: 0,
                  y: -8,
                }}
                transition={{
                  duration: 0.25,
                }}
              >
                <AgentProcessing />
              </motion.div>
            )}


            {!loading && error && (
              <motion.div
                key="error-state"
                initial={{
                  opacity: 0,
                  y: 8,
                  scale: 0.985,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1,
                }}
                exit={{
                  opacity: 0,
                  y: -6,
                }}
                transition={{
                  duration: 0.25,
                }}
                className="status-card status-card-error"
              >
                <div className="status-icon">
                  <AlertTriangle size={17} />
                </div>

                <div>
                  <p className="status-title">
                    We couldn't complete that request
                  </p>

                  <p className="status-message">
                    {error}
                  </p>
                </div>
              </motion.div>
            )}


            {!loading &&
              result?.status === "success" &&
              (
                result?.intent === "product_search" ||
                result?.intent === "outfit_recommendation"
              ) && (
              <motion.div
                key={`success-${result.query}`}
                initial={{
                  opacity: 0,
                  y: 8,
                  scale: 0.985,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1,
                }}
                exit={{
                  opacity: 0,
                  y: -6,
                }}
                transition={{
                  duration: 0.3,
                }}
                className="status-card status-card-success"
              >
                <div className="status-icon">
                  <CheckCircle2 size={17} />
                </div>

                <div className="min-w-0">
                  <p className="status-title">
                    Recommendation ready
                  </p>

                  <p className="status-message">
                    FitStyle AI found{" "}
                    <span className="font-medium text-white/80">
                      {result.result_count ??
                        result.item_count ??
                        0}
                    </span>{" "}
                    recommendation
                    {(result.result_count ??
                      result.item_count ??
                      0) !== 1
                      ? "s"
                      : ""}
                    .
                  </p>
                </div>
              </motion.div>
            )}



            {!loading &&
              result?.status === "success" &&
              result?.intent === "system_info" && (

              <motion.div
                key={`system-info-${result.query}`}
                initial={{
                  opacity: 0,
                  y: 10,
                  scale: 0.985,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1,
                }}
                exit={{
                  opacity: 0,
                  y: -6,
                }}
                transition={{
                  duration: 0.3,
                }}
                className="mx-auto mt-5 w-full max-w-3xl rounded-2xl border border-violet-300/25 bg-[linear-gradient(135deg,rgba(139,92,246,0.10),rgba(255,255,255,0.055))] p-5 text-left shadow-[0_20px_70px_rgba(76,29,149,0.12)] backdrop-blur-xl sm:p-6"
              >

                <div className="flex items-start gap-3">

                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-400/15 text-violet-200">
                    <Info size={18} />
                  </div>


                  <div className="min-w-0 flex-1">

                    <p className="text-sm font-semibold text-white/90">
                      {result.title || "About FitStyle AI"}
                    </p>

                    <p className="mt-2 text-sm leading-6 text-white/65">
                      {result.message}
                    </p>


                    {result.capabilities?.length > 0 && (
                      <div className="mt-5">

                        <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-white/72">
                          What I can help with
                        </p>

                        <div className="mt-3 grid gap-2 sm:grid-cols-2">

                          {result.capabilities.map(
                            (
                              capability,
                              index
                            ) => (
                              <div
                                key={index}
                                className="rounded-xl border border-white/[0.10] bg-black/25 px-3.5 py-3 text-xs leading-5 text-white/72"
                              >
                                {capability}
                              </div>
                            )
                          )}

                        </div>

                      </div>
                    )}


                    {result.supported_examples?.length > 0 && (
                      <div className="mt-5">

                        <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-white/72">
                          Try a fashion request
                        </p>

                        <div className="mt-2 flex flex-wrap gap-2">

                          {result.supported_examples.map(
                            (
                              example,
                              index
                            ) => (
                              <button
                                key={index}
                                type="button"
                                disabled={loading}
                                onClick={() =>
                                  submitQuery(
                                    example
                                  )
                                }
                                className="rounded-full border border-white/[0.12] bg-white/[0.055] px-3.5 py-2 text-xs text-white/72 transition hover:border-violet-300/20 hover:bg-violet-400/[0.07] hover:text-white/82 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                {example}
                              </button>
                            )
                          )}

                        </div>

                      </div>
                    )}

                  </div>

                </div>

              </motion.div>
            )}


            {!loading &&
              result?.status ===
                "unsupported_request" && (
              <motion.div
                key={`unsupported-${result.query}`}
                initial={{
                  opacity: 0,
                  y: 8,
                  scale: 0.985,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1,
                }}
                exit={{
                  opacity: 0,
                  y: -6,
                }}
                transition={{
                  duration: 0.3,
                }}
                className="status-card status-card-warning"
              >
                <div className="status-icon">
                  <AlertTriangle size={17} />
                </div>

                <div>
                  <p className="status-title">
                    Outside the supported fashion domain
                  </p>

                  <p className="status-message">
                    {result.message}
                  </p>
                </div>
              </motion.div>
            )}


            {!loading &&
              result?.status === "no_match" && (
              <motion.div
                key={`no-match-${result.query}`}
                initial={{
                  opacity: 0,
                  y: 8,
                  scale: 0.985,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                  scale: 1,
                }}
                exit={{
                  opacity: 0,
                  y: -6,
                }}
                transition={{
                  duration: 0.3,
                }}
                className="status-card status-card-no-match"
              >
                <div className="status-icon">
                  <SearchX size={17} />
                </div>

                <div className="min-w-0 flex-1">

                  <p className="status-title">
                    No exact match found
                  </p>

                  <p className="status-message">
                    {result.message}
                  </p>


                  {result.suggestions?.length > 0 && (
                    <div className="mt-4">

                      <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-white/72">
                        Try adjusting
                      </p>

                      <div className="mt-2 space-y-2">

                        {result.suggestions.map(
                          (
                            suggestion,
                            index
                          ) => (
                            <div
                              key={index}
                              className="flex gap-2 text-sm leading-6 text-white/72"
                            >
                              <span className="mt-[1px] text-violet-300">
                                •
                              </span>

                              <span>
                                {suggestion}
                              </span>
                            </div>
                          )
                        )}

                      </div>

                    </div>
                  )}


                  {result.missing_roles?.length > 0 && (
                    <p className="mt-4 text-xs text-white/65">
                      Missing outfit items:{" "}
                      <span className="capitalize text-white/72">
                        {result.missing_roles.join(
                          ", "
                        )}
                      </span>
                    </p>
                  )}

                </div>
              </motion.div>
            )}


            {!loading &&
              result?.status ===
                "needs_clarification" &&
              result?.clarification && (

              <motion.div
                key={`clarification-${result.query}`}
                initial={{
                  opacity: 0,
                  y: 8,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                exit={{
                  opacity: 0,
                  y: -6,
                }}
                transition={{
                  duration: 0.3,
                }}
              >
                <ClarificationCard
                  clarification={
                    result.clarification
                  }
                  loading={loading}
                  onSelect={
                    handleClarificationSelect
                  }
                />
              </motion.div>

            )}


            {!loading &&
              !error &&
              !result &&
              hasSearched && (
              <motion.div
                key="waiting-state"
                initial={{
                  opacity: 0,
                }}
                animate={{
                  opacity: 1,
                }}
                exit={{
                  opacity: 0,
                }}
                className="mt-4 text-sm text-white/65"
              >
                Preparing your next request...
              </motion.div>
            )}

          </AnimatePresence>


          {/* Example prompts */}
          <div className="mt-5 flex flex-wrap justify-center gap-2">

            {[
              "Women's interview outfit",
              "Casual cotton top size M",
              "Men's formal shirt",
            ].map((example) => (

              <button
                key={example}
                type="button"
                disabled={loading}
                onClick={() =>
                  setQuery(example)
                }
                className="rounded-full border border-white/15 bg-white/[0.03] px-4 py-2 text-xs text-white/72 transition hover:border-white/20 hover:bg-white/[0.07] hover:text-white/82 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {example}
              </button>

            ))}

          </div>

        </motion.div>


        {/* Product Search Results */}
        <AnimatePresence mode="wait">
          {result?.status === "success" &&
            result?.intent === "product_search" &&
            result?.products?.length > 0 && (

          <motion.section
            key={`products-${result.query}`}
            initial={{
              opacity: 0,
              y: 30,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.6,
            }}
            className="result-section mt-16 w-full max-w-7xl sm:mt-24"
          >

            {/* Results heading */}
            <div className="mb-6 flex flex-col items-start justify-between gap-4 text-left sm:mb-8 sm:flex-row sm:items-end">

              <div>
                <p className="text-sm text-violet-300">
                  Personalized Results
                </p>

                <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-4xl">
                  We found your matches
                </h2>

                <p className="mt-3 max-w-xl text-sm leading-6 text-white/55">
                  Recommendations based on your search preferences,
                  product availability and verified variant data.
                </p>
              </div>


              <div className="rounded-full border border-white/15 bg-white/[0.04] px-4 py-2 text-sm text-white/65">
                {result.result_count} products
              </div>

            </div>


            {/* Product grid */}
            <div className="grid gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3 xl:grid-cols-4">

              {result.products.map(
                (
                  product,
                  index
                ) => (

                  <ProductCard
                    key={
                      product.product_id
                    }
                    product={
                      product
                    }
                    index={
                      index
                    }
                  />

                )
              )}

            </div>


            {/* Fit disclaimer */}
            {result.fit_note && (
              <div className="mt-8 rounded-2xl border border-white/[0.11] bg-white/[0.04] px-5 py-4 text-left text-xs leading-5 text-white/65">
                {result.fit_note}
              </div>
            )}

          </motion.section>
          )}
        </AnimatePresence>


        {/* Outfit Recommendation Results */}
        <AnimatePresence mode="wait">
          {result?.status === "success" &&
            result?.intent === "outfit_recommendation" && (

            <motion.div
              key={`outfit-${result.query}`}
              initial={{
                opacity: 0,
                y: 20,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              exit={{
                opacity: 0,
                y: -12,
              }}
              transition={{
                duration: 0.35,
              }}
              className="result-transition-shell w-full"
            >
              <OutfitRecommendation
                result={result}
              />
            </motion.div>

          )}
        </AnimatePresence>


        {/* Initial empty / idle state */}
        {!hasSearched && (
          <motion.div
            initial={{
              opacity: 0,
              y: 16,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.6,
              delay: 0.55,
            }}
            className="mt-16 w-full max-w-3xl rounded-2xl border border-white/[0.11] bg-white/[0.04] px-5 py-5 text-left sm:mt-20 sm:px-6"
          >
            <div className="flex items-start gap-3">

              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-400/15 text-violet-200">
                <Sparkles size={17} />
              </div>

              <div>
                <p className="text-sm font-medium text-white/80">
                  Better details create better recommendations
                </p>

                <p className="mt-1.5 text-sm leading-6 text-white/55">
                  Try including a product type or occasion,
                  target group, budget, preferred color, and
                  size when they matter to you.
                </p>
              </div>

            </div>
          </motion.div>
        )}


        {/* Feature cards */}
        <motion.div
          initial={{
            opacity: 0,
            y: 35,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.8,
            delay: 0.6,
          }}
          className="mt-20 grid w-full max-w-4xl gap-3 sm:mt-28 sm:gap-4 md:grid-cols-3"
        >

          <FeatureCard
            number="01"
            title="Smart Discovery"
            text="Hybrid semantic and keyword retrieval finds relevant fashion products."
          />

          <FeatureCard
            number="02"
            title="Size Verification"
            text="Available sizes are checked against real product variants."
          />

          <FeatureCard
            number="03"
            title="AI Outfit Builder"
            text="Build complete outfits based on style, occasion and budget."
          />

        </motion.div>

      </section>
    </main>
  )
}


function FeatureCard({
  number,
  title,
  text,
}) {
  return (
    <motion.div
      whileHover={{
        y: -6,
      }}
      transition={{
        duration: 0.25,
      }}
      className="group rounded-2xl border border-white/[0.12] bg-white/[0.055] p-6 text-left backdrop-blur-xl"
    >

      <span className="text-xs text-white/55">
        {number}
      </span>

      <h3 className="mt-8 text-base font-medium">
        {title}
      </h3>

      <p className="mt-2 text-sm leading-6 text-white/55">
        {text}
      </p>

    </motion.div>
  )
}


export default App
