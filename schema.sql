
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

CREATE TABLE IF NOT EXISTS algorithm_runtimes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    algorithm_name VARCHAR(255) NOT NULL,
    input_size INTEGER NOT NULL,
    execution_time_ms DECIMAL(10, 3) NOT NULL,
    code_snippet TEXT,
    output_result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_algorithm_runtimes_user_id ON algorithm_runtimes(user_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_runtimes_algorithm_name ON algorithm_runtimes(algorithm_name);
CREATE INDEX IF NOT EXISTS idx_algorithm_runtimes_input_size ON algorithm_runtimes(input_size);
CREATE INDEX IF NOT EXISTS idx_algorithm_runtimes_created_at ON algorithm_runtimes(created_at);

-- ====================================================================
-- 🔒  ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================
ALTER TABLE algorithm_runtimes ENABLE ROW LEVEL SECURITY;

-- Users can only see their own runtime data
CREATE POLICY "Users can view own runtime data" ON algorithm_runtimes
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own runtime data
CREATE POLICY "Users can insert own runtime data" ON algorithm_runtimes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own runtime data
CREATE POLICY "Users can update own runtime data" ON algorithm_runtimes
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own runtime data
CREATE POLICY "Users can delete own runtime data" ON algorithm_runtimes
    FOR DELETE USING (auth.uid() = user_id);

-- ====================================================================
-- 🔄  UPDATED_AT TRIGGER
-- ====================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_algorithm_runtimes_updated_at 
    BEFORE UPDATE ON algorithm_runtimes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ====================================================================
-- 📊  SAMPLE DATA (OPTIONAL - FOR TESTING)
-- ====================================================================
-- Uncomment the following lines to insert sample data for testing
/*
INSERT INTO algorithm_runtimes (user_id, algorithm_name, input_size, execution_time_ms, code_snippet, output_result) VALUES
('00000000-0000-0000-0000-000000000000', 'Bubble Sort', 100, 2.5, 'def bubble_sort(arr): ...', 'Sorted array: [1, 2, 3, ...]'),
('00000000-0000-0000-0000-000000000000', 'Quick Sort', 100, 0.8, 'def quick_sort(arr): ...', 'Sorted array: [1, 2, 3, ...]'),
('00000000-0000-0000-0000-000000000000', 'Linear Search', 1000, 1.2, 'def linear_search(arr, target): ...', 'Found at index: 42'),
('00000000-0000-0000-0000-000000000000', 'Binary Search', 1000, 0.3, 'def binary_search(arr, target): ...', 'Found at index: 42');
*/

-- ====================================================================
-- 📈  USEFUL VIEWS FOR VISUALIZATION
-- ====================================================================

-- Average runtime by algorithm and input size
CREATE OR REPLACE VIEW algorithm_performance_summary AS
SELECT 
    algorithm_name,
    input_size,
    COUNT(*) as execution_count,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MIN(execution_time_ms) as min_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms,
    STDDEV(execution_time_ms) as stddev_execution_time_ms
FROM algorithm_runtimes
GROUP BY algorithm_name, input_size
ORDER BY algorithm_name, input_size;

-- Recent executions for dashboard
CREATE OR REPLACE VIEW recent_executions AS
SELECT 
    algorithm_name,
    input_size,
    execution_time_ms,
    created_at,
    user_id
FROM algorithm_runtimes
ORDER BY created_at DESC
LIMIT 50; 