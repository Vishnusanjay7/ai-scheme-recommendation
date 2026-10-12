import { Landmark, ExternalLink, ShieldCheck, Cpu, ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Footer() {
  const currentYear = new Date().getFullYear()
  const { isAuthenticated } = useAuth()

  return (
    <footer className="portal-footer bg-[#0a2342] text-slate-300 border-t border-slate-800 mt-auto transition-colors duration-200">
      <div className="footer-inner max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-10 text-left">
          {/* Brand & Purpose Column */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-400/40 text-amber-400">
                <Landmark className="w-5 h-5 text-amber-400" aria-hidden="true" />
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                  SchemeSetu
                  <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    Prototype
                  </span>
                </span>
                <p className="text-[11px] text-blue-200 tracking-wider font-medium">
                  Government Scheme Discovery Portal
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-300/90 leading-relaxed">
              SchemeSetu is an academic capstone prototype developed for public welfare scheme discovery.
              It pairs deterministic statutory eligibility evaluation with multilingual citizen assistance.
            </p>

            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700/60 text-[11px] text-amber-300/90">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" aria-hidden="true" />
              <span>Independent Academic Project</span>
            </div>
          </div>

          {/* Quick Portal Navigation */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
              Citizen Portal
            </h3>
            <ul className="space-y-2 text-xs">
              <li>
                <Link
                  to={isAuthenticated ? '/dashboard' : '/login'}
                  className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1.5 text-slate-300"
                >
                  <span>Dashboard</span>
                </Link>
              </li>
              <li>
                <Link
                  to={isAuthenticated ? '/recommendations' : '/login'}
                  className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1.5 text-slate-300"
                >
                  <span>Find Schemes</span>
                </Link>
              </li>
              <li>
                <Link
                  to={isAuthenticated ? '/saved-schemes' : '/login'}
                  className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1.5 text-slate-300"
                >
                  <span>Saved Schemes</span>
                </Link>
              </li>
              <li>
                <Link
                  to={isAuthenticated ? '/chatbot' : '/login'}
                  className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1.5 text-slate-300"
                >
                  <span>Scheme Assistant</span>
                </Link>
              </li>
              <li>
                <Link
                  to={isAuthenticated ? '/notifications' : '/login'}
                  className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1.5 text-slate-300"
                >
                  <span>Notifications</span>
                </Link>
              </li>
              <li>
                <Link
                  to={isAuthenticated ? '/profile' : '/login'}
                  className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1.5 text-slate-300"
                >
                  <span>Citizen Profile</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Official Portals Reference Links */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
              Official Portals
              <ExternalLink className="w-3 h-3 text-slate-400" aria-hidden="true" />
            </h3>
            <p className="text-[11px] text-slate-400 leading-snug">
              Official Indian government repositories for statutory verification and direct application:
            </p>
            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href="https://www.india.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-300 transition-colors duration-150 inline-flex items-center gap-1 text-slate-300 group"
                >
                  <span>National Portal of India</span>
                  <ArrowUpRight className="w-3 h-3 text-slate-500 group-hover:text-amber-300 transition-colors" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.myscheme.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-300 transition-colors duration-150 inline-flex items-center gap-1 text-slate-300 group"
                >
                  <span>myScheme Portal</span>
                  <ArrowUpRight className="w-3 h-3 text-slate-500 group-hover:text-amber-300 transition-colors" />
                </a>
              </li>
              <li>
                <a
                  href="https://dbtbharat.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-300 transition-colors duration-150 inline-flex items-center gap-1 text-slate-300 group"
                >
                  <span>Direct Benefit Transfer (DBT)</span>
                  <ArrowUpRight className="w-3 h-3 text-slate-500 group-hover:text-amber-300 transition-colors" />
                </a>
              </li>
              <li>
                <a
                  href="https://digitalindia.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-300 transition-colors duration-150 inline-flex items-center gap-1 text-slate-300 group"
                >
                  <span>Digital India</span>
                  <ArrowUpRight className="w-3 h-3 text-slate-500 group-hover:text-amber-300 transition-colors" />
                </a>
              </li>
            </ul>
          </div>

          {/* Platform Invariants & Verification */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-100 flex items-center gap-1.5">
              Engine & Standards
            </h3>
            <div className="space-y-2.5 text-xs text-slate-300/90 leading-relaxed">
              <div className="flex items-start gap-2">
                <Cpu className="w-4 h-4 text-sky-400 mt-0.5 flex-shrink-0" aria-hidden="true" />
                <div>
                  <span className="font-semibold text-white">Deterministic Rules: </span>
                  Eligibility is calculated via rule-based criteria matching rather than probabilistic inference.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" aria-hidden="true" />
                <div>
                  <span className="font-semibold text-white">Verification Mandate: </span>
                  Citizens must submit applications through official ministry channels.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Sub-bar */}
        <div className="border-t border-slate-800/80 mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-400">
          <p>
            © {currentYear} SchemeSetu — AI-Powered Government Scheme Recommendation System. Academic Project Prototype.
          </p>
          <p className="text-center sm:text-right max-w-xl text-slate-400">
            Disclaimer: SchemeSetu is an educational research prototype and is not an official portal of the Government of India or any state government.
          </p>
        </div>
      </div>
    </footer>
  )
}
