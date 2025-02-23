# Ryu-IDS
This code implements a Ryu-based IDS using two deep learning models: CNN-LSTM and Transformer. To run the IDS in a Ryu-enabled environment, follow these steps:

1- Install the SQLite database.
2- Run ids_data.py to create the IDS database.
3- Start the IDS by running ryu-ids.py using the ryu-manager command.
Notes:
1- You do not need to run the simple_switch app separately, as it is included in ryu-ids.py.
1- To switch to the CNN-LSTM model, modify lines 94 and 95 in dl_model.py with the corresponding file names for the CNN-LSTM model.
