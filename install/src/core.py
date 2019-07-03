import sys
import os
import urllib.request, urllib.parse, urllib.error
import urllib.parse
import zipfile
import shutil


class builder:
    '''
    Builder class
    '''
    def __init__(self, outdir=None):
        '''
        Workflow builder
        '''
        self.outdir = outdir if outdir else None
        self.prepare_workspace( self.outdir )        

    def prepare_workspace(self, dirs):
        '''
        Create directories recursively, if they don't exist
        '''
        if dirs:
            try:
                os.makedirs(dirs)
            except:
                pass

    def download_url(self, url, outdir=None, outfile=None):
        '''
        Download the file from the URL
        '''
        # get the file name from the URL
        split = urllib.parse.urlsplit(url)
        file = outdir + '/' + outfile if outfile else split.path.split("/")[-1]
        # downlaod
        urllib.request.urlretrieve(url, file)
        return file

    def unzip_file(self, file, outdir):
        '''
        Extract unzip file
        '''
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(outdir)

    def move_files(self, srcdir, trgdir):
        '''
        Move files
        '''
        dirs = [ name for name in os.listdir(srcdir) if os.path.isdir(os.path.join(srcdir, name)) ]
        srcdir = srcdir + '/' + dirs[0]
        print((srcdir +" > "+ trgdir))
        os.rename( srcdir, trgdir)

    def remove_dir(self, dirs):
        '''
        Remove a directory
        '''
        shutil.rmtree(dirs)

    def remove_file(self, file):
        '''
        Remove a file
        '''
        os.remove(file)
