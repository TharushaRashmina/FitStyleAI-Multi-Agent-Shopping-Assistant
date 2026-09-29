import { motion } from "motion/react"

import {
  CheckCircle2,
  ExternalLink,
  Sparkles,
  Wallet,
} from "lucide-react"


function OutfitRecommendation({ result }) {
  const products = result.selected_products || []


  return (
    <motion.section
      initial={{
        opacity: 0,
        y: 35,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        duration: 0.6,
      }}
      className="mt-24 w-full max-w-7xl"
    >

      {/* Header */}
      <div className="mb-8 text-left">

        <div className="flex items-center gap-2 text-sm text-violet-300">
          <Sparkles size={16} />

          AI Outfit Recommendation
        </div>

        <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
          Your complete look
        </h2>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-white/40">
          FitStyle AI selected these products based on your
          occasion, style, budget, size and product availability.
        </p>

      </div>


      {/* Outfit products */}
      <div className="grid gap-5 md:grid-cols-3">

        {products.map((product, index) => (

          <motion.article
            key={product.product_id}
            initial={{
              opacity: 0,
              y: 30,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.45,
              delay: index * 0.1,
            }}
            whileHover={{
              y: -6,
            }}
            className="group overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.035] text-left"
          >

            {/* Product image */}
            <div className="relative aspect-[4/5] overflow-hidden bg-white/[0.04]">

              {product.image_url && (
                <img
                  src={product.image_url}
                  alt={product.product_name}
                  className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.04]"
                />
              )}


              {/* Outfit role */}
              <div className="absolute left-3 top-3 rounded-full border border-white/10 bg-black/60 px-3 py-1.5 text-xs capitalize text-white/80 backdrop-blur-md">

                {product.outfit_role}

              </div>

            </div>


            {/* Product details */}
            <div className="p-5">

              <h3 className="text-base font-medium leading-6">
                {product.product_name}
              </h3>


              <p className="mt-3 text-xl font-semibold">
                Rs.{" "}
                {typeof product.price === "number"
                  ? product.price.toLocaleString()
                  : product.price}
              </p>


              {/* Requested size */}
              {product.requested_size &&
                product.size_available === true && (

                <div className="mt-4 flex items-center gap-2 text-xs text-emerald-400">

                  <CheckCircle2 size={15} />

                  Size {product.requested_size} available

                </div>
              )}


              {/* Available sizes */}
              {product.available_sizes?.length > 0 && (

                <div className="mt-4">

                  <p className="mb-2 text-xs text-white/35">
                    Available sizes
                  </p>

                  <div className="flex flex-wrap gap-1.5">

                    {product.available_sizes.map((size) => (

                      <span
                        key={size}
                        className={`rounded-lg border px-2.5 py-1.5 text-xs ${
                          size === product.requested_size
                            ? "border-violet-400/50 bg-violet-400/10 text-violet-200"
                            : "border-white/10 text-white/45"
                        }`}
                      >
                        {size}
                      </span>

                    ))}

                  </div>

                </div>
              )}


              {/* Product link */}
              {product.product_url && (

                <a
                  href={product.product_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-5 flex min-h-11 items-center justify-center gap-2 rounded-xl bg-white text-sm font-medium text-black transition hover:bg-white/90"
                >
                  View Product

                  <ExternalLink size={15} />
                </a>

              )}

            </div>

          </motion.article>

        ))}

      </div>


      {/* Outfit summary */}
      <div className="mt-8 grid gap-5 lg:grid-cols-[1fr_320px]">

        {/* AI explanation */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.035] p-6 text-left">

          <div className="flex items-center gap-2 text-sm text-violet-300">
            <Sparkles size={16} />

            Why this outfit?
          </div>

          <p className="mt-4 text-sm leading-7 text-white/55">
            {result.explanation}
          </p>

        </div>


        {/* Budget summary */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.035] p-6 text-left">

          <div className="flex items-center gap-2 text-sm text-white/50">

            <Wallet size={17} />

            Budget Summary

          </div>


          <div className="mt-6 flex items-end justify-between">

            <div>
              <p className="text-xs text-white/35">
                Total outfit
              </p>

              <p className="mt-1 text-2xl font-semibold">
                Rs.{" "}
                {result.total_price?.toLocaleString()}
              </p>
            </div>


            {result.within_budget === true && (

              <div className="flex items-center gap-1.5 text-xs text-emerald-400">

                <CheckCircle2 size={15} />

                Within budget

              </div>

            )}

          </div>


          {result.budget && (

            <div className="mt-5 border-t border-white/[0.07] pt-4">

              <div className="flex justify-between text-xs">

                <span className="text-white/35">
                  Your budget
                </span>

                <span className="text-white/70">
                  Rs. {result.budget.toLocaleString()}
                </span>

              </div>

            </div>

          )}

        </div>

      </div>

    </motion.section>
  )
}


export default OutfitRecommendation