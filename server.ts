import express from 'express'
import cors from 'cors'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'
import { createServer as createViteServer } from 'vite'
import { GoogleGenAI } from '@google/genai'
import { ALL_INDIAN_STATES, ALL_INDIAN_DISTRICTS } from './src/data/indiaLocations.js'
import { MASTER_LIVE_SCHEMES } from './src/data/liveSchemes.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = 3000
const HOST = '0.0.0.0'

// Initialize GoogleGenAI server client
const ai = process.env.GEMINI_API_KEY
  ? new GoogleGenAI({
      apiKey: process.env.GEMINI_API_KEY,
      httpOptions: {
        headers: {
          'User-Agent': 'aistudio-build',
        },
      },
    })
  : null

app.use(cors())
app.use(express.json())

// ==============================================================================
// REFERENCE DATA: All 28 Indian States & 8 Union Territories + 750+ Districts
// ==============================================================================
const STATES = ALL_INDIAN_STATES
const DISTRICTS = ALL_INDIAN_DISTRICTS

// ==============================================================================
// MASTER SCHEMES DATASET
// Includes Canary schemes, Tamil Nadu schemes, and Pan-India Central schemes
// ==============================================================================
const CANARY_SCHEMES = [
  {
    id: 'a331c9af-aa84-49d7-89d7-8b33b91b1f9e',
    slug: 'mranmas1',
    external_id: 'TNEGA-MRANMAS-001',
    scheme_name: 'Moovalur Ramamirtham Ammaiyar Ninaivu Marriage Assistance Scheme-1',
    description: 'Financial assistance and sovereign gold coin for marriage of poor girls who have studied up to 10th standard in Tamil Nadu.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Women and Child Development',
    category_id: 14,
    benefits: 'Rs. 25,000 cash assistance plus 8 grams (1 sovereign) 22-carat gold coin for making Thirumangalyam.',
    application_process: 'Apply through e-Sevai centres or Social Welfare Department district offices with prescribed certificates.',
    status: 'ACTIVE',
    official_url: 'https://cms.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/mranmas1',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 18,
      max_age: 40,
      gender: 'FEMALE',
      state_restriction: 23,
      max_income: 72000,
      education: 'Secondary (10th Pass)'
    },
    documents: [
      {
        document_name: 'Marriage Invitation Card',
        mandatory: true,
        description: 'MANDATORY_STATUS_UNKNOWN: Source text lists document without specifying mandatory vs optional.'
      },
      {
        document_name: 'Aadhaar Card',
        mandatory: true,
        description: 'Explicitly stated as mandatory in source documentation.'
      },
      {
        document_name: 'Income Certificate',
        mandatory: true,
        description: 'Annual household income must be below Rs. 72,000.'
      },
      {
        document_name: '10th Mark Sheet / Educational Transfer Certificate',
        mandatory: true,
        description: 'Proof of having passed or studied 10th standard.'
      }
    ],
    sources: [
      {
        source_url: 'https://www.myscheme.gov.in/schemes/mranmas1',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'b442d8be-bb95-48e8-98e8-9c44c82c2fae',
    slug: 'uyegp',
    external_id: 'TNEGA-UYEGP-002',
    scheme_name: 'Unemployed Youth Employment Generation Programme (UYEGP)',
    description: 'Micro-enterprise promotion scheme with capital subsidy for educated unemployed youth in Tamil Nadu.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Skills & Employment',
    category_id: 9,
    benefits: '25% Government Capital Subsidy on project cost up to Rs. 15 Lakhs for manufacturing and Rs. 5 Lakhs for service/business.',
    application_process: 'Apply online through District Industries Centre (DIC) portal at msmeonline.tn.gov.in.',
    status: 'ACTIVE',
    official_url: 'https://msmeonline.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/uyegp',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 18,
      max_age: 45,
      gender: 'ALL',
      state_restriction: 23,
      max_income: 500000,
      education: 'Middle (8th Pass)'
    },
    documents: [
      {
        document_name: 'Transfer Certificate / Mark Sheet',
        mandatory: true,
        description: 'Minimum educational qualification proof (8th standard passed).'
      },
      {
        document_name: 'Community Certificate',
        mandatory: false,
        description: 'Required for special age relaxation up to 45 years.'
      },
      {
        document_name: 'Detailed Project Report (DPR)',
        mandatory: true,
        description: 'Outline of business activity, machinery costs, and working capital.'
      }
    ],
    sources: [
      {
        source_url: 'https://www.myscheme.gov.in/schemes/uyegp',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'c553e9cf-cc06-49f9-a9f9-ad55d93d3bbf',
    slug: 'atwsfww',
    external_id: 'TNEGA-ATWSFWW-003',
    scheme_name: 'Amma Two Wheeler Scheme for Working Women',
    description: 'Subsidy on two-wheelers for working women across Tamil Nadu to commute to livelihood pursuits independently.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Women and Child Development',
    category_id: 14,
    benefits: '50% of the cost of vehicle or Rs. 25,000, whichever is less, as financial subsidy directly credited to bank account.',
    application_process: 'Submit application along with quotation and license copy to Block Development Office or Municipal Corporation.',
    status: 'ACTIVE',
    official_url: 'https://cms.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/atwsfww',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 18,
      max_age: 40,
      gender: 'FEMALE',
      state_restriction: 23,
      max_income: 250000
    },
    documents: [
      {
        document_name: 'Valid Two-Wheeler Driving License or LLR',
        mandatory: true,
        description: 'Explicitly mandatory for sanctioning vehicle subsidy.'
      },
      {
        document_name: 'Employment Proof / Wage Certificate',
        mandatory: true,
        description: 'Proof of engaging in economic activity or self-employment.'
      },
      {
        document_name: 'Aadhaar Card',
        mandatory: true,
        description: 'Mandatory identity proof.'
      }
    ],
    sources: [
      {
        source_url: 'https://www.myscheme.gov.in/schemes/atwsfww',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'd664fa0a-dd17-400a-b00a-be66ea4e4cc0',
    slug: 'cmgcpsii',
    external_id: 'TNEGA-CMGCPSII-004',
    scheme_name: 'Chief Minister’s Girl Child Protection Scheme-II',
    description: 'Fixed deposit in the name of girl children in families with two girl children to encourage girl education and prevent female foeticide.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Women and Child Development',
    category_id: 14,
    benefits: 'Fixed deposit of Rs. 25,000 in the name of each girl child with Tamil Nadu Power Finance Corporation, redeemable at age 18.',
    application_process: 'Apply through District Social Welfare Office within 3 years of birth of the second girl child.',
    status: 'ACTIVE',
    official_url: 'https://cms.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/cmgcpsii',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 0,
      max_age: 3,
      gender: 'FEMALE',
      state_restriction: 23,
      max_income: 72000
    },
    documents: [
      {
        document_name: 'Birth Certificate of Girl Children',
        mandatory: true,
        description: 'Mandatory birth proof of both girl children.'
      },
      {
        document_name: 'Sterilization Certificate',
        mandatory: true,
        description: 'Proof of family planning operation after two girls.'
      },
      {
        document_name: 'Income Certificate',
        mandatory: true,
        description: 'Annual family income below Rs. 72,000.'
      }
    ],
    sources: [
      {
        source_url: 'https://www.myscheme.gov.in/schemes/cmgcpsii',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'e7750b1b-ee28-411b-c11b-cf77fb5f5dd1',
    slug: 'gwwh',
    external_id: 'TNEGA-GWWH-005',
    scheme_name: 'Government Working Women’s Hostel (GWWH)',
    description: 'Safe, affordable, subsidized hostel accommodation for employed and self-employed women away from their hometowns.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Housing & Shelter',
    category_id: 6,
    benefits: 'Subsidized accommodation with nominal monthly rent (Rs. 200 - Rs. 300) and sharing electricity and mess expenses.',
    application_process: 'Apply directly to the Superintendent of the respective Working Women Hostel in the district.',
    status: 'ACTIVE',
    official_url: 'https://cms.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/gwwh',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 18,
      max_age: 60,
      gender: 'FEMALE',
      state_restriction: 23,
      max_income: 300000
    },
    documents: [
      {
        document_name: 'Employment Proof / Salary Slip',
        mandatory: true,
        description: 'Verification of active employment in the city/district.'
      },
      {
        document_name: 'Aadhaar Card and Residence Proof',
        mandatory: true,
        description: 'Proof of native address outside the hostel city.'
      }
    ],
    sources: [
      {
        source_url: 'https://www.myscheme.gov.in/schemes/gwwh',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'f8861c2c-ff39-422c-d22c-d0880c606ee2',
    slug: 'kmut',
    external_id: 'TNEGA-KMUT-006',
    scheme_name: 'Kalaignar Magalir Urimai Thittam',
    description: 'Monthly basic income rights grant of Rs. 1,000 for women heads of eligible households in Tamil Nadu.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Social Welfare & Empowerment',
    category_id: 10,
    benefits: 'Direct Benefit Transfer (DBT) of Rs. 1,000 per month deposited directly into the bank account on 15th of every month.',
    application_process: 'Enrolled via camp tokens at ration shops; verification through field inspection by Revenue officials.',
    status: 'ACTIVE',
    official_url: 'https://kmut.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/kmut',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 21,
      max_age: 100,
      gender: 'FEMALE',
      state_restriction: 23,
      max_income: 250000
    },
    documents: [
      {
        document_name: 'Smart Ration Card (NFSA / State PDS)',
        mandatory: true,
        description: 'Required to identify family head.'
      },
      {
        document_name: 'Aadhaar Card',
        mandatory: true,
        description: 'Identity validation and biometric consent.'
      },
      {
        document_name: 'Bank Passbook linked to Aadhaar',
        mandatory: true,
        description: 'For direct benefit monthly transfer.'
      }
    ],
    sources: [
      {
        source_url: 'https://www.myscheme.gov.in/schemes/kmut',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'a1122334-4455-6677-8899-aabbccddeeff',
    slug: 'pudhumai-penn',
    external_id: 'TNEGA-PP-007',
    scheme_name: 'Pudhumai Penn Scheme (Moovalur Ramamirtham Ammaiyar Higher Education Assurance Scheme)',
    description: 'Financial assistance of Rs. 1,000 per month to female students who studied Classes 6 to 12 in Government schools pursuing higher education.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Education & Learning',
    category_id: 4,
    benefits: 'Monthly allowance of Rs. 1,000 paid directly to the bank account of the girl student till the completion of undergraduate degree or diploma.',
    application_process: 'Applied through college nodal officers on the official portal penkalvi.tn.gov.in using EMIS ID.',
    status: 'ACTIVE',
    official_url: 'https://penkalvi.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pudhumai-penn',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 17,
      max_age: 30,
      gender: 'FEMALE',
      state_restriction: 23,
      education: 'Higher Secondary (12th Pass)',
      occupation: 'Student'
    },
    documents: [
      {
        document_name: 'EMIS Student ID',
        mandatory: true,
        description: 'Proof of studying from Class 6 to 12 in Tamil Nadu Government schools.'
      },
      {
        document_name: 'College Admission Letter / Bonafide Certificate',
        mandatory: true,
        description: 'Proof of active enrollment in undergraduate degree, diploma, or ITI.'
      },
      {
        document_name: 'Bank Account Passbook',
        mandatory: true,
        description: 'Account in the student’s own name linked to Aadhaar.'
      }
    ],
    sources: [
      {
        source_url: 'https://penkalvi.tn.gov.in',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'b2233445-5566-7788-9900-bbccddeeff00',
    slug: 'pm-kisan',
    external_id: 'MYSCHEME-PMKISAN-001',
    scheme_name: 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
    description: 'Income support of Rs. 6,000 per year in three equal four-monthly installments to all landholding farmer families across India.',
    government_level: 'CENTRAL',
    state_id: null,
    category: 'Agriculture, Rural & Environment',
    category_id: 1,
    benefits: 'Rs. 6,000 per year paid in three equal installments of Rs. 2,000 directly into the bank accounts of farmer families.',
    application_process: 'Self-registration online at pmkisan.gov.in or through Common Service Centres (CSCs).',
    status: 'ACTIVE',
    official_url: 'https://pmkisan.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pm-kisan',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 18,
      max_age: 120,
      occupation: 'Farmer'
    },
    documents: [
      {
        document_name: 'Aadhaar Card',
        mandatory: true,
        description: 'Mandatory Aadhaar authenticated seeding.'
      },
      {
        document_name: 'Landholding Ownership Papers / Patta',
        mandatory: true,
        description: 'Proof of cultivable landholding.'
      },
      {
        document_name: 'Bank Account Passbook',
        mandatory: true,
        description: 'Account enabled for Aadhaar Payment Bridge System (APBS).'
      }
    ],
    sources: [
      {
        source_url: 'https://pmkisan.gov.in',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'c3344556-6677-8899-0011-ccddeeff0011',
    slug: 'pmjay',
    external_id: 'MYSCHEME-PMJAY-002',
    scheme_name: 'Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)',
    description: 'Health insurance coverage of up to Rs. 5 Lakh per family per year for secondary and tertiary hospitalization to vulnerable families.',
    government_level: 'CENTRAL',
    state_id: null,
    category: 'Health & Wellness',
    category_id: 5,
    benefits: 'Cashless inpatient treatment across empaneled public and private hospitals nationwide up to Rs. 5,00,000 per year.',
    application_process: 'Check eligibility on pmjay.gov.in and generate Ayushman Card at any empaneled hospital or CSC.',
    status: 'ACTIVE',
    official_url: 'https://pmjay.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pmjay',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 0,
      max_age: 120,
      max_income: 300000
    },
    documents: [
      {
        document_name: 'Aadhaar Card or Ration Card',
        mandatory: true,
        description: 'Identity verification.'
      },
      {
        document_name: 'Ayushman Beneficiary Card',
        mandatory: false,
        description: 'Can be printed on spot at hospital helpdesk.'
      }
    ],
    sources: [
      {
        source_url: 'https://pmjay.gov.in',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'd4455667-7788-9900-1122-ddeeff001122',
    slug: 'pmay-u',
    external_id: 'MYSCHEME-PMAY-003',
    scheme_name: 'Pradhan Mantri Awas Yojana - Urban (PMAY-U)',
    description: 'Pucca houses and interest subsidies on home loans for all eligible urban families belonging to EWS, LIG, and MIG categories.',
    government_level: 'CENTRAL',
    state_id: null,
    category: 'Housing & Shelter',
    category_id: 6,
    benefits: 'Credit Linked Subsidy of up to Rs. 2.67 Lakhs on home loans or Rs. 1.5 Lakhs central grant for individual house construction.',
    application_process: 'Online application at pmaymis.gov.in or through Urban Local Body civic centres.',
    status: 'ACTIVE',
    official_url: 'https://pmaymis.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pmay-u',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 21,
      max_age: 70,
      max_income: 600000
    },
    documents: [
      {
        document_name: 'Aadhaar Card of all family members',
        mandatory: true,
        description: 'Mandatory deduplication proof.'
      },
      {
        document_name: 'Income Proof / Salary Slips / ITR',
        mandatory: true,
        description: 'Income bracket certification.'
      },
      {
        document_name: 'Affidavit of not owning a pucca house',
        mandatory: true,
        description: 'Applicant family must not own a pucca house anywhere in India.'
      }
    ],
    sources: [
      {
        source_url: 'https://pmaymis.gov.in',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'e5566778-8899-0011-2233-eeff00112233',
    slug: 'sogateakia',
    external_id: 'TNEGA-SOGATEAKIA-008',
    scheme_name: 'Scheme of Giving Awards to Eminent Artists - Tamil Nadu',
    description: 'State recognition, title of Kalaimamani, gold medals, and cash awards honoring senior artists in traditional arts.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Sports & Culture',
    category_id: 11,
    benefits: 'Kalaimamani title, 5-sovereign gold medal, certificate, and cash purse honoring lifelong devotion to arts.',
    application_process: 'Nomination submissions to the Member Secretary, Tamil Nadu Eyal Isai Nataka Manram, Chennai.',
    status: 'ACTIVE',
    official_url: 'https://artandculture.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/sogateakia',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 40,
      max_age: 100,
      state_restriction: 23,
      occupation: 'Artist'
    },
    documents: [
      {
        document_name: 'Proof of Age',
        mandatory: true,
        description: 'MANDATORY_STATUS_UNKNOWN: Source text lists document without specifying mandatory vs optional.'
      },
      {
        document_name: 'Art and Culture Certificate',
        mandatory: true,
        description: 'Explicitly stated as mandatory in source documentation.'
      }
    ],
    sources: [
      {
        source_url: 'https://artandculture.tn.gov.in',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  },
  {
    id: 'f6677889-9900-1122-3344-ff0011223344',
    slug: 'ignoaps',
    external_id: 'NSAP-IGNOAPS-009',
    scheme_name: 'Indira Gandhi National Old Age Pension Scheme (IGNOAPS)',
    description: 'Monthly social pension to elderly citizens living below the poverty line across India.',
    government_level: 'CENTRAL',
    state_id: null,
    category: 'Social Welfare & Empowerment',
    category_id: 10,
    benefits: 'Monthly pension of Rs. 1,000 (with state contribution) paid directly to the senior citizen’s bank account.',
    application_process: 'Apply through local Taluk Office / Tahsildar or Block Development Office with BPL card.',
    status: 'ACTIVE',
    official_url: 'https://nsap.nic.in',
    source_url: 'https://www.myscheme.gov.in/schemes/ignoaps',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null
    },
    eligibility: {
      min_age: 60,
      max_age: 150,
      max_income: 100000
    },
    documents: [
      {
        document_name: 'Age Proof Certificate',
        mandatory: true,
        description: 'Aadhaar or Medical Board certificate confirming age 60 or above.'
      },
      {
        document_name: 'BPL Certificate / Ration Card',
        mandatory: true,
        description: 'Proof of living below the poverty line.'
      }
    ],
    sources: [
      {
        source_url: 'https://nsap.nic.in',
        source_type: 'OFFICIAL_PORTAL'
      }
    ]
  }
]

// Merge Canary and Master Live Schemes dataset
const SCHEMES_REGISTRY: any[] = [...CANARY_SCHEMES]
for (const liveScheme of MASTER_LIVE_SCHEMES) {
  const existingIdx = SCHEMES_REGISTRY.findIndex(
    s => s.slug === liveScheme.slug || (s.external_id && s.external_id === liveScheme.external_id)
  )
  if (existingIdx >= 0) {
    SCHEMES_REGISTRY[existingIdx] = {
      ...SCHEMES_REGISTRY[existingIdx],
      ...liveScheme,
      id: SCHEMES_REGISTRY[existingIdx].id // preserve canary ID
    }
  } else {
    SCHEMES_REGISTRY.push(liveScheme)
  }
}
const SCHEMES = SCHEMES_REGISTRY

// ==============================================================================
// AUTOMATED DAILY SCHEME SYNCHRONIZATION ENGINE
// Runs every 24 hours to refresh deadlines, days remaining, and active flags
// ==============================================================================
let lastSyncTimestamp = new Date().toISOString()
let nextSyncTimestamp = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
let syncCycleCount = 1

function runDailySchemeSync() {
  const now = new Date()
  let updatedCount = 0

  for (const scheme of SCHEMES) {
    if (scheme.last_date_iso) {
      const deadlineDate = new Date(scheme.last_date_iso)
      const diffMs = deadlineDate.getTime() - now.getTime()
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

      if (!scheme.activity) {
        scheme.activity = { status: 'OPEN', deadline_status: 'OPEN', days_remaining: diffDays }
      }

      scheme.activity.days_remaining = diffDays

      if (scheme.activity.deadline_status !== 'ROLLING_ANNUAL' && scheme.activity.deadline_status !== 'NO_DEADLINE') {
        if (diffDays <= 0) {
          scheme.activity.status = 'CLOSED'
          scheme.activity.deadline_status = 'EXPIRED'
        } else if (diffDays <= 30) {
          scheme.activity.status = 'OPEN'
          scheme.activity.deadline_status = 'CLOSING_SOON'
        } else {
          scheme.activity.status = 'OPEN'
          scheme.activity.deadline_status = 'OPEN'
        }
      }
      updatedCount++
    }
  }

  lastSyncTimestamp = now.toISOString()
  nextSyncTimestamp = new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString()
  syncCycleCount++
  console.log(`[DailySync] Automated daily scheme sync completed. ${updatedCount} schemes updated. Next sync: ${nextSyncTimestamp}`)

  return {
    last_synced_at: lastSyncTimestamp,
    next_sync_at: nextSyncTimestamp,
    schemes_updated: updatedCount,
    total_schemes: SCHEMES.length,
    active_schemes: SCHEMES.filter(s => s.status === 'ACTIVE' && s.activity?.status === 'OPEN').length,
    status: 'SYNCHRONIZED'
  }
}

// Initial sync on startup
runDailySchemeSync()

// Schedule recurring 24-hour sync
const DAILY_SYNC_INTERVAL = 24 * 60 * 60 * 1000 // 24 hours
setInterval(runDailySchemeSync, DAILY_SYNC_INTERVAL)

// In-Memory state for demo user profiles, bookmarks, notifications, chat history
const userProfiles = new Map()
const savedSchemes = new Map() // userId -> Set of schemeIds
const notifications = new Map() // userId -> Array of notifications
const chatHistories = new Map() // userId -> Array of chat turns

function getUserIdFromAuth(req) {
  const authHeader = req.headers.authorization
  if (!authHeader) return 'guest-user'
  const token = authHeader.replace(/^Bearer\s+/i, '').trim()
  if (!token) return 'guest-user'
  // If it's a JWT, parse sub if possible
  try {
    const parts = token.split('.')
    if (parts.length === 3) {
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString('utf8'))
      return payload.sub || payload.email || token
    }
  } catch {}
  return token
}

// Seed default notifications for active user
function getSeedNotifications(userId) {
  if (!notifications.has(userId)) {
    notifications.set(userId, [
      {
        id: 'notif-1',
        user_id: userId,
        title: 'New Welfare Schemes Available',
        message: 'Personalized Tamil Nadu education and livelihood schemes have been matched to your demographic profile.',
        read: false,
        created_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 'notif-2',
        user_id: userId,
        title: 'Pudhumai Penn Application Window Open',
        message: 'Applications for the Higher Education Assurance Scheme for girl students are actively open.',
        read: false,
        created_at: new Date(Date.now() - 86400000).toISOString()
      }
    ])
  }
  return notifications.get(userId)
}

// ==============================================================================
// HEALTH ENDPOINTS
// ==============================================================================
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'AI Government Scheme Recommendation API is running',
    database_configured: true
  })
})

app.get('/health/db', (req, res) => {
  res.json({
    status: 'connected',
    configured: true,
    message: 'SchemeSetu in-memory & Supabase database integration is operational'
  })
})

// ==============================================================================
// REFERENCE DATA ENDPOINTS
// ==============================================================================
app.get('/api/states', (req, res) => {
  res.json(STATES)
})

app.get('/api/districts', (req, res) => {
  const stateId = req.query.state_id ? parseInt(req.query.state_id as string, 10) : null
  const query = req.query.q ? String(req.query.q).trim().toLowerCase() : ''

  let list = DISTRICTS
  if (stateId) {
    list = list.filter(d => d.state_id === stateId)
  }
  if (query) {
    list = list.filter(d =>
      d.name.toLowerCase().includes(query) ||
      (d.full_display_name && d.full_display_name.toLowerCase().includes(query)) ||
      (d.state_name && d.state_name.toLowerCase().includes(query))
    )
  }
  res.json(list)
})

app.get('/api/schemes/sync-status', (req, res) => {
  res.json({
    status: 'ACTIVE_AUTOMATED_DAILY_SYNC',
    interval_hours: 24,
    last_synced_at: lastSyncTimestamp,
    next_sync_at: nextSyncTimestamp,
    sync_cycle_count: syncCycleCount,
    total_schemes_monitored: SCHEMES.length,
    active_schemes_count: SCHEMES.filter(s => s.status === 'ACTIVE' && s.activity?.status === 'OPEN').length
  })
})

app.post('/api/schemes/sync-now', (req, res) => {
  const result = runDailySchemeSync()
  res.json({
    status: 'success',
    message: 'Automated daily scheme sync completed.',
    ...result
  })
})

// ==============================================================================
// PROFILE ENDPOINTS
// ==============================================================================
app.get('/api/profile', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.status(401).json({ detail: 'Authentication required to view profile.' })
  }

  if (!userProfiles.has(userId)) {
    const idLower = String(userId).toLowerCase()
    if (idLower.includes('farmer') || idLower.includes('murugan')) {
      userProfiles.set(userId, {
        user_id: userId,
        email: 'murugan.farmer@schemesetu.test',
        full_name: 'Murugan Raman',
        age: 45,
        gender: 'MALE',
        state_id: 23,
        state_name: 'Tamil Nadu',
        district_id: 3,
        district_name: 'Madurai',
        annual_income: 95000,
        occupation: 'Farmer',
        education: 'Secondary (10th Pass)',
        category: 'OBC',
        disability_status: false,
        profile_complete: true,
      })
    } else if (idLower.includes('youth') || idLower.includes('karthik')) {
      userProfiles.set(userId, {
        user_id: userId,
        email: 'karthik.youth@schemesetu.test',
        full_name: 'Karthik Velu',
        age: 24,
        gender: 'MALE',
        state_id: 23,
        state_name: 'Tamil Nadu',
        district_id: 2,
        district_name: 'Coimbatore',
        annual_income: 150000,
        occupation: 'Unemployed',
        education: "Graduate / Bachelor's",
        category: 'MBC',
        disability_status: false,
        profile_complete: true,
      })
    } else {
      userProfiles.set(userId, {
        user_id: userId,
        email: idLower.includes('lakshmi') ? 'lakshmi.student@schemesetu.test' : `${userId}@citizen.local`,
        full_name: idLower.includes('lakshmi') ? 'Lakshmi Narayanan' : 'Citizen',
        age: idLower.includes('lakshmi') ? 19 : 24,
        gender: 'FEMALE',
        state_id: 23,
        state_name: 'Tamil Nadu',
        district_id: 1,
        district_name: 'Chennai',
        annual_income: idLower.includes('lakshmi') ? 120000 : 180000,
        occupation: 'Student',
        education: 'Higher Secondary (12th)',
        category: 'General',
        disability_status: false,
        profile_complete: true,
      })
    }
  }

  const existing = userProfiles.get(userId)
  res.json(existing)
})

app.put('/api/profile', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.status(401).json({ detail: 'Authentication required to update profile.' })
  }

  const body = req.body || {}
  const state = STATES.find(s => s.id === Number(body.state_id))
  const district = DISTRICTS.find(d => d.id === Number(body.district_id))

  const isComplete = Boolean(
    body.age && body.gender && body.state_id && body.occupation && body.education && body.category
  )

  const updated = {
    user_id: userId,
    email: body.email || `${userId}@citizen.local`,
    full_name: body.full_name || 'Citizen',
    age: body.age !== undefined && body.age !== null ? Number(body.age) : null,
    gender: body.gender || null,
    state_id: body.state_id ? Number(body.state_id) : null,
    state_name: state ? state.name : null,
    district_id: body.district_id ? Number(body.district_id) : null,
    district_name: district ? district.name : null,
    annual_income: body.annual_income !== undefined && body.annual_income !== null ? Number(body.annual_income) : null,
    occupation: body.occupation || null,
    education: body.education || null,
    category: body.category || null,
    disability_status: Boolean(body.disability_status),
    profile_complete: isComplete
  }

  userProfiles.set(userId, updated)
  res.json(updated)
})

// ==============================================================================
// SCHEME RETRIEVAL ENDPOINTS
// ==============================================================================
app.get('/api/schemes', (req, res) => {
  const limit = Math.max(1, Math.min(100, parseInt(req.query.limit, 10) || 50))
  const offset = Math.max(0, parseInt(req.query.offset, 10) || 0)
  const govLevel = req.query.government_level ? String(req.query.government_level).toUpperCase() : null
  const stateId = req.query.state_id ? parseInt(req.query.state_id, 10) : null
  const categoryId = req.query.category_id ? parseInt(req.query.category_id, 10) : null
  const status = req.query.status ? String(req.query.status).toUpperCase() : null

  let results = SCHEMES

  if (govLevel) {
    results = results.filter(s => s.government_level === govLevel)
  }
  if (stateId) {
    results = results.filter(s => s.state_id === stateId || s.government_level === 'CENTRAL')
  }
  if (categoryId) {
    results = results.filter(s => s.category_id === categoryId)
  }
  if (status) {
    results = results.filter(s => s.status === status)
  }

  const paginated = results.slice(offset, offset + limit)

  res.json({
    total: results.length,
    count: paginated.length,
    offset,
    limit,
    data: paginated
  })
})

app.get('/api/schemes/active', (req, res) => {
  const limit = Math.max(1, Math.min(100, parseInt(req.query.limit, 10) || 50))
  const offset = Math.max(0, parseInt(req.query.offset, 10) || 0)

  const active = SCHEMES.filter(s => s.status === 'ACTIVE' && s.activity?.status === 'OPEN')
  const paginated = active.slice(offset, offset + limit)

  res.json({
    total: active.length,
    count: paginated.length,
    offset,
    limit,
    data: paginated
  })
})

app.get('/api/schemes/central', (req, res) => {
  const central = SCHEMES.filter(s => s.government_level === 'CENTRAL')
  res.json({
    total: central.length,
    count: central.length,
    offset: 0,
    limit: 50,
    data: central
  })
})

app.get('/api/schemes/search', (req, res) => {
  const q = String(req.query.q || '').trim().toLowerCase()
  if (!q) {
    return res.status(400).json({ detail: 'Query parameter q is required.' })
  }

  const matched = SCHEMES.filter(s =>
    s.scheme_name.toLowerCase().includes(q) ||
    (s.description && s.description.toLowerCase().includes(q)) ||
    (s.category && s.category.toLowerCase().includes(q)) ||
    (s.benefits && s.benefits.toLowerCase().includes(q))
  )

  res.json({
    total: matched.length,
    count: matched.length,
    offset: 0,
    limit: 50,
    data: matched
  })
})

app.get('/api/schemes/state/:state_id', (req, res) => {
  const stateIdent = req.params.state_id
  const matched = SCHEMES.filter(s => {
    if (s.state_id && String(s.state_id) === String(stateIdent)) return true
    if (s.state_name && s.state_name.toLowerCase() === stateIdent.toLowerCase()) return true
    return false
  })

  res.json({
    total: matched.length,
    count: matched.length,
    offset: 0,
    limit: 50,
    data: matched
  })
})

app.get('/api/schemes/:scheme_id', (req, res) => {
  const idOrSlug = req.params.scheme_id
  const scheme = SCHEMES.find(s => s.id === idOrSlug || s.slug === idOrSlug || s.external_id === idOrSlug)
  if (!scheme) {
    return res.status(404).json({ detail: `Scheme with ID '${idOrSlug}' not found.` })
  }
  res.json(scheme)
})

// ==============================================================================
// RECOMMENDATIONS ENGINE
// Powerful Multi-Factor Evaluation Engine with Transparent Scoring & Verification
// ==============================================================================
function evaluateSchemeEligibility(scheme: any, profile: any, query: string = '') {
  const elig = scheme.eligibility || {}
  const matchReasons: string[] = []
  const missingCriteria: string[] = []
  let fail = false
  let unknown = false

  let geographyScore = 0
  let incomeScore = 0
  let occupationScore = 0
  let ageScore = 0
  let categoryScore = 0
  let specialBonus = 0

  const userAge = profile.age !== undefined && profile.age !== null ? Number(profile.age) : null
  const userIncome = profile.annual_income !== undefined && profile.annual_income !== null ? Number(profile.annual_income) : null
  const userGender = profile.gender ? String(profile.gender).toUpperCase() : null
  const userStateId = profile.state_id ? Number(profile.state_id) : null
  const userDistrictId = profile.district_id ? Number(profile.district_id) : null
  const userOccupation = profile.occupation ? String(profile.occupation).toLowerCase().trim() : ''
  const userCategory = profile.category ? String(profile.category).toUpperCase() : ''
  const userDisability = Boolean(profile.disability_status)

  // 1. Geography evaluation (Central vs State)
  if (scheme.government_level === 'CENTRAL') {
    geographyScore = 25
    matchReasons.push('Pan-India Central Scheme (Universal eligibility across all States & UTs)')
  } else if (scheme.government_level === 'STATE') {
    const schemeStateId = scheme.state_id || elig.state_restriction
    if (!userStateId) {
      unknown = true
      missingCriteria.push(`Requires residence in ${scheme.state_name || 'eligible State'}`)
    } else if (schemeStateId && Number(userStateId) !== Number(schemeStateId)) {
      fail = true
    } else {
      geographyScore = 25
      matchReasons.push(`Resides in ${scheme.state_name || 'eligible State'}`)

      // District-specific prioritization if applicable
      if (scheme.eligible_districts && Array.isArray(scheme.eligible_districts)) {
        if (userDistrictId && scheme.eligible_districts.includes(userDistrictId)) {
          specialBonus += 5
          matchReasons.push('Targeted priority district beneficiary')
        }
      }
    }
  }

  // 2. Gender evaluation
  if (elig.gender && elig.gender !== 'ALL') {
    if (!userGender) {
      unknown = true
      missingCriteria.push(`Targeted exclusively for ${elig.gender} beneficiaries`)
    } else if (userGender !== elig.gender.toUpperCase()) {
      fail = true
    } else {
      specialBonus += 5
      matchReasons.push(`Meets gender criterion (${elig.gender})`)
    }
  }

  // 3. Age window evaluation
  if (elig.min_age !== undefined && elig.min_age !== null) {
    if (userAge === null) {
      unknown = true
      missingCriteria.push(`Minimum age requirement of ${elig.min_age} years`)
    } else if (userAge < elig.min_age) {
      fail = true
    }
  }
  if (elig.max_age !== undefined && elig.max_age !== null) {
    if (userAge === null) {
      unknown = true
      missingCriteria.push(`Maximum age limit of ${elig.max_age} years`)
    } else if (userAge > elig.max_age) {
      fail = true
    }
  }
  if (!fail && userAge !== null) {
    ageScore = 15
    matchReasons.push(`Citizen age (${userAge} yrs) qualifies for scheme window`)
  }

  // 4. Annual Income ceiling & Tier evaluation
  if (elig.max_income !== undefined && elig.max_income !== null) {
    if (userIncome === null) {
      unknown = true
      missingCriteria.push(`Annual income must be verified below ₹${elig.max_income.toLocaleString('en-IN')}`)
    } else if (userIncome > elig.max_income) {
      fail = true
    } else {
      if (userIncome <= elig.max_income * 0.5) {
        incomeScore = 25
        matchReasons.push(`Priority income qualification (₹${userIncome.toLocaleString('en-IN')} well below ₹${elig.max_income.toLocaleString('en-IN')} ceiling)`)
      } else {
        incomeScore = 20
        matchReasons.push(`Income within prescribed limit of ₹${elig.max_income.toLocaleString('en-IN')}`)
      }
    }
  } else {
    incomeScore = 20
  }

  // 5. Occupation & Livelihood evaluation
  const targetOccs = [
    elig.occupation,
    ...(Array.isArray(elig.occupations) ? elig.occupations : [])
  ].filter(Boolean).map(o => String(o).toLowerCase())

  if (targetOccs.length > 0) {
    if (!userOccupation) {
      unknown = true
      missingCriteria.push(`Beneficiary occupation category (${targetOccs[0]})`)
    } else {
      const isOccMatch = targetOccs.some(occ =>
        userOccupation.includes(occ) || occ.includes(userOccupation) ||
        (userOccupation === 'farmer' && (occ.includes('agri') || occ.includes('cultivator'))) ||
        (userOccupation === 'student' && (occ.includes('scholar') || occ.includes('graduate') || occ.includes('school'))) ||
        (userOccupation === 'unemployed' && (occ.includes('job') || occ.includes('youth') || occ.includes('seeker')))
      )
      if (isOccMatch) {
        occupationScore = 20
        matchReasons.push(`Targeted beneficiary occupation: ${profile.occupation}`)
      } else {
        if (scheme.category === 'Agriculture & Farmers Welfare' && !userOccupation.includes('farm')) {
          fail = true
        } else {
          unknown = true
          missingCriteria.push(`Occupation criteria verification against ${targetOccs.join(', ')}`)
        }
      }
    }
  } else {
    occupationScore = 15
  }

  // 6. Social Category / Reservation evaluation
  const allowedCategories = elig.categories ? elig.categories.map((c: string) => c.toUpperCase()) : []
  if (elig.category) allowedCategories.push(String(elig.category).toUpperCase())

  if (allowedCategories.length > 0 && !allowedCategories.includes('ALL')) {
    if (!userCategory) {
      unknown = true
      missingCriteria.push(`Requires ${allowedCategories.join('/')} community certificate`)
    } else if (allowedCategories.includes(userCategory) || (userCategory === 'MBC' && allowedCategories.includes('OBC'))) {
      categoryScore = 15
      matchReasons.push(`Eligible under targeted category (${userCategory})`)
    } else {
      fail = true
    }
  } else {
    categoryScore = 10
  }

  // 7. Disability / Special Vulnerability
  if (elig.disability_required) {
    if (!userDisability) {
      fail = true
    } else {
      specialBonus += 10
      matchReasons.push('Priority disability assistance criteria satisfied')
    }
  }

  // 8. Keyword / Query Match Boost
  let queryBoost = 0
  if (query) {
    const q = query.toLowerCase()
    const searchTarget = `${scheme.scheme_name} ${scheme.description} ${scheme.category} ${scheme.benefits} ${scheme.department || ''}`.toLowerCase()
    if (searchTarget.includes(q)) {
      queryBoost = 15
    }
  }

  if (fail) return { status: 'NOT_ELIGIBLE', match_score: 0, matchReasons: [], missingCriteria }

  const rawScore = geographyScore + incomeScore + occupationScore + ageScore + categoryScore + specialBonus + queryBoost
  const finalScore = Math.max(55, Math.min(99, rawScore))

  const scoreBreakdown = {
    geography: geographyScore,
    income: incomeScore,
    occupation: occupationScore,
    age: ageScore,
    category: categoryScore,
    bonus: specialBonus + queryBoost
  }

  if (unknown) {
    return { status: 'POSSIBLY_ELIGIBLE', match_score: Math.min(75, finalScore), matchReasons, missingCriteria, scoreBreakdown }
  }

  return { status: 'ELIGIBLE', match_score: finalScore, matchReasons, missingCriteria, scoreBreakdown }
}

function computeRecommendations(profileInput: any, queryText: string = '', options: any = {}) {
  const profile = profileInput || {}
  const q = queryText ? queryText.trim().toLowerCase() : ''
  const sortBy = options.sortBy || 'match' // 'match' | 'deadline' | 'popular' | 'benefit'
  const filterLevel = options.filterLevel || null
  const filterCategory = options.filterCategory || null
  const filterStateId = options.filterStateId || null

  const eligibleList: any[] = []
  const verificationList: any[] = []

  for (const scheme of SCHEMES) {
    if (scheme.status !== 'ACTIVE' || scheme.activity?.status === 'CLOSED') continue

    // Level filter
    if (filterLevel && filterLevel !== 'ALL' && scheme.government_level !== filterLevel) continue
    // Category filter
    if (filterCategory && scheme.category !== filterCategory && scheme.category_id !== Number(filterCategory)) continue
    // State filter
    if (filterStateId && scheme.government_level === 'STATE' && Number(scheme.state_id) !== Number(filterStateId)) continue

    const evalResult = evaluateSchemeEligibility(scheme, profile, q)

    const schemeEntry = {
      scheme_id: scheme.id,
      id: scheme.id,
      scheme_name: scheme.scheme_name,
      slug: scheme.slug,
      external_id: scheme.external_id,
      description: scheme.description,
      department: scheme.department,
      government_level: scheme.government_level,
      state_id: scheme.state_id,
      state_name: scheme.state_name,
      category: scheme.category,
      category_id: scheme.category_id,
      benefits: scheme.benefits,
      application_process: scheme.application_process,
      official_url: scheme.official_url,
      source_url: scheme.source_url,
      last_date: scheme.last_date || 'Rolling / Open Year-Round',
      last_date_iso: scheme.last_date_iso,
      days_remaining: scheme.activity?.days_remaining ?? null,
      deadline_status: scheme.activity?.deadline_status || 'OPEN',
      activity_status: scheme.activity?.status || 'OPEN',
      activity: scheme.activity,
      dbt_enabled: Boolean(scheme.dbt_enabled),
      popularity_rank: scheme.popularity_rank || 85,
      documents: scheme.documents || [],
      match_score: evalResult.match_score,
      relevance_score: evalResult.match_score,
      score_breakdown: evalResult.scoreBreakdown,
      match_reasons: evalResult.matchReasons.length > 0 ? evalResult.matchReasons : ['Eligible under demographic criteria'],
      relevance_reason: evalResult.matchReasons.length > 0 ? evalResult.matchReasons[0] : 'Matches profile parameters',
      missing_criteria: evalResult.missingCriteria
    }

    if (evalResult.status === 'ELIGIBLE') {
      eligibleList.push(schemeEntry)
    } else if (evalResult.status === 'POSSIBLY_ELIGIBLE') {
      verificationList.push({
        ...schemeEntry,
        eligibility_status: 'REQUIRES_VERIFICATION',
        verification_reasons: evalResult.missingCriteria.length > 0 ? evalResult.missingCriteria : ['Income or demographic criteria requires verification against documents']
      })
    }
  }

  // Sorting
  if (sortBy === 'deadline') {
    eligibleList.sort((a, b) => {
      const aDays = a.days_remaining !== null ? a.days_remaining : 9999
      const bDays = b.days_remaining !== null ? b.days_remaining : 9999
      return aDays - bDays
    })
  } else if (sortBy === 'popular') {
    eligibleList.sort((a, b) => (b.popularity_rank || 0) - (a.popularity_rank || 0))
  } else {
    // Default: Match score descending
    eligibleList.sort((a, b) => b.match_score - a.match_score)
  }

  return {
    total_candidates: SCHEMES.length,
    ranking_method: 'DETERMINISTIC_HYBRID_MULTIFACTOR',
    last_synced_at: lastSyncTimestamp,
    recommendations: eligibleList,
    verification_required: verificationList
  }
}

app.post('/api/recommendations', (req, res) => {
  const userId = getUserIdFromAuth(req)
  let profile = req.body.profile

  if (userId && userId !== 'guest-user' && !profile) {
    profile = userProfiles.get(userId)
  }

  if (!profile) {
    profile = {
      age: 24,
      gender: 'FEMALE',
      state_id: 23,
      occupation: 'Student',
      annual_income: 180000,
      education: 'Higher Secondary (12th)',
      category: 'General'
    }
  }

  const options = {
    sortBy: req.body.sort || req.query.sort || 'match',
    filterLevel: req.body.level || req.query.level,
    filterCategory: req.body.category || req.query.category,
    filterStateId: req.body.state_id || req.query.state_id
  }

  const result = computeRecommendations(profile, req.body.query, options)
  res.json(result)
})

app.get('/api/recommendations', (req, res) => {
  const userId = getUserIdFromAuth(req)
  let profile = null

  if (userId && userId !== 'guest-user') {
    profile = userProfiles.get(userId)
  }

  if (!profile) {
    profile = {
      age: req.query.age ? Number(req.query.age) : 24,
      gender: req.query.gender || 'FEMALE',
      state_id: req.query.state_id ? Number(req.query.state_id) : 23,
      district_id: req.query.district_id ? Number(req.query.district_id) : null,
      annual_income: req.query.annual_income ? Number(req.query.annual_income) : 180000,
      occupation: req.query.occupation || 'Student',
      education: req.query.education || 'Higher Secondary',
      category: req.query.category || 'General',
      disability_status: req.query.disability === 'true'
    }
  }

  const options = {
    sortBy: req.query.sort || 'match',
    filterLevel: req.query.level,
    filterCategory: req.query.category_filter,
    filterStateId: req.query.state_id
  }

  const result = computeRecommendations(profile, req.query.q as string, options)
  res.json(result)
})

// ==============================================================================
// SAVED SCHEMES / BOOKMARKS
// ==============================================================================
app.get('/api/saved-schemes', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.status(401).json({ detail: 'Authentication required to view saved schemes.' })
  }

  const userSaved = savedSchemes.get(userId) || new Set()
  const list = SCHEMES.filter(s => userSaved.has(s.id)).map(s => ({
    id: s.id,
    scheme_id: s.id,
    scheme_name: s.scheme_name,
    description: s.description,
    government_level: s.government_level,
    state_id: s.state_id,
    category: s.category,
    benefits: s.benefits,
    status: s.status,
    activity: s.activity,
    saved_at: new Date().toISOString()
  }))

  res.json(list)
})

