import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { MotionConfig } from 'motion/react'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Notifications from './pages/Notifications'
import Profile from './pages/Profile'
import Recommendations from './pages/Recommendations'
import Register from './pages/Register'
import SavedSchemes from './pages/SavedSchemes'
import SchemeDetails from './pages/SchemeDetails'
import ChatbotPage from './pages/ChatbotPage'

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <AuthProvider>
        <BrowserRouter>
          <div className="app-container min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-amber-100 selection:text-amber-900">
            {/* Skip to Main Content Link for Keyboard Accessibility */}
            <a
              href="#main-content"
              className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-amber-500 focus:text-slate-950 focus:font-bold focus:rounded-md focus:shadow-xl focus:outline-none focus:ring-2 focus:ring-slate-900"
            >
              Skip to main content
            </a>

            <Navbar />

            <main
              id="main-content"
              tabIndex={-1}
              className="main-content flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 focus:outline-none"
            >
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected Citizen Routes */}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <Profile />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/recommendations"
                  element={
                    <ProtectedRoute>
                      <Recommendations />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/chatbot"
                  element={
                    <ProtectedRoute>
                      <ChatbotPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/saved-schemes"
                  element={
                    <ProtectedRoute>
                      <SavedSchemes />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notifications"
                  element={
                    <ProtectedRoute>
                      <Notifications />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/schemes/:id"
                  element={
                    <ProtectedRoute>
                      <SchemeDetails />
                    </ProtectedRoute>
                  }
                />

                {/* Default Redirects */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </main>

            <Footer />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </MotionConfig>
  )
}
