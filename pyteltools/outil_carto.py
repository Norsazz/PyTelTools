import sys
import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))
import uuid
import shutil
import subprocess

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from pyteltools.conf import settings


class LandXMLtoTinDialog(QDialog):
    def __init__(self, dir_names, dir_paths, xml_name, overwrite):
        super().__init__()
        self.dir_names = dir_names
        self.dir_paths = dir_paths
        self.xml_name = xml_name
        self.overwrite = overwrite

        self.table = QTableWidget()
        self.table.setRowCount(len(dir_names))
        self.table.setColumnCount(2)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setDefaultSectionSize(100)
        self.table.setHorizontalHeaderLabels(['dossier', 'tin'])

        yellow = QColor(245, 255, 207, 255)
        for i, name in enumerate(self.dir_names):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(''))
            self.table.item(i, 1).setBackground(yellow)

        self.btnClose = QPushButton('Fermer', None)
        self.btnClose.setEnabled(False)
        self.btnClose.setFixedSize(120, 30)
        self.btnClose.clicked.connect(self.accept)

        vlayout = QVBoxLayout()
        vlayout.setSpacing(10)
        vlayout.addWidget(QLabel("(Les fichiers tin seront sauvegardés dans le dossier gis avec le même nom que LandXML)\n"
                                 "Patientez jusqu'à ce que toutes les cases jaunes deviennet vertes..."))
        vlayout.addWidget(self.table)
        vlayout.addStretch()
        vlayout.addWidget(self.btnClose, Qt.AlignRight)
        self.setLayout(vlayout)
        self.resize(500, 300)
        self.setWindowTitle('Convertir les fichiers LandXML en tin')
        self.show()
        QApplication.processEvents()
        self._run()
        self.btnClose.setEnabled(True)

    def _run(self):
        fail_messages = []
        nb_success, nb_reload = 0, 0

        green = QColor(180, 250, 165, 255)
        red = QColor(255, 160, 160, 255)

        python_path = settings.PY_ARCGIS
        if not os.path.exists(python_path):
            QMessageBox.critical(self, 'Erreur', "ArcGIS n'est pas disponible!"
                "Chemin introuvable : %s" % python_path,
                QMessageBox.Ok)
            return

        script_name = os.path.abspath(os.path.join('slf', 'data', 'landxml_to_tin.py'))

        for i, (dir_name, dir_path) in enumerate(zip(self.dir_names, self.dir_paths)):
            xml_name = os.path.join(dir_path, 'gis', self.xml_name)
            tin_name = os.path.join(dir_path, 'gis', self.xml_name[:-4]).lower()

            if os.path.exists(tin_name):
                if self.overwrite:
                    try:
                        os.remove(tin_name)
                    except PermissionError:
                        pass
                else:
                    nb_success += 1
                    nb_reload += 1
                    self.table.item(i, 1).setBackground(green)
                    QApplication.processEvents()
                    continue

            out = subprocess.Popen([python_path, script_name, xml_name, os.path.join(dir_path, 'gis'),
                                    self.xml_name[:-4]], stdout=subprocess.PIPE)
            result, returncode = out.communicate()[0], out.returncode
            if returncode == 1:
                self.table.item(i, 1).setBackground(red)
                QApplication.processEvents()
                fail_messages.append("%s : arcpy n'est pas disponible." % dir_name)
                continue
            elif returncode == 2:
                self.table.item(i, 1).setBackground(red)
                QApplication.processEvents()
                fail_messages.append("%s : L'extension ArcGIS 3D Analyst n'est pas disponible." % dir_name)
                continue
            elif returncode == 3:
                self.table.item(i, 1).setBackground(red)
                QApplication.processEvents()
                fail_messages.append('%s : LandXML_to_tin a échoué.' % dir_name)
                continue
            nb_success += 1
            self.table.item(i, 1).setBackground(green)
            QApplication.processEvents()

        if nb_success == len(self.dir_paths):
            message = 'Tous les fichiers tin ont été générés avec succès !'
            if nb_reload > 1:
                message += '\n(dont %d fichiers existants)' % nb_reload
            elif nb_reload == 1:
                message += '\n(dont un fichier existant)'
            QMessageBox.information(self, 'Succès', message, QMessageBox.Ok)
        else:
            message = "Les fichiers tin n'ont pas tous été générés :\n" + '\n'.join(fail_messages)
            QMessageBox.warning(self, 'Echec', message, QMessageBox.Ok)


class PngDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.openButton = QPushButton('Parcourir')
        self.openButton.setEnabled(False)
        self.openButton.setFixedWidth(100)
        self.openButton.clicked.connect(self._open)
        self.pathBox = QLineEdit()
        self.pathBox.setReadOnly(True)

        self.pngBox = QGroupBox('Choisir où sauvegarder les .PNG')
        self.separateButton = QRadioButton('Séparément : dans les dossiers source\n'
                                           '(les images porteront le nom du fichier .mxd)')
        self.separateButton.setChecked(True)
        self.togetherButton = QRadioButton('Ensemble : dans un même dossier\n'
                                           '(les images porteront le nom du dossier source et le nom du fichier .mxd)')
        self.togetherButton.toggled.connect(lambda checked: self.openButton.setEnabled(checked))
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.separateButton)
        vlayout.addWidget(self.togetherButton)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.openButton)
        hlayout.addWidget(self.pathBox)
        vlayout.addLayout(hlayout)
        self.pngBox.setLayout(vlayout)

        overwrite_box = QGroupBox("Re-générer si l'image existe déjà")
        self.overwrite_button = QRadioButton('Oui')
        self.no_button = QRadioButton('Non')
        self.no_button.setChecked(True)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.overwrite_button)
        hlayout.addWidget(self.no_button)
        overwrite_box.setLayout(hlayout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                   Qt.Horizontal, self)
        buttons.accepted.connect(self.check)
        buttons.rejected.connect(self.reject)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.pngBox)
        vlayout.addItem(QSpacerItem(10, 15))
        vlayout.addWidget(overwrite_box)
        vlayout.addStretch()
        vlayout.addWidget(buttons)
        self.setLayout(vlayout)
        self.resize(400, 300)
        self.setWindowTitle('Sauvegarder les .PNG')
        self.show()

    def check(self):
        if self.togetherButton.isChecked():
            if not self.pathBox.text():
                QMessageBox.critical(self, 'Erreur', 'Choisir un dossier.',
                                     QMessageBox.Ok)
                return
        self.accept()

    def _open(self):
        path = QFileDialog.getExistingDirectory(None, 'Choisir un dossier', '',
                                                options=QFileDialog.Options() | QFileDialog.ShowDirsOnly |
                                                        QFileDialog.DontUseNativeDialog)
        if not path:
            return
        self.pathBox.setText(path)


