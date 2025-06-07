-- algorithms table
CREATE TABLE algorithms (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    user_id UUID NOT NULL,
    language VARCHAR DEFAULT 'c',
    created_at TIMESTAMP DEFAULT NOW()
);

-- execution_logs table  
CREATE TABLE execution_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    algorithm_id UUID REFERENCES algorithms(id),
    runtime_ms FLOAT NOT NULL,
    output TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);