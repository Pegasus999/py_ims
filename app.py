import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QLabel,
    QLineEdit,
    QDateEdit,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt5.QtCore import QDate
from PyQt5.QtCore import Qt
import sqlite3
import uuid

# Charges / Credits


class AddPopup(QDialog):
    def __init__(self, table):
        super().__init__()
        self.setWindowTitle("Add Product")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.profit_input = QLineEdit()
        self.quantity_input = QLineEdit()

        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Price:"))
        layout.addWidget(self.price_input)
        layout.addWidget(QLabel("Profit:"))
        layout.addWidget(self.profit_input)
        layout.addWidget(QLabel("Quantity:"))
        layout.addWidget(self.quantity_input)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def accept(self):
        if self.validate_input():
            super().accept()

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "price": self.price_input.text(),
            "profit": self.profit_input.text(),
            "quantity": self.quantity_input.text(),
        }

    def validate_input(self):
        try:
            float(self.price_input.text())
            int(self.quantity_input.text())
            float(self.profit_input.text())
            return True
        except ValueError:
            return False


class SecondWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selling")
        self.setGeometry(100, 100, 860, 400)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        central_widget.setLayout(layout)
        left_table = QTableWidget(0, 7)
        right_table = QTableWidget(0, 6)

        # Search bar
        search_field = QLineEdit()
        search_button = QPushButton("Search")
        self.search_field = search_field
        search_button.clicked.connect(self.search_products)

        search_layout = QHBoxLayout()
        search_layout.addWidget(search_field, stretch=4)  # Takes 80% of width
        search_layout.addWidget(search_button, stretch=1)

        # Configure tables (e.g., headers, columns)
        # ...
        column_labels1 = [
            "id",
            "Name",
            "Selling Price",
            "Buying Price",
            "Quantity",
            "Inserted On",
            "Profit",
        ]
        column_labels2 = [
            "id",
            "Name",
            "Selling Price",
            "Quantity",
            "Buying Price",
            "Profit",
        ]

        left_table.setHorizontalHeaderLabels(column_labels1)
        right_table.setHorizontalHeaderLabels(column_labels2)
        left_table.setColumnHidden(0, True)
        left_table.setColumnHidden(3, True)
        left_table.setColumnHidden(6, True)
        right_table.setColumnHidden(0, True)
        right_table.setColumnHidden(4, True)
        right_table.setColumnHidden(5, True)
        left_table.setColumnHidden(0, True)

        # Labels and Checkout Button (Row 1)
        total_title = QLabel("Total:")
        total_label = QLabel("0,00$")
        checkout_button = QPushButton("Checkout")
        checkout_button.clicked.connect(self.checkout)
        delete_button = QPushButton("Delete")
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.show_add_dialog)
        self.total_label = total_label
        total_title.setStyleSheet("QLabel{font-size: 16pt;}")
        total_label.setStyleSheet("QLabel{font-size: 16pt;}")
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(total_title)
        labels_layout.addWidget(total_label)
        labels_layout.addWidget(add_button)
        labels_layout.addWidget(delete_button)
        labels_layout.addWidget(checkout_button)

        # Main layout structure
        main_layout = QVBoxLayout()
        main_layout.addLayout(search_layout)
        main_layout.addWidget(left_table, stretch=1)  # Takes 50% of width
        right_top_layout = QVBoxLayout()
        right_top_layout.addWidget(right_table, stretch=6)  # Takes 60% of height
        right_top_layout.addLayout(labels_layout)  # Labels and buttons
        main_layout.addLayout(right_top_layout, stretch=1)  # Takes 50% of width
        layout.addLayout(main_layout, 0, 0, 1, 1)

        self.right_table = right_table
        self.left_table = left_table

        left_table.itemDoubleClicked.connect(self.product_clicked)
        delete_button.clicked.connect(self.product_removed)
        right_table.itemClicked.connect(self.clicked)
        self.selected = 0

    def fillTable(self, left_table, result):
        # Fill the left table with all products initially
        if result == None:
            db_cursor.execute("SELECT * FROM Products")
            data = db_cursor.fetchall()
        else:
            data = result

        left_table.setRowCount(0)  # Clear existing rows

        for row_index, row_data in enumerate(data):
            left_table.insertRow(row_index)
            # Include the ID field
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))

                # Set profit column as uneditable
                if col_index == 5:  # Profit column index
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                left_table.setItem(row_index, col_index, item)

    def search_products(self):
        # Handle the search button click and populate the left table based on the search query
        query = self.search_field.text()
        if query:
            self.populateLeftTable(query)
        else:
            # If the search query is empty, display all products
            self.fillTable(self.left_table, None)

    def populateLeftTable(self, query):
        if query != "":
            db_cursor.execute(
                "SELECT * FROM Products WHERE Name LIKE ? AND Quantity > 0",
                ("%" + query + "%",),
            )
            data = db_cursor.fetchall()
            self.fillTable(self.left_table, data)
        else:
            self.fillTable(self.left_table, None)

    def add_to_profits(self, item_data):
        today_date = QDate.currentDate().toString("yyyy-MM-dd")
        db_cursor.execute(
            "SELECT quantity FROM Profits WHERE name = ? AND price = ? AND date = ?",
            (item_data["name"], item_data["price"], today_date),
        )
        existing_row = db_cursor.fetchone()

        if existing_row:
            # Update the existing row by adding the new quantity
            updated_quantity = existing_row[0] + int(item_data["quantity"])

            db_cursor.execute(
                """
                UPDATE Profits
                SET quantity = ?,
                    profit = ?
                WHERE name = ? AND price = ? AND date = ?
                """,
                (
                    updated_quantity,
                    item_data["profit"],
                    item_data["name"],
                    item_data["price"],
                    today_date,
                ),
            )
        else:
            # Insert a new row if the item doesn't exist for today's date
            db_cursor.execute(
                """
                INSERT INTO Profits (id, name, price, quantity, profit, date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    item_data["name"],
                    item_data["price"],
                    item_data["quantity"],
                    item_data["profit"],
                    today_date,
                ),
            )
        db_connection.commit()

        if item_data["id"] != "MANUAL":
            query = f"UPDATE Products SET quantity = quantity - {int(item_data['quantity'])} WHERE id = '{item_data['id']}'"
            db_cursor.execute(query)
            db_connection.commit()

    def checkout(self):
        for row in range(self.right_table.rowCount()):
            item_data = {
                "id": self.right_table.item(row, 0).text(),
                "name": self.right_table.item(row, 1).text(),
                "price": self.right_table.item(row, 2).text(),
                "quantity": self.right_table.item(row, 3).text(),
                "profit": self.right_table.item(row, 5).text(),
            }

            self.add_to_profits(item_data)
        self.right_table.setRowCount(0)
        self.count_total()
        load_data()

    def show_add_dialog(self):
        add_dialog = AddPopup(self)
        if add_dialog.exec_() == QDialog.Accepted:
            item_data = add_dialog.get_data()

            row_position = self.right_table.rowCount()
            self.right_table.insertRow(row_position)
            self.right_table.setItem(row_position, 0, QTableWidgetItem("MANUAL"))
            self.right_table.setItem(
                row_position, 1, QTableWidgetItem(item_data["name"])
            )
            self.right_table.setItem(
                row_position, 2, QTableWidgetItem(item_data["price"])
            )
            self.right_table.setItem(
                row_position, 3, QTableWidgetItem(item_data["quantity"])
            )
            self.right_table.setItem(row_position, 4, QTableWidgetItem("0"))
            self.right_table.setItem(
                row_position, 5, QTableWidgetItem(item_data["profit"])
            )
            self.count_total()

    def clicked(self, item):
        self.selected = item.row()
        self.right_table.itemChanged.connect(self.product_changed)

    def product_changed(self, item):
        self.right_table.itemChanged.disconnect(self.product_changed)
        col = item.column()
        row = item.row()
        if col == 3:
            self.right_table.setItem(row, 3, QTableWidgetItem(item.text()))
            self.count_total()
        elif col == 2:
            self.right_table.setItem(row, 2, QTableWidgetItem(item.text()))
            self.right_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    str(
                        float(self.right_table.item(row, 2).text())
                        - float(self.right_table.item(row, 4).text())
                    )
                ),
            )
            self.count_total()

    def product_removed(self):
        if (
            self.selected in range(self.right_table.rowCount())
            and show_confirmation_dialog("Are you sure you want to delete this item?")
            == QMessageBox.Yes
        ):
            self.right_table.removeRow(self.selected)
        else:
            return
        self.count_total()

    def product_clicked(self, item):
        selected_row = item.row()
        name_item = self.left_table.item(selected_row, 1)
        price_item = self.left_table.item(selected_row, 2)
        buyingPrice_item = self.left_table.item(selected_row, 3)
        self.right_table.insertRow(self.right_table.rowCount())
        self.right_table.setItem(
            self.right_table.rowCount() - 1,
            0,
            QTableWidgetItem(self.left_table.item(selected_row, 0).text()),
        )
        self.right_table.setItem(
            self.right_table.rowCount() - 1, 1, QTableWidgetItem(name_item.text())
        )
        self.right_table.setItem(
            self.right_table.rowCount() - 1, 2, QTableWidgetItem(price_item.text())
        )
        self.right_table.setItem(
            self.right_table.rowCount() - 1,
            4,
            QTableWidgetItem(buyingPrice_item.text()),
        )
        for col in range(self.right_table.columnCount()):
            item = self.right_table.item(self.right_table.rowCount() - 1, col)
            if col == 1 and item:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.right_table.setItem(
            self.right_table.rowCount() - 1, 3, QTableWidgetItem("1")
        )
        self.right_table.setItem(
            self.right_table.rowCount() - 1,
            5,
            QTableWidgetItem(
                str(float(price_item.text()) - float(buyingPrice_item.text()))
            ),
        )
        self.left_table.setRowCount(0)
        self.count_total()

    def count_total(self):
        total_price = 0
        for row in range(self.right_table.rowCount()):
            price = float(self.right_table.item(row, 2).text())
            quantity = int(self.right_table.item(row, 3).text())
            total_price += price * quantity
        self.total_label.setText(str(total_price))

    def closeEvent(self, a0) -> None:
        self.search_field.setText("")
        self.left_table.setRowCount(0)
        self.right_table.setRowCount(0)
        self.count_total()
        return super().closeEvent(a0)


class SearchDialog(QDialog):
    def __init__(self, table_widget):
        super().__init__()
        self.setWindowTitle("Search Item")

        self.table_widget = table_widget

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.search_input = QLineEdit()
        layout.addWidget(self.search_input)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_items)
        layout.addWidget(search_button)

    def search_items(self):
        search_text = self.search_input.text().strip()
        if search_text:
            for row in range(self.table_widget.rowCount()):
                name_item = self.table_widget.item(row, 1)
                if name_item and search_text.lower() in name_item.text().lower():
                    self.table_widget.selectRow(row)


class AddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Product")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.name_input = QLineEdit()
        self.selling_price_input = QLineEdit()
        self.buying_price_input = QLineEdit()
        self.quantity_input = QLineEdit()
        self.inserted_on_input = QDateEdit(QDate.currentDate())  # Set to today's date
        self.inserted_on_input.setDisplayFormat("dd-MM-yyyy")  # Set date format

        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Selling Price:"))
        layout.addWidget(self.selling_price_input)
        layout.addWidget(QLabel("Buying Price:"))
        layout.addWidget(self.buying_price_input)
        layout.addWidget(QLabel("Quantity:"))
        layout.addWidget(self.quantity_input)
        layout.addWidget(QLabel("Inserted On:"))
        layout.addWidget(self.inserted_on_input)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.accepted.connect(add_new_row)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "selling_price": self.selling_price_input.text(),
            "buying_price": self.buying_price_input.text(),
            "quantity": self.quantity_input.text(),
            "inserted_on": self.inserted_on_input.date().toString("yyyy-MM-dd"),
        }

    def accept(self):
        if self.validate_input():
            super().accept()

    def validate_input(self):
        try:
            float(self.selling_price_input.text())
            float(self.buying_price_input.text())
            int(self.quantity_input.text())
            self.inserted_on_input.date().toString("yyyy-MM-dd")
            return True
        except ValueError:
            return False


class ProfitWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monthly Profit")
        self.setGeometry(100, 100, 500, 500)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Get the current date
        current_date = QDate.currentDate()

        if current_date.day() > 20:
            last_month = current_date
        else:
            # Calculate the last month's date
            last_month = current_date.addMonths(-1)

        # Set the day to 20

        self.date_start = QDateEdit(QDate(last_month.year(), last_month.month(), 20))
        self.date_end = QDateEdit(QDate.currentDate())
        self.date_start.setDisplayFormat("yyyy-MM-dd")
        self.date_end.setDisplayFormat("yyyy-MM-dd")
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Id", "Name", "Price", "Profit", "Quantity", "Date"]
        )
        self.table.setColumnHidden(0, True)
        clear_button = QPushButton("CLEAR")
        cancel_button = QPushButton("CANCEL")
        clear_button.clicked.connect(self.clear_table)
        cancel_button.clicked.connect(self.cancel_action)

        total_label = QLabel("Total Profit: 0,00")
        total_label.setStyleSheet("QLabel{font-size: 16pt;}")
        self.total_label = total_label
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        main_layout.addWidget(self.date_start)
        main_layout.addWidget(self.date_end)
        main_layout.addWidget(self.table)

        main_layout.addWidget(total_label)

        button_layout.addWidget(clear_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)
        self.query_database(self.date_start.text(), self.date_end.text())
        self.date_start.dateChanged.connect(self.date_changed)
        self.date_end.dateChanged.connect(self.date_changed)
        self.table.itemClicked.connect(self.item_clicked)

    def item_clicked(self, item):
        self.selected = item.row()
        self.table.itemChanged.connect(self.item_changed)

    def item_changed(self, item):
        self.table.itemChanged.disconnect(self.item_changed)
        col = item.column()
        row = item.row()
        if col == 2:  # Check if the price column was edited
            # Get the edited price
            new_price = float(item.text())
            if (
                show_confirmation_dialog(
                    "Are you sure you want to clear these records?"
                )
                == QMessageBox.Yes
            ):
                # Create a new profit row and update the original row's quantity
                new_profit_row = self.create_profit_row(row, new_price)
                self.update_quantity(row)
                self.update_table_with_profit(new_profit_row)
                self.query_database(self.date_start.text(), self.date_end.text())
            else:
                return

    def update_quantity(self, row):
        id = self.table.item(row, 0).text()
        current_quantity = int(
            self.table.item(row, 4).text()
        )  # Assuming quantity is in the fourth column
        new_quantity = current_quantity - 1

        if new_quantity > 0:
            # Update the quantity in the database
            db_cursor.execute(
                "UPDATE Profits SET quantity = ? WHERE id = ?", (new_quantity, id)
            )
        else:
            # Remove the row from the database if quantity is 0
            db_cursor.execute("DELETE FROM Profits WHERE id = ?", (id,))

        # Update the quantity in the table
        self.table.setItem(row, 4, QTableWidgetItem(str(new_quantity)))

        # Commit the changes to the database
        db_connection.commit()

    def update_table_with_profit(self, profit_row):
        # Add the new profit row to the table
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Populate the cells with the values from the profit row
        self.table.setItem(row_position, 0, QTableWidgetItem(profit_row["id"]))
        self.table.setItem(row_position, 1, QTableWidgetItem(profit_row["name"]))
        self.table.setItem(row_position, 2, QTableWidgetItem(str(profit_row["price"])))
        self.table.setItem(row_position, 3, QTableWidgetItem(str(profit_row["profit"])))
        self.table.setItem(
            row_position, 4, QTableWidgetItem(str(profit_row["quantity"]))
        )
        self.table.setItem(row_position, 5, QTableWidgetItem(profit_row["date"]))
        db_cursor.execute(
            """
            INSERT INTO Profits (id, name, price, profit, quantity ,date)
            VALUES (?, ?, ?, ?, ? ,?)
        """,
            (
                profit_row["id"],
                profit_row["name"],
                profit_row["price"],
                profit_row["profit"],
                profit_row["quantity"],
                profit_row["date"],
            ),
        )

        db_connection.commit()
        # Update the total profit
        self.count_total()

    def create_profit_row(self, row, new_price):
        # Fetch the product details from the original row
        product_name = self.table.item(
            row, 1
        ).text()  # Assuming name is in the second column
        date = self.table.item(row, 5).text()

        # Calculate the profit using the difference between old and new prices
        old_price = float(
            self.table.item(row, 2).text()
        )  # Assuming old price is in the fourth column
        old_profit = float(
            self.table.item(row, 3).text()
        )  # Assuming old profit is in the fifth column
        new_profit = old_profit + (new_price - old_price)

        # Create a new profit row as a dictionary
        new_profit_row = {
            "id": str(uuid.uuid4()),
            "name": product_name,
            "price": new_price,
            "profit": new_profit,
            "quantity": 1,
            "date": date,
        }

        return new_profit_row

    def date_changed(self):
        new_start = self.date_start.text()
        new_end = self.date_end.text()
        self.query_database(new_start, new_end)

    def query_database(self, start_date, end_date):
        query = (
            f"SELECT * FROM Profits WHERE date BETWEEN '{start_date}' AND '{end_date}'"
        )

        db_cursor.execute(query)
        data = db_cursor.fetchall()
        self.table.setRowCount(0)  # Clear existing rows

        for row_index, row_data in enumerate(data):
            self.table.insertRow(row_index)
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.table.setItem(row_index, col_index, item)

        self.count_total()

    # id 0
    # name 1
    # price 2
    # profit 3
    # quantity 4

    def count_total(self):
        total_price = 0
        for row in range(self.table.rowCount()):
            price = float(
                self.table.item(row, 3).text()
            )  # Assuming price is in the third column
            quantity = int(
                self.table.item(row, 4).text()
            )  # Assuming quantity is in the fourth column
            total_price += price * quantity
        self.total_label.setText(f"Total Profit: {str(total_price)}")

    def clear_table(self):
        if (
            show_confirmation_dialog("Are you sure you want to clear these records?")
            == QMessageBox.Yes
        ):
            query = f"DELETE FROM Profits WHERE date BETWEEN '{self.date_start.text()}' AND '{self.date_end.text()}'"
            db_cursor.execute(query)
            db_connection.commit()
            self.table.setRowCount(0)
            self.count_total()
        else:
            return

    def closeEvent(self, a0) -> None:
        global profit_window
        profit_window = None
        return super().closeEvent(a0)

    def cancel_action(self):
        self.close()
        global profit_window
        profit_window = None


def delete_row():
    selected_row = (
        table_widget.currentRow()
    )  # Get the index of the currently selected row

    if selected_row >= 0:
        record_id = table_widget.item(
            selected_row, 0
        ).text()  # Get the UUID ID of the selected row
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText("Are you sure you want to delete this item?")
        msg_box.setWindowTitle("Confirm Deletion")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg_box.exec_()

        if result == QMessageBox.Yes:
            db_cursor.execute("DELETE FROM Products WHERE id = ?", (record_id,))
            db_connection.commit()

            # Remove the selected row from the table widget
            table_widget.removeRow(selected_row)


def showAlert(str):
    err = QMessageBox()

    # Set the dialog title and text
    err.setWindowTitle("Alert")
    err.setText(str)

    # Set the standard button(s) in the dialog
    err.setStandardButtons(QMessageBox.Ok)


def add_new_row():
    global add_dialog
    new_row_data = add_dialog.get_data()
    add_dialog = None
    try:
        id = str(uuid.uuid4())
        selling_price = float(new_row_data["selling_price"])
        buying_price = float(new_row_data["buying_price"])
        quantity = int(new_row_data["quantity"])
        profit = selling_price - buying_price

        # Insert data into the database
        db_cursor.execute(
            """
            INSERT INTO Products (id, name, selling_price, buying_price, quantity ,inserted_on, profit)
            VALUES (?, ?, ?, ?, ? ,?, ?)
        """,
            (
                id,
                new_row_data["name"],
                selling_price,
                buying_price,
                quantity,
                new_row_data["inserted_on"],
                profit,
            ),
        )

        db_connection.commit()

        load_data()

    except Exception as e:
        print("Error:", e)  # Print the error for debugging


def load_data():
    db_cursor.execute("SELECT * FROM Products")
    data = db_cursor.fetchall()
    table_widget.setRowCount(0)  # Clear existing rows

    for row_index, row_data in enumerate(data):
        table_widget.insertRow(row_index)
        # Include the ID field
        for col_index, cell_data in enumerate(row_data):
            item = QTableWidgetItem(str(cell_data))

            # Set profit column as uneditable
            if col_index == 5:  # Profit column index
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            table_widget.setItem(row_index, col_index, item)

        # Hide the ID column visually
    table_widget.setColumnHidden(0, True)


def update_profit(id, row, selling_price, buying_price):
    profit = selling_price - buying_price
    item = QTableWidgetItem(str(profit))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    table_widget.setItem(row, 6, item)
    db_cursor.execute(
        "UPDATE Products SET selling_price = ?, buying_price = ?, profit = ? WHERE id = ?",
        (selling_price, buying_price, profit, id),
    )
    db_connection.commit()


def update_quantity(id, row, quantity):
    item = QTableWidgetItem(str(quantity))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    table_widget.setItem(row, 4, item)
    db_cursor.execute("UPDATE Products SET quantity = ? WHERE id = ?", (quantity, id))
    db_connection.commit()


def update_name(id, row, name):
    item = QTableWidgetItem(name)
    table_widget.setItem(row, 1, item)
    db_cursor.execute("UPDATE Products SET name = ? WHERE id = ?", (name, id))
    db_connection.commit()


def show_confirmation_dialog(string):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setText(string)
    msg_box.setWindowTitle("Confirm Update")
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return msg_box.exec_()


previous_values = {}


def item_clicked(item):
    row = item.row()
    col = item.column()
    # Store the current value when an item is clicked
    previous_values[(row, col)] = item.text()
    table_widget.itemChanged.connect(item_changed)


def item_changed(item):
    row = item.row()
    col = item.column()
    table_widget.itemChanged.disconnect(item_changed)

    if col == 1:
        if (
            show_confirmation_dialog("Are you sure you want to update the name")
            == QMessageBox.Yes
        ):
            update_name(
                table_widget.item(row, 0).text(), row, table_widget.item(row, 1).text()
            )
    elif col == 4:
        if (
            show_confirmation_dialog("Are you sure you want to update the quanitity?")
            == QMessageBox.Yes
        ):
            quantity = int(table_widget.item(row, 4).text())
            update_quantity(table_widget.item(row, 0).text(), row, quantity)
    elif col == 2 or col == 3:
        try:
            if (
                show_confirmation_dialog("Are you sure you want to update the price?")
                == QMessageBox.Yes
            ):
                selling_price = float(table_widget.item(row, 2).text())
                buying_price = float(table_widget.item(row, 3).text())
                update_profit(
                    table_widget.item(row, 0).text(), row, selling_price, buying_price
                )
        except ValueError:
            # Invalid input, revert to the previous value
            prev_value = previous_values[
                (row, col)
            ]  # Get the previous value from the dictionary
            item.setText(prev_value)


app = QApplication(sys.argv)

# Connect to the SQLite database (creates if not exists)
db_connection = sqlite3.connect("products.db")
db_cursor = db_connection.cursor()

# Create the "Products" table if it doesn't exist
db_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS Products (
        id TEXT PRIMARY KEY,
        name TEXT,
        selling_price REAL,
        buying_price REAL,
        quantity INT,
        inserted_on TEXT,
        profit REAL
    )
"""
)
db_cursor.execute(
    """
     CREATE TABLE IF NOT EXISTS Profits (
                id TEXT PRIMARY KEY, 
                name TEXT,
                price REAL,
                profit REAL,
                quantity INTEGER,
                date TEXT
            )
"""
)
db_connection.commit()

