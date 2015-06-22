import npyscreen

__author__ = 'cosmin'


class EditRecord(npyscreen.ActionForm):
    def create(self):
        self.value = None
        self.wgLastName = self.add(npyscreen.TitleText, name="Last Name:", )
        self.wgOtherNames = self.add(npyscreen.TitleText, name="Other Names:")
        self.wgEmail = self.add(npyscreen.TitleText, name="Email:")

    def beforeEditing(self):
        if self.value:
            record = self.parentApp.image_list[self.value]
            self.name = "Record id : %s" % record[0]
            self.record_id = record[0]
            self.wgLastName.value = record[1]
            self.wgOtherNames.value = record[2]
            self.wgEmail.value = record[3]

    def on_ok(self):
        if self.record_id:  # We are editing an existing record
            self.parentApp.myDatabase.update_record(self.record_id,
                                                    last_name=self.wgLastName.value,
                                                    other_names=self.wgOtherNames.value,
                                                    email_address=self.wgEmail.value,
            )
        else:  # We are adding a new record.
            self.parentApp.myDatabase.add_record(last_name=self.wgLastName.value,
                                                 other_names=self.wgOtherNames.value,
                                                 email_address=self.wgEmail.value,
            )
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.switchFormPrevious()