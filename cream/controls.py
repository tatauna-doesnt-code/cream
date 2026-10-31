"""Small shared controls with predictable Qt5/Qt6 geometry."""
from .qt import QtCore, QtGui, QtWidgets as W


class InstantInfo(W.QLabel):
    def enterEvent(self, event):
        W.QToolTip.showText(self.mapToGlobal(QtCore.QPoint(self.width() + 4, self.height())), self.toolTip(), self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        W.QToolTip.hideText()
        super().leaveEvent(event)


def set_chevron(button, expanded=False):
    pixmap = QtGui.QPixmap(8, 8)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(QtGui.QColor('#cccccc'))
    points = [(1, 2), (7, 2), (4, 6)] if expanded else [(2, 1), (6, 4), (2, 7)]
    painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y) for x, y in points]))
    painter.end()
    button.setArrowType(QtCore.Qt.NoArrow)
    button.setIcon(QtGui.QIcon(pixmap))
    button.setIconSize(QtCore.QSize(8, 8))


class CenteredCheckDelegate(W.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter

    def indicator_rect(self, option):
        size = option.widget.style().pixelMetric(W.QStyle.PM_IndicatorWidth)
        return QtCore.QRect(option.rect.center().x() - size // 2,
                            option.rect.center().y() - size // 2, size, size)

    def paint(self, painter, option, index):
        view = W.QStyleOptionViewItem(option)
        self.initStyleOption(view, index)
        view.features &= ~W.QStyleOptionViewItem.HasCheckIndicator
        option.widget.style().drawControl(W.QStyle.CE_ItemViewItem, view, painter, option.widget)
        check = W.QStyleOptionButton()
        check.rect = self.indicator_rect(option)
        check.state = W.QStyle.State_Enabled | (W.QStyle.State_On if index.data(QtCore.Qt.CheckStateRole) in (2, QtCore.Qt.Checked) else W.QStyle.State_Off)
        option.widget.style().drawControl(W.QStyle.CE_CheckBox, check, painter, option.widget)

    def editorEvent(self, event, model, option, index):
        if not index.flags() & QtCore.Qt.ItemIsEnabled:
            return False
        click = event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton and self.indicator_rect(option).contains(event.pos())
        key = event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Space
        if click or key:
            value = QtCore.Qt.Unchecked if index.data(QtCore.Qt.CheckStateRole) in (2, QtCore.Qt.Checked) else QtCore.Qt.Checked
            return model.setData(index, value, QtCore.Qt.CheckStateRole)
        return False
