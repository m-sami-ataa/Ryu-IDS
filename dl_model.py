import pandas as pd
import numpy as np
import joblib
from tensorflow import keras
import sqlite3

class DLModelApp:
    def __init__(self, model_path: str, scaler_path: str, db_path: str):
        """
        Initialize the DLModelApp with paths to the model, scaler, and database.
        """
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.db_path = db_path
        self.model = None
        self.scaler = None
        self.data = None
        self.x_test = None
        self.flow_id = None

    def load_scaler(self):
        """Load the saved Standard Scaler for normalization."""
        self.scaler = joblib.load(self.scaler_path)

    def normalize_data(self):
        """Normalize test data using the loaded scaler."""
        self.x_test = self.scaler.transform(self.x_test)

    def load_model(self):
        """Load the pre-trained TensorFlow model."""
        self.model = keras.models.load_model(self.model_path)

    def load_data(self):
        """Load and preprocess the dataset from the database."""
        # Connect to the database
        connection = sqlite3.connect(self.db_path)
        
        # Load data from the extracted_features table
        query = "SELECT * FROM extracted_features"
        self.data = pd.read_sql_query(query, connection)

        
        # Extract features and Flow ID
        self.x_test = self.data.drop(columns=['id','flow_id'])
        self.flow_id = self.data['flow_id'].values
        
        # Close the connection
        connection.close()

    def make_predictions(self) -> np.ndarray:
        """Make predictions using the loaded model."""
        y_pred_prob = self.model.predict(self.x_test)
        y_pred = np.argmax(y_pred_prob, axis=1)
        return y_pred

    def save_predictions(self, y_pred: np.ndarray):
        """Save the predictions to the database."""
        # Connect to the database
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        # Create the predictions table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                Flow_ID TEXT PRIMARY KEY,
                Predicted_Label INTEGER
            )
        """)
        
        # Insert predictions
        for flow_id, pred in zip(self.flow_id, y_pred):
            cursor.execute("""
                INSERT OR REPLACE INTO predictions (Flow_ID, Predicted_Label) VALUES (?, ?)
            """, (flow_id, int(pred)))

        # Commit and close the connection
        connection.commit()
        connection.close()
        print('Predictions saved to the database.')

    def run(self):
        """Execute the full pipeline of loading, predicting, and saving results."""
        self.load_data()
        self.load_scaler()
        self.normalize_data()
        self.load_model()
        y_pred = self.make_predictions()
        self.save_predictions(y_pred)


if __name__ == '__main__':
    # Initialize the app with the appropriate paths
    app = DLModelApp(
        model_path='trans6_bi_model.h5',
        scaler_path='standard_scaler_Trans_bi.pkl',
        db_path='ids_data.db'
    )
    
    # Run the application
    app.run()

