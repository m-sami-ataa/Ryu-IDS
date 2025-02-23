from ryu.base import app_manager
import subprocess
import os
import time

class IDS(app_manager.RyuApp):
    OFP_VERSIONS = [1]  # No need for OF version, just coordinating the process

    def __init__(self, *args, **kwargs):
        super(IDS, self).__init__(*args, **kwargs)

        # Intialize GUI flag 
        self.gui = True

        # Start the Ryu apps (data_collector and simple_switch)
        self.start_ryu_apps()

    def start_ryu_apps(self):
        """Start data_collector.py and simple_switch.py using Ryu manager."""
        try:
            self.logger.info("Starting data collection and simple switch as Ryu apps...")

            # Start both data_collector.py and simple_switch.py together in one line
            subprocess.Popen('ryu-manager simple_switch.py data_collector.py', shell=True)

            # Continuously monitor and process the collected data
            self.monitor_and_process_data()
        except Exception as e:
            self.logger.error(f"Failed to start Ryu apps: {e}")

    def monitor_and_process_data(self):
        """Continuously monitor the data collection process and run feature extraction and prediction."""
        self.logger.info("Monitoring data collection progress...")

        # Continuous loop to keep checking and processing the collected data
        while True:
            time.sleep(10)  # Check for new data every 10 seconds (adjustable)           
            self.run_feature_extraction_and_prediction()

    def run_feature_extraction_and_prediction(self):
        """Run feature extraction and prediction after detecting new data."""
        try:
            # Step 1: Run feature extraction
            self.logger.info("Running feature extraction...")
            subprocess.run(['python3', 'feature_extractor.py'])

            # Step 2: Run the deep learning model for prediction
            self.logger.info("Running DL model prediction...")
            subprocess.run(['python3', 'dl_model.py'])

            self.logger.info(f"Prediction complete. Results saved in the database.")
            
            if self.gui:
               # Step 3: Run the GUI
               self.logger.info("Running the GUI...")
               subprocess.run(['python3', 'ids_gui.py'])
               self.gui = False


        except Exception as e:
            self.logger.error(f"Error during feature extraction or prediction: {e}")

