import os
import hashlib
import datetime
import logging
import json

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as evtypes

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__file__)

NOTE_BASE = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'


def get_configuration():
    """
    Load the JSON configuration file
    """
    LOGGER.info('Read configuration')

    config = json.load(open('config.json'))
    autofile = config['autofile']
    config = config['configuration']

    return config, autofile


def connect(config):
    """
    Connect and load a list of tags and notebooks
    """
    if config['sandbox']:
        token = config['developerToken']
        LOGGER.info('Connect to sandbox')
    else:
        token = config['productionToken']
        LOGGER.info('Connect to production system')

    client = EvernoteClient(token=token, sandbox=config['sandbox'])
    user_store = client.get_user_store()
    note_store = client.get_note_store()

    tags = note_store.listTags()
    LOGGER.info(f'Number of tags: {len(tags)}')

    notebooks = note_store.listNotebooks()
    LOGGER.info(f'Number of notebooks: {len(notebooks)}\n')

    return client, user_store, note_store, tags, notebooks


def tags_to_guids(taglist, tags, note_store, create_tag=True):
    """
    Called once for each search mapping - converts list of tag names to list of tag guids
    """
    for tag_index, tag_name in enumerate(taglist):
        # lookup by name in the list of tag objects
        guid = next((item.guid for item in tags if item.name.lower() == tag_name.lower()), None)
        # if it was not found, create it
        if not guid and create_tag:
            tag = evtypes.Tag()
            tag.name = tag_name
            LOGGER.info(f'Create tag "{tag.name}"')
            tag = note_store.createTag(tag)
            guid = tag.guid
        taglist[tag_index] = guid

    return taglist


def notebook_to_guid(notebook_config, notebooks, note_store, create_nb=True):
    """
    Converts notebook name to guid
    """
    notebook = notebook_config['target notebook']
    guid = next((item.guid for item in notebooks if item.name.lower() == notebook.lower()), None)
    # if it was not found, create it
    if not guid and create_nb:
        new_notebook = evtypes.Notebook()
        new_notebook.name = notebook
        new_notebook.stack = notebook_config['stack']
        LOGGER.info(f'Create notebook "{new_notebook.name}"')
        new_notebook = note_store.createNotebook(new_notebook)
        guid = new_notebook.guid

    return guid


def _prepare_evernote_note(note_title, notebook_guid, filepath):
    """
    Methd instantiates the note, attaches the file(s) and creates the note in evernote
    """
    # Create the new note
    note = evtypes.Note()

    note.title = os.path.basename(filepath)
    note.notebookGuid = notebook_guid
    note.content = NOTE_BASE
    note.content += f'<en-note>{note_title}<br/>'

    pdf_resource = _create_attachment(filename=filepath)

    # Add a link in the evernote body for this content
    note.content += f'<en-media type="{pdf_resource.mime}" hash="{pdf_resource.data.bodyHash}"/>'
    note.resources = [pdf_resource]
    note.content += '</en-note>'
    return note


def _create_attachment(filename):
    """
    Function receives a filepath and creates:
        - Data instance
        - Resource instance
        - ResourceAttributes instance

    from it, likes them and return the Resource instance.
    """
    with open(filename, 'rb') as f:
        pdf_bytes = f.read()

    # Create the Data type for evernote that goes into a resource
    pdf_data = evtypes.Data()
    pdf_data.bodyHash = hashlib.md5(pdf_bytes).hexdigest()
    pdf_data.size = len(pdf_bytes)
    pdf_data.body = pdf_bytes

    # Create a resource for the note that contains the pdf
    pdf_resource = evtypes.Resource()
    pdf_resource.data = pdf_data
    pdf_resource.mime = 'application/pdf'

    # Create meta information about the attachment
    res_attributes = evtypes.ResourceAttributes()
    res_attributes.attachment = False  # As attachment
    res_attributes.fileName = os.path.basename(filename)
    res_attributes.timestamp = int(datetime.datetime.now().timestamp())

    pdf_resource.attributes = res_attributes

    return pdf_resource


def import_files(files_dict: dict, itemconfigs: dict, note_store, notebooks, tags):
    """
    Function gets the information about the files (files_dict) and the configuration (itemconfigs)
    and creates one note with one attachment each, and deletes the imported file then.

    Returns the list of created note instances then.
    """
    _dirs = files_dict.keys()
    _created_notes = []
    for directory in _dirs:
        _file_list = files_dict[directory]
        _config = itemconfigs[directory]

        _config['tags'] = tags_to_guids(_config['tags'], tags, note_store)
        notebook_guid = notebook_to_guid(_config, notebooks, note_store)

        for _file in _file_list:
            _prep_note = _prepare_evernote_note(note_title='',
                                                notebook_guid=notebook_guid,
                                                filepath=_file)
            target_notebook = _config.get('target notebook')
            LOGGER.info(f'Import file "{_file}" to notebook "{target_notebook}"')
            _prep_note.tagGuids = _config['tags']
            _created_note = note_store.createNote(_prep_note)
            if _created_note:
                _created_notes.append(_created_note)
                delete_imported_file(filepath=_file)

    return _created_notes


def delete_imported_file(filepath: str) -> bool:
    """
    Receives a filepath and deletes the file it points to.
    """
    try:
        os.remove(filepath)
    except OSError as exc:
        LOGGER.warning(f'Cannot delete file: {filepath}')
        return False

    return True


def collect_files(start_directory: str, itemconfigs: dict):
    """
    Function collects all files in the start_directory and returns a dict with the sub directory as key
    and a list of filepathes in it.
    """
    _files_dict = {}

    for directory in itemconfigs.keys():
        _file_list = os.listdir(path=os.path.join(start_directory, directory))
        _files_dict[directory] = [os.path.join(start_directory, directory, item) for item in _file_list]

    return _files_dict


def main():
    """
    Main handler function
    """
    # Preparation
    config, autofile = get_configuration()
    client, user_store, note_store, tags, notebooks = connect(config=config)

    # Processing
    files_to_import = collect_files(start_directory=config["directory"], itemconfigs=autofile)
    _notes_created = import_files(files_dict=files_to_import, itemconfigs=autofile, note_store=note_store,
                                  notebooks=notebooks, tags=tags)

    LOGGER.info(f'{len(_notes_created)} notes created')


if __name__ == '__main__':
    main()
