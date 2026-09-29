import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "motion/react"

import {
  BrainCircuit,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react"


const processingSteps = [
  {
    label: "Understanding your request",
    icon: BrainCircuit,
  },
  {
    label: "Searching relevant fashion products",
    icon: Search,
  },
  {
    label: "Checking constraints and availability",
    icon: ShieldCheck,
  },
  {
    label: "Preparing your recommendation",
    icon: Sparkles,
  },
]


function AgentProcessing() {
  const [activeStep, setActiveStep] = useState(0)


  useEffect(() => {
    // This is a frontend loading animation only.
    // It does not represent live backend telemetry.
    const timer = setInterval(() => {
      setActiveStep((current) =>
        (current + 1) %
        processingSteps.length
      )
    }, 1200)

    return () => clearInterval(timer)
  }, [])


  const ActiveIcon =
    processingSteps[activeStep].icon


  return (
    <motion.div
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
        y: -6,
      }}
      transition={{
        duration: 0.3,
      }}
      className="mx-auto mt-5 max-w-xl rounded-2xl border border-violet-400/15 bg-violet-400/[0.045] p-5 text-left backdrop-blur-xl"
    >

      {/* Header */}
      <div className="flex items-center justify-between gap-4">

        <div className="flex items-center gap-3">

          <motion.div
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "linear",
            }}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-violet-300/15 bg-violet-400/10 text-violet-200"
          >
            <Sparkles size={17} />
          </motion.div>

          <div>
            <p className="text-sm font-medium text-white">
              FitStyle AI is working
            </p>

            <p className="mt-0.5 text-xs text-white/35">
              Multi-agent recommendation processing
            </p>
          </div>

        </div>


        <div className="flex items-center gap-1.5">

          {[0, 1, 2].map((dot) => (
            <motion.span
              key={dot}
              animate={{
                opacity: [0.25, 1, 0.25],
                y: [0, -3, 0],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: dot * 0.18,
              }}
              className="h-1.5 w-1.5 rounded-full bg-violet-300"
            />
          ))}

        </div>

      </div>


      {/* Current animated step */}
      <div className="mt-5 overflow-hidden rounded-xl border border-white/[0.07] bg-black/20 px-4 py-3">

        <AnimatePresence mode="wait">

          <motion.div
            key={activeStep}
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
              y: -8,
            }}
            transition={{
              duration: 0.25,
            }}
            className="flex items-center gap-3"
          >

            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.05] text-violet-200">
              <ActiveIcon size={16} />
            </div>

            <span className="text-sm text-white/60">
              {processingSteps[activeStep].label}
            </span>

          </motion.div>

        </AnimatePresence>

      </div>


      {/* Step indicators */}
      <div className="mt-4 grid grid-cols-4 gap-2">

        {processingSteps.map((step, index) => (

          <div
            key={step.label}
            className="h-1 overflow-hidden rounded-full bg-white/[0.06]"
          >
            <motion.div
              animate={{
                width:
                  index <= activeStep
                    ? "100%"
                    : "0%",
                opacity:
                  index === activeStep
                    ? 1
                    : 0.45,
              }}
              transition={{
                duration: 0.3,
              }}
              className="h-full rounded-full bg-violet-300"
            />
          </div>

        ))}

      </div>

    </motion.div>
  )
}


export default AgentProcessing
