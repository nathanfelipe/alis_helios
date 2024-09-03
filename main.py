import sys
from PyQt6.QtWidgets import QApplication, QDialog
from gui import MainWindow, WelcomeDialog, MissionSelectionDialog


def main():
    app = QApplication(sys.argv)

    # Show the welcome dialog
    welcome_dialog = WelcomeDialog()
    welcome_dialog.exec()

    # Show the mission selection dialog
    mission_selection_dialog = MissionSelectionDialog()
    if mission_selection_dialog.exec() == QDialog.DialogCode.Accepted:
        selected_mission = mission_selection_dialog.mission_dropdown.currentText()

        # Initialize the main window with the selected mission
        window = MainWindow(selected_mission)
        window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
