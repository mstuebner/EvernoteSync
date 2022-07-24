"""
This script reads a configuration, scans the given directory and collects all files in it. In the next step
the search result is then worked through and for each found file a note is created and the file is added.
At the end the processed files are deleted from directory.

Developer documentation: https://dev.evernote.com/doc/
API documentation:  https://dev.evernote.com/doc/reference/
Sandbox Developer Token:  https://sandbox.evernote.com/api/DeveloperToken.action
Production Developer Token:  https://www.evernote.com/api/DeveloperToken.action
"""
import os
import hashlib
import datetime
import logging
import json
import mimetypes

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as evtypes

from config_model import settings

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__file__)

NOTE_BASE = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'


def get_configuration() -> dict:
    """
    Load the JSON configuration file
    """
    LOGGER.debug('Read configuration for %s', 'Sandbox' if settings.sandbox else 'Production')

    config_file = 'configs/config.json'
    with open(config_file, encoding='utf-8') as config_json:
        config = json.load(config_json)

    autofile = config['autofile']

    return autofile


def connect():
    """
    Connect and load a list of tags and notebooks
    """
    application = 'Evernote '
    if settings.sandbox:
        token = settings.token_sandbox
        LOGGER.info('Connect to %s sandbox', application)
    else:
        token = settings.token_production
        LOGGER.info('Connect to %s production system', application)

    client = EvernoteClient(token=token, sandbox=settings.sandbox)
    user_store = client.get_user_store()
    note_store = client.get_note_store()

    tags = note_store.listTags()
    LOGGER.debug('Number of tags: %s', len(tags))

    notebooks = note_store.listNotebooks()
    LOGGER.debug('Number of notebooks: %s\n', len(notebooks))

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
            LOGGER.info('Create tag "%s"', tag.name)
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
        LOGGER.info('Create notebook "%s"', new_notebook.name)
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
    with open(filename, 'rb') as input_file:
        attachment_bytes = input_file.read()

    # Create the Data type for evernote that goes into a resource
    attachment_data = evtypes.Data()
    attachment_data.bodyHash = hashlib.md5(attachment_bytes).hexdigest()
    attachment_data.size = len(attachment_bytes)
    attachment_data.body = attachment_bytes

    # Create a resource for the note that contains the pdf
    attachment_resource = evtypes.Resource()
    attachment_resource.data = attachment_data
    attachment_resource.mime, _ = mimetypes.guess_type(filename)

    # Create meta information about the attachment
    res_attributes = evtypes.ResourceAttributes()
    res_attributes.attachment = False  # As attachment
    res_attributes.fileName = os.path.basename(filename)
    res_attributes.timestamp = int(datetime.datetime.now().timestamp())

    attachment_resource.attributes = res_attributes

    return attachment_resource


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
            LOGGER.info('Import file "%s" to notebook "%s"', _file, target_notebook)
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
    if settings.sandbox:
        return True

    try:
        os.remove(filepath)
    except OSError:
        LOGGER.warning('Cannot delete file: %s', filepath)
        return False

    return True


def collect_files(start_directory: str, itemconfigs: dict) -> dict:
    """
    Function collects all files in the start_directory and returns a dict with the subdirectory as key
    and a list of filepathes in it.
    """
    _files_dict = {}

    for directory in itemconfigs.keys():
        _path = os.path.join(start_directory, directory)
        if os.path.exists(_path):
            _file_list = os.listdir(path=_path)
            _files_dict[directory] = [os.path.join(start_directory, directory, item) for item in _file_list]

    return _files_dict


def get_specific_file(start_directory: str, specific_filepath: str) -> dict:
    """
    Function returns the required structure in case that there arn't files to be collected, because one specific
    filepath is given.
    """
    path_after_start_directory = os.path.normpath(specific_filepath[len(start_directory)+len(os.sep):])
    path_components = path_after_start_directory.split(os.sep)

    return {path_components[0]: [specific_filepath]}


def main(specific_filepath=None):
    """
    Main handler function
    """
    # Preparation
    autofile = get_configuration()
    _, _, note_store, tags, notebooks = connect()

    # Processing
    if not specific_filepath:
        files_to_import = collect_files(start_directory=settings.directory, itemconfigs=autofile)
    else:
        files_to_import = get_specific_file(start_directory=settings.directory, specific_filepath=specific_filepath)

    if len(files_to_import) > 0:
        LOGGER.info('%s file(s) collected', len(files_to_import))
        _notes_created = import_files(files_dict=files_to_import, itemconfigs=autofile, note_store=note_store,
                                      notebooks=notebooks, tags=tags)

        LOGGER.info('%s note(s) created', len(_notes_created))
    else:
        LOGGER.info('Nothing to import')