class MxdToPngDialog(QDialog):
    def __init__(self, dir_names, dir_paths, mxd_name, mxd_path, png_together, png_path, overwrite):
        super().__init__()

        self.dir_names = dir_names
        self.dir_paths = dir_paths
        self.mxd_name = mxd_name
        self.mxd_path = mxd_path
        self.png_together = png_together
        self.png_path = png_path
        self.overwrite = overwrite

        self.table = QTableWidget()
        self.table.setRowCount(len(dir_names))
        self.table.setColumnCount(2)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setDefaultSectionSize(100)
        self.table.setHorizontalHeaderLabels(['dossier', 'png'])

        yellow = QColor(245, 255, 207, 255)

        for i, name in enumerate(dir_names):
            self.table.setItem(i, 0, QTableWidgetItem(name))

            self.table.setItem(i, 1, QTableWidgetItem(''))
            self.table.item(i, 1).setBackground(yellow)

        self.btnClose = QPushButton('Fermer', None)
        self.btnClose.setEnabled(False)
        self.btnClose.setFixedSize(120, 30)
        self.btnClose.clicked.connect(self.accept)

        vlayout = QVBoxLayout()
        vlayout.addWidget(QLabel("Patientez jusqu'à ce que toutes les cases jaunes deviennet vertes..."))
        vlayout.addWidget(self.table)
        vlayout.addStretch()
        vlayout.addWidget(self.btnClose, Qt.AlignRight)
        self.setLayout(vlayout)
        self.resize(500, 300)
        self.setWindowTitle('Produire les cartes sous format PNG')
        self.show()
        QApplication.processEvents()

        self.success = self._run()
        self.btnClose.setEnabled(True)

    def _png_path(self, dir_name, dir_path):
        if self.png_together:
            return self.png_path, '%s_%s.png' % (dir_name, self.mxd_name)
        return os.path.join(dir_path, 'gis'), '%s.png' % self.mxd_name

    def _run(self):
        fail_messages = []
        nb_success, nb_reload = 0, 0

        green = QColor(180, 250, 165, 255)
        red = QColor(255, 160, 160, 255)

        python_path = 'C:\\Python27\\ArcGIS10.1\\python.exe'
        if not os.path.exists(python_path):
            QMessageBox.critical(self, 'Erreur', "ArcGIS10.1 n'est pas disponible!",
                                 QMessageBox.Ok)
            return False

        script_name = os.path.abspath(os.path.join('slf', 'data', 'mxd_to_png.py'))
        tmp_id = str(uuid.uuid4())

        for i, (dir_name, dir_path) in enumerate(zip(self.dir_names, self.dir_paths)):
            png_folder, png_name = self._png_path(dir_name, dir_path)

            if os.path.exists(os.path.join(png_folder, png_name)):
                if not self.overwrite:
                    nb_reload += 1
                    nb_success += 1
                    self.table.item(i, 1).setBackground(green)
                    QApplication.processEvents()
                    continue
                else:
                    try:
                        os.remove(os.path.join(png_folder, png_name))
                    except PermissionError:
                        pass

            # copy .mxd to sig folder
            tmp_mxd = os.path.join(dir_path, 'gis', tmp_id + '.mxd')
            shutil.copyfile(self.mxd_path, tmp_mxd)

            # mxd to png
            out = subprocess.Popen([python_path, script_name, tmp_mxd, png_name],
                                   stdout=subprocess.PIPE)
            result, returncode = out.communicate()[0], out.returncode

            # move .png to the specified folder
            if self.png_together:
                old_path = os.path.join(dir_path, 'gis', png_name)
                shutil.move(old_path, png_folder)

            # remove .mxd
            try:
                os.remove(tmp_mxd)
            except PermissionError:
                continue

            if returncode == 1:
                fail_messages.append("%s : arcpy.mapping n'est pas disponible." % dir_name)
                self.table.item(i, 1).setBackground(red)
                QApplication.processEvents()
                continue
            elif returncode == 2:
                fail_messages.append('%s : Lecture de .mxd a échoué.' % dir_name)
                self.table.item(i, 1).setBackground(red)
                QApplication.processEvents()
                continue
            elif returncode == 3:
                fail_messages.append('%s : ExportToPNG a échoué.' % dir_name)
                self.table.item(i, 1).setBackground(red)
                QApplication.processEvents()
                continue

            nb_success += 1
            self.table.item(i, 1).setBackground(green)
            QApplication.processEvents()

        if nb_success == len(self.dir_paths):
            message = 'Tous les fichiers .PNG ont été générés avec succès !'
            if nb_reload > 1:
                message += '\n(dont %d fichiers existants)' % nb_reload
            elif nb_reload == 1:
                message += '\n(dont un fichier existant)'
            QMessageBox.information(self, 'Succès', message, QMessageBox.Ok)
        else:
            message = "Les fichiers tin n'ont pas tous été générés :\n" + '\n'.join(fail_messages)
            QMessageBox.warning(self, 'Echec', message, QMessageBox.Ok)
        return True