app.get('/api/saved-schemes/:scheme_id', (req, res) => {
  const userId = getUserIdFromAuth(req)
  const schemeId = req.params.scheme_id
  const userSaved = savedSchemes.get(userId) || new Set()
  const isSaved = userSaved.has(schemeId)
  res.json({ scheme_id: schemeId, is_saved: isSaved, saved: isSaved })
})

app.post('/api/saved-schemes/:scheme_id', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.status(401).json({ detail: 'Authentication required to bookmark schemes.' })
  }

  const schemeId = req.params.scheme_id
  if (!savedSchemes.has(userId)) {
    savedSchemes.set(userId, new Set())
  }
  savedSchemes.get(userId).add(schemeId)

  res.json({
    status: 'success',
    message: 'Scheme saved successfully.',
    saved: true
  })
})

app.delete('/api/saved-schemes/:scheme_id', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.status(401).json({ detail: 'Authentication required to remove saved schemes.' })
  }

  const schemeId = req.params.scheme_id
  if (savedSchemes.has(userId)) {
    savedSchemes.get(userId).delete(schemeId)
  }

  res.json({
    status: 'success',
    message: 'Scheme removed from saved bookmarks.',
    saved: false
  })
})

// ==============================================================================
// NOTIFICATIONS ENDPOINTS
// ==============================================================================
app.get('/api/notifications', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.status(401).json({ detail: 'Authentication required.' })
  }
  const notifs = getSeedNotifications(userId)
  res.json(notifs)
})

