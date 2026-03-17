"""
config.py
─────────────────────────────────────────────
Central configuration for the backend server.
All paths, constants, and app settings live here.
"""

import os

# ── Base paths ────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ── ML model artifacts ────────────────────────────────────────────────────────
MODEL_PATH    = os.path.join(MODELS_DIR, "best_model.pkl")
ENCODERS_PATH = os.path.join(MODELS_DIR, "encoders.pkl")
SCALER_PATH   = os.path.join(MODELS_DIR, "scaler.pkl")
METADATA_PATH = os.path.join(MODELS_DIR, "metadata.json")
FEATURE_IMP_PATH = os.path.join(MODELS_DIR, "feature_importance.csv")

# ── App settings ──────────────────────────────────────────────────────────────
APP_NAME    = "AI Student Intelligence Platform API"
APP_VERSION = "1.0.0"
DEBUG       = True
HOST        = "0.0.0.0"
PORT        = 5000

# ── API settings ──────────────────────────────────────────────────────────────
API_PREFIX      = "/api/v1"
TOP_N_CAREERS   = 3       # Number of career predictions to return
TOP_N_XAI       = 6       # Number of XAI factors to return
XAI_SAMPLE_SIZE = 10      # Batch explanation sample size

# ── CORS ──────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:5173",
                   "http://127.0.0.1:3000", "*"]

# ── Scholarship filter defaults ───────────────────────────────────────────────
MAX_SCHOLARSHIPS_RETURNED = 20

