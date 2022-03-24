import hashlib
import typing

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types

NOTE_BASE = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'


def list_userinfo(client):
    user_store = client.get_user_store()
    user = user_store.getUser()

    print(user.username)


def list_notebooks(note_store):
    notebooks = note_store.listNotebooks()
    for notebook in notebooks:
        print(notebook.name)


def create_note(note_store):
    note = Types.Note()
    note.content = f'{NOTE_BASE}<en-note>Hello, world!</en-note>'
    note = note_store.createNote(note)

    return note


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

            r_list = [resource]
            note.resources = r_list
            # note.resources.append(resource)
            note.content += f"Attachment with hash {data.bodyHash}: and type {resource.mime}" \
                            f"<en-media type=\"{resource.mime}\" hash=\"NAME\" /><br />"

    note.content += "</en-note>"
    note = note_store.createNote(note)

    return note


def create_tag(note_store):
    tag = Types.Tag()
    tag.name = 'Generated Tag 1'
    tag = note_store.createTag(tag)

    return tag


if __name__ == '__main__':
    dev_token = "S=s1:U=92f57:E=186fab89818:C=17fa3076c18:P=1cd:A=en-devtoken:V=2:H=6f4d2a2ea62c48b2a1ec1e5bbc95fef6"
    client = EvernoteClient(token=dev_token)
    note_store = client.get_note_store()

    # list_userinfo(client=client)
    # create_tag(note_store=note_store)
    res = Types.Resource()
    create_note_with_attachment(note_store=note_store, attn=[{'src': r"d:\temp\Teilnehmerliste_211019.pdf",
                                                              'type': 'application/pdf'}])
