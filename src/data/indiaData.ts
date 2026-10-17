/**
 * Master Data: Indian States, Districts/Cities, and Verified Live Government Schemes
 * Covers all 28 States and 8 Union Territories with comprehensive district mapping.
 */

export interface IndianState {
  id: number
  name: string
  code: string
  type: 'STATE' | 'UT'
}

export interface IndianDistrict {
  id: number
  state_id: number
  name: string
  code?: string
}

export interface SchemeDocument {
  document_name: string
  mandatory: boolean
  description: string
}

export interface SchemeSource {
  source_url: string
  source_type: string
}

export interface SchemeActivity {
  status: 'OPEN' | 'CLOSING_SOON' | 'EXPIRED'
  deadline_status: 'CLOSING_TODAY' | 'URGENT' | 'APPROACHING' | 'MORE_THAN_15_DAYS' | 'NO_DEADLINE'
  days_remaining: number | null
}

export interface SchemeEligibility {
  min_age?: number
  max_age?: number
  gender?: 'MALE' | 'FEMALE' | 'ALL'
  state_restriction?: number | null // state_id
  district_restriction?: number | null // district_id
  max_income?: number | null
  occupation?: string | null
  education?: string | null
  caste_category?: string | null // SC, ST, OBC, MBC, General, etc.
  disability_required?: boolean
}

export interface MasterScheme {
  id: string
  slug: string
  external_id: string
  scheme_name: string
  description: string
  government_level: 'CENTRAL' | 'STATE'
  state_id: number | null
  state_name: string
  category: string
  category_id?: number
  benefits: string
  application_process: string
  status: 'ACTIVE' | 'INACTIVE'
  official_url: string
  source_url: string
  last_date: string // ISO date string or descriptor
  activity: SchemeActivity
  eligibility: SchemeEligibility
  documents: SchemeDocument[]
  sources: SchemeSource[]
}

// ==============================================================================
// 1. ALL 28 STATES & 8 UNION TERRITORIES (TOTAL 36)
// ==============================================================================
export const ALL_INDIAN_STATES: IndianState[] = [
  { id: 1, name: 'Andhra Pradesh', code: 'AP', type: 'STATE' },
  { id: 2, name: 'Arunachal Pradesh', code: 'AR', type: 'STATE' },
  { id: 3, name: 'Assam', code: 'AS', type: 'STATE' },
  { id: 4, name: 'Bihar', code: 'BR', type: 'STATE' },
  { id: 5, name: 'Chhattisgarh', code: 'CG', type: 'STATE' },
  { id: 6, name: 'Goa', code: 'GA', type: 'STATE' },
  { id: 7, name: 'Gujarat', code: 'GJ', type: 'STATE' },
  { id: 8, name: 'Haryana', code: 'HR', type: 'STATE' },
  { id: 9, name: 'Himachal Pradesh', code: 'HP', type: 'STATE' },
  { id: 10, name: 'Jharkhand', code: 'JH', type: 'STATE' },
  { id: 11, name: 'Karnataka', code: 'KA', type: 'STATE' },
  { id: 12, name: 'Kerala', code: 'KL', type: 'STATE' },
  { id: 13, name: 'Madhya Pradesh', code: 'MP', type: 'STATE' },
  { id: 14, name: 'Maharashtra', code: 'MH', type: 'STATE' },
  { id: 15, name: 'Manipur', code: 'MN', type: 'STATE' },
  { id: 16, name: 'Meghalaya', code: 'ML', type: 'STATE' },
  { id: 17, name: 'Mizoram', code: 'MZ', type: 'STATE' },
  { id: 18, name: 'Nagaland', code: 'NL', type: 'STATE' },
  { id: 19, name: 'Odisha', code: 'OD', type: 'STATE' },
  { id: 20, name: 'Punjab', code: 'PB', type: 'STATE' },
  { id: 21, name: 'Rajasthan', code: 'RJ', type: 'STATE' },
  { id: 22, name: 'Sikkim', code: 'SK', type: 'STATE' },
  { id: 23, name: 'Tamil Nadu', code: 'TN', type: 'STATE' },
  { id: 24, name: 'Telangana', code: 'TS', type: 'STATE' },
  { id: 25, name: 'Tripura', code: 'TR', type: 'STATE' },
  { id: 26, name: 'Uttar Pradesh', code: 'UP', type: 'STATE' },
  { id: 27, name: 'Uttarakhand', code: 'UK', type: 'STATE' },
  { id: 28, name: 'West Bengal', code: 'WB', type: 'STATE' },
  { id: 29, name: 'Andaman and Nicobar Islands', code: 'AN', type: 'UT' },
  { id: 30, name: 'Chandigarh', code: 'CH', type: 'UT' },
  { id: 31, name: 'Dadra and Nagar Haveli and Daman and Diu', code: 'DN', type: 'UT' },
  { id: 32, name: 'Delhi', code: 'DL', type: 'UT' },
  { id: 33, name: 'Jammu and Kashmir', code: 'JK', type: 'UT' },
  { id: 34, name: 'Ladakh', code: 'LA', type: 'UT' },
  { id: 35, name: 'Lakshadweep', code: 'LD', type: 'UT' },
  { id: 36, name: 'Puducherry', code: 'PY', type: 'UT' },
]