# ── Career knowledge (inline — replace with DB in production) ─────────────────
CAREER_KNOWLEDGE = {
    "Software Engineer": {
        "description": "Designs, develops, tests, and maintains software applications and systems.",
        "required_skills": ["Python", "Java", "Data Structures", "Algorithms", "OOP", "Git"],
        "tools": ["VS Code", "Git", "Docker", "Jenkins", "AWS", "IntelliJ"],
        "roadmap": ["Intern", "Junior Software Engineer", "Software Engineer",
                    "Senior Software Engineer", "Lead Engineer", "Architect"],
        "salary": {"entry": "₹4L–₹8L", "mid": "₹10L–₹20L", "senior": "₹22L–₹45L"},
        "job_demand": "Very High",
    },
    "Data Scientist": {
        "description": "Analyzes large datasets to extract insights and build predictive models.",
        "required_skills": ["Python", "Statistics", "Machine Learning", "SQL", "Data Visualization"],
        "tools": ["Pandas", "Scikit-learn", "TensorFlow", "SQL", "Power BI", "Jupyter"],
        "roadmap": ["Data Intern", "Junior Data Scientist", "Data Scientist",
                    "Senior Data Scientist", "Lead Data Scientist", "Chief Data Officer"],
        "salary": {"entry": "₹5L–₹10L", "mid": "₹12L–₹22L", "senior": "₹25L–₹50L"},
        "job_demand": "Very High",
    },
    "Machine Learning Engineer": {
        "description": "Builds and deploys machine learning models and pipelines at scale.",
        "required_skills": ["Python", "ML", "Deep Learning", "MLOps", "Cloud", "Docker"],
        "tools": ["TensorFlow", "PyTorch", "MLflow", "AWS SageMaker", "Docker", "Kubernetes"],
        "roadmap": ["ML Intern", "Junior MLE", "ML Engineer",
                    "Senior MLE", "ML Architect", "VP of AI"],
        "salary": {"entry": "₹6L–₹12L", "mid": "₹15L–₹28L", "senior": "₹30L–₹60L"},
        "job_demand": "Very High",
    },
    "AI Researcher": {
        "description": "Conducts research to advance the state of artificial intelligence.",
        "required_skills": ["Python", "Deep Learning", "Mathematics", "Research", "Publishing"],
        "tools": ["PyTorch", "JAX", "LaTeX", "Jupyter", "HuggingFace", "CUDA"],
        "roadmap": ["Research Intern", "Research Associate", "AI Researcher",
                    "Senior Researcher", "Principal Researcher", "Research Director"],
        "salary": {"entry": "₹8L–₹15L", "mid": "₹18L–₹35L", "senior": "₹40L–₹80L"},
        "job_demand": "High",
    },
    "Data Analyst": {
        "description": "Interprets data to help organizations make informed business decisions.",
        "required_skills": ["Excel", "SQL", "Python", "Data Visualization", "Statistics"],
        "tools": ["Excel", "Power BI", "Tableau", "SQL Server", "Python"],
        "roadmap": ["Junior Analyst", "Data Analyst", "Senior Analyst", "Analytics Manager"],
        "salary": {"entry": "₹3.5L–₹7L", "mid": "₹8L–₹15L", "senior": "₹16L–₹28L"},
        "job_demand": "High",
    },
    "Web Developer": {
        "description": "Builds and maintains websites and web applications for clients.",
        "required_skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "REST APIs"],
        "tools": ["VS Code", "React", "Node.js", "MongoDB", "Git", "Figma"],
        "roadmap": ["Intern", "Junior Developer", "Web Developer",
                    "Senior Developer", "Tech Lead", "CTO"],
        "salary": {"entry": "₹3L–₹6L", "mid": "₹8L–₹15L", "senior": "₹16L–₹30L"},
        "job_demand": "High",
    },
    "Full Stack Developer": {
        "description": "Works on both frontend and backend of web applications.",
        "required_skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "SQL", "NoSQL"],
        "tools": ["React", "Node.js", "PostgreSQL", "MongoDB", "Docker", "AWS"],
        "roadmap": ["Intern", "Junior Full Stack Dev", "Full Stack Developer",
                    "Senior Full Stack Dev", "Tech Lead"],
        "salary": {"entry": "₹4L–₹8L", "mid": "₹10L–₹18L", "senior": "₹20L–₹35L"},
        "job_demand": "Very High",
    },
    "Product Manager": {
        "description": "Oversees the development and strategy of a product from ideation to launch.",
        "required_skills": ["Product Strategy", "Agile", "Data Analysis", "Communication", "Roadmapping"],
        "tools": ["Jira", "Confluence", "Figma", "Mixpanel", "Notion", "Trello"],
        "roadmap": ["Associate PM", "Product Manager", "Senior PM",
                    "Director of Product", "VP of Product", "CPO"],
        "salary": {"entry": "₹6L–₹12L", "mid": "₹14L–₹25L", "senior": "₹28L–₹55L"},
        "job_demand": "High",
    },
    "Business Analyst": {
        "description": "Bridges business needs and technology solutions through data analysis.",
        "required_skills": ["Requirements Gathering", "SQL", "Excel", "Process Mapping", "Communication"],
        "tools": ["Excel", "SQL", "Jira", "Visio", "Tableau", "Confluence"],
        "roadmap": ["Junior BA", "Business Analyst", "Senior BA", "Lead BA", "BA Manager"],
        "salary": {"entry": "₹3.5L–₹7L", "mid": "₹8L–₹14L", "senior": "₹15L–₹25L"},
        "job_demand": "High",
    },
    "Cybersecurity Analyst": {
        "description": "Protects systems and networks from cyber threats and vulnerabilities.",
        "required_skills": ["Networking", "Linux", "Python", "Ethical Hacking", "SIEM"],
        "tools": ["Wireshark", "Metasploit", "Splunk", "Kali Linux", "Nessus", "Burp Suite"],
        "roadmap": ["Security Intern", "Junior Analyst", "Cybersecurity Analyst",
                    "Senior Analyst", "Security Architect", "CISO"],
        "salary": {"entry": "₹4.5L–₹9L", "mid": "₹10L–₹18L", "senior": "₹20L–₹40L"},
        "job_demand": "Very High",
    },
    "Cloud Architect": {
        "description": "Designs and manages cloud infrastructure and solutions at enterprise scale.",
        "required_skills": ["AWS/Azure/GCP", "Networking", "Linux", "Terraform", "Docker", "Security"],
        "tools": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Ansible"],
        "roadmap": ["Cloud Intern", "Cloud Engineer", "Senior Cloud Engineer",
                    "Cloud Architect", "Principal Architect", "CTO"],
        "salary": {"entry": "₹7L–₹14L", "mid": "₹16L–₹30L", "senior": "₹35L–₹70L"},
        "job_demand": "Very High",
    },
    "DevOps Engineer": {
        "description": "Manages CI/CD pipelines and infrastructure automation for software delivery.",
        "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "Python", "Cloud"],
        "tools": ["Docker", "Kubernetes", "Jenkins", "Terraform", "AWS", "Prometheus"],
        "roadmap": ["DevOps Intern", "Junior DevOps", "DevOps Engineer",
                    "Senior DevOps", "Platform Lead", "VP Engineering"],
        "salary": {"entry": "₹5L–₹10L", "mid": "₹12L–₹22L", "senior": "₹24L–₹45L"},
        "job_demand": "Very High",
    },
    "UX Designer": {
        "description": "Designs intuitive user interfaces and experiences for digital products.",
        "required_skills": ["User Research", "Wireframing", "Prototyping", "Figma", "Usability Testing"],
        "tools": ["Figma", "Adobe XD", "Sketch", "InVision", "Miro", "Zeplin"],
        "roadmap": ["Design Intern", "Junior UX Designer", "UX Designer",
                    "Senior UX Designer", "Lead Designer", "Head of Design"],
        "salary": {"entry": "₹3.5L–₹7L", "mid": "₹8L–₹16L", "senior": "₹18L–₹32L"},
        "job_demand": "High",
    },
    "Mobile App Developer": {
        "description": "Builds native and cross-platform mobile applications for iOS and Android.",
        "required_skills": ["Flutter", "React Native", "Swift", "Kotlin", "REST APIs", "Firebase"],
        "tools": ["Android Studio", "Xcode", "Flutter", "Firebase", "Postman", "Git"],
        "roadmap": ["Mobile Intern", "Junior Mobile Dev", "Mobile Developer",
                    "Senior Mobile Dev", "Mobile Architect", "Tech Lead"],
        "salary": {"entry": "₹4L–₹8L", "mid": "₹10L–₹18L", "senior": "₹20L–₹35L"},
        "job_demand": "High",
    },
    "Financial Analyst": {
        "description": "Analyzes financial data to guide investment and business decisions.",
        "required_skills": ["Excel", "Financial Modeling", "Accounting", "SQL", "Communication"],
        "tools": ["Excel", "Bloomberg", "Python", "Power BI", "SAP", "Tableau"],
        "roadmap": ["Finance Intern", "Junior Analyst", "Financial Analyst",
                    "Senior Analyst", "Finance Manager", "CFO"],
        "salary": {"entry": "₹4L–₹8L", "mid": "₹10L–₹18L", "senior": "₹20L–₹40L"},
        "job_demand": "High",
    },
    "Blockchain Developer": {
        "description": "Builds decentralized applications and smart contracts on blockchain platforms.",
        "required_skills": ["Solidity", "Python", "Cryptography", "Web3.js", "Smart Contracts"],
        "tools": ["Ethereum", "Hardhat", "Truffle", "IPFS", "MetaMask", "Remix IDE"],
        "roadmap": ["Blockchain Intern", "Junior Developer", "Blockchain Developer",
                    "Senior Developer", "Blockchain Architect"],
        "salary": {"entry": "₹6L–₹12L", "mid": "₹15L–₹28L", "senior": "₹30L–₹60L"},
        "job_demand": "High",
    },
}

