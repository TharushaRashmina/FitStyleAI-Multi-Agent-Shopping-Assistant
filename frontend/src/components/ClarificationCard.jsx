import { motion } from "motion/react"

import {
  ArrowRight,
  CircleHelp,
} from "lucide-react"


function ClarificationCard({
  clarification,
  loading,
  onSelect,
}) {
  const options =
    clarification?.options || []


  return (
    <motion.div
      initial={{
        opacity: 0,
        y: 12,
        scale: 0.98,
      }}
      animate={{
        opacity: 1,
        y: 0,
        scale: 1,
      }}
      transition={{
        duration: 0.35,
      }}
      className="mx-auto mt-5 max-w-xl rounded-2xl border border-violet-400/15 bg-violet-400/[0.05] p-5 text-left"
    >

      {/* Clarification heading */}
      <div className="flex items-center gap-2 text-violet-200">
        <CircleHelp size={17} />

        <span className="text-sm font-medium">
          One more detail
        </span>
      </div>


      {/* Question from backend */}
      <h3 className="mt-4 text-base font-medium text-white">
        {clarification.question}
      </h3>


      {/* Why the system is asking */}
      {clarification.reason && (
        <p className="mt-2 text-sm leading-6 text-white/40">
          {clarification.reason}
        </p>
      )}


      {/* Options are rendered dynamically from backend */}
      {options.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">

          {options.map((option) => (

            <button
              key={option}
              type="button"
              disabled={loading}
              onClick={() =>
                onSelect(option)
              }
              className="group flex min-h-11 items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 text-sm capitalize text-white/70 transition hover:border-violet-400/30 hover:bg-violet-400/[0.08] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {option}

              <ArrowRight
                size={14}
                className="transition group-hover:translate-x-0.5"
              />
            </button>

          ))}

        </div>
      )}

    </motion.div>
  )
}


export default ClarificationCard
