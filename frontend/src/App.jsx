import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
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
    <AuthProvider>
      <BrowserRouter>
        <div className="app-container">
          <Navbar />
          <main className="main-content">
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
          <footer className="portal-footer">
            <div className="footer-inner">
              <p>
                SchemeSetu — AI-Powered Government Scheme Recommendation System. Official Citizen Portal.
              </p>
              <p className="text-muted mt-1">
                Deterministic statutory eligibility verified server-side. Applications must be submitted on
                official government portals.
              </p>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  )
}
