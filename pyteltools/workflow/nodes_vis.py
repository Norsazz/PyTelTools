from itertools import cycle, islice
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.tri as mtri
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PyQt5.QtWidgets import *

from pyteltools.conf import settings
from pyteltools.gui.util import LineMapCanvas, MapCanvas, MapViewer, PointAttributeTable, PolygonMapCanvas, \
    ProjectLinesPlotViewer, MultiFrameLinePlotViewer, MultiVarLinePlotViewer
from pyteltools.slf.interpolation import MeshInterpolator
from pyteltools.slf.mesh2D import Mesh2D
from pyteltools.slf.misc import detect_vector_couples

from .Node import DoubleInputNode, Node, SingleInputNode
from .util import build_levels_from_minmax, MultiFigureSaveDialog, MultiLoadSerafinDialog, \
    MultiSaveProjectLinesDialog, MultiSaveMultiFrameLinePlotDialog, MultiSaveMultiVarLinePlotDialog, \
    MultiSaveVerticalCrossSectionDialog, MultiSaveVerticalProfileDialog, \
    ScalarMapViewer, SimpleFluxPlotViewer, SimplePointPlotViewer, SimpleVolumePlotViewer, \
    VectorMapViewer, VerticalCrossSectionPlotViewer, VerticalProfilePlotViewer