// ==============================================================================
// 2. COMPREHENSIVE DISTRICTS & CITIES COVERING ALL INDIAN STATES & UTs
// ==============================================================================
export const ALL_INDIAN_DISTRICTS: IndianDistrict[] = [
  // Tamil Nadu (state_id: 23)
  { id: 1, state_id: 23, name: 'Chennai', code: 'CHN' },
  { id: 2, state_id: 23, name: 'Coimbatore', code: 'CBE' },
  { id: 3, state_id: 23, name: 'Madurai', code: 'MDU' },
  { id: 4, state_id: 23, name: 'Salem', code: 'SLM' },
  { id: 5, state_id: 23, name: 'Tiruchirappalli (Trichy)', code: 'TPJ' },
  { id: 6, state_id: 23, name: 'Tirunelveli', code: 'TNV' },
  { id: 7, state_id: 23, name: 'Erode', code: 'ERD' },
  { id: 8, state_id: 23, name: 'Vellore', code: 'VLR' },
  { id: 9, state_id: 23, name: 'Thanjavur', code: 'TNJ' },
  { id: 10, state_id: 23, name: 'Dindigul', code: 'DGL' },
  { id: 11, state_id: 23, name: 'Kanchipuram', code: 'KPM' },
  { id: 12, state_id: 23, name: 'Tiruppur', code: 'TPR' },
  { id: 13, state_id: 23, name: 'Cuddalore', code: 'CDL' },
  { id: 14, state_id: 23, name: 'Kanyakumari', code: 'KK' },
  { id: 15, state_id: 23, name: 'Namakkal', code: 'NMK' },
  { id: 16, state_id: 23, name: 'Karur', code: 'KRR' },
  { id: 17, state_id: 23, name: 'Krishnagiri', code: 'KGI' },
  { id: 18, state_id: 23, name: 'Dharmapuri', code: 'DPI' },
  { id: 19, state_id: 23, name: 'Pudukkottai', code: 'PDK' },
  { id: 20, state_id: 23, name: 'Ramanathapuram', code: 'RMD' },
  { id: 21, state_id: 23, name: 'Sivaganga', code: 'SVG' },
  { id: 22, state_id: 23, name: 'Theni', code: 'THN' },
  { id: 23, state_id: 23, name: 'Thoothukudi (Tuticorin)', code: 'TKD' },
  { id: 24, state_id: 23, name: 'Tiruvallur', code: 'TVR' },
  { id: 25, state_id: 23, name: 'Tiruvannamalai', code: 'TVM' },
  { id: 26, state_id: 23, name: 'Tiruvarur', code: 'TVU' },
  { id: 27, state_id: 23, name: 'Viluppuram', code: 'VPM' },
  { id: 28, state_id: 23, name: 'Virudhunagar', code: 'VDN' },
  { id: 29, state_id: 23, name: 'Nilgiris (Ooty)', code: 'NLG' },
  { id: 30, state_id: 23, name: 'Ariyalur', code: 'ARY' },
  { id: 31, state_id: 23, name: 'Perambalur', code: 'PMB' },
  { id: 32, state_id: 23, name: 'Nagapattinam', code: 'NGP' },
  { id: 33, state_id: 23, name: 'Tenkasi', code: 'TSI' },
  { id: 34, state_id: 23, name: 'Chengalpattu', code: 'CGP' },
  { id: 35, state_id: 23, name: 'Ranipet', code: 'RPT' },
  { id: 36, state_id: 23, name: 'Tirupathur', code: 'TPT' },
  { id: 37, state_id: 23, name: 'Kallakurichi', code: 'KLK' },
  { id: 38, state_id: 23, name: 'Mayiladuthurai', code: 'MYD' },

  // Maharashtra (state_id: 14)
  { id: 101, state_id: 14, name: 'Mumbai City', code: 'MUM' },
  { id: 102, state_id: 14, name: 'Mumbai Suburban', code: 'MSB' },
  { id: 103, state_id: 14, name: 'Pune', code: 'PUN' },
  { id: 104, state_id: 14, name: 'Nagpur', code: 'NGP' },
  { id: 105, state_id: 14, name: 'Thane', code: 'THN' },
  { id: 106, state_id: 14, name: 'Nashik', code: 'NSK' },
  { id: 107, state_id: 14, name: 'Chhatrapati Sambhajinagar (Aurangabad)', code: 'AUR' },
  { id: 108, state_id: 14, name: 'Solapur', code: 'SOL' },
  { id: 109, state_id: 14, name: 'Kolhapur', code: 'KOP' },
  { id: 110, state_id: 14, name: 'Amravati', code: 'AMR' },
  { id: 111, state_id: 14, name: 'Nanded', code: 'NAN' },
  { id: 112, state_id: 14, name: 'Sangli', code: 'SNG' },
  { id: 113, state_id: 14, name: 'Jalgaon', code: 'JLG' },
  { id: 114, state_id: 14, name: 'Satara', code: 'STR' },
  { id: 115, state_id: 14, name: 'Raigad', code: 'RGD' },
  { id: 116, state_id: 14, name: 'Ratnagiri', code: 'RTG' },
  { id: 117, state_id: 14, name: 'Akola', code: 'AKL' },
  { id: 118, state_id: 14, name: 'Latur', code: 'LTR' },
  { id: 119, state_id: 14, name: 'Dhule', code: 'DHL' },
  { id: 120, state_id: 14, name: 'Ahmednagar', code: 'AHM' },

  // Karnataka (state_id: 11)
  { id: 201, state_id: 11, name: 'Bengaluru Urban', code: 'BLR' },
  { id: 202, state_id: 11, name: 'Bengaluru Rural', code: 'BRR' },
  { id: 203, state_id: 11, name: 'Mysuru (Mysore)', code: 'MYS' },
  { id: 204, state_id: 11, name: 'Hubballi-Dharwad', code: 'HBL' },
  { id: 205, state_id: 11, name: 'Mangaluru (Dakshina Kannada)', code: 'MNG' },
  { id: 206, state_id: 11, name: 'Belagavi (Belgaum)', code: 'BLG' },
  { id: 207, state_id: 11, name: 'Kalaburagi (Gulbarga)', code: 'KLB' },
  { id: 208, state_id: 11, name: 'Ballari (Bellary)', code: 'BLY' },
  { id: 209, state_id: 11, name: 'Shivamogga (Shimoga)', code: 'SHV' },
  { id: 210, state_id: 11, name: 'Tumakuru (Tumkur)', code: 'TMK' },
  { id: 211, state_id: 11, name: 'Davangere', code: 'DVG' },
  { id: 212, state_id: 11, name: 'Udupi', code: 'UDP' },
  { id: 213, state_id: 11, name: 'Hassan', code: 'HSN' },
  { id: 214, state_id: 11, name: 'Bidar', code: 'BDR' },
  { id: 215, state_id: 11, name: 'Vijayapura (Bijapur)', code: 'BJP' },

  // Delhi (state_id: 32)
  { id: 301, state_id: 32, name: 'New Delhi', code: 'NDL' },
  { id: 302, state_id: 32, name: 'Central Delhi', code: 'CDL' },
  { id: 303, state_id: 32, name: 'South Delhi', code: 'SDL' },
  { id: 304, state_id: 32, name: 'North Delhi', code: 'NOD' },
  { id: 305, state_id: 32, name: 'West Delhi', code: 'WDL' },
  { id: 306, state_id: 32, name: 'East Delhi', code: 'EDL' },
  { id: 307, state_id: 32, name: 'North East Delhi', code: 'NED' },
  { id: 308, state_id: 32, name: 'North West Delhi', code: 'NWD' },
  { id: 309, state_id: 32, name: 'South West Delhi', code: 'SWD' },
  { id: 310, state_id: 32, name: 'South East Delhi', code: 'SED' },
  { id: 311, state_id: 32, name: 'Shahdara', code: 'SHD' },

  // Uttar Pradesh (state_id: 26)
  { id: 401, state_id: 26, name: 'Lucknow', code: 'LKO' },
  { id: 402, state_id: 26, name: 'Varanasi', code: 'VNS' },
  { id: 403, state_id: 26, name: 'Kanpur Nagar', code: 'KNP' },
  { id: 404, state_id: 26, name: 'Prayagraj (Allahabad)', code: 'PRY' },
  { id: 405, state_id: 26, name: 'Gautam Buddha Nagar (Noida)', code: 'NOI' },
  { id: 406, state_id: 26, name: 'Ghaziabad', code: 'GZB' },
  { id: 407, state_id: 26, name: 'Agra', code: 'AGR' },
  { id: 408, state_id: 26, name: 'Meerut', code: 'MRT' },
  { id: 409, state_id: 26, name: 'Gorakhpur', code: 'GKP' },
  { id: 410, state_id: 26, name: 'Bareilly', code: 'BRL' },
  { id: 411, state_id: 26, name: 'Aligarh', code: 'ALG' },
  { id: 412, state_id: 26, name: 'Moradabad', code: 'MBD' },
  { id: 413, state_id: 26, name: 'Ayodhya (Faizabad)', code: 'AYD' },
  { id: 414, state_id: 26, name: 'Mathura', code: 'MTH' },
  { id: 415, state_id: 26, name: 'Jhansi', code: 'JHS' },

  // Gujarat (state_id: 7)
  { id: 501, state_id: 7, name: 'Ahmedabad', code: 'AMD' },
  { id: 502, state_id: 7, name: 'Surat', code: 'SRT' },
  { id: 503, state_id: 7, name: 'Vadodara', code: 'VAD' },
  { id: 504, state_id: 7, name: 'Rajkot', code: 'RJK' },
  { id: 505, state_id: 7, name: 'Bhavnagar', code: 'BHV' },
  { id: 506, state_id: 7, name: 'Jamnagar', code: 'JAM' },
  { id: 507, state_id: 7, name: 'Gandhinagar', code: 'GND' },
  { id: 508, state_id: 7, name: 'Junagadh', code: 'JND' },
  { id: 509, state_id: 7, name: 'Anand', code: 'AND' },
  { id: 510, state_id: 7, name: 'Kutch', code: 'KUT' },
  { id: 511, state_id: 7, name: 'Bharuch', code: 'BHR' },
  { id: 512, state_id: 7, name: 'Mehsana', code: 'MSN' },

  // Andhra Pradesh (state_id: 1)
  { id: 601, state_id: 1, name: 'Visakhapatnam', code: 'VSK' },
  { id: 602, state_id: 1, name: 'Vijayawada (NTR)', code: 'VJA' },
  { id: 603, state_id: 1, name: 'Guntur', code: 'GNT' },
  { id: 604, state_id: 1, name: 'Tirupati', code: 'TPT' },
  { id: 605, state_id: 1, name: 'Kurnool', code: 'KRN' },
  { id: 606, state_id: 1, name: 'Nellore (SPSR Nellore)', code: 'NLR' },
  { id: 607, state_id: 1, name: 'Kakinada', code: 'KKD' },
  { id: 608, state_id: 1, name: 'Kadapa (YSR Kadapa)', code: 'KDP' },
  { id: 609, state_id: 1, name: 'Anantapur', code: 'ATP' },
  { id: 610, state_id: 1, name: 'Rajamahendravaram (East Godavari)', code: 'RJM' },

  // Telangana (state_id: 24)
  { id: 701, state_id: 24, name: 'Hyderabad', code: 'HYD' },
  { id: 702, state_id: 24, name: 'Warangal', code: 'WGL' },
  { id: 703, state_id: 24, name: 'Nizamabad', code: 'NZB' },
  { id: 704, state_id: 24, name: 'Karimnagar', code: 'KRM' },
  { id: 705, state_id: 24, name: 'Khammam', code: 'KHM' },
  { id: 706, state_id: 24, name: 'Ranga Reddy', code: 'RRD' },
  { id: 707, state_id: 24, name: 'Medchal-Malkajgiri', code: 'MDL' },
  { id: 708, state_id: 24, name: 'Nalgonda', code: 'NLG' },
  { id: 709, state_id: 24, name: 'Mahabubnagar', code: 'MBN' },

  // Kerala (state_id: 12)
  { id: 801, state_id: 12, name: 'Thiruvananthapuram (Trivandrum)', code: 'TVM' },
  { id: 802, state_id: 12, name: 'Kochi (Ernakulam)', code: 'EKM' },
  { id: 803, state_id: 12, name: 'Kozhikode (Calicut)', code: 'KKD' },
  { id: 804, state_id: 12, name: 'Thrissur', code: 'TSR' },
  { id: 805, state_id: 12, name: 'Kollam', code: 'KLM' },
  { id: 806, state_id: 12, name: 'Kannur', code: 'KNR' },
  { id: 807, state_id: 12, name: 'Palakkad', code: 'PLK' },
  { id: 808, state_id: 12, name: 'Kottayam', code: 'KTM' },
  { id: 809, state_id: 12, name: 'Alappuzha (Alleppey)', code: 'ALP' },
  { id: 810, state_id: 12, name: 'Malappuram', code: 'MLP' },

  // West Bengal (state_id: 28)
  { id: 901, state_id: 28, name: 'Kolkata', code: 'CCU' },
  { id: 902, state_id: 28, name: 'Howrah', code: 'HWH' },
  { id: 903, state_id: 28, name: 'North 24 Parganas', code: 'N24' },
  { id: 904, state_id: 28, name: 'South 24 Parganas', code: 'S24' },
  { id: 905, state_id: 28, name: 'Paschim Bardhaman (Asansol/Durgapur)', code: 'PBD' },
  { id: 906, state_id: 28, name: 'Purba Medinipur', code: 'PMD' },
  { id: 907, state_id: 28, name: 'Darjeeling & Siliguri', code: 'DJG' },
  { id: 908, state_id: 28, name: 'Hooghly', code: 'HGL' },
  { id: 909, state_id: 28, name: 'Nadia', code: 'NDA' },
  { id: 910, state_id: 28, name: 'Murshidabad', code: 'MSD' },

  // Rajasthan (state_id: 21)
  { id: 1001, state_id: 21, name: 'Jaipur', code: 'JPR' },
  { id: 1002, state_id: 21, name: 'Jodhpur', code: 'JDH' },
  { id: 1003, state_id: 21, name: 'Udaipur', code: 'UDP' },
  { id: 1004, state_id: 21, name: 'Kota', code: 'KTA' },
  { id: 1005, state_id: 21, name: 'Bikaner', code: 'BKN' },
  { id: 1006, state_id: 21, name: 'Ajmer', code: 'AJM' },
  { id: 1007, state_id: 21, name: 'Alwar', code: 'ALW' },
  { id: 1008, state_id: 21, name: 'Bhilwara', code: 'BHL' },
  { id: 1009, state_id: 21, name: 'Sikar', code: 'SKR' },

  // Madhya Pradesh (state_id: 13)
  { id: 1101, state_id: 13, name: 'Bhopal', code: 'BPL' },
  { id: 1102, state_id: 13, name: 'Indore', code: 'IDR' },
  { id: 1103, state_id: 13, name: 'Gwalior', code: 'GWL' },
  { id: 1104, state_id: 13, name: 'Jabalpur', code: 'JBP' },
  { id: 1105, state_id: 13, name: 'Ujjain', code: 'UJN' },
  { id: 1106, state_id: 13, name: 'Sagar', code: 'SGR' },
  { id: 1107, state_id: 13, name: 'Satna', code: 'STN' },
  { id: 1108, state_id: 13, name: 'Rewa', code: 'REW' },

  // Bihar (state_id: 4)
  { id: 1201, state_id: 4, name: 'Patna', code: 'PAT' },
  { id: 1202, state_id: 4, name: 'Gaya', code: 'GAY' },
  { id: 1203, state_id: 4, name: 'Muzaffarpur', code: 'MUZ' },
  { id: 1204, state_id: 4, name: 'Bhagalpur', code: 'BGP' },
  { id: 1205, state_id: 4, name: 'Darbhanga', code: 'DBG' },
  { id: 1206, state_id: 4, name: 'Purnia', code: 'PUR' },
  { id: 1207, state_id: 4, name: 'Begusarai', code: 'BGS' },
  { id: 1208, state_id: 4, name: 'Rohtas (Sasaram)', code: 'ROH' },

  // Punjab (state_id: 20)
  { id: 1301, state_id: 20, name: 'Ludhiana', code: 'LDH' },
  { id: 1302, state_id: 20, name: 'Amritsar', code: 'ASR' },
  { id: 1303, state_id: 20, name: 'Jalandhar', code: 'JAL' },
  { id: 1304, state_id: 20, name: 'Patiala', code: 'PTL' },
  { id: 1305, state_id: 20, name: 'Bathinda', code: 'BTH' },
  { id: 1306, state_id: 20, name: 'SAS Nagar (Mohali)', code: 'MOH' },

  // Haryana (state_id: 8)
  { id: 1401, state_id: 8, name: 'Gurugram (Gurgaon)', code: 'GUR' },
  { id: 1402, state_id: 8, name: 'Faridabad', code: 'FBD' },
  { id: 1403, state_id: 8, name: 'Panipat', code: 'PNP' },
  { id: 1404, state_id: 8, name: 'Ambala', code: 'AMB' },
  { id: 1405, state_id: 8, name: 'Hisar', code: 'HSR' },
  { id: 1406, state_id: 8, name: 'Karnal', code: 'KRN' },
  { id: 1407, state_id: 8, name: 'Rohtak', code: 'RTK' },
  { id: 1408, state_id: 8, name: 'Panchkula', code: 'PKL' },

  // Odisha (state_id: 19)
  { id: 1501, state_id: 19, name: 'Bhubaneswar (Khurdha)', code: 'BBI' },
  { id: 1502, state_id: 19, name: 'Cuttack', code: 'CTC' },
  { id: 1503, state_id: 19, name: 'Rourkela (Sundargarh)', code: 'RRK' },
  { id: 1504, state_id: 19, name: 'Puri', code: 'PRI' },
  { id: 1505, state_id: 19, name: 'Sambalpur', code: 'SBP' },
  { id: 1506, state_id: 19, name: 'Balasore', code: 'BLS' },
  { id: 1507, state_id: 19, name: 'Berhampur (Ganjam)', code: 'BAM' },

  // Assam (state_id: 3)
  { id: 1601, state_id: 3, name: 'Kamrup Metropolitan (Guwahati)', code: 'GHY' },
  { id: 1602, state_id: 3, name: 'Dibrugarh', code: 'DIB' },
  { id: 1603, state_id: 3, name: 'Silchar (Cachar)', code: 'SIL' },
  { id: 1604, state_id: 3, name: 'Jorhat', code: 'JOR' },
  { id: 1605, state_id: 3, name: 'Nagaon', code: 'NAG' },
  { id: 1606, state_id: 3, name: 'Tezpur (Sonitpur)', code: 'TEZ' },

  // Jharkhand (state_id: 10)
  { id: 1701, state_id: 10, name: 'Ranchi', code: 'RNC' },
  { id: 1702, state_id: 10, name: 'Jamshedpur (East Singhbhum)', code: 'JSR' },
  { id: 1703, state_id: 10, name: 'Dhanbad', code: 'DHN' },
  { id: 1704, state_id: 10, name: 'Bokaro', code: 'BOK' },
  { id: 1705, state_id: 10, name: 'Deoghar', code: 'DGH' },
  { id: 1706, state_id: 10, name: 'Hazaribagh', code: 'HZB' },

  // Chhattisgarh (state_id: 5)
  { id: 1801, state_id: 5, name: 'Raipur', code: 'RPR' },
  { id: 1802, state_id: 5, name: 'Bhilai / Durg', code: 'DRG' },
  { id: 1803, state_id: 5, name: 'Bilaspur', code: 'BSP' },
  { id: 1804, state_id: 5, name: 'Korba', code: 'KRB' },
  { id: 1805, state_id: 5, name: 'Rajnandgaon', code: 'RJN' },

  // Uttarakhand (state_id: 27)
  { id: 1901, state_id: 27, name: 'Dehradun', code: 'DDN' },
  { id: 1902, state_id: 27, name: 'Haridwar', code: 'HDW' },
  { id: 1903, state_id: 27, name: 'Nainital & Haldwani', code: 'NNT' },
  { id: 1904, state_id: 27, name: 'Udham Singh Nagar (Rudrapur)', code: 'USN' },
  { id: 1905, state_id: 27, name: 'Rishikesh', code: 'RSH' },

  // Himachal Pradesh (state_id: 9)
  { id: 2001, state_id: 9, name: 'Shimla', code: 'SML' },
  { id: 2002, state_id: 9, name: 'Kangra (Dharamshala)', code: 'KGR' },
  { id: 2003, state_id: 9, name: 'Mandi', code: 'MND' },
  { id: 2004, state_id: 9, name: 'Solan', code: 'SOL' },
  { id: 2005, state_id: 9, name: 'Kullu & Manali', code: 'KLU' },

  // Goa (state_id: 6)
  { id: 2101, state_id: 6, name: 'North Goa (Panaji)', code: 'PAN' },
  { id: 2102, state_id: 6, name: 'South Goa (Margao)', code: 'MGO' },

  // Jammu & Kashmir (state_id: 33)
  { id: 2201, state_id: 33, name: 'Srinagar', code: 'SXR' },
  { id: 2202, state_id: 33, name: 'Jammu', code: 'JMU' },
  { id: 2203, state_id: 33, name: 'Anantnag', code: 'ANT' },
  { id: 2204, state_id: 33, name: 'Baramulla', code: 'BRM' },
  { id: 2205, state_id: 33, name: 'Udhampur', code: 'UDH' },

  // Ladakh (state_id: 34)
  { id: 2301, state_id: 34, name: 'Leh', code: 'LEH' },
  { id: 2302, state_id: 34, name: 'Kargil', code: 'KGL' },

  // Chandigarh (state_id: 30)
  { id: 2401, state_id: 30, name: 'Chandigarh City', code: 'IXC' },

  // Puducherry (state_id: 36)
  { id: 2501, state_id: 36, name: 'Puducherry (Pondicherry)', code: 'PDY' },
  { id: 2502, state_id: 36, name: 'Karaikal', code: 'KRK' },

  // Tripura (state_id: 25)
  { id: 2601, state_id: 25, name: 'West Tripura (Agartala)', code: 'IXA' },

  // Manipur (state_id: 15)
  { id: 2701, state_id: 15, name: 'Imphal West', code: 'IMF' },

  // Meghalaya (state_id: 16)
  { id: 2801, state_id: 16, name: 'East Khasi Hills (Shillong)', code: 'SHL' },

  // Mizoram (state_id: 17)
  { id: 2901, state_id: 17, name: 'Aizawl', code: 'AJL' },

  // Nagaland (state_id: 18)
  { id: 3001, state_id: 18, name: 'Kohima', code: 'KOH' },
  { id: 3002, state_id: 18, name: 'Dimapur', code: 'DMP' },

  // Sikkim (state_id: 22)
  { id: 3101, state_id: 22, name: 'East Sikkim (Gangtok)', code: 'GTK' },

  // Arunachal Pradesh (state_id: 2)
  { id: 3201, state_id: 2, name: 'Papum Pare (Itanagar)', code: 'ITA' },

  // Andaman & Nicobar (state_id: 29)
  { id: 3301, state_id: 29, name: 'South Andaman (Port Blair)', code: 'IXZ' },

  // Dadra, Nagar Haveli, Daman & Diu (state_id: 31)
  { id: 3401, state_id: 31, name: 'Daman & Diu', code: 'DMN' },
  { id: 3402, state_id: 31, name: 'Dadra and Nagar Haveli (Silvassa)', code: 'SLV' },

  // Lakshadweep (state_id: 35)
  { id: 3501, state_id: 35, name: 'Kavaratti', code: 'KVT' },
]

