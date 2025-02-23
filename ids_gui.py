import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from threading import Thread
import time

class IDSGUI:
    def __init__(self, root, db_path="ids_data.db"):
        self.root = root
        self.db_path = db_path
        self.auto_update_interval = 5000  # 5 seconds for auto-refresh
        self.auto_update_on = tk.BooleanVar(value=True)  # Auto-update enabled by default
        
        # Configure main window
        self.root.title("Ryu - Intrusion Detection System")
        self.root.geometry("800x500")

        # Title label
        title_label = tk.Label(root, text="Flow Predictions", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Search frame
        search_frame = tk.Frame(root)
        search_frame.pack(pady=5)
        tk.Label(search_frame, text="Search by Predicted Label: ").pack(side=tk.LEFT)
        self.search_entry = ttk.Combobox(search_frame, values=["Normal", "Attack"], width=15)
        self.search_entry.pack(side=tk.LEFT)
        self.search_button = tk.Button(search_frame, text="Search", command=self.search_data, bg="black", fg="white")
        self.search_button.pack(side=tk.LEFT, padx=5)

        # Table frame with new columns for Flow_ID details
        table_frame = tk.Frame(root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbars
        self.tree_scroll_y = tk.Scrollbar(table_frame, orient="vertical")
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_scroll_x = tk.Scrollbar(table_frame, orient="horizontal")
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        columns = ("Source IP", "Destination IP", "Source Port", "Destination Port", "Protocol", "Predicted Label")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, minwidth=100, width=120)
        
        # Configure scrollbars
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Button frame for Refresh and Stop Auto-update
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        self.refresh_button = tk.Button(button_frame, text="Refresh", command=self.update_table, bg="black", fg="white")
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        # Flush Predictions Button
        self.flush_button = tk.Button(button_frame, text="Flush Predictions", command=self.flush_predictions, bg="red", fg="white")
        self.flush_button.pack(side=tk.LEFT, padx=5)
        
        # Checkbox for stopping auto-update
        stop_auto_update_checkbox = tk.Checkbutton(button_frame, text="Auto-update", variable=self.auto_update_on, command=self.toggle_auto_update)
        stop_auto_update_checkbox.pack(side=tk.LEFT, padx=5)

       

        # Start auto-update in a separate thread
        self.start_auto_update()
        
        # Initial table load
        self.update_table()
        
    def run_query(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def update_table(self):
        # Clear the existing table
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Fetch data and populate the table
        try:
            rows = self.run_query("SELECT Flow_ID, Predicted_Label FROM predictions ORDER BY Flow_ID DESC")
            for flow_id, predicted_label in rows:
                # Split Flow_ID into components and strip any unwanted spaces
                source_ip, dest_ip, source_port, dest_port, protocol = [field.strip("()") for field in flow_id.split(",")]
                # Map 0/1 to Normal/Attack
                label_text = "Normal" if predicted_label == 0 else "Attack"
                # Insert row with appropriate color
                row_id = self.tree.insert("", tk.END, values=(source_ip, dest_ip, source_port, dest_port, protocol, label_text))
                if label_text == "Normal":
                    self.tree.item(row_id, tags=("normal",))
                else:
                    self.tree.item(row_id, tags=("attack",))
            # Define tag colors
            self.tree.tag_configure("normal", background="lightgreen")
            self.tree.tag_configure("attack", background="lightcoral")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error fetching data: {e}")

    def search_data(self):
        label = self.search_entry.get()
        if not label:
            messagebox.showinfo("Search", "Please select a label (Normal or Attack).")
            return

        # Convert label text to database equivalent
        label_value = 0 if label == "Normal" else 1

        # Search in the predictions table
        try:
            rows = self.run_query("SELECT Flow_ID, Predicted_Label FROM predictions WHERE Predicted_Label = ?", (label_value,))
            # Clear existing table data
            for row in self.tree.get_children():
                self.tree.delete(row)
            # Insert only the matching rows
            for flow_id, predicted_label in rows:
                source_ip, dest_ip, source_port, dest_port, protocol = [field.strip("()") for field in flow_id.split(",")]
                label_text = "Normal" if predicted_label == 0 else "Attack"
                row_id = self.tree.insert("", tk.END, values=(source_ip, dest_ip, source_port, dest_port, protocol, label_text))
                if label_text == "Normal":
                    self.tree.item(row_id, tags=("normal",))
                else:
                    self.tree.item(row_id, tags=("attack",))
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error searching data: {e}")
    
    def toggle_auto_update(self):
        """Toggle auto-update based on checkbox status.""" 
        if not self.auto_update_on.get():
            print("Auto-update stopped.")
        else:
            print("Auto-update started.")

    def flush_predictions(self):
        """Flush all predictions from the database."""
        try:
            confirm = messagebox.askyesno("Flush Predictions", "Are you sure you want to delete all predictions from the table?")
            if confirm:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM predictions")
                    conn.commit()
                messagebox.showinfo("Flush Predictions", "Predictions table has been flushed successfully.")
                self.update_table()  # Refresh the table after flushing
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error flushing predictions: {e}")

    def start_auto_update(self):
        def auto_update():
            while True:
                if self.auto_update_on.get():  # Only update if auto-update is on
                    self.update_table()
                time.sleep(self.auto_update_interval / 1000)  # Convert milliseconds to seconds
        # Run auto-update in a separate thread
        Thread(target=auto_update, daemon=True).start()

# Main application
root = tk.Tk()
app = IDSGUI(root)
root.mainloop()