class ShowMeshNode(SingleInputNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Show\nMesh'
        self.in_port.data_type = ('slf', 'slf 3d')
        self.state = Node.READY

        canvas = MapCanvas()
        self.map = MapViewer(canvas)
        self.has_map = False

    def reconfigure(self):
        super().reconfigure()
        self.has_map = False

    def configure(self, check=None):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if not self.has_map:
            mesh = Mesh2D(parent_node.data.header)
            self.map.canvas.initFigure(mesh)
            self.has_map = True
            self.map.canvas.draw()
        self.map.showMaximized()
        self.success()

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.has_map:
            mesh = Mesh2D(self.in_port.mother.parentItem().data.header)
            self.map.canvas.initFigure(mesh)

            self.has_map = True
            self.map.canvas.draw()
        self.map.showMaximized()
        self.success()


class VisualizeScalarValuesNode(SingleInputNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Visualize\nScalars'
        self.in_port.data_type = ('slf',)
        self.plot_viewer = ScalarMapViewer()
        self.state = Node.READY
        self.has_plot = False

    def configure(self, check=None):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!', QMessageBox.Ok)
            return
        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!', QMessageBox.Ok)
            return
        if not self.has_plot:
            self._prepare()
        self.plot_viewer.showMaximized()
        self.success()

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False

    def _prepare(self):
        input_data = self.in_port.mother.parentItem().data
        mesh = Mesh2D(input_data.header, False)
        self.plot_viewer.get_data(input_data, mesh)
        self.has_plot = True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.has_plot:
            self._prepare()
        self.plot_viewer.showMaximized()


class VisualizeVectorValuesNode(SingleInputNode):
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Visualize\nVectors'
        self.in_port.data_type = ('slf',)
        self.plot_viewer = VectorMapViewer()
        self.state = Node.READY
        self.has_plot = False

    def configure(self, check=None):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!', QMessageBox.Ok)
            return
        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!', QMessageBox.Ok)
            return
        if not self.has_plot:
            if not self._prepare():
                QMessageBox.critical(None, 'Error', 'No vector field available.', QMessageBox.Ok)
                return
        self.plot_viewer.showMaximized()
        self.success()

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False

    def _prepare(self):
        input_data = self.in_port.mother.parentItem().data
        _, _, _, couples = detect_vector_couples(input_data.header.var_IDs, input_data.header.var_IDs)
        if not couples:
            return False
        mesh = Mesh2D(input_data.header, False)
        self.plot_viewer.get_data(input_data, mesh, couples)
        self.has_plot = True
        return True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.has_plot:
            if not self._prepare():
                QMessageBox.critical(None, 'Error', 'No vector field available.', QMessageBox.Ok)
                self.fail('No vector field available.')
                return
        self.plot_viewer.showMaximized()


class LocateOpenLinesNode(DoubleInputNode):
    """!
    Locate open lines on a mesh from a top view
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Locate\nOpen\nLines'
        self.first_in_port.data_type = ('slf', 'slf 3d')
        self.second_in_port.data_type = ('polyline 2d',)
        self.state = Node.READY

        canvas = LineMapCanvas()
        self.map = MapViewer(canvas)
        self.has_map = False

    def reconfigure(self):
        super().reconfigure()
        self.has_map = False

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        line_node = self.second_in_port.mother.parentItem()
        if line_node.state != Node.SUCCESS:
            if line_node.ready_to_run():
                line_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if line_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if not self.has_map:
            self._prepare()
        self.map.showMaximized()
        self.success()

    def _prepare(self):
        mesh = Mesh2D(self.first_in_port.mother.parentItem().data.header)
        line_data = self.second_in_port.mother.parentItem().data
        self.map.canvas.reinitFigure(mesh, line_data.lines,
                                     ['Line %d' % (i+1) for i in range(len(line_data))],
                                     list(islice(cycle(['b', 'r', 'g', 'y', 'k', 'c', '#F28AD6', 'm']),
                                          len(line_data))))

        self.has_map = True
        self.map.canvas.draw()

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.has_map:
            self._prepare()
        self.map.showMaximized()
        self.success()


class LocatePolygonsNode(DoubleInputNode):
    """!
    Locate polygons (closed lines) on a mesh from a top view
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Locate\nPolygons'
        self.first_in_port.data_type = ('slf', 'slf 3d')
        self.second_in_port.data_type = ('polygon 2d',)
        self.state = Node.READY

        canvas = PolygonMapCanvas()
        self.map = MapViewer(canvas)
        self.has_map = False

    def reconfigure(self):
        super().reconfigure()
        self.has_map = False

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        line_node = self.second_in_port.mother.parentItem()
        if line_node.state != Node.SUCCESS:
            if line_node.ready_to_run():
                line_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if line_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if not self.has_map:
            self._prepare()
        self.map.showMaximized()
        self.success()

    def _prepare(self):
        mesh = Mesh2D(self.first_in_port.mother.parentItem().data.header)
        line_data = self.second_in_port.mother.parentItem().data
        self.map.canvas.reinitFigure(mesh, line_data.lines,
                                     ['Polygon %d' % (i+1) for i in range(len(line_data))])
        self.map.canvas.draw()
        self.has_map = True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.has_map:
            self._prepare()
        self.map.showMaximized()
        self.success()


class LocatePointsNode(DoubleInputNode):
    """!
    Locate points on a mesh from a top view
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Locate\nPoints'
        self.first_in_port.data_type = ('slf', 'slf 3d')
        self.second_in_port.data_type = ('point 2d',)
        self.state = Node.READY

        canvas = MapCanvas()
        self.map = MapViewer(canvas)
        self.has_map = False

    def reconfigure(self):
        super().reconfigure()
        self.has_map = False

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        point_node = self.second_in_port.mother.parentItem()
        if point_node.state != Node.SUCCESS:
            if point_node.ready_to_run():
                point_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if point_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if not self.has_map:
            self._prepare()
            self.map.showMaximized()
        self.success()

    def _prepare(self):
        mesh = Mesh2D(self.first_in_port.mother.parentItem().data.header)
        self.map.canvas.initFigure(mesh)
        points = self.second_in_port.mother.parentItem().data.points
        self.map.canvas.axes.scatter(*zip(*points))
        labels = ['%d' % (i+1) for i in range(len(points))]
        for label, (x, y) in zip(labels, points):
            self.map.canvas.axes.annotate(label, xy=(x, y), xytext=(-20, 20), fontsize=8,
                                          textcoords='offset points', ha='right', va='bottom',
                                          bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                                          arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        self.map.canvas.draw()
        self.has_map = True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.has_map:
            self._prepare()
        self.map.showMaximized()
        self.success()


class MultiVarLinePlotNode(DoubleInputNode):
    """!
    Plot multiple variables at a single frame on a longitudinal profile
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'MultiVar\nLine Plot'
        self.first_in_port.data_type = ('slf',)
        self.second_in_port.data_type = ('polyline 2d',)
        self.state = Node.READY
        self.has_plot = False

        self.plot_viewer = MultiVarLinePlotViewer()
        self.multi_save_act = QAction('Multi-Save', None, triggered=self.multi_save,
                                      icon=self.plot_viewer.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.plot_viewer.plotViewer.toolBar.addSeparator()
        self.plot_viewer.plotViewer.toolBar.addAction(self.multi_save_act)
        self.current_vars = {}

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!',
                                 QMessageBox.Ok)
            return
        line_node = self.second_in_port.mother.parentItem()
        if line_node.state != Node.SUCCESS:
            if line_node.ready_to_run():
                line_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if line_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not self.has_plot:
            success = self._prepare()
            if not success:
                QMessageBox.critical(None, 'Error', 'No line intersects the mesh continuously.',
                                     QMessageBox.Ok)
                return
        self.plot_viewer.showMaximized()

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False

    def _prepare(self):
        input_data = self.first_in_port.mother.parentItem().data
        mesh = MeshInterpolator(input_data.header, False)
        if input_data.triangles:
            mesh.index = input_data.index
            mesh.triangles = input_data.triangles
        else:
            self.progress_bar.setVisible(True)
            self.construct_mesh(mesh)
            input_data.index = mesh.index
            input_data.triangles = mesh.triangles

        lines = self.second_in_port.mother.parentItem().data.lines
        nb_nonempty, indices_nonempty, \
                     line_interpolators, line_interpolators_internal = mesh.get_line_interpolators(lines)
        if nb_nonempty == 0:
            return False
        self.success()
        self.plot_viewer.getInput(input_data, lines, line_interpolators, line_interpolators_internal)
        self.has_plot = True
        return True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.first_in_port.mother.parentItem().data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!',
                                 QMessageBox.Ok)
            return
        if not self.has_plot:
            success = self._prepare()
            if not success:
                QMessageBox.critical(None, 'Error', 'No line intersects the mesh continuously.',
                                     QMessageBox.Ok)
                self.fail('No line intersects the mesh continuously.')
                return
        self.plot_viewer.showMaximized()

    def plot(self, values, distances, values_internal, distances_internal, current_vars, png_name):
        fig, axes = plt.subplots(1)
        fig.set_size_inches(settings.FIG_SIZE[0], settings.FIG_SIZE[1])
        if self.plot_viewer.control.addInternal.isChecked():
            if self.plot_viewer.control.intersection.isChecked():
                for i, var in enumerate(current_vars):
                    axes.plot(distances, values[i], '-', linewidth=2, label=var,
                              color=self.plot_viewer.var_colors[var])
                    axes.plot(distances_internal, values_internal[i],
                              'o', color=self.plot_viewer.var_colors[var])
            else:
                for i, var in enumerate(current_vars):
                    axes.plot(distances_internal, values_internal[i], 'o-', linewidth=2, label=var,
                              color=self.plot_viewer.var_colors[var])

        else:
            if self.plot_viewer.control.intersection.isChecked():
                for i, var in enumerate(current_vars):
                    axes.plot(distances, values[i], '-', linewidth=2, label=var,
                              color=self.plot_viewer.var_colors[var])
            else:
                for i, var in enumerate(current_vars):
                    axes.plot(distances_internal, values_internal[i], '-', linewidth=2, label=var,
                              color=self.plot_viewer.var_colors[var])

        axes.legend()
        axes.grid(linestyle='dotted')
        axes.set_xlabel(self.plot_viewer.plotViewer.current_xlabel)
        axes.set_ylabel(self.plot_viewer.plotViewer.current_ylabel)
        axes.set_title(self.plot_viewer.plotViewer.current_title)
        fig.canvas.draw()
        fig.savefig(png_name, dpi=settings.FIG_OUT_DPI)

    def multi_save(self):
        current_vars = self.plot_viewer.getSelection()
        if not current_vars:
            return
        dlg = MultiLoadSerafinDialog([])
        if dlg.exec_() == QDialog.Accepted:
            input_options = (dlg.dir_paths, dlg.slf_name, dlg.job_ids)
        else:
            return
        dlg = MultiFigureSaveDialog('_multi_var_line_plot')
        if dlg.exec_() == QDialog.Accepted:
            output_options = dlg.panel.get_options()
        else:
            return

        line_id = int(self.plot_viewer.control.lineBox.currentText().split()[1]) - 1
        time_index = int(self.plot_viewer.control.timeSelection.index.text()) - 1
        compute_options = (self.second_in_port.mother.parentItem().data.lines,
                           line_id, time_index, current_vars, self.first_in_port.mother.parentItem().data.language)

        dlg = MultiSaveMultiVarLinePlotDialog(self, input_options, output_options, compute_options)
        dlg.run()
        dlg.exec_()


class MultiFrameLinePlotNode(DoubleInputNode):
    """!
    Plot a variable at multiple frames on a longitudinal profile
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'MultiFrame\nLine Plot'
        self.first_in_port.data_type = ('slf',)
        self.second_in_port.data_type = ('polyline 2d',)
        self.state = Node.READY
        self.has_plot = False

        self.plot_viewer = MultiFrameLinePlotViewer()
        self.multi_save_act = QAction('Multi-Save', None, triggered=self.multi_save,
                                      icon=self.plot_viewer.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.plot_viewer.plotViewer.toolBar.addSeparator()
        self.plot_viewer.plotViewer.toolBar.addAction(self.multi_save_act)
        self.current_vars = {}

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!',
                                 QMessageBox.Ok)
            return
        line_node = self.second_in_port.mother.parentItem()
        if line_node.state != Node.SUCCESS:
            if line_node.ready_to_run():
                line_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if line_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not self.has_plot:
            success = self._prepare()
            if not success:
                QMessageBox.critical(None, 'Error', 'No line intersects the mesh continuously.',
                                     QMessageBox.Ok)
                return
        self.plot_viewer.showMaximized()

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False

    def _prepare(self):
        input_data = self.first_in_port.mother.parentItem().data
        mesh = MeshInterpolator(input_data.header, False)
        if input_data.triangles:
            mesh.index = input_data.index
            mesh.triangles = input_data.triangles
        else:
            self.progress_bar.setVisible(True)
            self.construct_mesh(mesh)
            input_data.index = mesh.index
            input_data.triangles = mesh.triangles

        lines = self.second_in_port.mother.parentItem().data.lines
        nb_nonempty, indices_nonempty, \
                     line_interpolators, line_interpolators_internal = mesh.get_line_interpolators(lines)
        if nb_nonempty == 0:
            return False
        self.success()
        self.plot_viewer.getInput(input_data, lines, line_interpolators, line_interpolators_internal)
        self.has_plot = True
        return True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.first_in_port.mother.parentItem().data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!',
                                 QMessageBox.Ok)
            return
        if not self.has_plot:
            success = self._prepare()
            if not success:
                QMessageBox.critical(None, 'Error', 'No line intersects the mesh continuously.',
                                     QMessageBox.Ok)
                self.fail('No line intersects the mesh continuously.')
                return
        self.plot_viewer.showMaximized()

    def plot(self, values, distances, values_internal, distances_internal, time_indices, png_name):
        fig, axes = plt.subplots(1)
        fig.set_size_inches(settings.FIG_SIZE[0], settings.FIG_SIZE[1])
        if self.plot_viewer.control.addInternal.isChecked():
            if self.plot_viewer.control.intersection.isChecked():
                for i, index in enumerate(time_indices):
                    axes.plot(distances, values[i], '-', linewidth=2,
                              label='Frame %d' % (index+1), color=self.plot_viewer.frame_colors[index])
                    axes.plot(distances_internal, values_internal[i],
                              'o', color=self.plot_viewer.frame_colors[index])

            else:
                for i, index in enumerate(time_indices):
                    axes.plot(distances, values[i], 'o-', linewidth=2,
                              label='Frame %d' % (index+1), color=self.plot_viewer.frame_colors[index])

        else:
            if self.plot_viewer.control.intersection.isChecked():
                for i, index in enumerate(time_indices):
                    axes.plot(distances, values[i], '-', linewidth=2,
                              label='Frame %d' % (index+1), color=self.plot_viewer.frame_colors[index])
            else:
                for i, index in enumerate(time_indices):
                    axes.plot(distances_internal, values_internal[i], '-', linewidth=2,
                              label='Frame %d' % (index+1), color=self.plot_viewer.frame_colors[index])

        axes.legend()
        axes.grid(linestyle='dotted')
        axes.set_xlabel(self.plot_viewer.plotViewer.current_xlabel)
        axes.set_ylabel(self.plot_viewer.plotViewer.current_ylabel)
        axes.set_title(self.plot_viewer.plotViewer.current_title)
        fig.canvas.draw()
        fig.savefig(png_name, dpi=settings.FIG_OUT_DPI)

    def multi_save(self):
        time_indices = self.plot_viewer.getTime()
        if not time_indices:
            return
        dlg = MultiLoadSerafinDialog([])
        if dlg.exec_() == QDialog.Accepted:
            input_options = (dlg.dir_paths, dlg.slf_name, dlg.job_ids)
        else:
            return
        dlg = MultiFigureSaveDialog('_multi_frame_line_plot')
        if dlg.exec_() == QDialog.Accepted:
            output_options = dlg.panel.get_options()
        else:
            return

        line_id = int(self.plot_viewer.control.lineBox.currentText().split()[1]) - 1
        current_var = self.plot_viewer.control.varBox.currentText().split(' (')[0]
        compute_options = (self.second_in_port.mother.parentItem().data.lines,
                           line_id, current_var, time_indices, self.first_in_port.mother.parentItem().data.language)

        dlg = MultiSaveMultiFrameLinePlotDialog(self, input_options, output_options, compute_options)
        dlg.run()
        dlg.exec_()


class ProjectLinesPlotNode(DoubleInputNode):
    """!
    Plot values along lines projected on a reference line
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Project\nLines\nPlot'
        self.first_in_port.data_type = ('slf',)
        self.second_in_port.data_type = ('polyline 2d',)
        self.state = Node.READY
        self.has_plot = False

        self.plot_viewer = ProjectLinesPlotViewer()
        self.multi_save_act = QAction('Multi-Save', None, triggered=self.multi_save,
                                      icon=self.plot_viewer.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.plot_viewer.plotViewer.toolBar.addSeparator()
        self.plot_viewer.plotViewer.toolBar.addAction(self.multi_save_act)
        self.current_vars = {}

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!',
                                 QMessageBox.Ok)
            return
        line_node = self.second_in_port.mother.parentItem()
        if line_node.state != Node.SUCCESS:
            if line_node.ready_to_run():
                line_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if line_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not self.has_plot:
            success = self._prepare()
            if not success:
                QMessageBox.critical(None, 'Error', 'No line intersects the mesh continuously.',
                                     QMessageBox.Ok)
                return
        self.plot_viewer.showMaximized()

    def _prepare(self):
        input_data = self.first_in_port.mother.parentItem().data
        mesh = MeshInterpolator(input_data.header, False)
        if input_data.triangles:
            mesh.index = input_data.index
            mesh.triangles = input_data.triangles
        else:
            self.progress_bar.setVisible(True)
            self.construct_mesh(mesh)
            input_data.index = mesh.index
            input_data.triangles = mesh.triangles

        lines = self.second_in_port.mother.parentItem().data.lines
        nb_nonempty, indices_nonempty, \
                     line_interpolators, line_interpolators_internal = mesh.get_line_interpolators(lines)
        if nb_nonempty == 0:
            return False
        self.success()
        self.plot_viewer.getInput(input_data, lines, line_interpolators, line_interpolators_internal)
        self.has_plot = True
        return True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        if not self.first_in_port.mother.parentItem().data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 2D!',
                                 QMessageBox.Ok)
            return
        if not self.has_plot:
            success = self._prepare()
            if not success:
                QMessageBox.critical(None, 'Error', 'No line intersects the mesh continuously.',
                                     QMessageBox.Ok)
                self.fail('No line intersects the mesh continuously.')
                return
        self.plot_viewer.showMaximized()

    def plot(self, values, distances, values_internal, distances_internal, current_vars, png_name):
        fig, axes = plt.subplots(1)
        fig.set_size_inches(settings.FIG_SIZE[0], settings.FIG_SIZE[1])
        if self.plot_viewer.control.addInternal.isChecked():
            if self.plot_viewer.control.intersection.isChecked():
                for line_id, variables in current_vars.items():
                    for var in variables:
                        axes.plot(distances[line_id], values[line_id][var],
                                  linestyle=self.plot_viewer.current_linestyles[var],
                                  color=self.plot_viewer.line_colors[line_id], linewidth=2,
                                  label='%s$_%d$' % (var, line_id+1))

                        axes.plot(distances_internal[line_id], values_internal[line_id][var], 'o',
                                  color=self.plot_viewer.line_colors[line_id])
            else:
                for line_id, variables in current_vars.items():
                    for var in variables:
                        axes.plot(distances_internal[line_id], values_internal[line_id][var],
                                  marker='o', linestyle=self.plot_viewer.current_linestyles[var],
                                  color=self.plot_viewer.line_colors[line_id], linewidth=2,
                                  label='%s$_%d$' % (var, line_id+1))

        else:
            if self.plot_viewer.control.intersection.isChecked():
                for line_id, variables in current_vars.items():
                    for var in variables:
                        axes.plot(distances[line_id], values[line_id][var],
                                  linestyle=self.plot_viewer.current_linestyles[var],
                                  color=self.plot_viewer.line_colors[line_id], linewidth=2,
                                  label='%s$_%d$' % (var, line_id+1))
            else:
                for line_id, variables in current_vars.items():
                    for var in variables:
                        axes.plot(distances_internal[line_id], values_internal[line_id][var],
                                  linestyle=self.plot_viewer.current_linestyles[var],
                                  color=self.plot_viewer.line_colors[line_id], linewidth=2,
                                  label='%s$_%d$' % (var, line_id+1))

        axes.legend()
        axes.grid(linestyle='dotted')
        axes.set_xlabel(self.plot_viewer.plotViewer.current_xlabel)
        axes.set_ylabel(self.plot_viewer.plotViewer.current_ylabel)
        axes.set_title(self.plot_viewer.plotViewer.current_title)
        fig.canvas.draw()
        fig.savefig(png_name, dpi=settings.FIG_OUT_DPI)

    def multi_save(self):
        current_vars = self.plot_viewer.getSelection()
        if not current_vars:
            return
        dlg = MultiLoadSerafinDialog([])
        if dlg.exec_() == QDialog.Accepted:
            input_options = (dlg.dir_paths, dlg.slf_name, dlg.job_ids)
        else:
            return
        dlg = MultiFigureSaveDialog('_project_plot')
        if dlg.exec_() == QDialog.Accepted:
            output_options = dlg.panel.get_options()
        else:
            return

        ref_id = int(self.plot_viewer.control.lineBox.currentText().split()[1]) - 1
        reference = self.plot_viewer.lines[ref_id]
        max_distance = reference.length()
        time_index = int(self.plot_viewer.control.timeSelection.index.text()) - 1
        compute_options = (self.second_in_port.mother.parentItem().data.lines, ref_id, reference, max_distance,
                           time_index, current_vars, self.first_in_port.mother.parentItem().data.language)

        dlg = MultiSaveProjectLinesDialog(self, input_options, output_options, compute_options)
        dlg.run()
        dlg.exec_()


