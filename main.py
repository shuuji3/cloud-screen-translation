import wx
import wx.richtext
from PIL import ImageGrab

from utils import text_detection, translate, speak


class CaptureFrame(wx.Frame):
    """Window to set a capture window which has the translation target text."""

    def __init__(self, parent, title, pos, size):
        """Init the capture windows."""

        wx.Frame.__init__(self, parent, title=title, size=size, pos=pos)
        self.parent = parent
        self.Bind(wx.EVT_SIZE, self.set_capture_area)
        self.Bind(wx.EVT_MOVE, self.set_capture_area)
        self.SetTransparent(100)
        self.Show()

    def set_capture_area(self, event):
        """Set capture area."""

        pos = self.GetPosition()
        size = self.GetSize()

        # To obtain inner area, calculate the titlebar height
        titlebar_height = self.GetSize()[1] - self.GetClientSize()[1]
        size[1] -= titlebar_height
        pos[1] += titlebar_height

        title = 'Capture window: {}+{}'.format(pos, size)
        self.SetTitle(title)

        self.parent.capture_area_pos = pos
        self.parent.capture_area_size = size


class MainFrame(wx.Frame):
    """Main window of the application."""

    def __init__(self, parent, *args, **kwargs):
        """Init the main window"""

        wx.Frame.__init__(self, parent, *args, **kwargs, size=(800, 330))
        self.capture_area_pos = (200, 600)
        self.capture_area_size = (1100, 200)
        self.speech_checkbox_checked = False

        self.open_capture_window()

        translate_button = wx.Button(self, label='Capture\nand\nTranslate')
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        translate_button.SetFont(font)
        translate_button.SetMinClientSize((50, 80))
        translate_button.Bind(wx.EVT_BUTTON, self.translate_onclick)

        speech_checkbox = wx.CheckBox(self, label='Speak Japanese')
        speech_checkbox.SetMinClientSize((130, 20))
        speech_checkbox.Bind(wx.EVT_CHECKBOX, self.speech_checkbox_onchange)

        self.ja_text_ctrl = wx.richtext.RichTextCtrl(self, style=wx.richtext.RE_CENTRE_CARET)
        self.ja_text_ctrl.SetMinSize((700, 150))
        self.ja_text_ctrl.BeginFontSize(20)
        self.ja_text_ctrl.WriteText('日本語 (Japanese)')

        self.en_text_ctrl = wx.richtext.RichTextCtrl(self, style=wx.richtext.RE_CENTRE_CARET)
        self.en_text_ctrl.SetMinSize((700, 150))
        self.en_text_ctrl.BeginFontSize(20)
        self.en_text_ctrl.AddParagraph('English')

        input_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer.Add(translate_button, proportion=1, flag=wx.GROW)
        input_sizer.Add(speech_checkbox)

        text_sizer = wx.BoxSizer(wx.VERTICAL)
        text_sizer.Add(self.ja_text_ctrl)
        text_sizer.AddSpacer(5)
        text_sizer.Add(self.en_text_ctrl)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(input_sizer, proportion=1, flag=wx.GROW)
        sizer.Add(text_sizer, proportion=1, flag=wx.GROW)
        self.SetSizer(sizer)

        self.Center()
        self.Show()

    def open_capture_window(self):
        """Open capture window to set capture area."""

        frame = CaptureFrame(self, title='Capture window', pos=self.capture_area_pos, size=self.capture_area_size)

    def speech_checkbox_onchange(self, event):
        """Event handler on changing speech_checkbox."""
        self.speech_checkbox_checked: bool = event.EventObject.Value

    def translate_onclick(self, event):
        """Translate the text of area and show it in the main window."""

        x, y = self.capture_area_pos
        w, h = self.capture_area_size

        # Need to adjust size for Mac's Retina display
        scale = wx.Window.GetContentScaleFactor(self)

        # Detect text & translate it by Google Cloud
        image = ImageGrab.grab((x * scale, y * scale, (x + w) * scale, (y + h) * scale))
        ja_text = text_detection(image).replace('\n', '　').strip()
        en_text = translate(ja_text).strip()

        self.append_text(self.ja_text_ctrl, ja_text)
        self.append_text(self.en_text_ctrl, en_text)

        if self.speech_checkbox_checked:
            speak(ja_text)

    @staticmethod
    def append_text(rich_text_ctrl, ja_text):
        rich_text_ctrl.SetInsertionPointEnd()
        rich_text_ctrl.AddParagraph('-' * 4)
        rich_text_ctrl.AddParagraph(ja_text)
        rich_text_ctrl.SetInsertionPointEnd()
        rich_text_ctrl.ShowPosition(rich_text_ctrl.GetLastPosition())


def main():
    app = wx.App()
    MainFrame(None, title='Cloud Screen Translation')
    app.MainLoop()


if __name__ == '__main__':
    main()
