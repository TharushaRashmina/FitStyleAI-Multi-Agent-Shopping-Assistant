import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"

import {
  AlertCircle,
  ArrowRight,
  LockKeyhole,
  Mail,
  Shirt,
  Sparkles,
  UserRound,
} from "lucide-react"

import {
  getApiErrorMessage,
  loginUser,
  registerUser,
} from "../services/api"


function AuthPage({
  onAuthenticated,
  initialMessage = "",
}) {
  const [mode, setMode] = useState("login")

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("")

  const [loading, setLoading] =
    useState(false)

  const [error, setError] =
    useState("")

  const [message, setMessage] =
    useState(initialMessage)


  // -------------------------------------------------
  // Switch between login and register
  // -------------------------------------------------

  const switchMode = (
    nextMode
  ) => {
    setMode(nextMode)
    setError("")
    setMessage("")

    // Do not keep password values when
    // switching between authentication forms.
    setPassword("")
    setConfirmPassword("")
  }


  // -------------------------------------------------
  // Submit login or registration
  // -------------------------------------------------

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault()

    setError("")
    setMessage("")


    const cleanedEmail =
      email.trim().toLowerCase()


    if (!cleanedEmail) {
      setError(
        "Please enter your email address."
      )
      return
    }


    if (!password) {
      setError(
        "Please enter your password."
      )
      return
    }


    if (mode === "register") {

      const cleanedName =
        name.trim()


      if (cleanedName.length < 2) {
        setError(
          "Please enter your name."
        )
        return
      }


      if (password.length < 8) {
        setError(
          "Password must contain at least 8 characters."
        )
        return
      }


      if (
        password !==
        confirmPassword
      ) {
        setError(
          "Passwords do not match."
        )
        return
      }
    }


    try {
      setLoading(true)


      // ---------------------------------------------
      // Register
      // ---------------------------------------------

      if (mode === "register") {

        await registerUser({
          name: name.trim(),
          email: cleanedEmail,
          password,
        })


        // Registration is immediately followed by
        // login so the new user enters FitStyle AI
        // without manually signing in again.
        const loginData =
          await loginUser({
            email: cleanedEmail,
            password,
          })


        onAuthenticated(
          loginData.user
        )

        return
      }


      // ---------------------------------------------
      // Login
      // ---------------------------------------------

      const loginData =
        await loginUser({
          email: cleanedEmail,
          password,
        })


      onAuthenticated(
        loginData.user
      )

    } catch (err) {

      setError(
        getApiErrorMessage(
          err,
          mode === "register"
            ? "Account creation failed. Please try again."
            : "Login failed. Please try again."
        )
      )

    } finally {
      setLoading(false)
    }
  }


  return (
    <main className="relative min-h-screen overflow-hidden bg-[#08090c] text-white">

      {/* Background */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="blob blob-one" />
        <div className="blob blob-two" />
      </div>


      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10 sm:px-6">

        <motion.div
          initial={{
            opacity: 0,
            y: 18,
            scale: 0.985,
          }}
          animate={{
            opacity: 1,
            y: 0,
            scale: 1,
          }}
          transition={{
            duration: 0.5,
          }}
          className="w-full max-w-md"
        >

          {/* Brand */}
          <div className="mb-8 flex items-center justify-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-black shadow-[0_12px_40px_rgba(255,255,255,0.08)]">
              <Shirt size={21} />
            </div>

            <div className="text-left">
              <h1 className="text-lg font-semibold tracking-tight">
                FitStyle AI
              </h1>

              <p className="text-xs text-white/35">
                Intelligent Fashion Discovery
              </p>
            </div>

          </div>


          {/* Authentication card */}
          <div className="rounded-[26px] border border-white/[0.09] bg-white/[0.045] p-5 shadow-[0_35px_120px_rgba(0,0,0,0.45)] backdrop-blur-2xl sm:p-7">

            <div className="mb-7">

              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-violet-400/10 text-violet-200">
                <Sparkles size={18} />
              </div>


              <AnimatePresence mode="wait">

                <motion.div
                  key={mode}
                  initial={{
                    opacity: 0,
                    y: 5,
                  }}
                  animate={{
                    opacity: 1,
                    y: 0,
                  }}
                  exit={{
                    opacity: 0,
                    y: -5,
                  }}
                  transition={{
                    duration: 0.2,
                  }}
                >

                  <h2 className="text-2xl font-semibold tracking-[-0.03em]">
                    {mode === "login"
                      ? "Welcome back"
                      : "Create your account"}
                  </h2>

                  <p className="mt-2 text-sm leading-6 text-white/40">
                    {mode === "login"
                      ? "Sign in to continue to your personalized FitStyle AI experience."
                      : "Create a simple account to access protected fashion recommendations."}
                  </p>

                </motion.div>

              </AnimatePresence>

            </div>


            {/* Session message */}
            {message && (
              <div className="mb-4 rounded-xl border border-amber-300/10 bg-amber-300/[0.045] px-4 py-3 text-sm leading-6 text-amber-100/65">
                {message}
              </div>
            )}


            {/* Error */}
            {error && (
              <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-red-300/10 bg-red-300/[0.045] px-4 py-3">

                <AlertCircle
                  size={16}
                  className="mt-0.5 shrink-0 text-red-200/80"
                />

                <p className="text-sm leading-6 text-red-100/65">
                  {error}
                </p>

              </div>
            )}


            <form
              onSubmit={handleSubmit}
              className="space-y-4"
            >

              {/* Name - registration only */}
              <AnimatePresence initial={false}>

                {mode === "register" && (
                  <motion.div
                    initial={{
                      opacity: 0,
                      height: 0,
                    }}
                    animate={{
                      opacity: 1,
                      height: "auto",
                    }}
                    exit={{
                      opacity: 0,
                      height: 0,
                    }}
                    transition={{
                      duration: 0.22,
                    }}
                  >
                    <label className="mb-2 block text-xs font-medium text-white/45">
                      Name
                    </label>

                    <div className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-black/20 px-4 transition focus-within:border-violet-300/30 focus-within:bg-black/30">

                      <UserRound
                        size={17}
                        className="shrink-0 text-white/25"
                      />

                      <input
                        type="text"
                        value={name}
                        onChange={(event) =>
                          setName(
                            event.target.value
                          )
                        }
                        autoComplete="name"
                        disabled={loading}
                        placeholder="Your name"
                        className="min-h-12 w-full bg-transparent text-sm text-white outline-none placeholder:text-white/20"
                      />

                    </div>
                  </motion.div>
                )}

              </AnimatePresence>


              {/* Email */}
              <div>

                <label className="mb-2 block text-xs font-medium text-white/45">
                  Email
                </label>

                <div className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-black/20 px-4 transition focus-within:border-violet-300/30 focus-within:bg-black/30">

                  <Mail
                    size={17}
                    className="shrink-0 text-white/25"
                  />

                  <input
                    type="email"
                    value={email}
                    onChange={(event) =>
                      setEmail(
                        event.target.value
                      )
                    }
                    autoComplete="email"
                    disabled={loading}
                    placeholder="you@example.com"
                    className="min-h-12 w-full bg-transparent text-sm text-white outline-none placeholder:text-white/20"
                  />

                </div>

              </div>


              {/* Password */}
              <div>

                <label className="mb-2 block text-xs font-medium text-white/45">
                  Password
                </label>

                <div className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-black/20 px-4 transition focus-within:border-violet-300/30 focus-within:bg-black/30">

                  <LockKeyhole
                    size={17}
                    className="shrink-0 text-white/25"
                  />

                  <input
                    type="password"
                    value={password}
                    onChange={(event) =>
                      setPassword(
                        event.target.value
                      )
                    }
                    autoComplete={
                      mode === "login"
                        ? "current-password"
                        : "new-password"
                    }
                    disabled={loading}
                    placeholder="Minimum 8 characters"
                    className="min-h-12 w-full bg-transparent text-sm text-white outline-none placeholder:text-white/20"
                  />

                </div>

              </div>


              {/* Confirm password - registration only */}
              <AnimatePresence initial={false}>

                {mode === "register" && (
                  <motion.div
                    initial={{
                      opacity: 0,
                      height: 0,
                    }}
                    animate={{
                      opacity: 1,
                      height: "auto",
                    }}
                    exit={{
                      opacity: 0,
                      height: 0,
                    }}
                    transition={{
                      duration: 0.22,
                    }}
                  >

                    <label className="mb-2 block text-xs font-medium text-white/45">
                      Confirm password
                    </label>

                    <div className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-black/20 px-4 transition focus-within:border-violet-300/30 focus-within:bg-black/30">

                      <LockKeyhole
                        size={17}
                        className="shrink-0 text-white/25"
                      />

                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(event) =>
                          setConfirmPassword(
                            event.target.value
                          )
                        }
                        autoComplete="new-password"
                        disabled={loading}
                        placeholder="Enter password again"
                        className="min-h-12 w-full bg-transparent text-sm text-white outline-none placeholder:text-white/20"
                      />

                    </div>

                  </motion.div>
                )}

              </AnimatePresence>


              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="mt-2 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-60"
              >

                {loading
                  ? (
                    <>
                      <span className="loading-spinner" />

                      {mode === "login"
                        ? "Signing in..."
                        : "Creating account..."}
                    </>
                  )
                  : (
                    <>
                      {mode === "login"
                        ? "Sign in"
                        : "Create account"}

                      <ArrowRight size={16} />
                    </>
                  )}

              </button>

            </form>


            {/* Mode switch */}
            <div className="mt-6 border-t border-white/[0.06] pt-5 text-center">

              <p className="text-sm text-white/35">

                {mode === "login"
                  ? "Don't have an account?"
                  : "Already have an account?"}

                {" "}

                <button
                  type="button"
                  disabled={loading}
                  onClick={() =>
                    switchMode(
                      mode === "login"
                        ? "register"
                        : "login"
                    )
                  }
                  className="font-medium text-violet-200 transition hover:text-white disabled:opacity-50"
                >
                  {mode === "login"
                    ? "Create account"
                    : "Sign in"}
                </button>

              </p>

            </div>

          </div>


          <p className="mt-5 text-center text-xs leading-5 text-white/25">
            Passwords are securely hashed and the authentication
            token is stored in an HttpOnly cookie.
          </p>

        </motion.div>

      </div>

    </main>
  )
}


export default AuthPage