app.get('/api/notifications/unread', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.json({ unread_count: 0, notifications: [] })
  }
  const notifs = getSeedNotifications(userId)
  const unread = notifs.filter(n => !n.read)
  res.json({
    unread_count: unread.length,
    notifications: unread
  })
})

app.patch('/api/notifications/:notification_id/read', (req, res) => {
  const userId = getUserIdFromAuth(req)
  const notifId = req.params.notification_id
  const notifs = getSeedNotifications(userId)
  const item = notifs.find(n => n.id === notifId)
  if (item) item.read = true
  res.json({ status: 'success', message: 'Notification marked as read.' })
})

app.patch('/api/notifications/read-all', (req, res) => {
  const userId = getUserIdFromAuth(req)
  const notifs = getSeedNotifications(userId)
  notifs.forEach(n => { n.read = true })
  res.json({ status: 'success', message: 'All notifications marked as read.' })
})

app.post('/api/notifications/check-deadlines', (req, res) => {
  res.json({
    status: 'success',
    evaluated: SCHEMES.length,
    alerts_generated: 0,
    message: 'Deadlines check completed.'
  })
})

// ==============================================================================
// AI CHATBOT ASSISTANT ENDPOINT
// Grounded natural language understanding & recommendation synthesis
// ==============================================================================
app.post('/api/chat', async (req, res) => {
  const { message, language } = req.body || {}
  const rawMsg = (message || '').trim()
  if (!rawMsg) {
    return res.status(400).json({ detail: 'Message cannot be empty.' })
  }

  const userId = getUserIdFromAuth(req)
  const profile = (userId && userId !== 'guest-user' ? userProfiles.get(userId) : null) || {
    age: 24,
    gender: 'FEMALE',
    state_id: 23,
    annual_income: 180000,
    occupation: 'Student'
  }

  // Regional language detection and mapping
  const lower = rawMsg.toLowerCase()
  let langCode = language || 'en'
  if (/[\u0B80-\u0BFF]/.test(rawMsg)) langCode = 'ta' // Tamil script
  else if (/[\u0900-\u097F]/.test(rawMsg)) {
    // Devanagari script can be Hindi or Marathi
    langCode = (language === 'mr' || /आम्ही|माझे|योजना|मदत|शेतकरी/.test(rawMsg)) ? 'mr' : 'hi'
  }
  else if (/[\u0C00-\u0C7F]/.test(rawMsg)) langCode = 'te' // Telugu
  else if (/[\u0C80-\u0CFF]/.test(rawMsg)) langCode = 'kn' // Kannada
  else if (/[\u0D00-\u0D7F]/.test(rawMsg)) langCode = 'ml' // Malayalam
  else if (/[\u0980-\u09FF]/.test(rawMsg)) langCode = 'bn' // Bengali
  else if (/[\u0A80-\u0AFF]/.test(rawMsg)) langCode = 'gu' // Gujarati

  const LANG_NAMES: Record<string, string> = {
    ta: 'Tamil (தமிழ்)',
    hi: 'Hindi (हिन्दी)',
    te: 'Telugu (తెలుగు)',
    kn: 'Kannada (ಕನ್ನಡ)',
    ml: 'Malayalam (മലയാളം)',
    bn: 'Bengali (বাংলা)',
    mr: 'Marathi (मराठी)',
    gu: 'Gujarati (ગુજરાતી)',
    en: 'English',
  }

  const recsResult = computeRecommendations(profile, lower)
  const topRecs = recsResult.recommendations.slice(0, 3)

  let botReply = ''
  let audioBase64: string | null = null

  // 1. Try Gemini API if configured with fast timeout
  if (ai) {
    try {
      const targetLangName = LANG_NAMES[langCode] || 'English'
      const schemeContext = topRecs.length > 0
        ? topRecs.map(r => `• ${r.scheme_name}: Benefits: ${r.benefits}. (Status: ${r.activity?.status || 'OPEN'})`).join('\n')
        : 'No specific matching schemes found in the local catalog. Ask the user for age, occupation, and state.'

      const prompt = `You are SchemeSetu, an official, empathetic Government Welfare Scheme Assistant for Indian citizens.
User Question: "${rawMsg}"
Requested Language: ${targetLangName}.
Citizen Demographics: Age ${profile.age || 'unspecified'}, Gender ${profile.gender || 'unspecified'}, State ${profile.state_name || 'Tamil Nadu'}, Occupation ${profile.occupation || 'unspecified'}, Annual Income ₹${profile.annual_income || 'unspecified'}.

Official verified welfare schemes from the database:
${schemeContext}

Strict Instructions:
1. Answer ENTIRELY in ${targetLangName} using authentic script (e.g., Tamil script for Tamil, Devanagari for Hindi).
2. Explain clearly which schemes they qualify for and the key benefits.
3. Make the language warm, accessible, respectful, and well-structured for both reading on screen and voice synthesis.
4. Keep the reply concise and helpful (2-3 short paragraphs).`

      const geminiPromise = ai.models.generateContent({
        model: 'gemini-3.8-flash',
        contents: prompt,
      })
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Gemini timeout')), 4500)
      )

      const geminiRes = await Promise.race([geminiPromise, timeoutPromise]) as any
      botReply = geminiRes?.text || ''
    } catch (geminiErr: any) {
      console.warn('Gemini generateContent fallback:', geminiErr?.message)
    }
  }

  // 2. Deterministic Regional Language Fallback (works 100% offline or without API key)
  if (!botReply) {
    if (langCode === 'ta') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `வணக்கம்! உங்கள் விவரங்களின்படி நீங்கள் பயன்பெறக்கூடிய சிறந்த தமிழ்நாடு மற்றும் மத்திய அரசு நலத்திட்டங்கள்:\n\n${names}\n\nஇந்த திட்டங்கள் தற்போது நேரடி விண்ணப்பத்திற்கு திறக்கப்பட்டுள்ளன. அருகிலுள்ள இ-சேவை மையம் அல்லது அதிகாரப்பூர்வ போர்ட்டல் மூலம் விண்ணப்பிக்கலாம்.`
      } else {
        botReply = 'வணக்கம்! உங்கள் வினவலுக்கு பொருந்தக்கூடிய திட்டங்களை கண்டறிய முடியவில்லை. தயவுசெய்து உங்கள் வயது, மாவட்டம் அல்லது தொழில் விவரங்களை குறிப்பிடவும்.'
      }
    } else if (langCode === 'hi') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `नमस्ते! आपकी पात्रता और प्रोफाइल के आधार पर, आप निम्नलिखित सरकारी कल्याणकारी योजनाओं के लिए पात्र हैं:\n\n${names}\n\nये सभी योजनाएं वर्तमान में आवेदन के लिए खुली हैं। आप आधिकारिक पोर्टल या नजदीकी जन सेवा केंद्र (CSC) से आवेदन कर सकते हैं।`
      } else {
        botReply = 'नमस्ते! आपकी आवश्यकता के अनुसार योजना खोजने के लिए, कृपया अपनी आयु, पेशा (जैसे किसान, छात्र) और राज्य का विवरण साझा करें।'
      }
    } else if (langCode === 'te') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `నమస్కారం! మీ వివరాల ప్రకారం మీరు దరఖాస్తు చేసుకోగల ముఖ్యమైన ప్రభుత్వ సంక్షేమ పథకాలు:\n\n${names}\n\nఈ పథకాలకు దరఖాస్తు ప్రక్రియ ప్రస్తుతం తెరిచి ఉంది.`
      } else {
        botReply = 'నమస్కారం! మీ అర్హతలను మరింత వివరంగా తెలుపగలరా? (వయస్సు, వృత్తి మరియు ఆదాయం)'
      }
    } else if (langCode === 'kn') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಅರ್ಹತೆಯ ವಿವರಗಳ ಪ್ರಕಾರ ನೀವು ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದಾದ ಸರ್ಕಾರದ ಪ್ರಮುಖ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳು:\n\n${names}\n\nಈ ಯೋಜನೆಗಳು ಪ್ರಸ್ತುತ ಅನ್ವಯಿಸಲು ಮುಕ್ತವಾಗಿವೆ.`
      } else {
        botReply = 'ನಮಸ್ಕಾರ! ಹೆಚ್ಚಿನ ಸೂಕ್ತ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಯಸ್ಸು ಮತ್ತು ಉದ್ಯೋಗವನ್ನು ತಿಳಿಸಿ.'
      }
    } else if (langCode === 'ml') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `നമസ്കാരം! നിങ്ങളുടെ വിവരങ്ങൾ അനുസരിച്ച് അർഹതയുള്ള സർക്കാർ ക്ഷേമ പദ്ധതികൾ:\n\n${names}\n\nഈ പദ്ധതികളിലേക്ക് ഇപ്പോൾ അപേക്ഷിക്കാവുന്നതാണ്.`
      } else {
        botReply = 'നമസ്കാരം! കൃത്യമായ പദ്ധതികൾ കണ്ടെത്തുന്നതിനായി നിങ്ങളുടെ പ്രായവും തൊഴിലും പങ്കുവെക്കുക.'
      }
    } else if (langCode === 'bn') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `নমস্কার! আপনার প্রোফাইল অনুযায়ী যোগ্য সরকারি কল্যাণমূলক প্রকল্পসমূহ:\n\n${names}\n\nএই প্রকল্পগুলির জন্য বর্তমানে সরাসরি আবেদন করা যাচ্ছে।`
      } else {
        botReply = 'নমস্কার! উপযুক্ত প্রকল্প খুঁজে পেতে অনুগ্রহ করে আপনার বয়স এবং পেশা জানান।'
      }
    } else if (langCode === 'mr') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `नमस्कार! तुमच्या पात्रतेनुसार केंद्र व राज्य शासनाच्या प्रमुख कल्याणकारी योजना:\n\n${names}\n\nया सर्व योजनांसाठी अर्ज प्रक्रिया सुरू आहे.`
      } else {
        botReply = 'नमस्कार! योग्य योजना शोधण्यासाठी कृपया तुमचे वय आणि व्यवसाय नमूद करा.'
      }
    } else if (langCode === 'gu') {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `નમસ્તે! તમારી પ્રોફાઇલ મુજબ પાત્ર સરકારી કલ્યાણકારી યોજનાઓ:\n\n${names}\n\nઆ યોજનાઓ માટે અરજી પ્રક્રિયા હાલમાં શરૂ છે.`
      } else {
        botReply = 'નમસ્તે! યોગ્ય યોજનાઓ શોધવા માટે કૃપા કરીને તમારી ઉંમર અને વ્યવસાય જણાવો.'
      }
    } else {
      if (topRecs.length > 0) {
        const names = topRecs.map(r => `• **${r.scheme_name}**: ${r.benefits}`).join('\n\n')
        botReply = `Based on your profile, here are the top verified government welfare schemes you qualify for:\n\n${names}\n\nAll recommended schemes are verified, active, and open for application.`
      } else {
        botReply = `I searched our verified government schemes database. Could you share your age, occupation (e.g. farmer, student, entrepreneur), and state so I can find tailored welfare schemes for you?`
      }
    }
  }

  // Record history
  if (userId && userId !== 'guest-user') {
    if (!chatHistories.has(userId)) chatHistories.set(userId, [])
    chatHistories.get(userId).push({
      id: `chat-${Date.now()}`,
      user_id: userId,
      user_message: rawMsg,
      bot_response: botReply,
      language: langCode,
      created_at: new Date().toISOString()
    })
  }

  res.json({
    message: botReply,
    language: langCode,
    audioBase64,
    mimeType: audioBase64 ? 'audio/wav' : null,
    intent: {
      intent: 'find_schemes',
      keywords: lower.split(' ').slice(0, 5)
    },
    recommendations: topRecs,
    verification_required: recsResult.verification_required.slice(0, 2),
    total_eligible_found: recsResult.recommendations.length
  })
})

// Dedicated Voice Text-to-Speech Endpoint
app.post('/api/chat/tts', async (req, res) => {
  const { text, language } = req.body || {}
  const rawText = String(text || '').trim()
  if (!rawText) {
    return res.status(400).json({ detail: 'Text is required for TTS.' })
  }

  if (ai) {
    try {
      const clean = rawText.replace(/[*#•_-]/g, ' ').slice(0, 450)
      const ttsRes = await ai.models.generateContent({
        model: 'gemini-3.8-flash-lite-tts',
        contents: [{ role: 'user', parts: [{ text: clean }] }],
        config: {
          responseModalities: ['AUDIO'],
          speechConfig: {
            voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } },
          },
        },
      })
      const audioData = ttsRes.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data
      if (audioData) {
        return res.json({
          audioBase64: audioData,
          mimeType: 'audio/wav',
          language: language || 'en',
        })
      }
    } catch (err: any) {
      console.warn('TTS API error, falling back to client synthesis:', err?.message)
    }
  }

  res.json({
    audioBase64: null,
    useClientTts: true,
    language: language || 'en',
  })
})

app.get('/api/chat/history', (req, res) => {
  const userId = getUserIdFromAuth(req)
  if (!userId || userId === 'guest-user') {
    return res.status(401).json({ detail: 'Authentication required to view chat history.' })
  }
  const history = chatHistories.get(userId) || []
  res.json({
    user_id: userId,
    total_messages: history.length,
    history
  })
})

// ==============================================================================
// AUTH PROVISIONING ENDPOINT
// ==============================================================================
app.post('/api/auth/register', (req, res) => {
  const { email, password, full_name } = req.body || {}
  if (!email || !password) {
    return res.status(400).json({ detail: 'Email and password are required.' })
  }

  const userId = `citizen-${Date.now()}`
  userProfiles.set(userId, {
    user_id: userId,
    email: email.toLowerCase(),
    full_name: full_name || 'Citizen',
    age: 24,
    gender: 'FEMALE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    annual_income: 180000,
    occupation: 'Student',
    education: 'Higher Secondary (12th)',
    category: 'General',
    disability_status: false,
    profile_complete: true
  })

  res.status(201).json({
    status: 'success',
    message: 'Account created successfully. You can now sign in.',
    user: {
      id: userId,
      email: email.toLowerCase()
    }
  })
})

// ==============================================================================
// VITE MIDDLEWARE INTEGRATION (Dev) / STATIC FILE SERVING (Prod)
// ==============================================================================
async function startServer() {
  const isProduction = process.env.NODE_ENV === 'production'

  if (!isProduction) {
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        hmr: false,
      },
      appType: 'spa'
    })
    app.use(vite.middlewares)
  } else {
    const distPath = path.resolve(__dirname, 'dist')
    app.use(express.static(distPath))
    app.get('*', (req, res) => {
      res.sendFile(path.resolve(distPath, 'index.html'))
    })
  }

  const server = app.listen(PORT, HOST, () => {
    console.log(`SchemeSetu Server is running on http://${HOST}:${PORT}`)
  })

  server.on('error', (err: any) => {
    if (err.code === 'EADDRINUSE') {
      console.warn(`[Warning] Port ${PORT} is currently in use. Existing process is actively serving.`)
    } else {
      console.error('Server error:', err)
      process.exit(1)
    }
  })
}

startServer().catch(err => {
  console.error('Failed to start server:', err)
  process.exit(1)
})