class VerticalCrossSectionNode(DoubleInputNode):
    """!
    Plot a 3D scalar in a vertical cross section
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Vertical\nCross\nSection'
        self.first_in_port.data_type = ('slf 3d',)
        self.second_in_port.data_type = ('polyline 2d',)
        self.plot_viewer = VerticalCrossSectionPlotViewer()
        self.state = Node.READY
        self.has_plot = False

        self.multi_save_act = QAction('Multi-Save', None, triggered=self.multi_save,
                                      icon=self.plot_viewer.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.plot_viewer.toolBar.addSeparator()
        self.plot_viewer.toolBar.addAction(self.multi_save_act)

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 3D!', QMessageBox.Ok)
            return
        if 'Z' not in parent_node.data.header.var_IDs:
            QMessageBox.critical(None, 'Error', 'The variable Z is not found.', QMessageBox.Ok)
            return
        line_node = self.second_in_port.mother.parentItem()
        if line_node.state != Node.SUCCESS:
            if line_node.ready_to_run():
                line_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if line_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not self.has_plot:
            if not self._prepare():
                QMessageBox.critical(None, 'Error', 'No line inside the mesh', QMessageBox.Ok)
                self.fail('no line inside the mesh')
                return
        self.plot_viewer.showMaximized()
        self.success()

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False

    def _prepare(self):
        input_data = self.first_in_port.mother.parentItem().data
        mesh = MeshInterpolator(input_data.header, False)
        if input_data.triangles:
            mesh.index = input_data.index
            mesh.triangles = input_data.triangles
        else:
            self.progress_bar.setVisible(True)
            self.construct_mesh(mesh)
            input_data.index = mesh.index
            input_data.triangles = mesh.triangles

        sections = self.second_in_port.mother.parentItem().data.lines

        line_interpolators, distances, line_interpolators_internal, distances_internal = \
            mesh.get_line_interpolators(sections)

        is_inside = [True if dist[0] else False for dist in distances_internal]
        nb_inside = sum(map(int, is_inside))
        section_indices = [i for i in range(len(sections)) if is_inside[i]]
        if nb_inside == 0:
            return False
        self.success()
        self.plot_viewer.get_data(input_data, sections, line_interpolators_internal, section_indices)
        return True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 3D!', QMessageBox.Ok)
            self.fail('The input file is not 3D.')
            return
        if 'Z' not in parent_node.data.header.var_IDs:
            QMessageBox.critical(None, 'Error', 'The variable Z is not found.', QMessageBox.Ok)
            self.fail('The variable Z is not found.')
            return
        if not self.has_plot:
            if not self._prepare():
                QMessageBox.critical(None, 'Error', 'No section inside the mesh', QMessageBox.Ok)
                self.fail('no section inside the mesh')
                return
        self.plot_viewer.showMaximized()

    def plot(self, triang, point_values, png_name):
        fig, axes = plt.subplots(1)
        fig.set_size_inches(settings.FIG_SIZE[0], settings.FIG_SIZE[1])

        if self.plot_viewer.color_limits is not None:
            levels = np.linspace(self.plot_viewer.color_limits[0], self.plot_viewer.color_limits[1],
                                 settings.NB_COLOR_LEVELS)
            axes.tricontourf(triang, point_values, cmap=self.plot_viewer.current_style, levels = levels,
                            vmin=self.plot_viewer.color_limits[0], vmax=self.plot_viewer.color_limits[1])
        else:
            levels = build_levels_from_minmax(np.nanmin(point_values), np.nanmax(point_values))
            axes.tricontourf(triang, point_values, cmap=self.plot_viewer.current_style, levels=levels)

        divider = make_axes_locatable(axes)
        cax = divider.append_axes('right', size='5%', pad=0.2)
        cax.set(self.plot_viewer.current_var)
        cmap = cm.ScalarMappable(cmap=self.plot_viewer.current_style)
        cmap.set_array(levels)
        fig.colorbar(cmap, cax=cax)

        axes.set_xlabel(self.plot_viewer.current_xlabel)
        axes.set_ylabel(self.plot_viewer.current_ylabel)
        axes.set_title(self.plot_viewer.current_title)

        fig.canvas.draw()
        fig.savefig(png_name, dpi=settings.FIG_OUT_DPI)

    def multi_save(self):
        dlg = MultiLoadSerafinDialog([])
        if dlg.exec_() == QDialog.Accepted:
            input_options = (dlg.dir_paths, dlg.slf_name, dlg.job_ids)
        else:
            return
        dlg = MultiFigureSaveDialog('_vertical_cross_section_plot')
        if dlg.exec_() == QDialog.Accepted:
            output_options = dlg.panel.get_options()
        else:
            return

        section_id = int(self.plot_viewer.current_section.split()[1]) - 1
        line = self.plot_viewer.sections[section_id]
        compute_options = (line, self.plot_viewer.current_var, self.first_in_port.mother.parentItem().data.language)
        dlg = MultiSaveVerticalCrossSectionDialog(self, input_options, output_options, compute_options)
        dlg.run()
        dlg.exec_()


class VerticalTemporalProfileNode(DoubleInputNode):
    """!
    Temporal plot of a scalar vertical profile
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Vertical\nTemporal\nProfile 3D'
        self.first_in_port.data_type = ('slf 3d',)
        self.second_in_port.data_type = ('point 2d',)
        self.plot_viewer = VerticalProfilePlotViewer()
        self.state = Node.READY
        self.has_plot = False

        self.multi_save_act = QAction('Multi-Save', None, triggered=self.multi_save,
                                      icon=self.plot_viewer.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.plot_viewer.toolBar.addSeparator()
        self.plot_viewer.toolBar.addAction(self.multi_save_act)

    def configure(self, check=None):
        if not self.first_in_port.has_mother() or not self.second_in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 3D!', QMessageBox.Ok)
            return
        if 'Z' not in parent_node.data.header.var_IDs:
            QMessageBox.critical(None, 'Error', 'The variable Z is not found.', QMessageBox.Ok)
            return
        point_node = self.second_in_port.mother.parentItem()
        if point_node.state != Node.SUCCESS:
            if point_node.ready_to_run():
                point_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if point_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
        if not self.has_plot:
            if not self._prepare():
                QMessageBox.critical(None, 'Error', 'No point inside the mesh', QMessageBox.Ok)
                self.fail('no point inside the mesh')
                return
        self.plot_viewer.showMaximized()
        self.success()

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False

    def _prepare(self):
        input_data = self.first_in_port.mother.parentItem().data
        mesh = MeshInterpolator(input_data.header, False)
        if input_data.triangles:
            mesh.index = input_data.index
            mesh.triangles = input_data.triangles
        else:
            self.progress_bar.setVisible(True)
            self.construct_mesh(mesh)
            input_data.index = mesh.index
            input_data.triangles = mesh.triangles

        points = self.second_in_port.mother.parentItem().data.points
        is_inside, point_interpolators = mesh.get_point_interpolators(points)

        nb_inside = sum(map(int, is_inside))
        point_indices = [i for i in range(len(points)) if is_inside[i]]
        if nb_inside == 0:
            return False
        self.success()
        self.plot_viewer.get_data(input_data, points, point_interpolators, point_indices)
        return True

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        parent_node = self.first_in_port.mother.parentItem()
        if parent_node.data.header.is_2d:
            QMessageBox.critical(None, 'Error', 'The input file is not 3D!', QMessageBox.Ok)
            self.fail('The input file is not 3D.')
            return
        if 'Z' not in parent_node.data.header.var_IDs:
            QMessageBox.critical(None, 'Error', 'The variable Z is not found.', QMessageBox.Ok)
            self.fail('The variable Z is not found.')
            return
        if not self.has_plot:
            if not self._prepare():
                QMessageBox.critical(None, 'Error', 'No point inside the mesh', QMessageBox.Ok)
                self.fail('no point inside the mesh')
                return
        self.plot_viewer.showMaximized()

    def plot(self, time, y, z, triangles, str_datetime, str_datetime_bis, png_name):
        fig, axes = plt.subplots(1)
        fig.set_size_inches(settings.FIG_SIZE[0], settings.FIG_SIZE[1])

        triang = mtri.Triangulation(time[self.timeFormat], y, triangles)
        if self.plot_viewer.color_limits is not None:
            levels = np.linspace(self.plot_viewer.color_limits[0], self.plot_viewer.color_limits[1],
                                 settings.NB_COLOR_LEVELS)
            axes.tricontourf(triang, z, cmap=self.plot_viewer.current_style, levels = levels,
                             vmin=self.plot_viewer.color_limits[0], vmax=self.plot_viewer.color_limits[1])
        else:
            levels = build_levels_from_minmax(np.nanmin(z), np.nanmax(z))
            axes.tricontourf(triang, z, cmap=self.plot_viewer.current_style, levels=levels)

        divider = make_axes_locatable(axes)
        cax = divider.append_axes('right', size='5%', pad=0.2)
        cmap = cm.ScalarMappable(cmap=self.plot_viewer.current_style)
        cmap.set_array(levels)
        fig.colorbar(cmap, cax=cax)

        axes.set_xlabel(self.plot_viewer.current_xlabel)
        axes.set_ylabel(self.plot_viewer.current_ylabel)
        axes.set_title(self.plot_viewer.current_title)
        if self.plot_viewer.timeFormat in [1, 2]:
            axes.set_xticklabels(str_datetime if self.plot_viewer.timeFormat == 1
                                 else str_datetime_bis)
            for label in axes.get_xticklabels():
                label.set_rotation(45)
                label.set_fontsize(8)
        fig.canvas.draw()
        fig.savefig(png_name, dpi=settings.FIG_OUT_DPI)

    def multi_save(self):
        dlg = MultiLoadSerafinDialog([])
        if dlg.exec_() == QDialog.Accepted:
            input_options = (dlg.dir_paths, dlg.slf_name, dlg.job_ids)
        else:
            return
        dlg = MultiFigureSaveDialog('_vertical_profile_plot')
        if dlg.exec_() == QDialog.Accepted:
            output_options = dlg.panel.get_options()
        else:
            return

        point_id = int(self.plot_viewer.current_columns[0].split()[1]) - 1
        point = self.plot_viewer.points[point_id]
        compute_options = (point, self.plot_viewer.current_var, self.first_in_port.mother.parentItem().data.language)
        dlg = MultiSaveVerticalProfileDialog(self, input_options, output_options, compute_options)
        dlg.run()
        dlg.exec_()


class VolumePlotNode(SingleInputNode):
    """!
    Temporal plot of volumes within polygons
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Volume\nPlot'
        self.in_port.data_type = ('volume csv',)
        self.state = Node.READY
        self.plot_viewer = SimpleVolumePlotViewer()
        self.has_plot = False

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False
        self.plot_viewer.reset()
        self.plot_viewer.current_columns = ('Polygon 1',)

    def configure(self, check=None):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if self.has_plot:
            self.plot_viewer.show()
        else:
            self.plot_viewer.get_data(parent_node.data)
            self.has_plot = True
            self.plot_viewer.show()
            self.success()

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        parent_node = self.in_port.mother.parentItem()
        if not self.has_plot:
            self.plot_viewer.get_data(parent_node.data)
            self.has_plot = True
        self.success()


class FluxPlotNode(SingleInputNode):
    """!
    Temporal plot of fluxes through open lines
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Flux\nPlot'
        self.in_port.data_type = ('flux csv',)
        self.state = Node.READY
        self.plot_viewer = SimpleFluxPlotViewer()
        self.has_plot = False

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False
        self.plot_viewer.reset()
        self.plot_viewer.current_columns = ('Section 1',)

    def configure(self, check=None):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if self.has_plot:
            self.plot_viewer.show()
        else:
            self.plot_viewer.get_data(parent_node.data)
            self.has_plot = True
            self.plot_viewer.show()
            self.success()

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        parent_node = self.in_port.mother.parentItem()
        if not self.has_plot:
            self.plot_viewer.get_data(parent_node.data)
            self.has_plot = True
        self.success()


class PointPlotNode(SingleInputNode):
    """!
    Temporal plot of a variable at points
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Point\nPlot'
        self.in_port.data_type = ('point csv',)
        self.state = Node.READY
        self.plot_viewer = SimplePointPlotViewer()
        self.has_plot = False

    def reconfigure(self):
        super().reconfigure()
        self.has_plot = False
        self.plot_viewer.reset()
        self.plot_viewer.current_columns = ('Point 1',)

    def configure(self, check=None):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if self.has_plot:
            self.plot_viewer.show()
        else:
            self.plot_viewer.get_data(parent_node.data)
            self.has_plot = True
            self.plot_viewer.show()
            self.success()

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        parent_node = self.in_port.mother.parentItem()
        if not self.has_plot:
            self.plot_viewer.get_data(parent_node.data)
            self.has_plot = True
        self.success()


class PointAttributeTableNode(SingleInputNode):
    """!
    Display attributes table of a points set
    """
    def __init__(self, index):
        super().__init__(index)
        self.category = 'Visualization'
        self.label = 'Point\nAttribute\nTable'
        self.in_port.data_type = ('point 2d',)
        self.state = Node.READY
        self.table = PointAttributeTable()
        self.has_table = False

    def reconfigure(self):
        super().reconfigure()
        self.has_table = False

    def configure(self, check=None):
        if not self.in_port.has_mother():
            QMessageBox.critical(None, 'Error', 'Connect and run the input before configure this node!',
                                 QMessageBox.Ok)
            return

        parent_node = self.in_port.mother.parentItem()
        if parent_node.state != Node.SUCCESS:
            if parent_node.ready_to_run():
                parent_node.run()
            else:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return
            if parent_node.state != Node.SUCCESS:
                QMessageBox.critical(None, 'Error', 'Configure and run the input before configure this node!',
                                     QMessageBox.Ok)
                return

        if self.has_table:
            self.table.show()
        else:
            self.table.getData(parent_node.data.points, [], parent_node.data.fields_name,
                               parent_node.data.attributes_decoded)
            self.has_table = True
            self.table.show()
            self.success()

    def run(self):
        success = super().run_upward()
        if not success:
            self.fail('input failed.')
            return
        parent_node = self.in_port.mother.parentItem()
        if not self.has_table:
            self.table.get_data(parent_node.data.points, [], parent_node.data.fields_name,
                               parent_node.data.attributes_decoded)
            self.has_table = True
        self.success()