# ── Scholarship data ───────────────────────────────────────────────────────────
SCHOLARSHIPS = [
    {"id": "SCH001", "name": "National Scholarship Scheme (NSP)", "type": "Scholarship",
     "provider": "Central Government", "education_levels": ["High School","Undergraduate","Postgraduate"],
     "income_max": 250000, "regions": ["All India"], "gender": "All",
     "categories": ["SC","ST","OBC","EWS","Minority"],
     "benefit": "₹25,000/year", "deadline": "2025-10-31",
     "link": "https://scholarships.gov.in", "description": "National scholarship for meritorious students from minority and reserved categories."},
    {"id": "SCH002", "name": "PM Yasasvi Scholarship", "type": "Scholarship",
     "provider": "Ministry of Social Justice", "education_levels": ["High School","Undergraduate"],
     "income_max": 250000, "regions": ["All India"], "gender": "All",
     "categories": ["OBC","EBC","DNT"],
     "benefit": "₹75,000–₹1,25,000/year", "deadline": "2025-09-30",
     "link": "https://yet.nta.ac.in", "description": "Merit-based scholarship for OBC, EBC and DNT students."},
    {"id": "SCH003", "name": "Pragati Scholarship (AICTE)", "type": "Scholarship",
     "provider": "AICTE", "education_levels": ["Undergraduate"],
     "income_max": 800000, "regions": ["All India"], "gender": "Female",
     "categories": ["All"],
     "benefit": "₹50,000/year + ₹2,000/month", "deadline": "2025-11-30",
     "link": "https://aicte-india.org", "description": "Scholarship for female students pursuing technical education."},
    {"id": "SCH004", "name": "AI Skill Development Program (NIELIT)", "type": "Skill Program",
     "provider": "MeitY / NIELIT", "education_levels": ["High School","Undergraduate","Postgraduate"],
     "income_max": 9999999, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "Free AI/ML Training + Certificate", "deadline": "Rolling",
     "link": "https://nielit.gov.in", "description": "Government-sponsored free AI and ML skill development program."},
    {"id": "SCH005", "name": "Digital India Internship Program", "type": "Internship",
     "provider": "Ministry of Electronics & IT", "education_levels": ["Undergraduate","Postgraduate"],
     "income_max": 9999999, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "₹10,000 stipend/month", "deadline": "Quarterly",
     "link": "https://digitalindia.gov.in", "description": "Internship program under Digital India mission."},
    {"id": "SCH006", "name": "Skill India PMKVY 4.0", "type": "Skill Program",
     "provider": "Ministry of Skill Development", "education_levels": ["High School","Undergraduate"],
     "income_max": 9999999, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "Free vocational training + ₹8,000", "deadline": "Rolling",
     "link": "https://pmkvyofficial.org", "description": "Pradhan Mantri Kaushal Vikas Yojana - free skill training."},
    {"id": "SCH007", "name": "Inspire Scholarship (DST)", "type": "Scholarship",
     "provider": "Dept. of Science & Technology", "education_levels": ["High School","Undergraduate"],
     "income_max": 9999999, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "₹80,000/year", "deadline": "2025-08-31",
     "link": "https://online-inspire.gov.in", "description": "Scholarship for top 1% science students."},
    {"id": "SCH008", "name": "Post-Matric Scholarship (SC)", "type": "Scholarship",
     "provider": "Ministry of Social Justice", "education_levels": ["High School","Undergraduate","Postgraduate"],
     "income_max": 250000, "regions": ["All India"], "gender": "All",
     "categories": ["SC"],
     "benefit": "Course fees + maintenance allowance", "deadline": "2025-10-31",
     "link": "https://scholarships.gov.in", "description": "Post-matric scholarship for SC students."},
    {"id": "SCH009", "name": "Google Generation Scholarship", "type": "Scholarship",
     "provider": "Google India", "education_levels": ["Undergraduate"],
     "income_max": 9999999, "regions": ["All India"], "gender": "Female",
     "categories": ["All"],
     "benefit": "₹75,000 one-time", "deadline": "2025-12-15",
     "link": "https://buildyourfuture.withgoogle.com", "description": "Google scholarship for women in tech."},
    {"id": "SCH010", "name": "Saksham Scholarship (AICTE)", "type": "Scholarship",
     "provider": "AICTE", "education_levels": ["Undergraduate","Postgraduate"],
     "income_max": 800000, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "₹50,000/year + ₹2,000/month", "deadline": "2025-11-30",
     "link": "https://aicte-india.org", "description": "Scholarship for differently-abled students in technical institutions."},
    {"id": "SCH011", "name": "State Merit Scholarship Telangana", "type": "Scholarship",
     "provider": "Govt. of Telangana", "education_levels": ["High School","Undergraduate"],
     "income_max": 200000, "regions": ["Telangana"], "gender": "All",
     "categories": ["BC","SC","ST","EBC"],
     "benefit": "₹3,500–₹20,000/year", "deadline": "2025-09-30",
     "link": "https://telanganaepass.cgg.gov.in", "description": "Telangana state merit scholarship for backward classes."},
    {"id": "SCH012", "name": "Central Sector Scheme UG/PG", "type": "Scholarship",
     "provider": "Ministry of Education", "education_levels": ["Undergraduate","Postgraduate"],
     "income_max": 450000, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "₹10,000–₹20,000/year", "deadline": "2025-10-31",
     "link": "https://scholarships.gov.in", "description": "For top 20 percentile students in Class 12."},
    {"id": "SCH013", "name": "Infosys Foundation Scholarship", "type": "Scholarship",
     "provider": "Infosys Foundation", "education_levels": ["Undergraduate"],
     "income_max": 500000, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "₹1,00,000/year", "deadline": "2026-01-31",
     "link": "https://infosys.com/foundation", "description": "Engineering scholarship from Infosys Foundation."},
    {"id": "SCH014", "name": "Amazon Future Engineer Scholarship", "type": "Scholarship",
     "provider": "Amazon India", "education_levels": ["Undergraduate"],
     "income_max": 600000, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "₹1,00,000/year + internship", "deadline": "2026-01-31",
     "link": "https://amazonin.hirepro.in", "description": "Amazon scholarship for CS/IT/Engineering students."},
    {"id": "SCH015", "name": "Tata Capital Pankh Scholarship", "type": "Scholarship",
     "provider": "Tata Capital", "education_levels": ["High School","Undergraduate"],
     "income_max": 400000, "regions": ["All India"], "gender": "All",
     "categories": ["All"],
     "benefit": "Up to ₹50,000/year", "deadline": "2025-11-30",
     "link": "https://tatacapital.com/pankh", "description": "Tata Capital scholarship for meritorious students."},
]

