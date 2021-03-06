# -*- coding: utf-8 -*-
import filecmp
import os
import unittest

from six.moves import range
import timeout_decorator
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import ApiRequestError

from test import test_util


class GoogleDriveFileTest(unittest.TestCase):
  """Tests basic file operations of files.GoogleDriveFile.
  Mainly upload and download of contents and metadata.
  Equivalent to Files.insert, Files.update, Files.patch in Google Drive API.
  """

  ga = GoogleAuth('settings/test1.yaml')
  ga.LocalWebserverAuth()
  first_file = 'a.png'
  second_file = 'b.png'

  def test_01_Files_Insert(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = 'firsttestfile'
    file1['title'] = filename
    file1.Upload()  # Files.insert

    self.assertEqual(file1.metadata['title'], filename)
    file2 = drive.CreateFile({'id': file1['id']})  # Download file from id.
    self.assertEqual(file2['title'], filename)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_02_Files_Insert_Unicode(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = u'첫번째 파일'
    file1['title'] = filename
    file1.Upload()  # Files.insert

    self.assertEqual(file1.metadata['title'], filename)
    file2 = drive.CreateFile({'id': file1['id']})  # Download file from id.
    self.assertEqual(file2['title'], filename)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_03_Files_Insert_Content_String(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = 'secondtestfile'
    content = 'hello world!'
    file1['title'] = filename
    file1.SetContentString(content)
    file1.Upload()  # Files.insert

    self.assertEqual(file1.GetContentString(), content)

    file1.FetchContent()  # Force download and double check content
    self.assertEqual(file1.metadata['title'], filename)
    self.assertEqual(file1.GetContentString(), content)

    file2 = drive.CreateFile({'id': file1['id']})  # Download file from id.
    self.assertEqual(file2.GetContentString(), content)
    self.assertEqual(file2.metadata['title'], filename)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_04_Files_Insert_Content_Unicode_String(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = u'두번째 파일'
    content = u'안녕 세상아!'
    file1['title'] = filename
    file1.SetContentString(content)
    file1.Upload()  # Files.insert

    self.assertEqual(file1.GetContentString(), content)
    self.assertEqual(file1.metadata['title'], filename)
    file1.FetchContent()  # Force download and double check content.
    self.assertEqual(file1.GetContentString(), content)

    file2 = drive.CreateFile({'id': file1['id']})  # Download file from id.
    self.assertEqual(file2.GetContentString(), content)
    self.assertEqual(file2.metadata['title'], filename)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_05_Files_Insert_Content_File(self):
    self.DeleteOldFile(self.first_file+'1')
    self.DeleteOldFile(self.first_file+'2')
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = 'filecontent'
    file1['title'] = filename
    file1.SetContentFile(self.first_file)
    file1.Upload()  # Files.insert

    self.assertEqual(file1.metadata['title'], filename)
    file1.FetchContent()  # Force download and double check content.
    file1.GetContentFile(self.first_file+'1')
    self.assertEqual(filecmp.cmp(self.first_file, self.first_file+'1'), True)

    file2 = drive.CreateFile({'id': file1['id']})  # Download file from id.
    file2.GetContentFile(self.first_file+'2')
    self.assertEqual(filecmp.cmp(self.first_file, self.first_file+'2'), True)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_06_Files_Patch(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = 'prepatchtestfile'
    newfilename = 'patchtestfile'
    file1['title'] = filename
    file1.Upload()  # Files.insert

    self.assertEqual(file1.metadata['title'], filename)
    file1['title'] = newfilename
    file1.Upload()  # Files.patch

    self.assertEqual(file1.metadata['title'], newfilename)
    file2 = drive.CreateFile({'id': file1['id']})  # Download file from id.
    file2.FetchMetadata()
    self.assertEqual(file2.metadata['title'], newfilename)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_07_Files_Patch_Skipping_Content(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = 'prepatchtestfile'
    newfilename = 'patchtestfile'
    content = 'hello world!'

    file1['title'] = filename
    file1.SetContentString(content)
    file1.Upload()  # Files.insert
    self.assertEqual(file1.metadata['title'], filename)

    file1['title'] = newfilename
    file1.Upload()  # Files.patch
    self.assertEqual(file1.metadata['title'], newfilename)
    self.assertEqual(file1.GetContentString(), content)
    self.assertEqual(file1.GetContentString(), content)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_08_Files_Update_String(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = 'preupdatetestfile'
    newfilename = 'updatetestfile'
    content = 'hello world!'
    newcontent = 'hello new world!'

    file1['title'] = filename
    file1.SetContentString(content)
    file1.Upload()  # Files.insert
    self.assertEqual(file1.metadata['title'], filename)
    self.assertEqual(file1.GetContentString(), content)

    file1.FetchContent()  # Force download and double check content.
    self.assertEqual(file1.GetContentString(), content)

    file1['title'] = newfilename
    file1.SetContentString(newcontent)
    file1.Upload()  # Files.update
    self.assertEqual(file1.metadata['title'], newfilename)
    self.assertEqual(file1.GetContentString(), newcontent)
    self.assertEqual(file1.GetContentString(), newcontent)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_09_Files_Update_File(self):
    self.DeleteOldFile(self.first_file+'1')
    self.DeleteOldFile(self.second_file+'1')
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    filename = 'preupdatetestfile'
    newfilename = 'updatetestfile'

    file1['title'] = filename
    file1.SetContentFile(self.first_file)
    file1.Upload()  # Files.insert
    self.assertEqual(file1.metadata['title'], filename)

    file1.FetchContent()  # Force download and double check content.
    file1.GetContentFile(self.first_file+'1')
    self.assertEqual(filecmp.cmp(self.first_file, self.first_file+'1'), True)

    file1['title'] = newfilename
    file1.SetContentFile(self.second_file)
    file1.Upload()  # Files.update
    self.assertEqual(file1.metadata['title'], newfilename)
    file1.GetContentFile(self.second_file+'1')
    self.assertEqual(filecmp.cmp(self.second_file, self.second_file+'1'), True)

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_Files_Trash_File(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    file1.Upload()
    self.assertFalse(file1.metadata[u'labels'][u'trashed'])

    # Download to verify non-trashed state on GDrive.
    file2 = drive.CreateFile({'id': file1['id']})
    file2.FetchMetadata()
    self.assertFalse(file2.metadata[u'labels'][u'trashed'])

    file1.Trash()
    self.assertTrue(file1.metadata[u'labels'][u'trashed'])

    file2.FetchMetadata()
    self.assertTrue(file2.metadata[u'labels'][u'trashed'])

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_Files_Trash_File_Just_ID(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    file1.Upload()
    self.assertFalse(file1.metadata[u'labels'][u'trashed'])

    # Trash file by ID.
    file2 = drive.CreateFile({'id': file1['id']})
    file2.Trash()

    # Verify trashed by downloading metadata.
    file1.FetchMetadata()
    self.assertTrue(file1.metadata[u'labels'][u'trashed'])

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_Files_UnTrash_File(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    file1.Upload()
    file1.Trash()
    self.assertTrue(file1.metadata[u'labels'][u'trashed'])

    # Verify that file is trashed by downloading metadata.
    file2 = drive.CreateFile({'id': file1['id']})
    file2.FetchMetadata()
    self.assertTrue(file2.metadata[u'labels'][u'trashed'])

    # Un-trash the file, and assert local metadata is updated correctly.
    file1.UnTrash()
    self.assertFalse(file1.metadata[u'labels'][u'trashed'])

    # Re-fetch the metadata, and assert file un-trashed on GDrive.
    file2.FetchMetadata()
    self.assertFalse(file2.metadata[u'labels'][u'trashed'])

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_Files_UnTrash_File_Just_ID(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    file1.Upload()
    file1.Trash()
    self.assertTrue(file1.metadata[u'labels'][u'trashed'])

    file2 = drive.CreateFile({'id': file1['id']})
    file2.UnTrash()  # UnTrash without fetching metadata.

    file1.FetchMetadata()
    self.assertFalse(file1.metadata[u'labels'][u'trashed'])

    self.DeleteUploadedFiles(drive, [file1['id']])

  def test_Files_Delete_File(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    file1.Upload()
    file2 = drive.CreateFile({'id': file1['id']})

    file1.Delete()

    try:
      file2.FetchMetadata()
      self.fail("File not deleted correctly.")
    except ApiRequestError as e:
      pass

  def test_Files_Delete_File_Just_ID(self):
    drive = GoogleDrive(self.ga)
    file1 = drive.CreateFile()
    file1.Upload()
    file2 = drive.CreateFile({'id': file1['id']})

    file2.Delete()

    try:
      file1.FetchMetadata()
      self.fail("File not deleted correctly.")
    except ApiRequestError as e:
      pass

  # Setup for concurrent upload testing.
  # =====================================
  class UploadWorker:
    def __init__(self, gdrive_file, generate_http=False):
      self.gdrive_file = gdrive_file
      self.param = {}
      if generate_http:
        self.param = {"http": gdrive_file.auth.Get_Http_Object()}

    def run(self):
      self.gdrive_file.Upload(param=self.param)

  def _parallel_uploader(self, num_of_uploads, num_of_workers,
                         use_per_thread_http=False):
    drive = GoogleDrive(self.ga)
    thread_pool = ThreadPoolExecutor(max_workers=num_of_workers)

    # Create list of gdrive_files.
    upload_files = []
    remote_name = test_util.CreateRandomFileName()
    for i in range(num_of_uploads):
      file_name = self.first_file if i % 2 == 0 else self.second_file
      up_file = drive.CreateFile()
      up_file['title'] = remote_name
      up_file.SetContentFile(file_name)
      upload_files.append(up_file)

    # Ensure there are no files with the random file name.
    files = drive.ListFile(param={'q': "title = '%s' and trashed = false" %
                               remote_name}).GetList()
    self.assertTrue(len(files) == 0)

    # Submit upload jobs to ThreadPoolExecutor.
    futures = []
    for i in range(num_of_uploads):
      upload_worker = self.UploadWorker(upload_files[i],
                                        use_per_thread_http)
      futures.append(thread_pool.submit(upload_worker.run))

    # Ensure that all threads a) return, and b) encountered no exceptions.
    for future in as_completed(futures):
      self.assertIsNone(future.exception())
    thread_pool.shutdown()

    # Ensure 10 files were uploaded.
    files = drive.ListFile(param={'q': "title = '%s' and trashed = false" %
                                       remote_name}).GetList()
    self.assertTrue(len(files) == 10)

    # Remove uploaded files.
    self.DeleteUploadedFiles(drive, [fi['id'] for fi in upload_files])

  @timeout_decorator.timeout(80)
  def test_Parallel_Files_Insert_File_Auto_Generated_HTTP(self):
    self._parallel_uploader(10, 10)

  @timeout_decorator.timeout(80)
  def test_Parallel_Insert_File_Passed_HTTP(self):
    self._parallel_uploader(10, 10, True)

  # Helper functions.
  # =================

  def DeleteOldFile(self, file_name):
    try:
      os.remove(file_name)
    except OSError:
      pass

  def DeleteUploadedFiles(self, drive, ids):
    for element in ids:
      tmp_file = drive.CreateFile({'id': element})
      tmp_file.Delete()


if __name__ == '__main__':
  unittest.main()
