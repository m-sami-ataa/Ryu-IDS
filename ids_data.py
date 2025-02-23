import sqlite3

# Connect to (or create) the database
conn = sqlite3.connect('ids_data.db')
cursor = conn.cursor()

# Table 1: Collected Data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS collected_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        source_ip TEXT,
        destination_ip TEXT,
        source_port INTEGER,
        destination_port INTEGER,
        protocol TEXT,
        header_length INTEGER,
        packet_length INTEGER
    )
''')

# Table 2: Extracted Features
cursor.execute('''
    CREATE TABLE IF NOT EXISTS extracted_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id TEXT,
        flow_duration REAL,
        flow_bytes_per_second REAL,
        forward_header_length INTEGER,
        backward_header_length INTEGER,
        packet_length_std_dev REAL,
        packet_size_avg REAL
    )
''')

# Table 3: Predictions
cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id TEXT,
        predicted_label INTEGER
    )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully.")

