// Comprehensive Indian States, Union Territories, Districts and Major Cities
// Covers all 28 States and 8 Union Territories with official administrative districts

export const ALL_INDIAN_STATES = [
  { id: 1, name: 'Andhra Pradesh', code: 'AP', type: 'STATE', capital: 'Amaravati' },
  { id: 2, name: 'Arunachal Pradesh', code: 'AR', type: 'STATE', capital: 'Itanagar' },
  { id: 3, name: 'Assam', code: 'AS', type: 'STATE', capital: 'Dispur' },
  { id: 4, name: 'Bihar', code: 'BR', type: 'STATE', capital: 'Patna' },
  { id: 5, name: 'Chhattisgarh', code: 'CG', type: 'STATE', capital: 'Raipur' },
  { id: 6, name: 'Goa', code: 'GA', type: 'STATE', capital: 'Panaji' },
  { id: 7, name: 'Gujarat', code: 'GJ', type: 'STATE', capital: 'Gandhinagar' },
  { id: 8, name: 'Haryana', code: 'HR', type: 'STATE', capital: 'Chandigarh' },
  { id: 9, name: 'Himachal Pradesh', code: 'HP', type: 'STATE', capital: 'Shimla' },
  { id: 10, name: 'Jharkhand', code: 'JH', type: 'STATE', capital: 'Ranchi' },
  { id: 11, name: 'Karnataka', code: 'KA', type: 'STATE', capital: 'Bengaluru' },
  { id: 12, name: 'Kerala', code: 'KL', type: 'STATE', capital: 'Thiruvananthapuram' },
  { id: 13, name: 'Madhya Pradesh', code: 'MP', type: 'STATE', capital: 'Bhopal' },
  { id: 14, name: 'Maharashtra', code: 'MH', type: 'STATE', capital: 'Mumbai' },
  { id: 15, name: 'Manipur', code: 'MN', type: 'STATE', capital: 'Imphal' },
  { id: 16, name: 'Meghalaya', code: 'ML', type: 'STATE', capital: 'Shillong' },
  { id: 17, name: 'Mizoram', code: 'MZ', type: 'STATE', capital: 'Aizawl' },
  { id: 18, name: 'Nagaland', code: 'NL', type: 'STATE', capital: 'Kohima' },
  { id: 19, name: 'Odisha', code: 'OD', type: 'STATE', capital: 'Bhubaneswar' },
  { id: 20, name: 'Punjab', code: 'PB', type: 'STATE', capital: 'Chandigarh' },
  { id: 21, name: 'Rajasthan', code: 'RJ', type: 'STATE', capital: 'Jaipur' },
  { id: 22, name: 'Sikkim', code: 'SK', type: 'STATE', capital: 'Gangtok' },
  { id: 23, name: 'Tamil Nadu', code: 'TN', type: 'STATE', capital: 'Chennai' },
  { id: 24, name: 'Telangana', code: 'TS', type: 'STATE', capital: 'Hyderabad' },
  { id: 25, name: 'Tripura', code: 'TR', type: 'STATE', capital: 'Agartala' },
  { id: 26, name: 'Uttar Pradesh', code: 'UP', type: 'STATE', capital: 'Lucknow' },
  { id: 27, name: 'Uttarakhand', code: 'UK', type: 'STATE', capital: 'Dehradun' },
  { id: 28, name: 'West Bengal', code: 'WB', type: 'STATE', capital: 'Kolkata' },
  { id: 29, name: 'Andaman and Nicobar Islands', code: 'AN', type: 'UT', capital: 'Port Blair' },
  { id: 30, name: 'Chandigarh', code: 'CH', type: 'UT', capital: 'Chandigarh' },
  { id: 31, name: 'Dadra and Nagar Haveli and Daman and Diu', code: 'DN', type: 'UT', capital: 'Daman' },
  { id: 32, name: 'Delhi', code: 'DL', type: 'UT', capital: 'New Delhi' },
  { id: 33, name: 'Jammu and Kashmir', code: 'JK', type: 'UT', capital: 'Srinagar / Jammu' },
  { id: 34, name: 'Ladakh', code: 'LA', type: 'UT', capital: 'Leh' },
  { id: 35, name: 'Lakshadweep', code: 'LD', type: 'UT', capital: 'Kavaratti' },
  { id: 36, name: 'Puducherry', code: 'PY', type: 'UT', capital: 'Puducherry' },
]

