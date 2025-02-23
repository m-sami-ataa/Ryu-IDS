# Ryu-IDS
This code implements a Ryu-based IDS using two deep learning models: CNN-LSTM and Transformer. To run the IDS in a Ryu-enabled environment, follow these steps:

Install the SQLite database.
Run ids_data.py to create the IDS database.
Start the IDS by running ryu-ids.py using the ryu-manager command.
Notes:

You do not need to run the simple_switch app separately, as it is included in ryu-ids.py.
To switch to the CNN-LSTM model, modify lines 94 and 95 in dl_model.py with the corresponding file names for the CNN-LSTM model.
