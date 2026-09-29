import axios from "axios"


// -------------------------------------------------
// Shared Axios client
// -------------------------------------------------
//
// IMPORTANT:
// Use localhost for BOTH the React frontend and
// FastAPI backend during local development.
//
// Frontend:
//   http://localhost:5173
//
// Backend:
//   http://localhost:8000
//
// This keeps the HttpOnly authentication cookie
// working correctly with SameSite="lax".
//

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    "http://localhost:8000",

  // Required so the browser sends/receives the
  // HttpOnly JWT cookie with API requests.
  withCredentials: true,

  headers: {
    "Content-Type": "application/json",
  },
})


// -------------------------------------------------
// Helper: readable backend error message
// -------------------------------------------------

export const getApiErrorMessage = (
  error,
  fallbackMessage =
    "Something went wrong. Please try again."
) => {
  return (
    error?.response?.data?.error?.message ||
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    fallbackMessage
  )
}


// -------------------------------------------------
// Authentication API
// -------------------------------------------------

export const registerUser = async ({
  name,
  email,
  password,
}) => {
  const response = await api.post(
    "/auth/register",
    {
      name,
      email,
      password,
    }
  )

  return response.data
}


export const loginUser = async ({
  email,
  password,
}) => {
  const response = await api.post(
    "/auth/login",
    {
      email,
      password,
    }
  )

  return response.data
}


export const getCurrentUser = async () => {
  const response = await api.get(
    "/auth/me"
  )

  return response.data
}


export const logoutUser = async () => {
  const response = await api.post(
    "/auth/logout"
  )

  return response.data
}


// -------------------------------------------------
// FitStyle AI Recommendation API
// -------------------------------------------------

export const getRecommendation = async (
  query
) => {
  const response = await api.post(
    "/recommend",
    {
      query,
    }
  )

  return response.data
}


export default api
