"""
Database migration for admin dashboard tables
Creates billing_events, app_errors, credit_ledger, and admin_metrics tables
"""
import psycopg2
import os
import logging

def run_migration():
    """Create admin dashboard tables"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found")
    
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Create billing_events table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS billing_events (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        stripe_event_id VARCHAR(255) UNIQUE NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        customer_id VARCHAR(255),
                        team_id UUID REFERENCES teams(id),
                        user_id UUID REFERENCES users(id),
                        
                        amount INTEGER,
                        currency VARCHAR(3) DEFAULT 'usd',
                        status VARCHAR(50),
                        description TEXT,
                        
                        subscription_id VARCHAR(255),
                        plan_id VARCHAR(255),
                        plan_name VARCHAR(100),
                        interval VARCHAR(20),
                        
                        raw_data JSONB,
                        processed BOOLEAN DEFAULT FALSE,
                        error_message TEXT,
                        
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP WITH TIME ZONE
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_billing_events_stripe_event_id ON billing_events(stripe_event_id);
                    CREATE INDEX IF NOT EXISTS idx_billing_events_team_id ON billing_events(team_id);
                    CREATE INDEX IF NOT EXISTS idx_billing_events_created_at ON billing_events(created_at);
                    CREATE INDEX IF NOT EXISTS idx_billing_events_event_type ON billing_events(event_type);
                """)
                
                # Create app_errors table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_errors (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES users(id),
                        team_id UUID REFERENCES teams(id),
                        
                        error_type VARCHAR(100) NOT NULL,
                        error_code VARCHAR(50),
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        
                        endpoint VARCHAR(255),
                        method VARCHAR(10),
                        request_data JSONB,
                        response_data JSONB,
                        
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_at TIMESTAMP WITH TIME ZONE,
                        resolution_notes TEXT,
                        
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_app_errors_user_id ON app_errors(user_id);
                    CREATE INDEX IF NOT EXISTS idx_app_errors_created_at ON app_errors(created_at);
                    CREATE INDEX IF NOT EXISTS idx_app_errors_error_type ON app_errors(error_type);
                    CREATE INDEX IF NOT EXISTS idx_app_errors_resolved ON app_errors(resolved);
                """)
                
                # Create credit_ledger table (extended credit tracking)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS credit_ledger (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        team_id UUID REFERENCES teams(id) NOT NULL,
                        user_id UUID REFERENCES users(id),
                        
                        transaction_type VARCHAR(50) NOT NULL,
                        amount INTEGER NOT NULL,
                        balance_after INTEGER NOT NULL,
                        
                        source VARCHAR(50),
                        source_id VARCHAR(255),
                        
                        description TEXT,
                        metadata JSONB,
                        
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_credit_ledger_team_id ON credit_ledger(team_id);
                    CREATE INDEX IF NOT EXISTS idx_credit_ledger_created_at ON credit_ledger(created_at);
                    CREATE INDEX IF NOT EXISTS idx_credit_ledger_transaction_type ON credit_ledger(transaction_type);
                """)
                
                # Create admin_metrics table for pre-calculated metrics
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_metrics (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        metric_date TIMESTAMP WITH TIME ZONE NOT NULL,
                        metric_type VARCHAR(50) NOT NULL,
                        
                        value FLOAT NOT NULL,
                        previous_value FLOAT,
                        change_percent FLOAT,
                        
                        breakdown JSONB,
                        
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_admin_metrics_date_type ON admin_metrics(metric_date, metric_type);
                """)
                
                # Add missing columns to users table if they don't exist
                cur.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                     WHERE table_name='users' AND column_name='role') THEN
                            ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'analyst';
                        END IF;
                        
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                     WHERE table_name='users' AND column_name='last_login') THEN
                            ALTER TABLE users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
                        END IF;
                    END $$;
                """)
                
                conn.commit()
                logging.info("Admin dashboard tables created successfully")
                print("✅ Admin dashboard tables created successfully")
                
    except Exception as e:
        logging.error(f"Error creating admin tables: {e}")
        print(f"❌ Error creating admin tables: {e}")
        raise

if __name__ == "__main__":
    run_migration()