import sqlite3
import time
from collections import defaultdict
from statistics import stdev, mean

class FeatureExtractorApp:

    def __init__(self, db_path='ids_data.db'):
        # Initialize the SQLite database connection
        self.db_path = db_path
        self.flows = defaultdict(list)

    def load_packets(self):
        """Load packet information from the database table collected_data."""
        # Connect to the database
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        # Fetch all packet data from collected_data table
        cursor.execute("SELECT * FROM collected_data")
        rows = cursor.fetchall()

        # Delete processed packets immediately after loading
        self.delete_loaded_packets()

        # Process each row and group packets by flow
        for row in rows:
            (_,timestamp, src_ip, dst_ip, src_port, dst_port, protocol, header_length, packet_length) = row
            flow_id = self.get_flow_id(src_ip, dst_ip, src_port, dst_port, protocol)
            self.flows[flow_id].append({
                'timestamp': timestamp,
                'header_length': header_length,
                'packet_length': packet_length,
                'src_ip': src_ip,
                'dst_ip': dst_ip
            })

        # Close the database connection
        connection.close()

    def get_flow_id(self, src_ip, dst_ip, src_port, dst_port, protocol):
        """
        Returns a canonical flow ID that treats forward and reverse flows as the same flow.
        """
        if (src_ip < dst_ip) or (src_ip == dst_ip and src_port < dst_port):
            return (src_ip, dst_ip, src_port, dst_port, protocol)
        else:
            return (dst_ip, src_ip, dst_port, src_port, protocol)

    def extract_features(self):
        """Extract features for each flow and save them to the extracted_features table in the database."""
        # Connect to the database
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        # Clear any existing data in the extracted_features table
        cursor.execute("DELETE FROM extracted_features")

        # Iterate over each flow and extract features
        for flow_id, packets in self.flows.items():
            if len(packets) < 2:
                # Skip flows with only one packet
                continue

            # Sort packets by timestamp to calculate flow duration
            packets_sorted = sorted(packets, key=lambda x: x['timestamp'])

            # Calculate Flow Duration
            start_time = packets_sorted[0]['timestamp']
            end_time = packets_sorted[-1]['timestamp']
            flow_duration = end_time - start_time

            # Calculate Flow Bytes per Second
            total_bytes = sum(pkt['packet_length'] for pkt in packets_sorted)
            flow_bps = total_bytes / flow_duration if flow_duration > 0 else 0

            # Calculate Forward and Backward Header Lengths
            forward_header_length = sum(pkt['header_length'] for pkt in packets_sorted
                                        if pkt['src_ip'] == flow_id[0] and pkt['dst_ip'] == flow_id[1])
            backward_header_length = sum(pkt['header_length'] for pkt in packets_sorted
                                         if pkt['src_ip'] == flow_id[1] and pkt['dst_ip'] == flow_id[0])

            # Calculate Packet Length Standard Deviation and Average Size
            packet_lengths = [pkt['packet_length'] for pkt in packets_sorted]
            packet_len_std_dev = stdev(packet_lengths) if len(packet_lengths) > 1 else 0
            packet_size_avg = mean(packet_lengths)

            # Insert extracted features into the database
            cursor.execute("""
                INSERT INTO extracted_features (Flow_ID, Flow_Duration, Flow_Bytes_per_Second, 
                                                Forward_Header_Length, Backward_Header_Length, 
                                                Packet_Length_Std_Dev, Packet_Size_Avg)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(flow_id), flow_duration, flow_bps, forward_header_length, 
                  backward_header_length, packet_len_std_dev, packet_size_avg))

        # Commit changes and close the database connection
        connection.commit()
        connection.close()

    def delete_loaded_packets(self):
        """Delete processed packets from the database."""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        
        # Delete packets from the collected_packets table
        cursor.execute("DELETE FROM collected_data")
        
        connection.commit()
        connection.close()

    def run(self):
        """Run the feature extraction process."""
        self.load_packets()
        self.extract_features()

# Instantiate and run the feature extractor app
if __name__ == "__main__":
    app = FeatureExtractorApp()
    app.run()

