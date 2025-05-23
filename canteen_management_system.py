import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime
import hashlib
from PIL import Image, ImageTk
import os

DB_NAME = 'canteen.db'

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class CanteenDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()
        self.init_sample_data()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                total_price REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                menu_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(menu_id) REFERENCES menu(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                phone TEXT
            )
        ''')
        self.conn.commit()

    def init_sample_data(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE is_admin=1')
        if not c.fetchone():
            c.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                      ('admin', hash_password('admin123'), 1))
        c.execute('SELECT * FROM staff')
        if not c.fetchone():
            c.execute('INSERT INTO staff (name, role, phone) VALUES (?, ?, ?)',
                      ('John Doe', 'Manager', '1234567890'))
        self.conn.commit()

    def add_user(self, username, password, is_admin=0):
        c = self.conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                      (username, hash_password(password), is_admin))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def validate_user(self, username, password):
        c = self.conn.cursor()
        c.execute('SELECT id, is_admin FROM users WHERE username=? AND password=?',
                  (username, hash_password(password)))
        return c.fetchone()

    def add_menu_item(self, name, price, qty):
        c = self.conn.cursor()
        c.execute('INSERT INTO menu (item_name, price, quantity) VALUES (?, ?, ?)', (name, price, qty))
        self.conn.commit()

    def list_menu(self):
        c = self.conn.cursor()
        c.execute('SELECT id, item_name, price, quantity FROM menu')
        return c.fetchall()

    def update_menu_item(self, item_id, name, price, qty):
        c = self.conn.cursor()
        c.execute('UPDATE menu SET item_name=?, price=?, quantity=? WHERE id=?', (name, price, qty, item_id))
        self.conn.commit()

    def delete_menu_item(self, item_id):
        c = self.conn.cursor()
        c.execute('DELETE FROM menu WHERE id=?', (item_id,))
        self.conn.commit()

    def add_customer(self, name, phone):
        c = self.conn.cursor()
        c.execute('INSERT INTO customers (name, phone) VALUES (?, ?)', (name, phone))
        self.conn.commit()
        c.execute('SELECT last_insert_rowid()')
        return c.fetchone()[0]

    def update_customer(self, customer_id, name, phone):
        c = self.conn.cursor()
        c.execute('UPDATE customers SET name=?, phone=? WHERE id=?', (name, phone, customer_id))
        self.conn.commit()

    def delete_customer(self, customer_id):
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) FROM orders WHERE customer_id=?', (customer_id,))
        if c.fetchone()[0] > 0:
            return False
        c.execute('DELETE FROM customers WHERE id=?', (customer_id,))
        self.conn.commit()
        return True

    def list_customers(self):
        c = self.conn.cursor()
        c.execute('SELECT id, name, phone FROM customers')
        return c.fetchall()

    def create_order(self, customer_id, order_date, total_price, status='Pending'):
        c = self.conn.cursor()
        c.execute('INSERT INTO orders (customer_id, order_date, total_price, status) VALUES (?, ?, ?, ?)',
                  (customer_id, order_date, total_price, status))
        self.conn.commit()
        return c.lastrowid

    def add_order_item(self, order_id, menu_id, quantity):
        c = self.conn.cursor()
        c.execute('INSERT INTO order_items (order_id, menu_id, quantity) VALUES (?, ?, ?)', (order_id, menu_id, quantity))
        self.conn.commit()

    def list_orders(self):
        c = self.conn.cursor()
        c.execute('SELECT id, customer_id, order_date, total_price, status FROM orders')
        return c.fetchall()

    def get_order_items(self, order_id):
        c = self.conn.cursor()
        c.execute('''
            SELECT oi.id, m.item_name, oi.quantity, m.price
            FROM order_items oi
            JOIN menu m ON oi.menu_id = m.id
            WHERE oi.order_id=?
        ''', (order_id,))
        return c.fetchall()

    def get_customer_orders(self, customer_id):
        c = self.conn.cursor()
        c.execute('SELECT id, order_date, total_price, status FROM orders WHERE customer_id=?', (customer_id,))
        return c.fetchall()

    def update_order_status(self, order_id, status):
        c = self.conn.cursor()
        c.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
        self.conn.commit()

    def add_inventory_item(self, item_name, quantity):
        c = self.conn.cursor()
        c.execute('INSERT INTO inventory (item_name, quantity) VALUES (?, ?)', (item_name, quantity))
        self.conn.commit()

    def list_inventory(self):
        c = self.conn.cursor()
        c.execute('SELECT id, item_name, quantity FROM inventory')
        return c.fetchall()

    def update_inventory(self, item_id, quantity):
        c = self.conn.cursor()
        c.execute('UPDATE inventory SET quantity=? WHERE id=?', (quantity, item_id))
        self.conn.commit()

    def add_staff(self, name, role, phone):
        c = self.conn.cursor()
        c.execute('INSERT INTO staff (name, role, phone) VALUES (?, ?, ?)', (name, role, phone))
        self.conn.commit()

    def list_staff(self):
        c = self.conn.cursor()
        c.execute('SELECT id, name, role, phone FROM staff')
        return c.fetchall()

    def update_staff(self, staff_id, name, role, phone):
        c = self.conn.cursor()
        c.execute('UPDATE staff SET name=?, role=?, phone=? WHERE id=?', (name, role, phone, staff_id))
        self.conn.commit()

    def delete_staff(self, staff_id):
        c = self.conn.cursor()
        c.execute('DELETE FROM staff WHERE id=?', (staff_id,))
        self.conn.commit()

    def __del__(self):
        self.conn.close()

class CanteenApp:
    def __init__(self, root):
        self.db = CanteenDB()
        self.root = root
        self.root.title("Canteen Management System")
        self.root.geometry("800x600")
        self.current_order_items = []
        self.login_bg_image = None
        self.main_bg_image = None
        self.load_background_images()
        self.root.bind('<Configure>', self.resize_background)
        self.show_login()

    def load_background_images(self):
        try:
            if os.path.exists("assets/canteen1.png"):
                self.login_bg_image_orig = Image.open("assets/canteen1.png")
            else:
                self.login_bg_image_orig = None
            if os.path.exists("assets/canteen1.png"):
                self.main_bg_image_orig = Image.open("assets/canteen1.png")
            else:
                self.main_bg_image_orig = None
        except Exception as e:
            print(f"Error loading images: {e}")
            self.login_bg_image_orig = None
            self.main_bg_image_orig = None

    def resize_background(self, event=None):
        if hasattr(self, 'current_canvas'):
            self.set_background(self.current_canvas, for_login=self.current_canvas.for_login)

    def set_background(self, canvas, for_login=True):
        canvas.delete("all")
        w = max(self.root.winfo_width(), 1)
        h = max(self.root.winfo_height(), 1)
        canvas.for_login = for_login
        if for_login and self.login_bg_image_orig:
            bg_image = self.login_bg_image_orig.resize((w, h), Image.Resampling.LANCZOS)
            self.login_bg_image = ImageTk.PhotoImage(bg_image)
            canvas.create_image(0, 0, anchor='nw', image=self.login_bg_image)
        elif not for_login and self.main_bg_image_orig:
            bg_image = self.main_bg_image_orig.resize((w, h), Image.Resampling.LANCZOS)
            self.main_bg_image = ImageTk.PhotoImage(bg_image)
            canvas.create_image(0, 0, anchor='nw', image=self.main_bg_image)
        else:
            canvas.create_rectangle(0, 0, w, h, fill='#f0f0f0')

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=True)

        frame = tk.Frame(canvas, bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Canteen Login", font=("Arial", 20, "bold")).pack(pady=20)
        tk.Label(frame, text="Username:", bg='white').pack()
        self.login_username = tk.Entry(frame, font=('Arial', 12))
        self.login_username.pack(pady=5)
        tk.Label(frame, text="Password:", bg='white').pack()
        self.login_password = tk.Entry(frame, show='*', font=('Arial', 12))
        self.login_password.pack(pady=5)
        tk.Button(frame, text="Login", command=self.do_login, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(frame, text="Register", command=self.show_register, bg='#4a90e2', fg='white').pack()

    def do_login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return
        user = self.db.validate_user(username, password)
        if user:
            self.user_id = user[0]
            self.is_admin = user[1] == 1
            self.show_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def show_register(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=True)

        frame = tk.Frame(canvas, bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Register User", font=("Arial", 20, "bold")).pack(pady=20)
        tk.Label(frame, text="Username:", bg='white').pack()
        username_entry = tk.Entry(frame, font=('Arial', 12))
        username_entry.pack(pady=5)
        tk.Label(frame, text="Password:", bg='white').pack()
        password_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        password_entry.pack(pady=5)
        tk.Label(frame, text="Confirm Password:", bg='white').pack()
        confirm_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        confirm_entry.pack(pady=5)

        def register():
            u = username_entry.get().strip()
            p = password_entry.get().strip()
            cp = confirm_entry.get().strip()
            if not u or not p or not cp:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            if len(p) < 6:
                messagebox.showwarning("Input Error", "Password must be at least 6 characters")
                return
            if p != cp:
                messagebox.showerror("Input Error", "Passwords do not match")
                return
            if self.db.add_user(u, p):
                messagebox.showinfo("Success", "User registered successfully. Please login.")
                self.show_login()
            else:
                messagebox.showerror("Error", "Username already exists")

        tk.Button(frame, text="Register", command=register, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(frame, text="Back to Login", command=self.show_login, bg='#4a90e2', fg='white').pack()

    def show_dashboard(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Canteen Dashboard", font=("Arial", 20, "bold")).pack(pady=20)
        buttons = [
            ("Manage Menu", self.manage_menu, self.is_admin),
            ("Place Order", self.create_order, True),
            ("View Orders", self.view_orders, True),
            ("Manage Customers", self.manage_customers, True),
            ("Manage Staff", self.manage_staff, self.is_admin),
            ("Manage Inventory", self.manage_inventory, self.is_admin),
            ("Logout", self.show_login, True)
        ]
        for text, cmd, show in buttons:
            if show:
                tk.Button(frame, text=text, font=('Arial', 12), width=20, command=cmd, bg='#4a90e2', fg='white').pack(pady=5)

    def manage_menu(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Menu Management", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        columns = ('ID', 'Item Name', 'Price', 'Quantity')
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        self.menu_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.menu_tree.yview)
        for col in columns:
            self.menu_tree.heading(col, text=col)
            self.menu_tree.column(col, width=150, anchor='center')
        self.menu_tree.pack(fill='both', expand=True)

        for item in self.db.list_menu():
            self.menu_tree.insert('', 'end', values=item)

        button_frame = tk.Frame(frame, bg='white')
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Add Item", command=self.add_menu_item, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Update Item", command=self.update_menu_item, bg='#FFA500', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Delete Item", command=self.delete_menu_item, bg='#f44336', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Back", command=self.show_dashboard, bg='#4a90e2', fg='white').pack(side='left', padx=5)

    def add_menu_item(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Add Menu Item", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Item Name:", bg='white').pack()
        item_name = tk.Entry(frame, font=('Arial', 12))
        item_name.pack(pady=5)
        tk.Label(frame, text="Price:", bg='white').pack()
        price = tk.Entry(frame, font=('Arial', 12))
        price.pack(pady=5)
        tk.Label(frame, text="Quantity:", bg='white').pack()
        quantity = tk.Entry(frame, font=('Arial', 12))
        quantity.pack(pady=5)

        def save():
            name = item_name.get().strip()
            price_val = price.get().strip()
            qty_val = quantity.get().strip()
            if not name or not price_val or not qty_val:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            try:
                price_num = float(price_val)
                qty_num = int(qty_val)
                if price_num <= 0 or qty_num < 0:
                    messagebox.showwarning("Input Error", "Price must be positive, quantity cannot be negative")
                    return
                self.db.add_menu_item(name, price_num, qty_num)
                messagebox.showinfo("Success", "Menu item added")
                self.manage_menu()
            except ValueError:
                messagebox.showerror("Input Error", "Invalid price or quantity")

        tk.Button(frame, text="Save", command=save, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_menu, bg='#4a90e2', fg='white').pack()

    def update_menu_item(self):
        selected = self.menu_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a menu item")
            return
        item_id, name, price, qty = self.menu_tree.item(selected[0])['values']

        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Update Menu Item", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Item Name:", bg='white').pack()
        item_name = tk.Entry(frame, font=('Arial', 12))
        item_name.insert(0, name)
        item_name.pack(pady=5)
        tk.Label(frame, text="Price:", bg='white').pack()
        price_entry = tk.Entry(frame, font=('Arial', 12))
        price_entry.insert(0, price)
        price_entry.pack(pady=5)
        tk.Label(frame, text="Quantity:", bg='white').pack()
        quantity = tk.Entry(frame, font=('Arial', 12))
        quantity.insert(0, qty)
        quantity.pack(pady=5)

        def save():
            new_name = item_name.get().strip()
            price_val = price_entry.get().strip()
            qty_val = quantity.get().strip()
            if not new_name or not price_val or not qty_val:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            try:
                price_num = float(price_val)
                qty_num = int(qty_val)
                if price_num <= 0 or qty_num < 0:
                    messagebox.showwarning("Input Error", "Price must be positive, quantity cannot be negative")
                    return
                self.db.update_menu_item(item_id, new_name, price_num, qty_num)
                messagebox.showinfo("Success", "Menu item updated")
                self.manage_menu()
            except ValueError:
                messagebox.showerror("Input Error", "Invalid price or quantity")

        tk.Button(frame, text="Save", command=save, bg='#FFA500', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_menu, bg='#4a90e2', fg='white').pack()

    def delete_menu_item(self):
        selected = self.menu_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a menu item")
            return
        item_id = self.menu_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this menu item?"):
            self.db.delete_menu_item(item_id)
            messagebox.showinfo("Success", "Menu item deleted")
            self.manage_menu()

    def manage_customers(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Customer Management", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        columns = ('ID', 'Name', 'Phone')
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        self.customer_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.customer_tree.yview)
        for col in columns:
            self.customer_tree.heading(col, text=col)
            self.customer_tree.column(col, width=150, anchor='center')
        self.customer_tree.pack(fill='both', expand=True)

        for customer in self.db.list_customers():
            self.customer_tree.insert('', 'end', values=customer)

        button_frame = tk.Frame(frame, bg='white')
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Add Customer", command=self.add_customer, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Update Customer", command=self.update_customer, bg='#FFA500', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Delete Customer", command=self.delete_customer, bg='#f44336', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="View Orders", command=self.view_customer_orders, bg='#4a90e2', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Back", command=self.show_dashboard, bg='#4a90e2', fg='white').pack(side='left', padx=5)

    def add_customer(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Add Customer", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Name:", bg='white').pack()
        name = tk.Entry(frame, font=('Arial', 12))
        name.pack(pady=5)
        tk.Label(frame, text="Phone:", bg='white').pack()
        phone = tk.Entry(frame, font=('Arial', 12))
        phone.pack(pady=5)

        def save():
            name_val = name.get().strip()
            phone_val = phone.get().strip()
            if not name_val or not phone_val:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            if not phone_val.isdigit() or len(phone_val) < 10:
                messagebox.showwarning("Input Error", "Phone must be a valid number (at least 10 digits)")
                return
            self.db.add_customer(name_val, phone_val)
            messagebox.showinfo("Success", "Customer added")
            self.manage_customers()

        tk.Button(frame, text="Save", command=save, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_customers, bg='#4a90e2', fg='white').pack()

    def update_customer(self):
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a customer")
            return
        customer_id, name, phone = self.customer_tree.item(selected[0])['values']

        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Update Customer", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Name:", bg='white').pack()
        name_entry = tk.Entry(frame, font=('Arial', 12))
        name_entry.insert(0, name)
        name_entry.pack(pady=5)
        tk.Label(frame, text="Phone:", bg='white').pack()
        phone_entry = tk.Entry(frame, font=('Arial', 12))
        phone_entry.insert(0, phone)
        phone_entry.pack(pady=5)

        def save():
            name_val = name_entry.get().strip()
            phone_val = phone_entry.get().strip()
            if not name_val or not phone_val:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            if not phone_val.isdigit() or len(phone_val) < 10:
                messagebox.showwarning("Input Error", "Phone must be a valid number (at least 10 digits)")
                return
            self.db.update_customer(customer_id, name_val, phone_val)
            messagebox.showinfo("Success", "Customer updated")
            self.manage_customers()

        tk.Button(frame, text="Save", command=save, bg='#FFA500', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_customers, bg='#4a90e2', fg='white').pack()

    def delete_customer(self):
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showblancobourg. showwarning("Selection Error", "Please select a customer")
            return
        customer_id = self.customer_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this customer?"):
            if self.db.delete_customer(customer_id):
                messagebox.showinfo("Success", "Customer deleted")
            else:
                messagebox.showerror("Error", "Cannot delete customer with existing orders")
            self.manage_customers()

    def view_customer_orders(self):
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a customer")
            return
        customer_id = self.customer_tree.item(selected[0])['values'][0]
        self.show_customer_orders(customer_id)

    def show_customer_orders(self, customer_id):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text=f"Customer Orders (ID: {customer_id})", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        columns = ('ID', 'Order Date', 'Total Price', 'Status')
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        order_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=order_tree.yview)
        for col in columns:
            order_tree.heading(col, text=col)
            order_tree.column(col, width=150, anchor='center')
        order_tree.pack(fill='both', expand=True)

        for order in self.db.get_customer_orders(customer_id):
            order_tree.insert('', 'end', values=order)

        def view_details():
            selected = order_tree.selection()
            if not selected:
                messagebox.showwarning("Selection Error", "Please select an order")
                return
            order_id = order_tree.item(selected[0])['values'][0]
            self.show_order_details(order_id)

        tk.Button(frame, text="View Order Details", command=view_details, bg='#4CAF50', fg='white').pack(pady=5)
        tk.Button(frame, text="Back", command=self.manage_customers, bg='#4a90e2', fg='white').pack(pady=5)

    def manage_staff(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Staff Management", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        columns = ('ID', 'Name', 'Role', 'Phone')
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        self.staff_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.staff_tree.yview)
        for col in columns:
            self.staff_tree.heading(col, text=col)
            self.staff_tree.column(col, width=150, anchor='center')
        self.staff_tree.pack(fill='both', expand=True)

        for staff in self.db.list_staff():
            self.staff_tree.insert('', 'end', values=staff)

        button_frame = tk.Frame(frame, bg='white')
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Add Staff", command=self.add_staff, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Update Staff", command=self.update_staff, bg='#FFA500', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Delete Staff", command=self.delete_staff, bg='#f44336', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Back", command=self.show_dashboard, bg='#4a90e2', fg='white').pack(side='left', padx=5)

    def add_staff(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Add Staff", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Name:", bg='white').pack()
        name = tk.Entry(frame, font=('Arial', 12))
        name.pack(pady=5)
        tk.Label(frame, text="Role:", bg='white').pack()
        role = tk.Entry(frame, font=('Arial', 12))
        role.pack(pady=5)
        tk.Label(frame, text="Phone:", bg='white').pack()
        phone = tk.Entry(frame, font=('Arial', 12))
        phone.pack(pady=5)

        def save():
            name_val = name.get().strip()
            role_val = role.get().strip()
            phone_val = phone.get().strip()
            if not name_val or not role_val or not phone_val:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            if not phone_val.isdigit() or len(phone_val) < 10:
                messagebox.showwarning("Input Error", "Phone must be a valid number (at least 10 digits)")
                return
            self.db.add_staff(name_val, role_val, phone_val)
            messagebox.showinfo("Success", "Staff added")
            self.manage_staff()

        tk.Button(frame, text="Save", command=save, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_staff, bg='#4a90e2', fg='white').pack()

    def update_staff(self):
        selected = self.staff_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a staff member")
            return
        staff_id, name, role, phone = self.staff_tree.item(selected[0])['values']

        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Update Staff", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Name:", bg='white').pack()
        name_entry = tk.Entry(frame, font=('Arial', 12))
        name_entry.insert(0, name)
        name_entry.pack(pady=5)
        tk.Label(frame, text="Role:", bg='white').pack()
        role_entry = tk.Entry(frame, font=('Arial', 12))
        role_entry.insert(0, role)
        role_entry.pack(pady=5)
        tk.Label(frame, text="Phone:", bg='white').pack()
        phone_entry = tk.Entry(frame, font=('Arial', 12))
        phone_entry.insert(0, phone)
        phone_entry.pack(pady=5)

        def save():
            name_val = name_entry.get().strip()
            role_val = role_entry.get().strip()
            phone_val = phone_entry.get().strip()
            if not name_val or not role_val or not phone_val:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            if not phone_val.isdigit() or len(phone_val) < 10:
                messagebox.showwarning("Input Error", "Phone must be a valid number (at least 10 digits)")
                return
            self.db.update_staff(staff_id, name_val, role_val, phone_val)
            messagebox.showinfo("Success", "Staff updated")
            self.manage_staff()

        tk.Button(frame, text="Save", command=save, bg='#FFA500', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_staff, bg='#4a90e2', fg='white').pack()

    def delete_staff(self):
        selected = self.staff_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a staff member")
            return
        staff_id = self.staff_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this staff member?"):
            self.db.delete_staff(staff_id)
            messagebox.showinfo("Success", "Staff member deleted")
            self.manage_staff()

    def create_order(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Place Order", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Customer Name:", bg='white').pack()
        cust_name = tk.Entry(frame, font=('Arial', 12))
        cust_name.pack(pady=5)
        tk.Label(frame, text="Phone:", bg='white').pack()
        cust_phone = tk.Entry(frame, font=('Arial', 12))
        cust_phone.pack(pady=5)
        tk.Label(frame, text="Menu Item:", bg='white').pack()
        menu_items = self.db.list_menu()
        menu_var = tk.StringVar()
        menu_dropdown = ttk.Combobox(frame, textvariable=menu_var, values=[f"{item[1]} (ID: {item[0]})" for item in menu_items], font=('Arial', 12))
        menu_dropdown.pack(pady=5)
        tk.Label(frame, text="Quantity:", bg='white').pack()
        quantity = tk.Entry(frame, font=('Arial', 12))
        quantity.pack(pady=5)

        order_frame = tk.Frame(frame, bg='white')
        order_frame.pack(fill='both', expand=True)
        columns = ('Item Name', 'Quantity', 'Price', 'Total')
        self.order_tree = ttk.Treeview(order_frame, columns=columns, show='headings')
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=150, anchor='center')
        self.order_tree.pack(fill='both', expand=True)

        def add_to_order():
            try:
                qty = int(quantity.get().strip())
                if qty <= 0:
                    messagebox.showwarning("Input Error", "Quantity must be positive")
                    return
                selected = menu_var.get()
                if not selected:
                    messagebox.showwarning("Input Error", "Please select a menu item")
                    return
                menu_id = int(selected.split('(ID: ')[1].rstrip(')'))
                menu_item = next(item for item in menu_items if item[0] == menu_id)
                if qty > menu_item[3]:
                    messagebox.showwarning("Input Error", f"Only {menu_item[3]} available")
                    return
                self.current_order_items.append((menu_id, menu_item[1], qty, menu_item[2]))
                self.order_tree.insert('', 'end', values=(menu_item[1], qty, menu_item[2], qty * menu_item[2]))
                self.db.update_menu_item(menu_id, menu_item[1], menu_item[2], menu_item[3] - qty)
            except ValueError:
                messagebox.showerror("Input Error", "Invalid quantity")

        def save_order():
            if not self.current_order_items:
                messagebox.showwarning("Input Error", "No items in order")
                return
            name = cust_name.get().strip()
            phone = cust_phone.get().strip()
            if not name or not phone:
                messagebox.showwarning("Input Error", "Please enter customer details")
                return
            if not phone.isdigit() or len(phone) < 10:
                messagebox.showwarning("Input Error", "Phone must be a valid number (at least 10 digits)")
                return
            try:
                customer_id = self.db.add_customer(name, phone)
                total_price = sum(item[2] * item[3] for item in self.current_order_items)
                order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                order_id = self.db.create_order(customer_id, order_date, total_price)
                for item in self.current_order_items:
                    self.db.add_order_item(order_id, item[0], item[2])
                self.current_order_items = []
                messagebox.showinfo("Success", "Order placed")
                self.show_dashboard()
            except Exception as e:
                messagebox.showerror("Error", f"Error placing order: {str(e)}")

        button_frame = tk.Frame(frame, bg='white')
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Add to Order", command=add_to_order, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Place Order", command=save_order, bg='#FFA500', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Back", command=self.show_dashboard, bg='#4a90e2', fg='white').pack(side='left', padx=5)

    def view_orders(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="View Orders", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        columns = ('ID', 'Customer ID', 'Order Date', 'Total Price', 'Status')
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        self.order_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.order_tree.yview)
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=150, anchor='center')
        self.order_tree.pack(fill='both', expand=True)

        for order in self.db.list_orders():
            self.order_tree.insert('', 'end', values=order)

        status_frame = tk.Frame(frame, bg='white')
        status_frame.pack(pady=5)
        tk.Label(status_frame, text="Change Status:", bg='white').pack(side='left')
        status_var = tk.StringVar()
        status_dropdown = ttk.Combobox(status_frame, textvariable=status_var, 
                                    values=['Pending', 'Processing', 'Completed', 'Cancelled'], 
                                    font=('Arial', 12), state='readonly')
        status_dropdown.pack(side='left', padx=5)

        def change_status():
            selected = self.order_tree.selection()
            if not selected:
                messagebox.showwarning("Selection Error", "Please select an order")
                return
            order_id = self.order_tree.item(selected[0])['values'][0]
            new_status = status_var.get()
            if not new_status:
                messagebox.showwarning("Input Error", "Please select a status")
                return
            self.db.update_order_status(order_id, new_status)
            messagebox.showinfo("Success", f"Order status updated to {new_status}")
            self.view_orders()

        def view_details():
            selected = self.order_tree.selection()
            if not selected:
                messagebox.showwarning("Selection Error", "Please select an order")
                return
            order_id = self.order_tree.item(selected[0])['values'][0]
            self.show_order_details(order_id)

        button_frame = tk.Frame(frame, bg='white')
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="View Details", command=view_details, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Change Status", command=change_status, bg='#FFA500', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Back", command=self.show_dashboard, bg='#4a90e2', fg='white').pack(side='left', padx=5)

    def show_order_details(self, order_id):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text=f"Order Details (ID: {order_id})", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        columns = ('ID', 'Item Name', 'Quantity', 'Price')
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        order_items_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=order_items_tree.yview)
        for col in columns:
            order_items_tree.heading(col, text=col)
            order_items_tree.column(col, width=150, anchor='center')
        order_items_tree.pack(fill='both', expand=True)

        for item in self.db.get_order_items(order_id):
            order_items_tree.insert('', 'end', values=item)

        tk.Button(frame, text="Back", command=self.view_orders, bg='#4a90e2', fg='white').pack(pady=5)

    def manage_inventory(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Inventory Management", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        columns = ('ID', 'Item Name', 'Quantity')
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        self.inventory_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.inventory_tree.yview)
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=150, anchor='center')
        self.inventory_tree.pack(fill='both', expand=True)

        for item in self.db.list_inventory():
            self.inventory_tree.insert('', 'end', values=item)

        button_frame = tk.Frame(frame, bg='white')
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Add Item", command=self.add_inventory_item, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Update Item", command=self.update_inventory, bg='#FFA500', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Back", command=self.show_dashboard, bg='#4a90e2', fg='white').pack(side='left', padx=5)

    def add_inventory_item(self):
        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Add Inventory Item", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Item Name:", bg='white').pack()
        item_name = tk.Entry(frame, font=('Arial', 12))
        item_name.pack(pady=5)
        tk.Label(frame, text="Quantity:", bg='white').pack()
        quantity = tk.Entry(frame, font=('Arial', 12))
        quantity.pack(pady=5)

        def save():
            name = item_name.get().strip()
            qty = quantity.get().strip()
            if not name or not qty:
                messagebox.showwarning("Input Error", "Please fill all fields")
                return
            try:
                qty_num = int(qty)
                if qty_num < 0:
                    messagebox.showwarning("Input Error", "Quantity cannot be negative")
                    return
                self.db.add_inventory_item(name, qty_num)
                messagebox.showinfo("Success", "Inventory item added")
                self.manage_inventory()
            except ValueError:
                messagebox.showerror("Input Error", "Invalid quantity")

        tk.Button(frame, text="Save", command=save, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_inventory, bg='#4a90e2', fg='white').pack()

    def update_inventory(self):
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an inventory item")
            return
        item_id, name, qty = self.inventory_tree.item(selected[0])['values']

        self.clear_window()
        canvas = tk.Canvas(self.root)
        canvas.pack(fill='both', expand=True)
        self.current_canvas = canvas
        self.set_background(canvas, for_login=False)

        frame = tk.Frame(canvas, bg='white', bd=2, relief='raised')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Update Inventory Item", font=("Arial", 20, "bold"), bg='white').pack(pady=10)
        tk.Label(frame, text="Item Name:", bg='white').pack()
        item_name = tk.Entry(frame, font=('Arial', 12))
        item_name.insert(0, name)
        item_name.pack(pady=5)
        tk.Label(frame, text="Quantity:", bg='white').pack()
        quantity = tk.Entry(frame, font=('Arial', 12))
        quantity.insert(0, qty)
        quantity.pack(pady=5)

        def save():
            qty = quantity.get().strip()
            if not qty:
                messagebox.showwarning("Input Error", "Please enter quantity")
                return
            try:
                qty_num = int(qty)
                if qty_num < 0:
                    messagebox.showwarning("Input Error", "Quantity cannot be negative")
                    return
                self.db.update_inventory(item_id, qty_num)
                messagebox.showinfo("Success", "Inventory item updated")
                self.manage_inventory()
            except ValueError:
                messagebox.showerror("Input Error", "Invalid quantity")

        tk.Button(frame, text="Save", command=save, bg='#FFA500', fg='white').pack(pady=10)
        tk.Button(frame, text="Back", command=self.manage_inventory, bg='#4a90e2', fg='white').pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = CanteenApp(root)
    root.mainloop()