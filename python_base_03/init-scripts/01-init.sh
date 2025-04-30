#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

# Create the database and set up initial configuration
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Set up permissions
    ALTER DATABASE $POSTGRES_DB SET search_path TO public;
    
    -- Create schema if not exists
    CREATE SCHEMA IF NOT EXISTS credit_system;
    
    -- Set up search path
    ALTER DATABASE $POSTGRES_DB SET search_path TO credit_system, public;
    
    -- Grant necessary permissions
    GRANT ALL ON SCHEMA credit_system TO $POSTGRES_USER;
    GRANT ALL ON ALL TABLES IN SCHEMA credit_system TO $POSTGRES_USER;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA credit_system TO $POSTGRES_USER;
    
    -- Create initial tables
    CREATE TABLE IF NOT EXISTS credit_system.transactions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        from_user_id UUID NOT NULL,
        to_user_id UUID NOT NULL,
        amount DECIMAL(20,8) NOT NULL,
        transaction_type VARCHAR(50) NOT NULL,
        metadata JSONB,
        reference_id VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS credit_system.wallets (
        user_id UUID PRIMARY KEY,
        balance DECIMAL(20,8) NOT NULL DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_transactions_from_user_id ON credit_system.transactions(from_user_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_to_user_id ON credit_system.transactions(to_user_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_reference_id ON credit_system.transactions(reference_id);
    
    -- Create function to update updated_at timestamp
    CREATE OR REPLACE FUNCTION credit_system.update_updated_at_column()
    RETURNS TRIGGER AS \$\$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    \$\$ language 'plpgsql';
    
    -- Create triggers for updated_at
    CREATE TRIGGER update_transactions_updated_at
        BEFORE UPDATE ON credit_system.transactions
        FOR EACH ROW
        EXECUTE FUNCTION credit_system.update_updated_at_column();
    
    CREATE TRIGGER update_wallets_updated_at
        BEFORE UPDATE ON credit_system.wallets
        FOR EACH ROW
        EXECUTE FUNCTION credit_system.update_updated_at_column();
EOSQL 