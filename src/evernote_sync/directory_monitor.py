"""
Module implements a watchdog that monitors a directory tree for new files to import to Evernote
"""
import logging
import sys
import time
import zc.lockfile

# Third party modules
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import evernote_file_upload

# Project owned modules
from config_model import settings

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger('evernotesync.directory_monitor')


def monitoring(monitoring_settings):
    """Main function to monitor the directory defined in monitoring_settings.directory"""
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True

    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    LOG.debug('PatternMatchingEventHandler created')

    def on_created(event):
        """Event handler for CREATE event, fires when a new file is created"""
        if not event.is_directory:
            LOG.info("The file \"%s\" has been created!", event.src_path)
            LOG.info("Starting evernote importer")
            evernote_file_upload.main(event.src_path)
            LOG.info("Evernote importer ended\n-------------------------")

    my_event_handler.on_created = on_created
    LOG.debug('"on_created" eventhandler added')

    observer = Observer()
    observer.schedule(my_event_handler, monitoring_settings.directory, recursive=True)
    observer.start()
    LOG.debug('Observer scheduled and started.')
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
        LOG.debug('Observer stopped')


if __name__ == "__main__":
    APPLICATION = 'EvernoteDirectoryMonitor'
    LOCK = None

    try:
        LOCK = zc.lockfile.LockFile(APPLICATION)
        LOG.info('%s started.', APPLICATION)
        settings.sandbox = False  # Override sandbox value which is set to True by default
        monitoring(monitoring_settings=settings)
        LOCK.close()
    except zc.lockfile.LockError:
        LOG.warning('Application %s is already running and cannot run twice!', APPLICATION)
        sys.exit(-1)
    except KeyboardInterrupt:
        LOG.info('%s stpped.', APPLICATION)