export const STATE_DISTRICTS_MAP = {
  // 1. Andhra Pradesh (26 districts)
  1: [
    'Alluri Sitharama Raju', 'Anakapalli', 'Ananthapuramu', 'Annamayya', 'Bapatla',
    'Chittoor', 'East Godavari (Rajamahendravaram)', 'Eluru', 'Guntur', 'Kakinada',
    'Konaseema (Amalapuram)', 'Krishna (Machilipatnam)', 'Kurnool', 'Nandyal',
    'NTR (Vijayawada)', 'Palnadu (Narasaraopet)', 'Parvathipuram Manyam', 'Prakasam (Ongole)',
    'Sri Potti Sriramulu Nellore', 'Sri Sathya Sai (Puttaparthi)', 'Srikakulam',
    'Tirupati', 'Visakhapatnam', 'Vizianagaram', 'West Godavari (Bhimavaram)', 'YSR Kadapa'
  ],

  // 2. Arunachal Pradesh (26 districts)
  2: [
    'Anjaw', 'Changlang', 'Dibang Valley', 'East Kameng (Seppa)', 'East Siang (Pasighat)',
    'Itanagar Capital Complex', 'Kamle', 'Kra Daadi', 'Kurung Kumey', 'Lepa Rada',
    'Lohit (Tezu)', 'Longding', 'Lower Dibang Valley (Roing)', 'Lower Siang',
    'Lower Subansiri (Ziro)', 'Namsai', 'Pakke Kessang', 'Papum Pare (Yupia)',
    'Shi Yomi', 'Siang', 'Tawang', 'Tirap (Khonsa)', 'Upper Siang (Yingkiong)',
    'Upper Subansiri (Daporijo)', 'West Kameng (Bomdila)', 'West Siang (Aalo)'
  ],

  // 3. Assam (35 districts)
  3: [
    'Baksa', 'Bajali', 'Barpeta', 'Biswanath', 'Bongaigaon', 'Cachar (Silchar)',
    'Charaideo', 'Chirang', 'Darrang (Mangaldai)', 'Dhemaji', 'Dhubri', 'Dibrugarh',
    'Dima Hasao (Haflong)', 'Goalpara', 'Golaghat', 'Hailakandi', 'Hojai', 'Jorhat',
    'Kamrup (Amingaon)', 'Kamrup Metropolitan (Guwahati)', 'Karbi Anglong (Diphu)',
    'Karimganj', 'Kokrajhar', 'Lakhimpur (North Lakhimpur)', 'Majuli', 'Morigaon',
    'Nagaon', 'Nalbari', 'Sivasagar', 'Sonitpur (Tezpur)', 'South Salmara-Mankachar',
    'Tamulpur', 'Tinsukia', 'Udalguri', 'West Karbi Anglong (Hamren)'
  ],

  // 4. Bihar (38 districts)
  4: [
    'Araria', 'Arwal', 'Aurangabad', 'Banka', 'Begusarai', 'Bhagalpur', 'Bhojpur (Ara)',
    'Buxar', 'Darbhanga', 'East Champaran (Motihari)', 'Gaya', 'Gopalganj', 'Jamui',
    'Jehanabad', 'Kaimur (Bhabua)', 'Katihar', 'Khagaria', 'Kishanganj', 'Lakhisarai',
    'Madhepura', 'Madhubani', 'Munger', 'Muzaffarpur', 'Nalanda (Bihar Sharif)',
    'Nawada', 'Patna', 'Purnia', 'Rohtas (Sasaram)', 'Saharsa', 'Samastipur',
    'Saran (Chhapra)', 'Sheikhpura', 'Sheohar', 'Sitamarhi', 'Siwan', 'Supaul',
    'Vaishali (Hajipur)', 'West Champaran (Bettiah)'
  ],

  // 5. Chhattisgarh (33 districts)
  5: [
    'Balod', 'Baloda Bazar-Bhatapara', 'Balrampur-Ramanujganj', 'Bastar (Jagdalpur)',
    'Bemetara', 'Bijapur', 'Bilaspur', 'Dakshin Bastar Dantewada', 'Dhamtari',
    'Durg', 'Gariaband', 'Gaurela-Pendra-Marwahi', 'Janjgir-Champa', 'Jashpur',
    'Kabirdham (Kawardha)', 'Kanker (Uttar Bastar)', 'Khairagarh-Chhuikhadan-Gandai',
    'Kondagaon', 'Korba', 'Koriya (Baikunthpur)', 'Mahasamund', 'Manendragarh-Chirmiri-Bharatpur',
    'Mohla-Manpur-Ambagarh Chowki', 'Mungeli', 'Narayanpur', 'Raigarh', 'Raipur',
    'Rajnandgaon', 'Sakti', 'Sarangarh-Bilaigarh', 'Sukma', 'Surajpur', 'Surguja (Ambikapur)'
  ],

  // 6. Goa (2 districts)
  6: [
    'North Goa (Panaji / Mapusa)', 'South Goa (Margao / Vasco da Gama)'
  ],

  // 7. Gujarat (33 districts)
  7: [
    'Ahmedabad', 'Amreli', 'Anand', 'Aravalli (Modasa)', 'Banaskantha (Palanpur)',
    'Bharuch', 'Bhavnagar', 'Botad', 'Chhota Udaipur', 'Dahod', 'Dang (Ahwa)',
    'Devbhumi Dwarka (Khambhalia)', 'Gandhinagar', 'Gir Somnath (Veraval)', 'Jamnagar',
    'Junagadh', 'Kheda (Nadiad)', 'Kutch (Bhuj)', 'Mahisagar (Lunawada)', 'Mehsana',
    'Morbi', 'Narmada (Rajpipla)', 'Navsari', 'Panchmahal (Godhra)', 'Patan',
    'Porbandar', 'Rajkot', 'Sabarkantha (Himmatnagar)', 'Surat', 'Surendranagar',
    'Tapi (Vyara)', 'Vadodara', 'Valsad'
  ],

  // 8. Haryana (22 districts)
  8: [
    'Ambala', 'Bhiwani', 'Charkhi Dadri', 'Faridabad', 'Fatehabad', 'Gurugram',
    'Hisar', 'Jhajjar', 'Jind', 'Kaithal', 'Karnal', 'Kurukshetra', 'Mahendragarh (Narnaul)',
    'Nuh (Mewat)', 'Palwal', 'Panchkula', 'Panipat', 'Rewari', 'Rohtak', 'Sirsa',
    'Sonipat', 'Yamunanagar'
  ],

  // 9. Himachal Pradesh (12 districts)
  9: [
    'Bilaspur', 'Chamba', 'Hamirpur', 'Kangra (Dharamshala)', 'Kinnaur (Reckong Peo)',
    'Kullu', 'Lahaul and Spiti (Keylong)', 'Mandi', 'Shimla', 'Sirmaur (Nahan)',
    'Solan', 'Una'
  ],

  // 10. Jharkhand (24 districts)
  10: [
    'Bokaro', 'Chatra', 'Deoghar', 'Dhanbad', 'Dumka', 'East Singhbhum (Jamshedpur)',
    'Garhwa', 'Giridih', 'Godda', 'Gumla', 'Hazaribagh', 'Jamtara', 'Khunti',
    'Koderma', 'Latehar', 'Lohardaga', 'Pakur', 'Palamu (Medininagar)', 'Ramgarh',
    'Ranchi', 'Sahibganj', 'Seraikela Kharsawan', 'Simdega', 'West Singhbhum (Chaibasa)'
  ],

  // 11. Karnataka (31 districts)
  11: [
    'Bagalkote', 'Ballari (Bellary)', 'Belagavi (Belgaum)', 'Bengaluru Rural',
    'Bengaluru Urban (Bangalore)', 'Bidar', 'Chamarajanagar', 'Chikkaballapura',
    'Chikkamagaluru', 'Chitradurga', 'Dakshina Kannada (Mangaluru)', 'Davanagere',
    'Dharwad (Hubballi)', 'Gadag', 'Hassan', 'Haveri', 'Kalaburagi (Gulbarga)',
    'Kodagu (Madikeri)', 'Kolar', 'Koppal', 'Mandya', 'Mysuru (Mysore)',
    'Raichur', 'Ramanagara', 'Shivamogga (Shimoga)', 'Tumakuru (Tumkur)',
    'Udupi', 'Uttara Kannada (Karwar)', 'Vijayanagara (Hosapete)', 'Vijayapura (Bijapur)',
    'Yadgir'
  ],

  // 12. Kerala (14 districts)
  12: [
    'Alappuzha', 'Ernakulam (Kochi)', 'Idukki (Painavu)', 'Kannur', 'Kasaragod',
    'Kollam', 'Kottayam', 'Kozhikode (Calicut)', 'Malappuram', 'Palakkad',
    'Pathanamthitta', 'Thiruvananthapuram (Trivandrum)', 'Thrissur', 'Wayanad (Kalpetta)'
  ],

  // 13. Madhya Pradesh (55 districts)
  13: [
    'Agar Malwa', 'Alirajpur', 'Anuppur', 'Ashoknagar', 'Balaghat', 'Barwani',
    'Betul', 'Bhind', 'Bhopal', 'Burhanpur', 'Chhatarpur', 'Chhindwara', 'Damoh',
    'Datia', 'Dewas', 'Dhar', 'Dindori', 'Guna', 'Gwalior', 'Harda', 'Hoshangabad (Narmadapuram)',
    'Indore', 'Jabalpur', 'Jhabua', 'Katni', 'Khandwa (East Nimar)', 'Khargone (West Nimar)',
    'Maihar', 'Mandla', 'Mandsaur', 'Mauganj', 'Morena', 'Narsinghpur', 'Neemuch',
    'Niwari', 'Pandhurna', 'Panna', 'Raisen', 'Rajgarh', 'Ratlam', 'Rewa', 'Sagar',
    'Satna', 'Sehore', 'Seoni', 'Shahdol', 'Shajapur', 'Sheopur', 'Shivpuri',
    'Sidhi', 'Singrauli', 'Tikamgarh', 'Ujjain', 'Umaria', 'Vidisha'
  ],

  // 14. Maharashtra (36 districts)
  14: [
    'Ahmednagar (Ahilyanagar)', 'Akola', 'Amravati', 'Beed', 'Bhandara', 'Buldhana',
    'Chandrapur', 'Chhatrapati Sambhajinagar (Aurangabad)', 'Dharashiv (Osmanabad)',
    'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 'Kolhapur',
    'Latur', 'Mumbai City', 'Mumbai Suburban', 'Nagpur', 'Nanded', 'Nandurbar',
    'Nashik', 'Palghar', 'Parbhani', 'Pune', 'Raigad (Alibag)', 'Ratnagiri',
    'Sangli', 'Satara', 'Sindhudurg (Oros)', 'Solapur', 'Thane', 'Wardha',
    'Washim', 'Yavatmal'
  ],

  // 15. Manipur (16 districts)
  15: [
    'Bishnupur', 'Chandel', 'Churachandpur', 'Imphal East', 'Imphal West', 'Jiribam',
    'Kakching', 'Kamjong', 'Kangpokpi', 'Noney', 'Pherzawl', 'Senapati',
    'Tamenglong', 'Tengnoupal', 'Thoubal', 'Ukhrul'
  ],

  // 16. Meghalaya (12 districts)
  16: [
    'East Garo Hills (Williamnagar)', 'East Jaintia Hills (Khliehriat)', 'East Khasi Hills (Shillong)',
    'Eastern West Khasi Hills (Mairang)', 'North Garo Hills (Resubelpara)', 'Ri Bhoi (Nongpoh)',
    'South Garo Hills (Baghmara)', 'South West Garo Hills (Ampati)', 'South West Khasi Hills (Mawkyrwat)',
    'West Garo Hills (Tura)', 'West Jaintia Hills (Jowai)', 'West Khasi Hills (Nongstoin)'
  ],

  // 17. Mizoram (11 districts)
  17: [
    'Aizawl', 'Champhai', 'Hnahthial', 'Khawzawl', 'Kolasib', 'Lawngtlai',
    'Lunglei', 'Mamit', 'Saiha', 'Saitual', 'Serchhip'
  ],

  // 18. Nagaland (16 districts)
  18: [
    'Chümoukedima', 'Dimapur', 'Kiphire', 'Kohima', 'Longleng', 'Mokokchung',
    'Mon', 'Niuland', 'Noklak', 'Peren', 'Phek', 'Shamator', 'Tseminyu',
    'Tuensang', 'Wokha', 'Zunheboto'
  ],

  // 19. Odisha (30 districts)
  19: [
    'Angul', 'Balangir', 'Balasore (Baleswar)', 'Bargarh', 'Bhadrak', 'Boudh',
    'Cuttack', 'Deogarh', 'Dhenkanal', 'Gajapati (Paralakhemundi)', 'Ganjam (Chhatrapur)',
    'Jagatsinghpur', 'Jajpur', 'Jharsuguda', 'Kalahandi (Bhawanipatna)', 'Kandhamal (Phulbani)',
    'Kendrapara', 'Kendujhar (Keonjhar)', 'Khordha (Bhubaneswar)', 'Koraput', 'Malkangiri',
    'Mayurbhanj (Baripada)', 'Nabarangpur', 'Nayagarh', 'Nuapada', 'Puri',
    'Rayagada', 'Sambalpur', 'Subarnapur (Sonepur)', 'Sundargarh (Rourkela)'
  ],

  // 20. Punjab (23 districts)
  20: [
    'Amritsar', 'Barnala', 'Bathinda', 'Faridkot', 'Fatehgarh Sahib', 'Fazilka',
    'Ferozepur', 'Gurdaspur', 'Hoshiarpur', 'Jalandhar', 'Kapurthala', 'Ludhiana',
    'Malerkotla', 'Mansa', 'Moga', 'Pathankot', 'Patiala', 'Rupnagar (Ropar)',
    'Sahibzada Ajit Singh Nagar (Mohali)', 'Sangrur', 'Shahid Bhagat Singh Nagar (Nawanshahr)',
    'Sri Muktsar Sahib', 'Tarn Taran'
  ],

  // 21. Rajasthan (50 districts)
  21: [
    'Ajmer', 'Alwar', 'Anupgarh', 'Balotra', 'Banswara', 'Baran', 'Barmer', 'Beawar',
    'Bharatpur', 'Bhilwara', 'Bikaner', 'Bundi', 'Chittorgarh', 'Churu', 'Dausa',
    'Deeg', 'Dholpur', 'Didwana-Kuchaman', 'Dudu', 'Dungarpur', 'Ganganagar',
    'Gangapur City', 'Hanumangarh', 'Jaipur', 'Jaipur Rural', 'Jaisalmer', 'Jalore',
    'Jhalawar', 'Jhunjhunu', 'Jodhpur', 'Jodhpur Rural', 'Karauli', 'Kekri',
    'Khairthal-Tijara', 'Kota', 'Kotputli-Behror', 'Nagaur', 'Neem Ka Thana',
    'Pali', 'Phalodi', 'Pratapgarh', 'Rajsamand', 'Salumbar', 'Sanchore',
    'Sawai Madhopur', 'Shahpura', 'Sikar', 'Sirohi', 'Tonk', 'Udaipur'
  ],

  // 22. Sikkim (6 districts)
  22: [
    'Gangtok (East Sikkim)', 'Gyalshing (West Sikkim)', 'Mangan (North Sikkim)',
    'Namchi (South Sikkim)', 'Pakyong', 'Soreng'
  ],

  // 23. Tamil Nadu (38 districts)
  23: [
    'Ariyalur', 'Chengalpattu', 'Chennai', 'Coimbatore', 'Cuddalore', 'Dharmapuri',
    'Dindigul', 'Erode', 'Kallakurichi', 'Kanchipuram', 'Kanyakumari (Nagercoil)',
    'Karur', 'Krishnagiri', 'Madurai', 'Mayiladuthurai', 'Nagapattinam', 'Namakkal',
    'Nilgiris (Udhagamandalam / Ooty)', 'Perambalur', 'Pudukkottai', 'Ramanathapuram',
    'Ranipet', 'Salem', 'Sivaganga', 'Tenkasi', 'Thanjavur', 'Theni', 'Thoothukudi (Tuticorin)',
    'Tiruchirappalli (Trichy)', 'Tirunelveli', 'Tirupathur', 'Tiruppur', 'Tiruvallur',
    'Tiruvannamalai', 'Tiruvarur', 'Vellore', 'Viluppuram', 'Virudhunagar'
  ],

  // 24. Telangana (33 districts)
  24: [
    'Adilabad', 'Bhadradri Kothagudem', 'Hanumakonda (Warangal Urban)', 'Hyderabad',
    'Jagtial', 'Jangaon', 'Jayashankar Bhupalpally', 'Jogulamba Gadwal', 'Kamareddy',
    'Karimnagar', 'Khammam', 'Kumuram Bheem Asifabad', 'Mahabubabad', 'Mahabubnagar',
    'Mancherial', 'Medak', 'Medchal-Malkajgiri', 'Mulugu', 'Nagarkurnool', 'Nalgonda',
    'Narayanpet', 'Nirmal', 'Nizamabad', 'Peddapalli', 'Rajanna Sircilla', 'Ranga Reddy',
    'Sangareddy', 'Siddipet', 'Suryapet', 'Vikarabad', 'Wanaparthy', 'Warangal (Warangal Rural)',
    'Yadadri Bhuvanagiri'
  ],

  // 25. Tripura (8 districts)
  25: [
    'Dhalai (Ambassa)', 'Gomati (Udaipur)', 'Khowai', 'North Tripura (Dharmanagar)',
    'Sepahijala (Bishramganj)', 'South Tripura (Belonia)', 'Unakoti (Kailashahar)',
    'West Tripura (Agartala)'
  ],

  // 26. Uttar Pradesh (75 districts)
  26: [
    'Agra', 'Aligarh', 'Ambedkar Nagar', 'Amethi (Chhatrapati Shahuji Maharaj Nagar)',
    'Amroha (Jyotiba Phule Nagar)', 'Auraiya', 'Ayodhya (Faizabad)', 'Azamgarh',
    'Baghpat', 'Bahraich', 'Ballia', 'Balrampur', 'Banda', 'Barabanki', 'Bareilly',
    'Basti', 'Bhadohi (Sant Ravidas Nagar)', 'Bijnor', 'Budaun', 'Bulandshahr',
    'Chandauli', 'Chitrakoot', 'Deoria', 'Etah', 'Etawah', 'Farrukhabad', 'Fatehpur',
    'Firozabad', 'Gautam Buddha Nagar (Noida / Greater Noida)', 'Ghaziabad', 'Ghazipur',
    'Gonda', 'Gorakhpur', 'Hamirpur', 'Hapur (Panchsheel Nagar)', 'Hardoi', 'Hathras (Mahamaya Nagar)',
    'Jalaun (Orai)', 'Jaunpur', 'Jhansi', 'Kannauj', 'Kanpur Dehat (Ramabai Nagar)',
    'Kanpur Nagar', 'Kasganj (Kanshiram Nagar)', 'Kaushambi', 'Kheri (Lakhimpur Kheri)',
    'Kushinagar (Padrauna)', 'Lalitpur', 'Lucknow', 'Maharajganj', 'Mahoba', 'Mainpuri',
    'Mathura', 'Mau', 'Meerut', 'Mirzapur', 'Moradabad', 'Muzaffarnagar', 'Pilibhit',
    'Pratapgarh', 'Prayagraj (Allahabad)', 'Raebareli', 'Rampur', 'Saharanpur',
    'Sambhal (Bhim Nagar)', 'Sant Kabir Nagar (Khalilabad)', 'Shahjahanpur', 'Shamli (Prabuddh Nagar)',
    'Shravasti', 'Siddharthnagar (Navgarh)', 'Sitapur', 'Sonbhadra (Robertsganj)',
    'Sultanpur', 'Unnao', 'Varanasi'
  ],

  // 27. Uttarakhand (13 districts)
  27: [
    'Almora', 'Bageshwar', 'Chamoli (Gopeshwar)', 'Champawat', 'Dehradun',
    'Haridwar', 'Nainital', 'Pauri Garhwal', 'Pithoragarh', 'Rudraprayag',
    'Tehri Garhwal (New Tehri)', 'Udham Singh Nagar (Rudrapur)', 'Uttarkashi'
  ],

  // 28. West Bengal (23 districts)
  28: [
    'Alipurduar', 'Bankura', 'Birbhum (Suri)', 'Cooch Behar', 'Dakshin Dinajpur (Balurghat)',
    'Darjeeling', 'Hooghly (Chinsurah)', 'Howrah', 'Jalpaiguri', 'Jhargram',
    'Kalimpong', 'Kolkata', 'Malda (English Bazar)', 'Murshidabad (Baharampur)',
    'Nadia (Krishnanagar)', 'North 24 Parganas (Barasat)', 'Paschim Bardhaman (Asansol)',
    'Paschim Medinipur (Midnapore)', 'Purba Bardhaman (Bardhaman)', 'Purba Medinipur (Tamluk)',
    'Purulia', 'South 24 Parganas (Alipore)', 'Uttar Dinajpur (Raiganj)'
  ],

  // 29. Andaman and Nicobar Islands (3 districts)
  29: [
    'Nicobar (Car Nicobar)', 'North and Middle Andaman (Mayabunder)', 'South Andaman (Port Blair)'
  ],

  // 30. Chandigarh (1 district)
  30: [
    'Chandigarh (City & District)'
  ],

  // 31. Dadra and Nagar Haveli and Daman and Diu (3 districts)
  31: [
    'Dadra and Nagar Haveli (Silvassa)', 'Daman', 'Diu'
  ],

  // 32. Delhi (11 districts)
  32: [
    'Central Delhi', 'East Delhi', 'New Delhi', 'North Delhi', 'North East Delhi',
    'North West Delhi', 'Shahdara', 'South Delhi', 'South East Delhi', 'South West Delhi',
    'West Delhi'
  ],

  // 33. Jammu and Kashmir (20 districts)
  33: [
    'Anantnag', 'Bandipora', 'Baramulla', 'Budgam', 'Doda', 'Ganderbal', 'Jammu',
    'Kathua', 'Kishtwar', 'Kulgam', 'Kupwara', 'Poonch', 'Pulwama', 'Rajouri',
    'Ramban', 'Reasi', 'Samba', 'Shopian', 'Srinagar', 'Udhampur'
  ],

  // 34. Ladakh (2 districts)
  34: [
    'Kargil', 'Leh'
  ],

  // 35. Lakshadweep (1 district)
  35: [
    'Lakshadweep (Kavaratti / Agatti / Amini / Andrott / Minicoy)'
  ],

  // 36. Puducherry (4 districts)
  36: [
    'Karaikal', 'Mahe', 'Puducherry', 'Yanam'
  ]
}

