# Database Schema — AI Student Intelligence Platform
# PostgreSQL

## Core Tables

### users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) DEFAULT 'student',  -- student|counselor|admin|institution
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### student_profiles
```sql
CREATE TABLE student_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    age                 INTEGER,
    gender              VARCHAR(10),
    location            VARCHAR(100),
    education_level     VARCHAR(30),
    degree              VARCHAR(50),
    gpa                 DECIMAL(3,2),
    math_score          DECIMAL(5,2),
    english_score       DECIMAL(5,2),
    science_score       DECIMAL(5,2),
    social_score        DECIMAL(5,2),
    aptitude_score      INTEGER,
    college_credits     INTEGER,
    highest_degree      VARCHAR(50),
    parent_education    VARCHAR(30),
    income              DECIMAL(12,2),
    category            VARCHAR(20),
    region              VARCHAR(50),
    preferred_industries JSONB,         -- ["Technology", "Finance"]
    skills_enjoyed       JSONB,         -- ["Coding", "Design"]
    personality_traits   JSONB,         -- ["Analytical", "Creative"]
    updated_at          TIMESTAMP DEFAULT NOW()
);
```

### career_predictions
```sql
CREATE TABLE career_predictions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES student_profiles(id) ON DELETE CASCADE,
    career_1        VARCHAR(100),
    prob_1          DECIMAL(5,2),
    career_2        VARCHAR(100),
    prob_2          DECIMAL(5,2),
    career_3        VARCHAR(100),
    prob_3          DECIMAL(5,2),
    shap_values     JSONB,             -- {feature: value, ...}
    predicted_at    TIMESTAMP DEFAULT NOW()
);
```

### careers
```sql
CREATE TABLE careers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(100) UNIQUE NOT NULL,
    description     TEXT,
    job_demand      VARCHAR(20),
    salary_entry    VARCHAR(30),
    salary_mid      VARCHAR(30),
    salary_senior   VARCHAR(30),
    roadmap_steps   JSONB,             -- ["Intern", "Junior", "Senior"]
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### skills
```sql
CREATE TABLE skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) UNIQUE NOT NULL,
    category        VARCHAR(50),
    priority_level  VARCHAR(20)        -- must-have|good-to-have|advanced
);
```

### career_skills (many-to-many)
```sql
CREATE TABLE career_skills (
    career_id   UUID REFERENCES careers(id) ON DELETE CASCADE,
    skill_id    UUID REFERENCES skills(id) ON DELETE CASCADE,
    importance  VARCHAR(20) DEFAULT 'required',  -- required|recommended
    PRIMARY KEY (career_id, skill_id)
);
```

### skill_dependencies (D3 graph edges)
```sql
CREATE TABLE skill_dependencies (
    skill_id        UUID REFERENCES skills(id) ON DELETE CASCADE,
    depends_on_id   UUID REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (skill_id, depends_on_id)
);
```

### scholarships
```sql
CREATE TABLE scholarships (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(200) NOT NULL,
    type                VARCHAR(50),       -- Scholarship|Internship|Skill Program
    provider            VARCHAR(150),
    education_levels    JSONB,             -- ["Undergraduate", "Postgraduate"]
    income_max          DECIMAL(12,2),
    region              VARCHAR(100),
    gender              VARCHAR(20),
    categories          JSONB,             -- ["SC", "ST", "OBC"]
    benefit             VARCHAR(200),
    deadline            DATE,
    application_link    VARCHAR(500),
    description         TEXT,
    is_active           BOOLEAN DEFAULT TRUE,
    updated_at          TIMESTAMP DEFAULT NOW()
);
```

### learning_resources
```sql
CREATE TABLE learning_resources (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id    UUID REFERENCES skills(id) ON DELETE SET NULL,
    title       VARCHAR(200) NOT NULL,
    type        VARCHAR(30),               -- Course|Book|Video|Certification
    provider    VARCHAR(100),
    difficulty  VARCHAR(20),               -- Beginner|Intermediate|Advanced
    duration    VARCHAR(50),
    is_free     BOOLEAN DEFAULT FALSE,
    rating      DECIMAL(3,2),
    link        VARCHAR(500),
    career_tags JSONB,                     -- ["Data Scientist", "ML Engineer"]
    updated_at  TIMESTAMP DEFAULT NOW()
);
```

### student_progress
```sql
CREATE TABLE student_progress (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id  UUID REFERENCES student_profiles(id) ON DELETE CASCADE,
    skill_id    UUID REFERENCES skills(id) ON DELETE CASCADE,
    status      VARCHAR(20) DEFAULT 'not_started',  -- not_started|in_progress|completed
    updated_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, skill_id)
);
```

### saved_scholarships
```sql
CREATE TABLE saved_scholarships (
    student_id      UUID REFERENCES student_profiles(id) ON DELETE CASCADE,
    scholarship_id  UUID REFERENCES scholarships(id) ON DELETE CASCADE,
    saved_at        TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (student_id, scholarship_id)
);
```

### saved_resources
```sql
CREATE TABLE saved_resources (
    student_id  UUID REFERENCES student_profiles(id) ON DELETE CASCADE,
    resource_id UUID REFERENCES learning_resources(id) ON DELETE CASCADE,
    status      VARCHAR(20) DEFAULT 'saved',    -- saved|in_progress|completed
    saved_at    TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (student_id, resource_id)
);
```

## Key Indexes
```sql
CREATE INDEX idx_student_profiles_user_id     ON student_profiles(user_id);
CREATE INDEX idx_career_predictions_student   ON career_predictions(student_id);
CREATE INDEX idx_scholarships_region          ON scholarships(region);
CREATE INDEX idx_scholarships_income_max      ON scholarships(income_max);
CREATE INDEX idx_scholarships_is_active       ON scholarships(is_active);
CREATE INDEX idx_learning_resources_skill     ON learning_resources(skill_id);
CREATE INDEX idx_student_progress_student     ON student_progress(student_id);
```
