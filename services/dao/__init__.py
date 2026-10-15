# CREATE TABLE IF NOT EXISTS report_records (
#     id SERIAL PRIMARY KEY,
#     created_at TIMESTAMP DEFAULT NOW(),
#     raw_input JSONB,
#     llm_result JSONB,
#     risk_level TEXT
# );

# CREATE TABLE IF NOT EXISTS env_record (
#     id SERIAL PRIMARY KEY,
#     created_at TIMESTAMP DEFAULT NOW(),
#     temperature NUMERIC(4,2),
#     humidity NUMERIC(4,2),
#     remark TEXT
# );