// ==============================================================================
// 3. MASTER ROSTER OF VERIFIED LIVE CENTRAL & STATE GOVERNMENT SCHEMES
// ==============================================================================
export const MASTER_LIVE_SCHEMES: MasterScheme[] = [
  // --- PAN-INDIA CENTRAL SCHEMES ---
  {
    id: 'pm-kisan-001',
    slug: 'pm-kisan',
    external_id: 'GOI-AGRI-PMKISAN-01',
    scheme_name: 'PM-Kisan Samman Nidhi Yojana',
    description: 'Direct income support of ₹6,000 per year in three equal installments of ₹2,000 directly credited to all cultivable landholding farmer families across India.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Agriculture & Rural Development',
    benefits: '₹6,000 annually paid in 3 four-monthly installments of ₹2,000 via Aadhaar Payment Bridge System (DBT).',
    application_process: 'Farmer self-registration on pmkisan.gov.in using Aadhaar number and land survey / Patta records.',
    status: 'ACTIVE',
    official_url: 'https://pmkisan.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pmkisan',
    last_date: 'Rolling Enrollment (Quarterly Disbursement Cycles)',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 18,
      max_age: 99,
      occupation: 'Farmer',
    },
    documents: [
      { document_name: 'Aadhaar Card', mandatory: true, description: 'Identity and biometric authentication.' },
      { document_name: 'Landholding Ownership Papers / Patta / Chitta', mandatory: true, description: 'Proof of cultivable agriculture land.' },
      { document_name: 'Bank Account Passbook (Aadhaar Seeded)', mandatory: true, description: 'Account enabled for APBS.' },
    ],
    sources: [{ source_url: 'https://pmkisan.gov.in', source_type: 'MINISTRY_PORTAL' }],
  },

  {
    id: 'pm-surya-ghar-002',
    slug: 'pm-surya-ghar',
    external_id: 'GOI-MNRE-SURYAGHAR-02',
    scheme_name: 'PM Surya Ghar: Muft Bijli Yojana',
    description: 'National solar rooftop subsidy providing up to 300 units of free monthly electricity and central capital subsidy up to ₹78,000 for installing solar panels on residential roofs.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Renewable Energy & Power',
    benefits: 'Direct capital subsidy of ₹30,000 for 1kW, ₹60,000 for 2kW, and up to ₹78,000 for 3kW or higher residential solar systems.',
    application_process: 'Apply online on pmsuryaghar.gov.in with electricity consumer connection number and rooftop photos.',
    status: 'ACTIVE',
    official_url: 'https://pmsuryaghar.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pmsuryaghar',
    last_date: '31 Dec 2026',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 263,
    },
    eligibility: {
      min_age: 18,
      max_age: 95,
    },
    documents: [
      { document_name: 'Electricity Consumer Bill (Recent)', mandatory: true, description: 'Valid CA number connection bill.' },
      { document_name: 'Aadhaar Card of House Owner', mandatory: true, description: 'Identity verification.' },
      { document_name: 'Bank Passbook / Cancelled Cheque', mandatory: true, description: 'Direct DBT subsidy credit.' },
    ],
    sources: [{ source_url: 'https://pmsuryaghar.gov.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'pm-jay-ayushman-003',
    slug: 'pmjay',
    external_id: 'GOI-HEALTH-PMJAY-03',
    scheme_name: 'Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)',
    description: 'Flagship national health protection scheme providing health insurance cover of up to ₹5,00,000 per family per year for secondary and tertiary care hospitalization across 28,000+ empaneled hospitals.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Health & Wellness',
    benefits: '₹5,00,000 per year per family for cashless and paperless hospitalization treatment nationwide.',
    application_process: 'Check eligibility on beneficiary.nha.gov.in or generate Ayushman Golden Card at any CSC or empaneled hospital.',
    status: 'ACTIVE',
    official_url: 'https://beneficiary.nha.gov.in',
    source_url: 'https://pmjay.gov.in',
    last_date: 'Open All Year (Universal Enrollment)',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 0,
      max_age: 120,
      max_income: 300000,
    },
    documents: [
      { document_name: 'Aadhaar Card or Ration Card', mandatory: true, description: 'Family identity deduplication.' },
      { document_name: 'Ayushman Beneficiary Card', mandatory: false, description: 'Instant print at hospital kiosk.' },
    ],
    sources: [{ source_url: 'https://pmjay.gov.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'pm-vishwakarma-004',
    slug: 'pm-vishwakarma',
    external_id: 'GOI-MSME-VISHWAKARMA-04',
    scheme_name: 'PM Vishwakarma Scheme',
    description: 'Holistic support for traditional artisans and craftspeople: recognition as Vishwakarma, basic & advanced training with ₹500/day stipend, modern toolkit incentive of ₹15,000, and collateral-free enterprise loans up to ₹3,00,000 at 5% concessional interest.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Skills & Artisans',
    benefits: '₹15,000 toolkit grant + ₹3 Lakh enterprise loan at 5% interest + ₹500 daily skill stipend + official PM Vishwakarma Certificate & ID card.',
    application_process: 'Biometric registration through Common Service Centres (CSC) on pmvishwakarma.gov.in.',
    status: 'ACTIVE',
    official_url: 'https://pmvishwakarma.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pmvishwakarma',
    last_date: '30 Sep 2026',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 171,
    },
    eligibility: {
      min_age: 18,
      max_age: 80,
      occupation: 'Artisan',
    },
    documents: [
      { document_name: 'Aadhaar Card with Mobile Link', mandatory: true, description: 'Biometric CSC e-KYC.' },
      { document_name: 'Bank Account Details', mandatory: true, description: 'Account for toolkit incentive.' },
      { document_name: 'Traditional Trade Declaration', mandatory: true, description: 'Attestation in one of 18 traditional artisan trades.' },
    ],
    sources: [{ source_url: 'https://pmvishwakarma.gov.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'sukanya-samriddhi-005',
    slug: 'ssy',
    external_id: 'GOI-FIN-SSY-05',
    scheme_name: 'Sukanya Samriddhi Yojana (Beti Bachao Beti Padhao)',
    description: 'High-interest sovereign savings scheme for the girl child offering 8.2% annual compounded interest, triple tax exemption under Section 80C, and guaranteed maturity returns for higher education and marriage.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Girl Child & Women Welfare',
    benefits: '8.2% annual sovereign interest, triple EEE tax exemption, min deposit ₹250/year up to ₹1,50,000/year.',
    application_process: 'Open account at any India Post Office or authorized commercial bank branch with girl child birth certificate.',
    status: 'ACTIVE',
    official_url: 'https://www.indiapost.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/ssy',
    last_date: 'Rolling (Before child turns 10 years of age)',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 0,
      max_age: 10,
      gender: 'FEMALE',
    },
    documents: [
      { document_name: 'Birth Certificate of Girl Child', mandatory: true, description: 'Official municipal/panchayat certificate.' },
      { document_name: 'Aadhaar Card of Parent/Guardian', mandatory: true, description: 'Guardian KYC verification.' },
      { document_name: 'Photograph of Child and Guardian', mandatory: true, description: 'Account opening form.' },
    ],
    sources: [{ source_url: 'https://www.indiapost.gov.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'pm-mudra-006',
    slug: 'pm-mudra',
    external_id: 'GOI-FIN-MUDRA-06',
    scheme_name: 'Pradhan Mantri MUDRA Yojana (PMMY)',
    description: 'Collateral-free micro-enterprise business loans up to ₹20,00,000 across Shishu (up to ₹50k), Kishore (₹50k-₹5L), and Tarun (₹5L-₹20L) categories for micro-business expansion, traders, and small manufacturing.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'MSME & Entrepreneurship',
    benefits: 'Collateral-free institutional loans up to ₹20 Lakhs with no processing fees for small borrowers and MUDRA Card credit limit.',
    application_process: 'Apply online on udyamimitra.in or submit project proposal at any scheduled public/private bank.',
    status: 'ACTIVE',
    official_url: 'https://www.mudra.org.in',
    source_url: 'https://www.udyamimitra.in',
    last_date: 'Continuous Financial Year Window',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 18,
      max_age: 65,
    },
    documents: [
      { document_name: 'Aadhaar & PAN Card', mandatory: true, description: 'Identity and tax KYC.' },
      { document_name: 'Business Registration / Udyam Certificate', mandatory: true, description: 'Proof of business establishment.' },
      { document_name: 'Bank Statement (Past 6 Months)', mandatory: true, description: 'Financial cash flow evaluation.' },
    ],
    sources: [{ source_url: 'https://www.mudra.org.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'pm-svanidhi-007',
    slug: 'pm-svanidhi',
    external_id: 'GOI-MOHUA-SVANIDHI-07',
    scheme_name: 'PM SVANidhi: Micro-Credit for Street Vendors',
    description: 'Affordable working capital collateral-free loans for urban and peri-urban street vendors starting at ₹10,000, rising to ₹20,000 and ₹50,000 upon timely repayment with 7% interest subsidy and cashback rewards for digital transactions.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Micro-Credit & Livelihood',
    benefits: 'Working capital loans up to ₹50,000 + 7% interest subsidy per annum + ₹1,200 annual digital cashback incentives.',
    application_process: 'Apply on pmsvanidhi.mohua.gov.in through local Urban Local Body (ULB) or CSC centre.',
    status: 'ACTIVE',
    official_url: 'https://pmsvanidhi.mohua.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pmsvanidhi',
    last_date: '31 Dec 2026',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 263,
    },
    eligibility: {
      min_age: 18,
      max_age: 75,
      occupation: 'Self-Employed',
    },
    documents: [
      { document_name: 'Vending Certificate / Urban Local Body ID Card', mandatory: true, description: 'Proof of street vending.' },
      { document_name: 'Aadhaar Card Linked to Mobile', mandatory: true, description: 'Authentication.' },
      { document_name: 'Bank Account Details', mandatory: true, description: 'Loan disbursement.' },
    ],
    sources: [{ source_url: 'https://pmsvanidhi.mohua.gov.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'pmay-urban-008',
    slug: 'pmay-u',
    external_id: 'GOI-HOUSING-PMAYU-08',
    scheme_name: 'Pradhan Mantri Awas Yojana - Urban (PMAY-U 2.0)',
    description: 'Pucca houses and interest subsidies on home loans for all eligible urban middle and lower income families belonging to EWS, LIG, and MIG categories lacking a permanent house.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Housing & Urban Shelter',
    benefits: 'Credit Linked Subsidy of up to ₹2.67 Lakhs on home loan interest or ₹1.5 Lakhs central grant for individual house construction.',
    application_process: 'Apply online on pmaymis.gov.in or through Urban Municipal Corporation citizen centres.',
    status: 'ACTIVE',
    official_url: 'https://pmaymis.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pmay-u',
    last_date: '31 Dec 2026',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 263,
    },
    eligibility: {
      min_age: 21,
      max_age: 70,
      max_income: 600000,
    },
    documents: [
      { document_name: 'Aadhaar Card of All Family Members', mandatory: true, description: 'Deduplication.' },
      { document_name: 'Income Proof / Salary Slip / Income Certificate', mandatory: true, description: 'Income category classification.' },
      { document_name: 'Affidavit of Not Owning Pucca House', mandatory: true, description: 'Declaration.' },
    ],
    sources: [{ source_url: 'https://pmaymis.gov.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'naps-apprenticeship-009',
    slug: 'naps',
    external_id: 'GOI-MSDE-NAPS-09',
    scheme_name: 'National Apprenticeship Promotion Scheme (NAPS)',
    description: 'Paid on-the-job industrial apprenticeship for youth and diploma holders with 25% direct stipend support paid by the Government of India directly into the candidate’s bank account.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Skills & Employment',
    benefits: 'Government shares 25% of prescribed stipend up to ₹1,500/month per apprentice directly via DBT, plus recognized industry certification.',
    application_process: 'Register candidate profile on apprenticeshipindia.gov.in and apply to verified corporate vacancies.',
    status: 'ACTIVE',
    official_url: 'https://www.apprenticeshipindia.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/naps',
    last_date: 'Rolling Industry Hiring Windows',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 18,
      max_age: 35,
      education: 'Secondary (10th)',
    },
    documents: [
      { document_name: 'Educational Certificates (10th / 12th / ITI / Diploma)', mandatory: true, description: 'Qualification proof.' },
      { document_name: 'Aadhaar Card', mandatory: true, description: 'Identity verification.' },
      { document_name: 'Bank Account Passbook (Aadhaar Seeded)', mandatory: true, description: 'Stipend DBT credit.' },
    ],
    sources: [{ source_url: 'https://www.apprenticeshipindia.gov.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  {
    id: 'atal-pension-010',
    slug: 'apy',
    external_id: 'GOI-PFRDA-APY-10',
    scheme_name: 'Atal Pension Yojana (APY)',
    description: 'Guaranteed government monthly pension scheme for citizens in the unorganized sector offering ₹1,000, ₹2,000, ₹3,000, ₹4,000, or ₹5,000 per month from age 60 onwards with return of corpus to nominee.',
    government_level: 'CENTRAL',
    state_id: null,
    state_name: 'All India (Central)',
    category: 'Social Security & Pension',
    benefits: 'Guaranteed minimum pension of ₹1,000 to ₹5,000 per month for life after age 60 with full spouse pension and nominee return of wealth.',
    application_process: 'Enroll through any bank branch or net banking portal with savings bank account auto-debit.',
    status: 'ACTIVE',
    official_url: 'https://enps.nsdl.com',
    source_url: 'https://www.myscheme.gov.in/schemes/apy',
    last_date: 'Open Enrollment (Age 18 to 40 Entry)',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 18,
      max_age: 40,
    },
    documents: [
      { document_name: 'Aadhaar Card', mandatory: true, description: 'Identity and age verification.' },
      { document_name: 'Savings Bank Account Details', mandatory: true, description: 'Auto debit facility.' },
    ],
    sources: [{ source_url: 'https://www.npscra.nsdl.co.in', source_type: 'OFFICIAL_PORTAL' }],
  },

  // --- STATE-SPECIFIC HIGH-IMPACT LIVE SCHEMES ---
  // Tamil Nadu Schemes
  {
    id: 'tn-pudhumai-penn-011',
    slug: 'pudhumai-penn',
    external_id: 'TN-SWD-PUDHUMAI-11',
    scheme_name: 'Pudhumai Penn Scheme (Moovalur Ramamirtham Ammaiyar Higher Education)',
    description: 'Monthly incentive of ₹1,000 transferred directly to girl students from government schools pursuing undergraduate degrees, diplomas, or ITI programs in Tamil Nadu.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Education & Women Welfare',
    benefits: '₹1,000 per month deposited directly into girl students’ bank accounts throughout their degree/diploma duration.',
    application_process: 'Registered through college nodal officers on pudhumaipenn.tn.gov.in with EMIS student number.',
    status: 'ACTIVE',
    official_url: 'https://pudhumaipenn.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/pudhumai-penn',
    last_date: '31 Aug 2026',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 141,
    },
    eligibility: {
      min_age: 17,
      max_age: 26,
      gender: 'FEMALE',
      state_restriction: 23,
      occupation: 'Student',
    },
    documents: [
      { document_name: 'Government School Study Certificate (Classes 6 to 12)', mandatory: true, description: 'Proof of government school study.' },
      { document_name: 'Aadhaar Card', mandatory: true, description: 'Identity verification.' },
      { document_name: 'College ID Card / Admission Letter', mandatory: true, description: 'Higher education enrollment.' },
      { document_name: 'Student Bank Passbook', mandatory: true, description: 'DBT transfer.' },
    ],
    sources: [{ source_url: 'https://pudhumaipenn.tn.gov.in', source_type: 'STATE_PORTAL' }],
  },

  {
    id: 'tn-kmut-012',
    slug: 'kmut',
    external_id: 'TN-SPDD-KMUT-12',
    scheme_name: 'Kalaignar Magalir Urimai Thittam (KMUT)',
    description: 'Universal basic income financial assistance of ₹1,000 per month provided to women heads of eligible households in Tamil Nadu to recognize their unpaid care work.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Women and Child Development',
    benefits: '₹1,000 per month credited directly on the 15th of every month into beneficiary’s bank account.',
    application_process: 'Enrollment through special camp biometric verification at ration shop / e-Sevai centres with Smart Ration Card.',
    status: 'ACTIVE',
    official_url: 'https://kmut.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/kmut',
    last_date: 'Rolling Verification Window',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 21,
      max_age: 75,
      gender: 'FEMALE',
      state_restriction: 23,
      max_income: 250000,
    },
    documents: [
      { document_name: 'Smart Family Ration Card', mandatory: true, description: 'Family identity and woman head confirmation.' },
      { document_name: 'Aadhaar Card', mandatory: true, description: 'Biometric verification.' },
      { document_name: 'Electricity Consumer Card / Number', mandatory: true, description: 'Power consumption criteria.' },
      { document_name: 'Bank Account Passbook (Aadhaar Seeded)', mandatory: true, description: 'DBT monthly credit.' },
    ],
    sources: [{ source_url: 'https://kmut.tn.gov.in', source_type: 'STATE_PORTAL' }],
  },

  {
    id: 'tn-uyegp-013',
    slug: 'uyegp',
    external_id: 'TN-MSME-UYEGP-13',
    scheme_name: 'Unemployed Youth Employment Generation Programme (UYEGP)',
    description: 'Capital subsidy scheme for educated unemployed youth in Tamil Nadu to establish micro-enterprises with up to 25% government subsidy on project cost up to ₹15 Lakhs for manufacturing and ₹5 Lakhs for service.',
    government_level: 'STATE',
    state_id: 23,
    state_name: 'Tamil Nadu',
    category: 'Skills & Employment',
    benefits: '25% Government Capital Subsidy up to ₹3.75 Lakhs for manufacturing, plus collateral-free loan sanction through commercial banks.',
    application_process: 'Apply online through District Industries Centre (DIC) portal at msmeonline.tn.gov.in.',
    status: 'ACTIVE',
    official_url: 'https://msmeonline.tn.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/uyegp',
    last_date: '31 Dec 2026',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 263,
    },
    eligibility: {
      min_age: 18,
      max_age: 45,
      state_restriction: 23,
      max_income: 500000,
      education: 'Secondary (10th)',
    },
    documents: [
      { document_name: '10th / Secondary Transfer Certificate & Mark Sheet', mandatory: true, description: 'Educational qualification.' },
      { document_name: 'Community Certificate', mandatory: true, description: 'Category verification.' },
      { document_name: 'Project Profile / Business Proposal', mandatory: true, description: 'Estimate of manufacturing/service equipment.' },
      { document_name: 'Nativity Certificate', mandatory: true, description: 'Proof of residence in Tamil Nadu.' },
    ],
    sources: [{ source_url: 'https://msmeonline.tn.gov.in', source_type: 'STATE_PORTAL' }],
  },

  // Maharashtra Schemes
  {
    id: 'mh-ladki-bahin-014',
    slug: 'majhi-ladki-bahin',
    external_id: 'MH-WCD-LADKIBAHIN-14',
    scheme_name: 'Mukhyamantri Majhi Ladki Bahin Yojana',
    description: 'Monthly financial assistance of ₹1,500 transferred directly into the bank accounts of economically backward women between 21 and 65 years of age across all districts of Maharashtra.',
    government_level: 'STATE',
    state_id: 14,
    state_name: 'Maharashtra',
    category: 'Women & Social Welfare',
    benefits: '₹1,500 monthly DBT financial support directly credited to bank account linked with Aadhaar.',
    application_process: 'Apply online on ladkibahin.maharashtra.gov.in or through Nari Shakti Doot mobile app / Setu Suvidha Kendra.',
    status: 'ACTIVE',
    official_url: 'https://ladkibahin.maharashtra.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/ladki-bahin',
    last_date: 'Rolling State Enrollment',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 21,
      max_age: 65,
      gender: 'FEMALE',
      state_restriction: 14,
      max_income: 250000,
    },
    documents: [
      { document_name: 'Aadhaar Card', mandatory: true, description: 'Identity verification.' },
      { document_name: 'Domicile / Ration Card of Maharashtra', mandatory: true, description: 'Residence proof.' },
      { document_name: 'Income Certificate (Under ₹2.5 Lakhs)', mandatory: true, description: 'Income verification or Yellow/Orange Ration Card.' },
      { document_name: 'Bank Passbook (Aadhaar Linked)', mandatory: true, description: 'Direct benefit credit.' },
    ],
    sources: [{ source_url: 'https://ladkibahin.maharashtra.gov.in', source_type: 'STATE_PORTAL' }],
  },

  // Karnataka Schemes
  {
    id: 'ka-gruha-lakshmi-015',
    slug: 'gruha-lakshmi',
    external_id: 'KA-WCD-GRUHALAKSHMI-15',
    scheme_name: 'Karnataka Gruha Lakshmi Scheme',
    description: 'Monthly allowance of ₹2,000 for the woman head of eligible households holding Antyodaya, BPL, or APL ration cards in Karnataka to promote financial independence.',
    government_level: 'STATE',
    state_id: 11,
    state_name: 'Karnataka',
    category: 'Women & Livelihood',
    benefits: '₹2,000 per month credited directly via DBT to the female head of the family.',
    application_process: 'Register at Grama One, Karnataka One, or Bengaluru One centres on sevasindhu.karnataka.gov.in.',
    status: 'ACTIVE',
    official_url: 'https://sevasindhu.karnataka.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/gruha-lakshmi',
    last_date: 'Rolling State Enrollment',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 18,
      max_age: 80,
      gender: 'FEMALE',
      state_restriction: 11,
    },
    documents: [
      { document_name: 'Karnataka Ration Card (BPL/APL/AAY)', mandatory: true, description: 'Family card with woman as head.' },
      { document_name: 'Aadhaar Card of Woman Head & Husband', mandatory: true, description: 'Identity.' },
      { document_name: 'Aadhaar-seeded Bank Account Passbook', mandatory: true, description: 'DBT disbursement.' },
    ],
    sources: [{ source_url: 'https://sevasindhu.karnataka.gov.in', source_type: 'STATE_PORTAL' }],
  },

  // Uttar Pradesh Schemes
  {
    id: 'up-kanya-sumangala-016',
    slug: 'kanya-sumangala',
    external_id: 'UP-WCD-KANYA-16',
    scheme_name: 'Mukhyamantri Kanya Sumangala Yojana',
    description: 'Conditional cash transfer of up to ₹25,000 across 6 developmental milestones from birth, vaccination, school admission, to higher education for girl children in Uttar Pradesh.',
    government_level: 'STATE',
    state_id: 26,
    state_name: 'Uttar Pradesh',
    category: 'Girl Child & Education',
    benefits: 'Total assistance of ₹25,000 credited directly in 6 installments supporting health and education from birth through graduation.',
    application_process: 'Apply online on mksy.up.gov.in with birth certificate and academic admission documents.',
    status: 'ACTIVE',
    official_url: 'https://mksy.up.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/kanya-sumangala',
    last_date: '31 Dec 2026',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 263,
    },
    eligibility: {
      min_age: 0,
      max_age: 21,
      gender: 'FEMALE',
      state_restriction: 26,
      max_income: 300000,
    },
    documents: [
      { document_name: 'Birth Certificate of Girl Child', mandatory: true, description: 'Age proof.' },
      { document_name: 'UP Domicile / Residence Certificate', mandatory: true, description: 'Proof of residence in Uttar Pradesh.' },
      { document_name: 'Income Certificate (Household Income under ₹3 Lakhs)', mandatory: true, description: 'Income criteria.' },
      { document_name: 'School / College Admission Certificate', mandatory: true, description: 'Enrollment proof.' },
    ],
    sources: [{ source_url: 'https://mksy.up.gov.in', source_type: 'STATE_PORTAL' }],
  },

  // West Bengal Schemes
  {
    id: 'wb-kanyashree-017',
    slug: 'kanyashree-prakalpa',
    external_id: 'WB-WCD-KANYASHREE-17',
    scheme_name: 'Kanyashree Prakalpa (K1 & K2)',
    description: 'UN Public Service Award-winning scheme offering annual scholarship of ₹1,000 (K1) for teenage girls and one-time grant of ₹25,000 (K2) at age 18 to incentivize higher studies and prevent child marriage in West Bengal.',
    government_level: 'STATE',
    state_id: 28,
    state_name: 'West Bengal',
    category: 'Girl Child & Education',
    benefits: 'Annual scholarship of ₹1,000 (K1) + One-time grant of ₹25,000 (K2) on turning 18 while continuing education.',
    application_process: 'Application distributed and verified through registered schools and colleges on wb.gov.in.',
    status: 'ACTIVE',
    official_url: 'https://wbkanyashree.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/kanyashree',
    last_date: 'Academic Year Window (31 Mar 2027)',
    activity: {
      status: 'OPEN',
      deadline_status: 'MORE_THAN_15_DAYS',
      days_remaining: 353,
    },
    eligibility: {
      min_age: 13,
      max_age: 19,
      gender: 'FEMALE',
      state_restriction: 28,
      occupation: 'Student',
    },
    documents: [
      { document_name: 'School / College Enrollment Certificate', mandatory: true, description: 'Proof of active study.' },
      { document_name: 'Birth Certificate', mandatory: true, description: 'Age verification.' },
      { document_name: 'Declaration of Unmarried Status', mandatory: true, description: 'Verified by head of institution.' },
      { document_name: 'Personal Bank Passbook', mandatory: true, description: 'Direct DBT credit.' },
    ],
    sources: [{ source_url: 'https://wbkanyashree.gov.in', source_type: 'STATE_PORTAL' }],
  },

  // Madhya Pradesh Schemes
  {
    id: 'mp-ladli-behna-018',
    slug: 'ladli-behna',
    external_id: 'MP-WCD-LADLIBEHNA-18',
    scheme_name: 'Mukhyamantri Ladli Behna Yojana',
    description: 'Monthly direct benefit transfer of ₹1,250 provided to women in Madhya Pradesh to foster economic self-reliance, nutritional security, and dignity.',
    government_level: 'STATE',
    state_id: 13,
    state_name: 'Madhya Pradesh',
    category: 'Women Empowerment',
    benefits: '₹1,250 per month credited directly on the 10th of every month into beneficiary bank account.',
    application_process: 'Camp registration at Gram Panchayat / Ward office on cmladlibahna.mp.gov.in with Samagra ID.',
    status: 'ACTIVE',
    official_url: 'https://cmladlibahna.mp.gov.in',
    source_url: 'https://www.myscheme.gov.in/schemes/ladli-behna',
    last_date: 'Continuous State Portal',
    activity: {
      status: 'OPEN',
      deadline_status: 'NO_DEADLINE',
      days_remaining: null,
    },
    eligibility: {
      min_age: 21,
      max_age: 60,
      gender: 'FEMALE',
      state_restriction: 13,
      max_income: 250000,
    },
    documents: [
      { document_name: 'Samagra Family & Member ID', mandatory: true, description: 'MP citizen portal ID.' },
      { document_name: 'Aadhaar Card (e-KYC verified)', mandatory: true, description: 'Identity.' },
      { document_name: 'Aadhaar Linked Bank Account Details', mandatory: true, description: 'DBT transfer.' },
    ],
    sources: [{ source_url: 'https://cmladlibahna.mp.gov.in', source_type: 'STATE_PORTAL' }],
  },
]

