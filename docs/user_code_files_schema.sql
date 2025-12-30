-- ====================================================================
-- 💾  USER CODE FILES TABLE - Simplified 2-File Limit
-- ====================================================================
-- Each user can store exactly 2 files: code.py and user.cpp
-- This enforces a simple storage limit while providing database persistence

CREATE TABLE IF NOT EXISTS user_code_files (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- File type: 'python' or 'cpp' (enforced at DB level)
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('python', 'cpp')),
    
    -- Auto-generated filename based on type
    filename VARCHAR(50) GENERATED ALWAYS AS (
        CASE 
            WHEN file_type = 'python' THEN 'code.py'
            WHEN file_type = 'cpp' THEN 'user.cpp'
        END
    ) STORED,
    
    -- Code content
    code_content TEXT NOT NULL CHECK (code_content <> ''),
    
    -- Metadata (auto-calculated via trigger)
    file_size INTEGER NOT NULL DEFAULT 0,
    line_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Enforce: One file per type per user
    CONSTRAINT unique_user_file_type UNIQUE (user_id, file_type)
);

-- ====================================================================
-- 📊  INDEXES
-- ====================================================================
CREATE INDEX idx_user_code_user_id ON user_code_files(user_id);
CREATE INDEX idx_user_code_file_type ON user_code_files(user_id, file_type);

-- ====================================================================
-- 🔒  ROW LEVEL SECURITY
-- ====================================================================
-- TEMPORARILY DISABLED for custom JWT auth
-- Re-enable when using Supabase Auth or implement custom RLS
ALTER TABLE user_code_files ENABLE ROW LEVEL SECURITY;

-- Option 1: Allow all operations (for development with service role key)
CREATE POLICY "Allow all for service role" ON user_code_files
    FOR ALL USING (true);

-- Option 2: Use when switching to Supabase native auth
-- CREATE POLICY "Users manage own code files" ON user_code_files
--     FOR ALL USING (auth.uid() = user_id);

-- ====================================================================
-- 🔄  TRIGGERS
-- ====================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_code_files_updated_at 
    BEFORE UPDATE ON user_code_files 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-calculate file metadata (size and line count)
CREATE OR REPLACE FUNCTION calculate_code_metadata()
RETURNS TRIGGER AS $$
BEGIN
    NEW.file_size = LENGTH(NEW.code_content);
    NEW.line_count = LENGTH(NEW.code_content) - LENGTH(REPLACE(NEW.code_content, E'\n', '')) + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_code_metadata_trigger
    BEFORE INSERT OR UPDATE OF code_content ON user_code_files
    FOR EACH ROW 
    EXECUTE FUNCTION calculate_code_metadata();

-- ====================================================================
-- 📈  VIEWS
-- ====================================================================

-- User's active files with metadata
CREATE OR REPLACE VIEW user_code_files_summary AS
SELECT 
    user_id,
    file_type,
    filename,
    file_size,
    line_count,
    created_at,
    updated_at,
    -- Preview (first 200 chars)
    LEFT(code_content, 200) as preview
FROM user_code_files
ORDER BY user_id, file_type;

-- ====================================================================
-- 💡  USAGE EXAMPLES
-- ====================================================================

-- Insert or update Python file (upsert)
-- INSERT INTO user_code_files (user_id, file_type, code_content)
-- VALUES ('user-uuid-here', 'python', 'print("Hello")')
-- ON CONFLICT (user_id, file_type) 
-- DO UPDATE SET code_content = EXCLUDED.code_content;

-- Get user's Python file
-- SELECT * FROM user_code_files 
-- WHERE user_id = 'user-uuid-here' AND file_type = 'python';

-- Get all user's files
-- SELECT * FROM user_code_files WHERE user_id = 'user-uuid-here';