# Create the main window
window = QWidget()
window.setWindowTitle("Gestion de stock")
window.setGeometry(100, 100, 730, 400)

# Create a layout for the main window
main_layout = QHBoxLayout(window)

# Create a QTableWidget with 5 columns
table_widget = QTableWidget(0, 7)  # 0 rows initially
main_layout.addWidget(table_widget)


# Set column labels
column_labels = [
    "id",
    "Name",
    "Selling Price",
    "Buying Price",
    "Quantity",
    "Inserted On",
    "Profit",
]
table_widget.setHorizontalHeaderLabels(column_labels)

# Connect the itemClicked signal to the item_clicked function
table_widget.itemClicked.connect(item_clicked)


# Create a layout for the buttons
buttons_layout = QVBoxLayout()

# Create buttons and add them to the layout
button_labels = ["Add", "Find", "Delete", "Sell", "Monthly Profit"]
buttons = [QPushButton(label) for label in button_labels]
for button in buttons:
    button.setFixedHeight(50)  # Set button height
    buttons_layout.addWidget(button)

second_window = None
profit_window = None
add_dialog = None


def showSellWindow():
    global second_window  # Declare the variable as global
    if second_window is None:
        second_window = SecondWindow()
    second_window.show()


def showProfitWindow():
    global profit_window  # Declare the variable as global
    if profit_window is None:
        profit_window = ProfitWindow()
    profit_window.show()


def showAddWindow():
    global add_dialog  # Declare the variable as global
    if add_dialog is None:
        add_dialog = AddDialog(window)

    add_dialog.show()


add_button = buttons[0]
sell_button = buttons[3]
sell_button.clicked.connect(showSellWindow)
profit_button = buttons[4]
profit_button.clicked.connect(showProfitWindow)
add_button.clicked.connect(showAddWindow)
search_dialog = SearchDialog(table_widget)
search_button = buttons[1]
search_button.clicked.connect(search_dialog.exec_)
delete_button = buttons[2]

delete_button.clicked.connect(delete_row)
main_layout.addLayout(buttons_layout)

# Add the buttons layout to the main layout

load_data()

window.show()

sys.exit(app.exec_())
