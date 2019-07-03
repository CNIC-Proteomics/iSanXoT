#!/usr/bin/python
import sys
import core

def main(sys):
    '''
    Main function
    '''
    # Get input parameters
    url = sys.argv[1]
    outdir = sys.argv[2]
    tmpdir = sys.argv[3]

    print("-- create builder")
    c = core.builder(tmpdir)

    print("-- download files: "+url+" > "+tmpdir)
    file = c.download_url(url, tmpdir)

    print("-- unzip files: "+file+" > "+tmpdir)
    c.unzip_file(file, tmpdir)

    print("-- move files to outdir")
    c.move_files(tmpdir, outdir)

    print("-- remove tmpdir")
    c.remove_dir(tmpdir)

# call the main function
main(sys)