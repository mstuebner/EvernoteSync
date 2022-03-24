import hashlib
import typing

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
from evernote.edam.error.ttypes import EDAMUserException, EDAMNotFoundException


NOTE_BASE = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'


def list_userinfo(client):
    user_store = client.get_user_store()
    user = user_store.getUser()

    print(user.username)


def create_note_with_attachment(note_store, attn: typing.List):
    note = Types.Note()
    note.title = "I'm a note with attachment 1!"
    note.content = f'{NOTE_BASE}<en-note>Hello, attachment!'

    if attn:
        note.resources = []
        note.content += "<br />" * 2

        for att in attn:
            with(open(att['src'], 'rb')) as input_file:
                file_content = input_file.read()

            data = Types.Data()
            data.size = len(file_content)
            data.body = file_content
            data.bodyHash = hashlib.md5(file_content).hexdigest()

            resource = Types.Resource()
            resource.mime = att['type']
            resource.data = data

            note.resources.append(resource)
            note.content += f"Attachment with hash {data.bodyHash}: and type {resource.mime}" \
                            f"<en-media type=\"{resource.mime}\" hash=\"{data.bodyHash}\" /><br />"

    note.content += "</en-note>"

    # Attempt to create note in Evernote account
    try:
        note = note_store.createNote(note)
    except EDAMUserException as edue:
        # Something was wrong with the note data
        # See EDAMErrorCode enumeration for error code explanation
        # http://dev.evernote.com/documentation/reference/Errors.html#Enum_EDAMErrorCode
        print("EDAMUserException:", edue)
        return None
    except EDAMNotFoundException as ednfe:
        # Parent Notebook GUID doesn't correspond to an actual notebook
        print("EDAMNotFoundException: Invalid parent notebook GUID")
        return None
    # Return created note object
    return note


if __name__ == '__main__':
    dev_token = "S=s1:U=92f57:E=186fab89818:C=17fa3076c18:P=1cd:A=en-devtoken:V=2:H=6f4d2a2ea62c48b2a1ec1e5bbc95fef6"
    client = EvernoteClient(token=dev_token)
    note_store = client.get_note_store()

    create_note_with_attachment(note_store=note_store, attn=[{'src': r"d:\temp\Teilnehmerliste_211019.pdf",
                                                              'type': 'application/pdf'}])
