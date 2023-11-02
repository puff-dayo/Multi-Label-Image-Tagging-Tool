import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel,
                               QFileDialog, QGroupBox, QTableWidget,
                               QTableWidgetItem, QLineEdit, QWidget, QSplitter, QSizePolicy, QCheckBox,
                               QMessageBox)
from PySide6.QtGui import QPixmap, QImage, QKeySequence, QShortcut
from PySide6.QtCore import Qt
import csv
import os


class ImageTaggingApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main window properties
        self.setWindowTitle("Multi Label Image Tagging")
        self.setGeometry(100, 100, 800, 600)
        self.night_mode = False
        self.night_style = """
            QMainWindow {
                background-color: #2C2C2C;
            }
            QLabel, QTableWidget, QHeaderView::section {
                background-color: #2C2C2C;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #3A3A3A;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QGroupBox {
                color: #FFFFFF;
            }
            QTableWidget {
                gridline-color: #5A5A5A;
            }
            QLineEdit {
                background-color: #3A3A3A;
                color: #FFFFFF;
            }
        """

        # Main layout
        main_splitter = QSplitter(Qt.Horizontal)

        # Image label
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_splitter.addWidget(self.image_label)

        # Right side layout
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_widget.setFixedWidth(400)  # Set a fixed width for the right side

        # Top group
        self.top_group = QGroupBox("Control")
        top_layout = QVBoxLayout()
        self.load_folder_btn = QPushButton("Open Folder")
        self.next_btn = QPushButton("Next (keyboard: d)")
        self.prev_btn = QPushButton("Previous (keyboard: a)")
        top_layout.addWidget(self.load_folder_btn)
        self.current_image_label = QLabel()
        top_layout.addWidget(self.current_image_label)
        top_layout.addWidget(self.next_btn)
        top_layout.addWidget(self.prev_btn)
        self.top_group.setLayout(top_layout)
        right_layout.addWidget(self.top_group)

        # Middle group
        self.middle_group = QGroupBox("Tag Manager")
        middle_layout = QVBoxLayout()
        self.tag_line_edit = QLineEdit()
        self.add_tag_btn = QPushButton("Add Tag")
        self.delete_tag_btn = QPushButton("Delete Tag (select a ROW)")
        self.tag_table = QTableWidget(0, 3)
        self.tag_table.setHorizontalHeaderLabels(['Tag Name', 'Count', 'Do Tag'])
        middle_layout.addWidget(self.tag_line_edit)
        middle_layout.addWidget(self.add_tag_btn)
        middle_layout.addWidget(self.delete_tag_btn)
        middle_layout.addWidget(QLabel("HOW TO USE:"))
        middle_layout.addWidget(QLabel("1. Add some tags. Double click to rename.\n2. Select the 'Do Tag' column with a click. \nLeft hand on A/D to change images; \nright hand on Up/Down to change tags; \nleft thumb on Space to toggle a tag selected."))
        middle_layout.addWidget(QLabel("Nya~"))
        middle_layout.addWidget(self.tag_table)
        self.middle_group.setLayout(middle_layout)
        right_layout.addWidget(self.middle_group)

        # Bottom group
        self.bottom_group = QGroupBox("Operations")
        bottom_layout = QVBoxLayout()
        self.import_btn = QPushButton("Import")
        self.export_btn = QPushButton("Export")
        bottom_layout.addWidget(self.import_btn)
        bottom_layout.addWidget(self.export_btn)
        self.night_mode_btn = QPushButton("Night Mode (manual)")
        bottom_layout.addWidget(self.night_mode_btn)
        encode_csv_btn = QPushButton("Encode CSV")

        bottom_layout.addWidget(encode_csv_btn)
        self.bottom_group.setLayout(bottom_layout)
        right_layout.addWidget(self.bottom_group)

        main_splitter.addWidget(right_widget)
        self.setCentralWidget(main_splitter)

        # Signals and slots
        encode_csv_btn.clicked.connect(self.encode_csv)
        self.night_mode_btn.clicked.connect(self.toggle_night_mode)
        self.load_folder_btn.clicked.connect(self.load_folder)
        self.next_btn.clicked.connect(self.next_image)
        self.prev_btn.clicked.connect(self.prev_image)
        self.add_tag_btn.clicked.connect(self.add_tag)
        self.delete_tag_btn.clicked.connect(self.delete_tag)
        self.import_btn.clicked.connect(self.import_tags)
        self.export_btn.clicked.connect(self.export_tags)

        # Image list and index
        self.image_list = []
        self.current_index = 0

        # Initialize a dictionary to store the tags for each image
        self.image_tags = {}

        next_shortcut = QShortcut(QKeySequence("d"), self)
        next_shortcut.activated.connect(self.next_image)

        prev_shortcut = QShortcut(QKeySequence("a"), self)
        prev_shortcut.activated.connect(self.prev_image)

    def encode_csv(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Choose CSV", "", "CSV Files (*.csv);;All Files (*)",
                                                   options=options)

        if file_name:
            # Read the CSV using pandas
            df = pd.read_csv(file_name)

            # Check if 'Classes' column exists
            if 'Tags' in df.columns:
                # Split the 'Classes' column based on space
                all_tags = df['Tags'].str.split(' ', expand=True).stack()
                df_encoded = pd.get_dummies(all_tags, prefix='').groupby(level=0).sum()

                # Merge the encoded tags back to the original dataframe
                df = df.join(df_encoded)
                df.drop(columns='Tags', inplace=True)

                # Save the encoded data to a new CSV file
                save_path, _ = QFileDialog.getSaveFileName(self, "Save Encoded CSV", "",
                                                           "CSV Files (*.csv);;All Files (*)", options=options)
                if save_path:
                    df.to_csv(save_path, index=False)
                    QMessageBox.information(self, "Success", "CSV encoded and saved successfully!")
            else:
                QMessageBox.warning(self, "Error", "Selected CSV does not have a 'Tags' column!")

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.image_list = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                               f.endswith(('.png', '.jpg', '.jpeg'))]
            self.current_index = 0
            self.show_image()

    def show_image(self):
        if self.image_list:
            pixmap = QPixmap(self.image_list[self.current_index])
            self.image_label.setPixmap(
                pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio))

            # Update the checkboxes based on the tags of the current image
            current_image_path = self.image_list[self.current_index]
            image_tags = self.image_tags.get(current_image_path, set())
            for row in range(self.tag_table.rowCount()):
                tag = self.tag_table.item(row, 0).text()
                checkbox = self.tag_table.cellWidget(row, 2)
                checkbox.blockSignals(True)  # Block signals to avoid triggering update_image_tags
                checkbox.setChecked(tag in image_tags)
                checkbox.blockSignals(False)

            self.current_image_label.setText(f"Image {self.current_index + 1} of {len(self.image_list)}")

    def update_image_tags(self):
        # Update the tags of the current image based on the checkbox states
        current_image_path = self.image_list[self.current_index]
        self.image_tags[current_image_path] = set()

        for row in range(self.tag_table.rowCount()):
            tag = self.tag_table.item(row, 0).text()
            checkbox = self.tag_table.cellWidget(row, 2)
            if checkbox.isChecked():
                self.image_tags[current_image_path].add(tag)

        # Update the count for each tag
        for row in range(self.tag_table.rowCount()):
            tag = self.tag_table.item(row, 0).text()
            count = sum(1 for image_tags in self.image_tags.values() if tag in image_tags)
            self.tag_table.item(row, 1).setText(str(count))

    def next_image(self):
        if self.image_list:
            self.current_index += 1
            if self.current_index >= len(self.image_list):
                self.current_index = 0
            self.show_image()

    def prev_image(self):
        if self.image_list:
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.image_list) - 1
            self.show_image()

    def add_tag(self):
        tag = self.tag_line_edit.text().strip()
        if tag:
            # Check if tag already exists in the table
            for row in range(self.tag_table.rowCount()):
                if self.tag_table.item(row, 0).text() == tag:
                    return

            # If tag doesn't exist, add a new row with a checkbox
            row_position = self.tag_table.rowCount()
            self.tag_table.insertRow(row_position)

            # Create a checkbox for tagging
            tag_checkbox = QCheckBox()
            tag_checkbox.stateChanged.connect(self.update_image_tags)

            self.tag_table.setCellWidget(row_position, 2, tag_checkbox)
            self.tag_table.setItem(row_position, 0, QTableWidgetItem(tag))
            self.tag_table.setItem(row_position, 1, QTableWidgetItem("0"))

    def delete_tag(self):
        # Get the selected tag to delete
        selected_rows = self.tag_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No tag selected to delete!")
            return

        # Remove the tag from the table
        for index in selected_rows:
            tag_to_delete = self.tag_table.item(index.row(), 0).text()
            self.tag_table.removeRow(index.row())

            # Remove the tag from the image_tags dictionary for all images
            for tags in self.image_tags.values():
                tags.discard(tag_to_delete)

        # Update the count for each tag (you can call update_image_tags to do this if it has the counting logic)
        self.update_image_tags()

    def import_tags(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Tags - Choose CSV", "",
                                                   "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            with open(file_name, "r") as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Skip the header
                self.image_tags = {}
                for row in csv_reader:
                    image_path, tags = row
                    self.image_tags[image_path] = set(tags.split(','))
            # Update the checkboxes for the current image
            self.show_image()

    def export_tags(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Tags - Save CSV", "",
                                                   "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            with open(file_name, "w", newline='') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(["Image Path", "Tags"])
                for image_path, tags in self.image_tags.items():
                    csv_writer.writerow([image_path, ' '.join(tags)])

    def toggle_night_mode(self):
        if self.night_mode:
            self.setStyleSheet("")  # Reset to default style
            self.night_mode = False
        else:
            self.setStyleSheet(self.night_style)
            self.night_mode = True


# Running the app
if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    window = ImageTaggingApp()
    window.showMaximized()
    app.exec()
