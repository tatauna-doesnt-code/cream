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
        check = W.QStyleOptionViewItem(view)
        check.rect = self.indicator_rect(option)
        check.state = W.QStyle.State_Enabled | (W.QStyle.State_On if index.data(QtCore.Qt.CheckStateRole) in (2, QtCore.Qt.Checked) else W.QStyle.State_Off)
        option.widget.style().drawPrimitive(W.QStyle.PE_IndicatorItemViewItemCheck, check, painter, option.widget)

    def editorEvent(self, event, model, option, index):
        if not index.flags() & QtCore.Qt.ItemIsEnabled:
            return False
        click = event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton and self.indicator_rect(option).contains(event.pos())
        key = event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Space
        if click or key:
            # Item models require an integer QVariant. A Qt6 enum can display
            # as checked while QTableWidgetItem.checkState() still reads unchecked.
            value = 0 if index.data(QtCore.Qt.CheckStateRole) in (2, QtCore.Qt.Checked) else 2
            return model.setData(index, value, QtCore.Qt.CheckStateRole)
        return False


class WorkflowTabBar(W.QTabBar):
    """Native tab sizing/alignment, with per-tab override fonts and instant help."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modified_index = -1
        self.setMouseTracking(True)

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        if index == self.modified_index:
            font = QtGui.QFont(self.font())
            font.setBold(True)
            font.setItalic(True)
            size.setWidth(size.width() + max(0, QtGui.QFontMetrics(font).horizontalAdvance(self.tabText(index)) - self.fontMetrics().horizontalAdvance(self.tabText(index))) + 2)
        return size

    def paintEvent(self, event):
        painter = W.QStylePainter(self)
        for index in range(self.count()):
            if not self.isTabVisible(index):
                continue
            option = W.QStyleOptionTab()
            self.initStyleOption(option, index)
            font = QtGui.QFont(self.font())
            if index == self.modified_index:
                font.setBold(True)
                font.setItalic(True)
            painter.setFont(font)
            option.fontMetrics = QtGui.QFontMetrics(font)
            painter.drawControl(W.QStyle.CE_TabBarTabShape, option)
            painter.drawControl(W.QStyle.CE_TabBarTabLabel, option)

    def mouseMoveEvent(self, event):
        index = self.tabAt(event.pos())
        text = self.tabToolTip(index) if index >= 0 else ''
        if text:
            W.QToolTip.showText(self.mapToGlobal(event.pos()), text, self, self.tabRect(index))
        else:
            W.QToolTip.hideText()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        W.QToolTip.hideText()
        super().leaveEvent(event)
