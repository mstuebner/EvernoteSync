"""
Module implements a watchdog that monitors a directory tree for new files to import to Evernote
"""
import time
import logging

# Third party modules
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# Project owned modules
from config_model import settings
import evernote_file_upload


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    LOG = logging.getLogger('evernotesync.directory_monitor')
    settings.sandbox = False

    patterns = ["*"]
    IGNORE_PATTERNS = None
    IGNORE_DIRECTORIES = False
    CASE_SENSITIVE = True
    my_event_handler = PatternMatchingEventHandler(patterns, IGNORE_PATTERNS, IGNORE_DIRECTORIES, CASE_SENSITIVE)
    LOG.debug('PatternMatchingEventHandler created')

    def on_created(event):
        """Event handler for CREATE event, fires when a new file is created"""
        if not event.is_directory:
            LOG.info("The file \"%s\" has been created!", event.src_path)
            LOG.info("Starting evernote importer")
            evernote_file_upload.main()
            LOG.info("Evernote importer ended")

    my_event_handler.on_created = on_created
    LOG.debug('"on_created" eventhandler added')

    observer = Observer()
    observer.schedule(my_event_handler, settings.directory, recursive=True)
    observer.start()
    LOG.debug('Observer scheduled and started.')
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
        LOG.debug('Observer stopped')