class LandXMLtoTin(QWidget):
    def __init__(self):
        super().__init__()
        self.dir_names = []
        self.dir_paths = []

        self._initWidgets()
        self._setLayout()
        self._bindEvents()
        self.setWindowTitle('Convertir LandXML en tin')

    def _initWidgets(self):
        # create the open button
        self.btnOpen = QPushButton('Ouvrir', self, icon=self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.btnOpen.setToolTip('<b>Ouvrir</b> des fichiers .xml')
        self.btnOpen.setFixedSize(105, 50)

        # create a checkbox for overwrite option
        self.overwriteBox = QCheckBox("Re-générer si le fichier tin existe déjà (risque d'échec)")
        self.overwriteBox.setChecked(False)

        # create a combo box for input file name
        self.fileBox = QComboBox()
        self.fileBox.setFixedSize(200, 30)

        # create the next button
        self.btnRun = QPushButton('Convertir', self, icon=self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.btnRun.setFixedSize(105, 50)
        self.btnRun.setEnabled(False)

    def _setLayout(self):
        mainLayout = QVBoxLayout()
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.setSpacing(15)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btnOpen)
        hlayout.addWidget(self.btnRun)
        mainLayout.addLayout(hlayout)
        mainLayout.setSpacing(10)
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.addWidget(QLabel('<p style="font-size:10pt">'
                                    'Choisir un ou plusieurs dossiers contenant un sous-dossier nommé gis.<br>'
                                    'Chaque dossier gis doit contenir un fichier .xml avec le même nom.<br>'))
        mainLayout.addWidget(self.overwriteBox)
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel('   Choisir les fichiers .xml  '))
        hlayout.addWidget(self.fileBox, Qt.AlignLeft)
        hlayout.addStretch()
        mainLayout.addLayout(hlayout)
        mainLayout.addStretch()
        self.setLayout(mainLayout)

    def _bindEvents(self):
        self.btnOpen.clicked.connect(self.btnOpenEvent)
        self.btnRun.clicked.connect(self.run)

    def btnOpenEvent(self):
        self.btnRun.setEnabled(False)
        w = QFileDialog()
        w.setWindowTitle('Choisir un ou plusieurs dossiers contenant un sous-dossier gis')
        w.setFileMode(QFileDialog.DirectoryOnly)
        w.setOption(QFileDialog.DontUseNativeDialog, True)
        tree = w.findChild(QTreeView)
        if tree:
            tree.setSelectionMode(QAbstractItemView.MultiSelection)
            tree.setSelectionBehavior(QAbstractItemView.SelectRows)

        if w.exec_() != QDialog.Accepted:
            return
        current_dir = w.directory().path()
        self.dir_names = []
        self.dir_paths = []
        for index in tree.selectionModel().selectedRows():
            name = tree.model().data(index)
            self.dir_names.append(name)
            self.dir_paths.append(os.path.join(current_dir, name))
        for name, path in zip(self.dir_names, self.dir_paths):
            if not os.path.exists(os.path.join(path, 'gis')):
                QMessageBox.critical(self, 'Erreur', 'Pas de sous-dossier gis dans le dossier %s !' % name,
                                     QMessageBox.Ok)
                return
        all_slfs = set()
        for name, path in zip(self.dir_names, self.dir_paths):
            slfs = set()
            for f in os.listdir(os.path.join(path, 'gis')):
                if os.path.isfile(os.path.join(path, 'gis', f)) and f[-4:] == '.xml':
                    slfs.add(f)
            if not slfs:
                QMessageBox.critical(self, 'Erreur', "Le dossier '%s/gis' ne contient pas de fichier .xml !" % name,
                                     QMessageBox.Ok)
                return
            if not all_slfs:
                all_slfs = slfs.copy()
            else:
                all_slfs.intersection_update(slfs)
            if not all_slfs:
                QMessageBox.critical(self, 'Erreur', 'Pas de fichier .xml avec un nom identique !',
                                     QMessageBox.Ok)
                return

        self.fileBox.clear()
        for slf in all_slfs:
            self.fileBox.addItem(slf)
        self.btnRun.setEnabled(True)

    def run(self):
        dlg = LandXMLtoTinDialog(self.dir_names, self.dir_paths, self.fileBox.currentText(),
                                 self.overwriteBox.isChecked())
        dlg.exec_()