# ── Learning resources (sample — full in DB) ──────────────────────────────────
LEARNING_RESOURCES = [
    {"id":"LR001","skill":"Python","title":"Python for Everybody","type":"Course","provider":"Coursera","difficulty":"Beginner","is_free":True,"career_tags":["Data Scientist","Data Analyst","ML Engineer"],"link":"https://coursera.org/specializations/python"},
    {"id":"LR002","skill":"Python","title":"100 Days of Code: Python","type":"Course","provider":"Udemy","difficulty":"Beginner","is_free":False,"career_tags":["Software Engineer","Web Developer"],"link":"https://udemy.com/course/100-days-of-code"},
    {"id":"LR003","skill":"Machine Learning","title":"ML Specialization (Andrew Ng)","type":"Course","provider":"Coursera","difficulty":"Intermediate","is_free":True,"career_tags":["ML Engineer","Data Scientist","AI Researcher"],"link":"https://coursera.org/specializations/machine-learning-introduction"},
    {"id":"LR004","skill":"Machine Learning","title":"Hands-On Machine Learning","type":"Book","provider":"O'Reilly","difficulty":"Intermediate","is_free":False,"career_tags":["ML Engineer","Data Scientist"],"link":"https://oreilly.com/library/view/hands-on-machine-learning"},
    {"id":"LR005","skill":"SQL","title":"SQL for Data Analysis","type":"Course","provider":"Mode Analytics","difficulty":"Beginner","is_free":True,"career_tags":["Data Analyst","Data Scientist","Business Analyst"],"link":"https://mode.com/sql-tutorial"},
    {"id":"LR006","skill":"Deep Learning","title":"Deep Learning Specialization","type":"Course","provider":"Coursera / DeepLearning.AI","difficulty":"Advanced","is_free":True,"career_tags":["AI Researcher","ML Engineer"],"link":"https://coursera.org/specializations/deep-learning"},
    {"id":"LR007","skill":"Statistics","title":"Statistics and Probability","type":"Course","provider":"Khan Academy","difficulty":"Beginner","is_free":True,"career_tags":["Data Scientist","Data Analyst"],"link":"https://khanacademy.org/math/statistics-probability"},
    {"id":"LR008","skill":"Web Development","title":"The Odin Project","type":"Course","provider":"Open Source","difficulty":"Beginner","is_free":True,"career_tags":["Web Developer","Full Stack Developer"],"link":"https://theodinproject.com"},
    {"id":"LR009","skill":"Cloud Computing","title":"AWS Solutions Architect","type":"Course","provider":"Udemy","difficulty":"Intermediate","is_free":False,"career_tags":["Cloud Architect","DevOps Engineer"],"link":"https://udemy.com/course/aws-certified-solutions-architect-associate"},
    {"id":"LR010","skill":"Cybersecurity","title":"Google Cybersecurity Certificate","type":"Course","provider":"Coursera","difficulty":"Beginner","is_free":True,"career_tags":["Cybersecurity Analyst"],"link":"https://coursera.org/professional-certificates/google-cybersecurity"},
    {"id":"LR011","skill":"UX Design","title":"Google UX Design Certificate","type":"Course","provider":"Coursera","difficulty":"Beginner","is_free":True,"career_tags":["UX Designer","Product Manager"],"link":"https://coursera.org/professional-certificates/google-ux-design"},
    {"id":"LR012","skill":"Data Visualization","title":"Storytelling with Data","type":"Book","provider":"Cole Knaflic","difficulty":"Beginner","is_free":False,"career_tags":["Data Analyst","Business Analyst"],"link":"https://storytellingwithdata.com"},
    {"id":"LR013","skill":"Flutter","title":"Flutter & Dart Complete Guide","type":"Course","provider":"Udemy","difficulty":"Intermediate","is_free":False,"career_tags":["Mobile App Developer"],"link":"https://udemy.com/course/flutter-bootcamp-with-dart"},
    {"id":"LR014","skill":"DevOps","title":"Docker & Kubernetes Practical Guide","type":"Course","provider":"Udemy","difficulty":"Intermediate","is_free":False,"career_tags":["DevOps Engineer","Cloud Architect"],"link":"https://udemy.com/course/docker-kubernetes-the-practical-guide"},
    {"id":"LR015","skill":"React","title":"React - The Complete Guide","type":"Course","provider":"Udemy","difficulty":"Intermediate","is_free":False,"career_tags":["Web Developer","Full Stack Developer","Mobile App Developer"],"link":"https://udemy.com/course/react-the-complete-guide"},
]
