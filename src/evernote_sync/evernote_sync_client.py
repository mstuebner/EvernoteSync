"""
- read json file with config
    - directory root to care about
    - config about sub directories > tags, searches, notebooks
- get data from evernote
    - Tags, notebooks
- per directory
    - collect files
    - process files according config
    - upload
"""

######
# autofile.py (https://gist.github.com/lookingcloudy/8d4fe1d3c221b4428549)
# search evernote api for key words, then automatically apply tags, ttitle, and move to specified notebook
# This is using my personal Evernote account, therefore, no need to use oAuth.  Just need a developertoken from
# my account.  Be sure to set "sandbox = False" when using a production account.
#
# Developer documentation: https://dev.evernote.com/doc/
# API documentation:  https://dev.evernote.com/doc/reference/
# Sandbox Developer Token:  https://sandbox.evernote.com/api/DeveloperToken.action
# Production Developer Token:  https://www.evernote.com/api/DeveloperToken.action


from datetime import datetime
import logging
import json

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
from evernote.edam.notestore.ttypes import *


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__file__)


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
    LOGGER.info(f'Number of notebooks: {len(notebooks)}')

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
            tag = Types.Tag()
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
        new_notebook = Types.Notebook()
        new_notebook.name = notebook
        new_notebook.stack = notebook_config['stack']
        LOGGER.info(f'Create notebook "{new_notebook.name}"')
        new_notebook = note_store.createNotebook(new_notebook)
        guid = new_notebook.guid

    return guid


def file_notes(notes, mapitem, note_store):
    """
    """
    for note in notes:
        # build a new title
        # if not note.title.strip()[:1].isdigit():
        note.title = datetime.fromtimestamp(note.created / 1e3).strftime('%Y-%m-%d') + ' - ' + mapitem['title']
        LOGGER.info(f'New note title: {note.title}')

        note.tagGuids = mapitem['tags']
        note.notebookGuid = mapitem['target notebook']
        note_store.updateNote(note)


def auto_file(autofile: dict, note_store, tags, notebooks):
    """
    """
    spec = NotesMetadataResultSpec()
    spec.includeTitle = True
    spec.includeCreated = True
    spec.includeTagGuids = True

    for autofile_item in autofile:

        # Convert tags and notebooks to guids
        autofile_item['tags'] = tags_to_guids(autofile_item['tags'], tags, note_store)
        autofile_item['target notebook'] = notebook_to_guid(autofile_item, notebooks, note_store)

        # Instantiate filter and set search words
        note_filter = NoteFilter()
        note_filter.words = autofile_item['search']

        LOGGER.info(f'Search notes for "{note_filter.words}"')
        # Execute search
        results = note_store.findNotesMetadata(note_filter, 0, 99, spec)
        LOGGER.info(f'Number of results: {results.totalNotes}')

        if results.totalNotes:
            file_notes(results.notes, autofile_item, note_store)


def main():
    """
    Main handler function
    """
    # Preparation
    config, autofile = get_configuration()
    client, user_store, note_store, tags, notebooks = connect(config=config)

    # Processing
    auto_file(autofile=autofile, note_store=note_store, tags=tags, notebooks=notebooks)


if __name__ == '__main__':
    main()