// Generate flat structured districts list for API and search indexing
let globalDistrictId = 1
export const ALL_INDIAN_DISTRICTS = []

for (const state of ALL_INDIAN_STATES) {
  const districtNames = STATE_DISTRICTS_MAP[state.id] || []
  for (const name of districtNames) {
    const cleanName = name.replace(/\s*\([^)]*\)/g, '').trim()
    const code = cleanName.substring(0, 3).toUpperCase()
    ALL_INDIAN_DISTRICTS.push({
      id: globalDistrictId++,
      state_id: state.id,
      state_name: state.name,
      name: cleanName,
      full_display_name: name,
      code,
      is_major_city: [
        'Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli', 'Tirunelveli',
        'Mumbai City', 'Mumbai Suburban', 'Pune', 'Nagpur', 'Nashik', 'Thane',
        'Bengaluru Urban', 'Mysuru', 'Hubballi', 'Mangaluru',
        'Hyderabad', 'Warangal', 'Visakhapatnam', 'Vijayawada', 'Guntur',
        'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar',
        'Kolkata', 'Howrah', 'Asansol', 'Siliguri',
        'Lucknow', 'Kanpur Nagar', 'Varanasi', 'Prayagraj', 'Agra', 'Noida', 'Ghaziabad',
        'Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur',
        'Jaipur', 'Jodhpur', 'Kota', 'Bikaner', 'Udaipur',
        'Bhopal', 'Indore', 'Gwalior', 'Jabalpur',
        'Chandigarh', 'Ludhiana', 'Amritsar', 'Jalandhar',
        'Gurugram', 'Faridabad', 'Panipat',
        'New Delhi', 'Central Delhi', 'South Delhi',
        'Thiruvananthapuram', 'Ernakulam', 'Kozhikode',
        'Ranchi', 'Jamshedpur', 'Dhanbad',
        'Raipur', 'Bilaspur', 'Durg',
        'Bhubaneswar', 'Cuttack', 'Rourkela',
        'Guwahati', 'Silchar', 'Dibrugarh',
        'Dehradun', 'Haridwar', 'Shimla', 'Srinagar', 'Jammu'
      ].some(city => name.includes(city))
    })
  }
}
