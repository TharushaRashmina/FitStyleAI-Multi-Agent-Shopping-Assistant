import { useState } from "react"
import { motion } from "motion/react"

import {
  CheckCircle2,
  ExternalLink,
  Shirt,
} from "lucide-react"


function ProductCard({ product, index }) {
  const [imageError, setImageError] = useState(false)

  // Format product price for the UI.
  const formattedPrice =
    typeof product.price === "number"
      ? product.price.toLocaleString()
      : product.price


  return (
    <motion.article
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
        delay: index * 0.06,
      }}
      whileHover={{
        y: -6,
      }}
      className="group overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.035] text-left backdrop-blur-xl"
    >

      {/* Product image */}
      <div className="relative aspect-[4/5] overflow-hidden bg-white/[0.04]">

        {product.image_url && !imageError ? (
          <img
            src={product.image_url}
            alt={product.product_name}
            onError={() => setImageError(true)}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.04]"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-white/20">
            <Shirt size={42} />
          </div>
        )}


        {/* Availability badge */}
        {product.available && (
          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full border border-white/10 bg-black/60 px-3 py-1.5 text-xs text-white/80 backdrop-blur-md">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Available
          </div>
        )}

      </div>


      {/* Product information */}
      <div className="p-5">

        <div className="flex flex-wrap gap-2">

          {product.category && (
            <span className="rounded-full bg-white/[0.06] px-2.5 py-1 text-[11px] capitalize text-white/45">
              {product.category}
            </span>
          )}

          {product.style && (
            <span className="rounded-full bg-white/[0.06] px-2.5 py-1 text-[11px] capitalize text-white/45">
              {product.style}
            </span>
          )}

        </div>


        <h3 className="mt-4 min-h-[48px] text-base font-medium leading-6 text-white">
          {product.product_name}
        </h3>


        <p className="mt-3 text-lg font-semibold">
          Rs. {formattedPrice}
        </p>


        {/* Size information */}
        {product.available_sizes?.length > 0 && (
          <div className="mt-4">

            <p className="mb-2 text-xs text-white/35">
              Available sizes
            </p>

            <div className="flex flex-wrap gap-1.5">

              {product.available_sizes.map((size) => (
                <span
                  key={size}
                  className={`flex h-8 min-w-8 items-center justify-center rounded-lg border px-2 text-xs ${
                    size === product.requested_size
                      ? "border-violet-400/50 bg-violet-400/10 text-violet-200"
                      : "border-white/10 bg-white/[0.03] text-white/50"
                  }`}
                >
                  {size}
                </span>
              ))}

            </div>

          </div>
        )}


        {/* Verified requested size */}
        {product.requested_size &&
          product.size_available === true && (

          <div className="mt-4 flex items-center gap-2 text-xs text-emerald-400">
            <CheckCircle2 size={15} />

            Size {product.requested_size} available
          </div>
        )}


        {/* Product link */}
        {product.product_url && (
          <a
            href={product.product_url}
            target="_blank"
            rel="noreferrer"
            className="mt-5 flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-white/10 bg-white text-sm font-medium text-black transition hover:bg-white/90"
          >
            View Product
            <ExternalLink size={15} />
          </a>
        )}

      </div>

    </motion.article>
  )
}


export default ProductCard