class MxdToPng(QWidget):
    def __init__(self):
        super().__init__()
        self.dir_names = []
        self.dir_paths = []

        self._initWidgets()
        self._setLayout()
        self.btnOpen.clicked.connect(self.btnOpenEvent)
        self.btnRun.clicked.connect(self.carto)
        self.setWindowTitle('Convertir .mxd en images')

    def _initWidgets(self):
        # create the open button
        self.btnOpen = QPushButton('Ouvrir', self, icon=self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.btnOpen.setToolTip('<b>Ouvrir</b> des fichiers .xml')
        self.btnOpen.setFixedSize(105, 50)

        # create a combo box for mxd file name
        self.mxdBox = QComboBox()
        self.mxdBox.setFixedSize(200, 30)

        # create the next button
        self.btnRun = QPushButton('Carto', self, icon=self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.btnRun.setFixedSize(105, 50)
        self.btnRun.setEnabled(False)

    def _setLayout(self):
        mainLayout = QVBoxLayout()
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.setSpacing(15)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btnOpen)
        hlayout.addWidget(self.btnRun)
        mainLayout.addLayout(hlayout)
        mainLayout.setSpacing(10)
        mainLayout.addItem(QSpacerItem(10, 10))
        mainLayout.addWidget(QLabel('<p style="font-size:10pt">'
                                    'Choisir un ou plusieurs dossiers contenant un sous-dossier nommé gis.<br>'
                                    'Au moins un dossier gis doit contenir un fichier .mxd<br>'))
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel('   Choisir le fichier .mxd  '))
        hlayout.addWidget(self.mxdBox, Qt.AlignLeft)
        hlayout.addStretch()
        mainLayout.addLayout(hlayout)
        mainLayout.addStretch()
        self.setLayout(mainLayout)

    def btnOpenEvent(self):
        self.btnRun.setEnabled(False)
        w = QFileDialog()
        w.setWindowTitle('Choisir un ou plusieurs dossiers')
        w.setFileMode(QFileDialog.DirectoryOnly)
        w.setOption(QFileDialog.DontUseNativeDialog, True)
        tree = w.findChild(QTreeView)
        if tree:
            tree.setSelectionMode(QAbstractItemView.MultiSelection)
            tree.setSelectionBehavior(QAbstractItemView.SelectRows)

        if w.exec_() != QDialog.Accepted:
            return
        current_dir = w.directory().path()
        self.dir_names = []
        self.dir_paths = []
        for index in tree.selectionModel().selectedRows():
            name = tree.model().data(index)
            self.dir_names.append(name)
            self.dir_paths.append(os.path.join(current_dir, name))
            if not os.path.exists(os.path.join(current_dir, name, 'gis')):
                QMessageBox.critical(self, 'Erreur', "Le dossier %s n'a pas de sous-dossier gis!" % name,
                                     QMessageBox.Ok)
                return
        mxds = {}
        found = False
        for name, path in zip(self.dir_names, self.dir_paths):
            mxds[name] = []
            sig_path = os.path.join(path, 'gis')
            for f in os.listdir(sig_path):
                if os.path.isfile(os.path.join(sig_path, f)) and f[-4:] == '.mxd':
                    found = True
                    mxds[name].append((f, sig_path))
        if not found:
            QMessageBox.critical(self, 'Erreur', 'Les dossiers gis/ ne contiennent aucun .mxd !',
                                 QMessageBox.Ok)
            return
        for name in mxds:
            for mxd, path in mxds[name]:
                item = '%s/gis/%s' % (name, mxd)
                self.mxdBox.addItem(item)
        self.btnRun.setEnabled(True)

    def carto(self):
        dir_name, mxd_name = self.mxdBox.currentText().split('/gis/')
        dir_path = self.dir_paths[self.dir_names.index(dir_name)]
        mxd_path = os.path.join(dir_path, 'gis', mxd_name)

        dlg = PngDialog()
        if dlg.exec_() == QDialog.Rejected:
            return
        together, png_path = False, ''
        if dlg.togetherButton.isChecked():
            together = True
            png_path = dlg.pathBox.text()
        overwrite = dlg.overwrite_button.isChecked()

        final_dialog = MxdToPngDialog(self.dir_names, self.dir_paths,
                                      mxd_name, mxd_path, together, png_path, overwrite)
        final_dialog.exec_()


class WelcomeToCarto(QWidget):
    def __init__(self):
        super().__init__()
        left_button = QPushButton("Convertir LandXML en tin\n\nJ'ai des dossiers contenant des fichiers .xml\n"
                                  "J'aimerais les convertir en tin")
        right_button = QPushButton("Convertir .mxd en images\n\nJ'ai déjà toutes les couches .shp et tin\n"
                                   "J'aimerais faire des cartes avec différents .mxd")
        for bt in [left_button, right_button]:
            bt.setFixedSize(300, 150)

        vlayout = QVBoxLayout()
        vlayout.addWidget(left_button)
        vlayout.addWidget(right_button)
        self.setLayout(vlayout)
        self.setWindowTitle("Bienvenue dans l'outil Carto !")

        self.first_page = LandXMLtoTin()
        self.second_page = MxdToPng()

        left_button.clicked.connect(lambda: self.first_page.show())
        right_button.clicked.connect(lambda: self.second_page.show())


def exception_hook(exctype, value, traceback):
    """!
    @brief Needed for suppressing traceback silencing in newer version of PyQt5
    """
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


if __name__ == '__main__':
    # suppress explicitly traceback silencing
    sys._excepthook = sys.excepthook
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    welcome = WelcomeToCarto()
    welcome.show()
    app.exec_()


