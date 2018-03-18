import wx
import wx.adv
import os
import json
import random
import time
from fuzzywuzzy import fuzz

TRAY_TOOLTIP = 'Japanese quiz'
TRAY_ICON = os.path.join(os.getcwd(),'japanese.ico')

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self):
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.onDoubleClick)
        self.dClickCallback = None

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(path, wx.BITMAP_TYPE_ANY))
        #icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, TRAY_TOOLTIP)

    def setDoubleClickCallback(self, callback):
        self.dClickCallback = callback

    def onDoubleClick(self, event):
        if self.dClickCallback:
            self.dClickCallback()

    def on_exit(self, event):
        exit()



class MainWindow(wx.Frame):
    def __init__(self, parent, title, test):
        # A "-1" in the size parameter instructs wxWidgets to use the default size.
        # In this case, we select 200px width and the default height.
        super().__init__(parent, title=title, size=(400, 320))
        self.solutions = {}
        self.Centre()
        self.CreateStatusBar() # A Statusbar in the bottom of the window

        self.initUI(test)
        self.Layout()
        self.Show()

    def initUI(self, test):
        self.test = test
        if "kanji" in self.test:
            question = test["kanji"]
            questions = ["hiragana", "romaji", "meaning"]
        else:
            question = test["hiragana"]
            questions = ["romaji", "meaning"]

        filemenu = wx.Menu()
        suggerimento = filemenu.Append(wx.ID_ANY, "&Help me", "Give me the correct answer")

        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(TRAY_ICON, wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        panel = wx.Panel(self)
        self.panel = panel
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        rightbox = wx.BoxSizer(wx.VERTICAL)
        leftbox = wx.StaticBoxSizer(wx.VERTICAL, panel)

        font = wx.Font(32, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        label = wx.StaticText(leftbox.GetStaticBox(), label=question, style=wx.ALIGN_CENTRE)
        label.SetFont(font)
        leftbox.Add(label, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER, 20)

        self.ticks = {}
        for el in questions:
            box = wx.BoxSizer(wx.HORIZONTAL)
            image = wx.StaticBitmap(panel,-1, wx.Bitmap("wrong.png", wx.BITMAP_TYPE_ANY))
            text =wx.TextCtrl(panel)
            text.SetHint(el)
            text.Bind(wx.EVT_KEY_DOWN, self.onEnter)
            box.Add(text, 1, wx.RIGHT|wx.EXPAND, 5)
            box.Add(image, 0, 0)
            rightbox.Add(box,0,wx.ALL|wx.EXPAND,5)
            self.solutions[el] = text
            image.Hide()
            self.ticks[el] = image


        cbtn = wx.Button(panel, label='Submit')
        cbtn.Bind(wx.EVT_BUTTON, lambda event, data=self.solutions, correct=self.test, signal=self.ticks: self.onSubmit(event, data, correct, signal))
        self.Bind(wx.EVT_MENU,  lambda event, data=self.solutions, correct=self.test, signal=self.ticks: self.onSuggest(event, data, correct, signal), suggerimento)
        rightbox.Add(cbtn, 0, wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT| wx.TOP, 25)

        hbox.Add(leftbox, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER, 10)
        hbox.Add(rightbox, 1, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(hbox)

    def onEnter(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            self.onSubmit(None, self.solutions, self.test, self.ticks)
        event.Skip()


    def onSubmit(self,event,data, correct, signal):
        if "kanji" in correct:
            questions = ["hiragana", "romaji", "meaning"]
        else:
            questions = ["romaji", "meaning"]

        close = True
        for el in questions:
            if fuzz.ratio(data[el].GetValue(), correct[el]) < 90:
                close = False
                signal[el].SetBitmap(wx.Bitmap("wrong.png", wx.BITMAP_TYPE_ANY))
            else:
                signal[el].SetBitmap(wx.Bitmap("correct.png", wx.BITMAP_TYPE_ANY))
            signal[el].Show()

        self.Layout()
        self.panel.Layout()

        if close:
            self.Close()


    def onSuggest(self, event, data, correct, signal):
        if "kanji" in correct:
            questions = ["hiragana", "romaji", "meaning"]
        else:
            questions = ["romaji", "meaning"]

        for el in questions:
            data[el].SetValue(correct[el])
            signal[el].SetBitmap(wx.Bitmap("correct.png", wx.BITMAP_TYPE_ANY))
            signal[el].Show()

        self.Layout()
        self.panel.Layout()

class App(wx.App):
    def OnInit(self):
        frame=wx.Frame(None)
        self.subframe = None
        self.SetTopWindow(frame)
        self.tb = TaskBarIcon()
        self.tb.setDoubleClickCallback(self.raiseOrOpen)
        self.timer = None
        return True

    def run(self):
        if self.subframe:
            self.subframe.Destroy()
        if self.timer:
            self.timer.Stop()

        self.subframe = MainWindow(None, "Kanji", random.choice(tests))
        self.subframe.Bind(wx.EVT_CLOSE, self.reboot)
        self.MainLoop()


    def raiseOrOpen(self):
        if self.timer and not self.timer.HasRun():
            self.timer.Notify()
        elif not self.subframe:
            self.subframe = MainWindow(None, "Kanji", random.choice(tests))
            self.subframe.Bind(wx.EVT_CLOSE, self.reboot)
        elif self.subframe:
            self.subframe.Raise()

    def openNew(self):
        if self.subframe:
            self.subframe.Destroy()
            #self.subframe = None
        
        self.subframe = MainWindow(None, "Kanji", random.choice(tests))
        self.subframe.Bind(wx.EVT_CLOSE, self.reboot)

    def reboot(self, event):
        if self.subframe:
            self.subframe.Destroy()
            #self.subframe = None
        interval = random.randint(5*60,15*60)
        interval = 2
        self.timer = wx.CallLater(interval*1000, self.openNew)





if __name__ == '__main__':

    tests = json.load(open(os.path.join(os.getcwd(), "japanese.json"), "r"))
    app = App()
    app.run()