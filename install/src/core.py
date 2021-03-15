import sys
import os
import urllib.request, urllib.parse, urllib.error
import urllib.parse
import zipfile
import shutil
import time



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
        url_fname = urllib.parse.urlsplit(url)
        outfile = outfile if outfile else url_fname.path.split("/")[-1]
        file = f"{outdir}/{outfile}"
        # downlaod
        print( f"URL: {url} > FILE: {file}")
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
        self.remove_dir(trgdir);
        print((srcdir +" > "+ trgdir))
        startTime = time.clock()
        while 1:
            try:
                os.rename(srcdir, trgdir)
                break
            except OSError:
                if (time.clock() - startTime) > 5:
                    raise
                else:
                    time.sleep(0)

    def remove_dir(self, dirs):
        '''
        Remove a directory
        '''
        if os.path.exists(dirs):
            shutil.rmtree(dirs)

    def remove_file(self, file):
        '''
        Remove a file
        '''
        os.remove(file)
