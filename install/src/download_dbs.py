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
    outfname = 'current_dbs.zip'

    print("-- create builder")
    c = core.builder(outdir)

    print("-- download files: "+url+" > "+outdir)
    file = c.download_url(url, outdir, outfname)

    print("-- unzip files: "+file+" > "+outdir)
    c.unzip_file(file, outdir)

    print("-- remove file")
    c.remove_file(outdir+'/'+outfname)


# call the main function
main(sys)