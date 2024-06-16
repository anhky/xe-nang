from distutils.core import setup
from Cython.Build import cythonize
import os


list_file_py = []
path = os.getcwd()
files = os.listdir(path)

def checkFilePython(path, file):
   file_name, file_extension = os.path.splitext(os.path.basename(file))
   if file_extension =='.py' and file_name != '__init__' and file_name!='setup' and file_name!='main':
      if f'{path}\{file}' in list_file_py:
         pass
      else:
         list_file_py.append(f'{path}/{file}')
   
def forCheckPython(flash_isDirectory, path, files):
   for file in files:
      isFile = os.path.isfile(file)
      isDirectory = os.path.isdir(file)

      if flash_isDirectory:
         path_new = f'{path}/{file}'
         isDirectory1 = os.path.isdir(path_new)
         if isDirectory1: 
            path_new = f'{path}/{file}'
            files_new = os.listdir(path_new)
            forCheckPython(isDirectory1, path_new, files_new)
         else:
            checkFilePython(path, file)

      if isDirectory:
         path_new = f'{path}/{file}'
         files_new = os.listdir(path_new)
         forCheckPython(isDirectory, path_new, files_new)
      else:
         checkFilePython(path, file)

  
if __name__ == "__main__":
   forCheckPython(False, path, files)  
   fileSet = set()
   for i in list_file_py:
      i_OK = i.replace("//", "/")
      fileSet.add(i_OK)
   setup(
      ext_modules=cythonize(fileSet)
   )