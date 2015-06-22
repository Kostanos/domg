import curses.ascii
import os
import npyscreen
import yaml
from domg.configurator import EditRecord
from domg.dockerfile import finder

__author__ = 'cosmin'


class ImageList(npyscreen.MultiLineAction):
    def __init__(self, *args, **keywords):
        super(ImageList, self).__init__(*args, **keywords)
        self.add_handlers({
            curses.ascii.ESC: self.parent.parentApp.switchFormPrevious,
            "^Q": quit
        })

    def display_value(self, vl):
        return os.path.dirname(vl)

    def actionHighlighted(self, act_on_this, keypress):
        self.parent.parentApp.getForm('EDITRECORDFM').value = act_on_this[0]
        self.parent.parentApp.switchForm('EDITRECORDFM')


class ContainerList(npyscreen.MultiLineAction):
    def __init__(self, *args, **keywords):
        super(ContainerList, self).__init__(*args, **keywords)
        self.add_handlers({
            "^A": self.when_add_record,
            "^D": self.when_delete_record,
            "^Q": quit
        })

    def display_value(self, vl):
        return os.path.dirname(vl)

    def actionHighlighted(self, act_on_this, keypress):
        self.parent.parentApp.getForm('EDITRECORDFM').value = act_on_this[0]
        self.parent.parentApp.switchForm('EDITRECORDFM')

    def when_add_record(self, *args, **keywords):
        self.parent.parentApp.getForm('EDITRECORDFM').value = None
        self.parent.parentApp.switchForm('EDITRECORDFM')

    def when_delete_record(self, *args, **keywords):
        self.parent.parentApp.myDatabase.delete_record(self.values[self.cursor_line][0])
        self.parent.update_list()


class RecordListDisplay(npyscreen.FormMutt):
    MAIN_WIDGET_CLASS = ContainerList

    def beforeEditing(self):
        self.update_list()
        self.wStatus1.value = "Configured containers:"
        self.wStatus1.update()

        self.wStatus2.value = "Ctrl-A to add, Ctrl-D to delete, Ctrl-Q to quit"
        self.wStatus2.update()

    def update_list(self):
        config = self.parentApp.config
        if 'containers' in config:
            containers = config['containers']
        else:
            containers = []
        self.wMain.values = containers
        self.wMain.values = containers
        self.wMain.display()





class DockerManager(npyscreen.NPSAppManaged):
    def __init__(self, images_path, config_file):
        if not os.path.isdir(images_path):
            raise Exception('Images path is not a directory: %s' % images_path)

        self.images_path = images_path
        self.image_list = finder(images_path)
        self.config_file = config_file
        try:
            self.config = Configuration(config_file)
        except IOError:
            with open(config_file, "w+"):
                pass
            self.config = Configuration(config_file)
        print self.config.items()
        super(DockerManager, self).__init__()


    def onStart(self):
        self.addForm("MAIN", RecordListDisplay, name="CEva")
        self.addForm("EDITRECORDFM", EditRecord)