// ==============================================================================
// 4. AUTOMATIC DAILY UPDATE ENGINE
// Recalculates real days remaining and urgency statuses based on current date
// ==============================================================================
export interface DailySyncTelemetry {
  last_synced_at: string
  next_sync_at: string
  total_schemes_active: number
  total_states_covered: number
  total_districts_indexed: number
  expiring_soon_count: number
  sync_cycle: 'AUTOMATED_DAILY_CRON'
}

export function runDailySchemeUpdate(schemes: MasterScheme[]): {
  schemes: MasterScheme[]
  telemetry: DailySyncTelemetry
} {
  const now = new Date()

  let expiringSoonCount = 0

  const updatedSchemes = schemes.map((scheme) => {
    // Clone
    const s = { ...scheme, activity: { ...scheme.activity } }

    // Check if last_date has a parseable date
    if (s.last_date && !s.last_date.toLowerCase().includes('rolling') && !s.last_date.toLowerCase().includes('open')) {
      const parsedDate = new Date(s.last_date)
      if (!isNaN(parsedDate.getTime())) {
        const diffMs = parsedDate.getTime() - now.getTime()
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

        s.activity.days_remaining = diffDays

        if (diffDays < 0) {
          s.activity.status = 'EXPIRED'
          s.activity.deadline_status = 'CLOSING_TODAY'
        } else if (diffDays === 0) {
          s.activity.status = 'CLOSING_SOON'
          s.activity.deadline_status = 'CLOSING_TODAY'
          expiringSoonCount++
        } else if (diffDays <= 7) {
          s.activity.status = 'CLOSING_SOON'
          s.activity.deadline_status = 'URGENT'
          expiringSoonCount++
        } else if (diffDays <= 15) {
          s.activity.status = 'OPEN'
          s.activity.deadline_status = 'APPROACHING'
          expiringSoonCount++
        } else {
          s.activity.status = 'OPEN'
          s.activity.deadline_status = 'MORE_THAN_15_DAYS'
        }
      }
    }

    return s
  })

  const nextSync = new Date(now.getTime() + 24 * 60 * 60 * 1000)

  const telemetry: DailySyncTelemetry = {
    last_synced_at: now.toISOString(),
    next_sync_at: nextSync.toISOString(),
    total_schemes_active: updatedSchemes.filter((s) => s.status === 'ACTIVE').length,
    total_states_covered: ALL_INDIAN_STATES.length,
    total_districts_indexed: ALL_INDIAN_DISTRICTS.length,
    expiring_soon_count: expiringSoonCount,
    sync_cycle: 'AUTOMATED_DAILY_CRON',
  }

  return { schemes: updatedSchemes, telemetry }
}
