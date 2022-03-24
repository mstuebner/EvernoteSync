"""
Based on: https://gist.github.com/virantha/7294365

References/documentation:
- https://dev.evernote.com/doc/articles/resources.php
"""
import datetime
import os
import hashlib
import sys
import typing

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
from evernote.edam.error.ttypes import EDAMUserException
from evernote.edam.error.ttypes import EDAMSystemException
from evernote.edam.error.ttypes import EDAMErrorCode


class EvernoteUpload(object):
    note_bs = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'

    def __init__(self, dev_token):
        self._connect_to_evernote(dev_token)

    def _connect_to_evernote(self, dev_token):
        user = None
        try:
            self.client = EvernoteClient(token=dev_token)
            # self.client = EvernoteClient(token=dev_token, sandbox=False)
            self.user_store = self.client.get_user_store()
            user = self.user_store.getUser()
        except EDAMUserException as e:
            err = e.errorCode
            print("Error attempting to authenticate to Evernote: %s - %s" % (
                EDAMErrorCode._VALUES_TO_NAMES[err], e.parameter))
            return False
        except EDAMSystemException as e:
            err = e.errorCode
            print("Error attempting to authenticate to Evernote: %s - %s" % (
                EDAMErrorCode._VALUES_TO_NAMES[err], e.message))
            sys.exit(-1)

        if user:
            print(f'Authenticated to evernote as user "{user.username}"')
            return True
        else:
            return False

    def _get_notebooks(self):
        note_store = self.client.get_note_store()
        notebooks = note_store.listNotebooks()
        return {n.name: n for n in notebooks}

    def _create_notebook(self, notebook):
        note_store = self.client.get_note_store()
        return note_store.createNotebook(notebook)

    def _update_notebook(self, notebook):
        note_store = self.client.get_note_store()
        note_store.updateNotebook(notebook)
        return

    def _check_and_make_notebook(self, notebook_name, stack=None):
        """
        Method checks whether the notebook exists and creates it is not. If stack is not None, the notebook
        will be moved into that stack.
        """
        notebooks = self._get_notebooks()
        if notebook_name in notebooks:
            # Existing notebook, so just update the stack if needed
            notebook = notebooks[notebook_name]
            if stack:
                notebook.stack = stack
                self._update_notebook(notebook)
            # else:
                # notebook.stack = None
                # self._update_notebook(notebook)
            return notebook
        else:
            # Need to create a new notebook
            notebook = Types.Notebook()
            notebook.name = notebook_name

            if stack:
                notebook.stack = stack
            notebook = self._create_notebook(notebook)
            return notebook

    def _create_evernote_note(self, note_title, notebook, filepath):
        """
        Methd instantiates the note, attaches the file(s) and creates the note in evernote
        """
        # Create the new note
        note = Types.Note()

        note.title = os.path.basename(filepath)
        note.notebookGuid = notebook.guid
        note.content = self.note_bs
        note.content += f'<en-note>{note_title}<br/>'

        tags = self.get_tags_from_path(filepath=filepath)

        print(f'Attach file "{os.path.basename(filepath)}" to note "{note_title}"')
        pdf_resource = self._create_attachment(filename=filepath)

        # Add a link in the evernote body for this content
        note.content += f'<en-media type="{pdf_resource.mime}" hash="{pdf_resource.data.bodyHash}"/>'
        note.resources = [pdf_resource]
        note.content += '</en-note>'
        return note

    def get_tags_from_path(self, filepath: str) -> typing.List[str]:
        """
        Returns the last two levels of directories from filepath and returns them as tags instances
        """
        # ToDo: Specific for Windows!!
        dirs = filepath.split('\\')
        max_levels = 2
        stop_dir = 'temp'
        level = 0
        list_of_tags = []

        while level < max_levels:
            dir_name = dirs[(level+2)*-1]
            if dir_name == stop_dir:
                break
            list_of_tags.append(Types.Tag(name=dir_name))
            level += 1

        return list_of_tags

    @staticmethod
    def _create_attachment(filename):

        with open(filename, 'rb') as f:
            pdf_bytes = f.read()

        # Create the Data type for evernote that goes into a resource
        pdf_data = Types.Data()
        pdf_data.bodyHash = hashlib.md5(pdf_bytes).hexdigest()
        pdf_data.size = len(pdf_bytes)
        pdf_data.body = pdf_bytes

        # Create a resource for the note that contains the pdf
        pdf_resource = Types.Resource()
        pdf_resource.data = pdf_data
        pdf_resource.mime = 'application/pdf'

        # Create meta information about the attachment
        res_attributes = Types.ResourceAttributes()
        res_attributes.attachment = False  # As attachment
        res_attributes.fileName = os.path.basename(filename)
        res_attributes.timestamp = int(datetime.datetime.now().timestamp())

        pdf_resource.attributes = res_attributes

        return pdf_resource

    def upload_to_notebook(self, filenames, notebookname):
        """
        Method checks whether the notebook exists, creates it if it doesn't exist and create a note
        with the attachments.
        """
        print(f'Checking for notebook "{notebookname}"')
        notebook = self._check_and_make_notebook(notebookname, stack='Automatic File Uploads')

        for filename in filenames:
            note = self._create_evernote_note(f'Automatic file upload: {str(datetime.datetime.now())}',
                                              notebook,
                                              filename)

        # Store the note in evernote
        note = self.client.get_note_store().createNote(note)


if __name__ == '__main__':
    dev_token = "S=s1:U=92f57:E=186fab89818:C=17fa3076c18:P=1cd:A=en-devtoken:V=2:H=6f4d2a2ea62c48b2a1ec1e5bbc95fef6"
    p = EvernoteUpload(dev_token)
    file_list = [r"d:\temp\evernote_upload\python\Left to Sell Specialist Gesamt Info-2.pdf"]
    p.upload_to_notebook(filenames=file_list, notebookname="Uploads 1")
