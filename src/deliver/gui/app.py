
from .vendor.Qt5 import QtWidgets
from . import view


class Window(QtWidgets.QWidget):

    def __init__(self, ctrl, parent=None):
        super(Window, self).__init__(parent=parent)

        pages = {
            "pkgBook": view.PackageBookView(),
            "installer": view.InstallerView(),
        }

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(pages["pkgBook"])
        layout.addWidget(pages["installer"])

        # setup
        pages["pkgBook"].set_model(ctrl.models["pkgBook"])
        pages["installer"].set_model(ctrl.models["detail"],
                                     ctrl.models["targets"],
                                     ctrl.models["pathKeys"])

        # signals
        ctrl.models["pathKeys"].formatted.connect(self.on_target_formatted)
        pages["pkgBook"].selected.connect(ctrl.on_package_selected)
        pages["installer"].targeted.connect(ctrl.defer_load_target_keys)

        self._ctrl = ctrl
        self._pages = pages

    def on_target_formatted(self):
        kwargs = self._ctrl.models["pathKeys"].kwargs()
        path = self._ctrl.state["releaseTemplate"].format(**kwargs)
        self._pages["installer"].set_path(path)
