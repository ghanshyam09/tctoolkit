'''
common.py
Common utility functions required for the other modules.

Copyright (C) 2009 Nitin Bhide (nitinbhide@gmail.com, nitinbhide@thinkingcraftsman.in)

This module is part of Thinking Craftsman Toolkit (TC Toolkit) and is released under the
New BSD License: http://www.opensource.org/licenses/bsd-license.php
TC Toolkit is hosted at http://code.google.com/p/tctoolkit/
'''

import fnmatch
import os
import string
import sys
import time
from contextlib import contextmanager

IGNOREDIRS = set(['.svn','.cvs', '.hg', '.git'])

@contextmanager
def FileOrStdout(filename):
    '''
    return an file or stdout if the name is None that can used with 'with' statement.
    '''
    #enter code
    output = sys.stdout
    if( filename != None):        
        try:
            output = open(filename, "w")
        except:
            pass
    yield(output)
    #exit code
    if( output != sys.stdout):
        output.close()

@contextmanager
def TimeIt(fout,prefix=''):
    '''
    return a timer context manager. return the elapsed time.
    '''
    start_time = time.clock()
    
    yield
    
    end_time = time.clock()
    timediff = end_time - start_time
    fout.write("%s : %.2f seconds" % (prefix, timediff))
    
def RemoveIgnoreDirs(dirs):
    '''
    remove directories in the IGNOREDIRS list from the 'dirs'
    '''
    dirs = list(set(dirs) - IGNOREDIRS)
    return(dirs)

def GetDirFileList(dirname):
    rawfilelist = []
    #prepare list of all files ignore the directories defined in 'ignoredirs' list.
    for root, dirs, files in os.walk(dirname):
        dirs = RemoveIgnoreDirs(dirs)
        for fname in files:
            rawfilelist.append(os.path.join(root, fname))
    return(rawfilelist)

def PreparePygmentsFileList(dirname):
    '''
    Use the lexer list and file extensions from the Pygments and prepare the list of files for which
    lexers are available.
    '''
    import fnmatch,re
    from pygments.lexers import get_all_lexers
    
    #Prepare a list of fnmatch patterns from lexers
    fnmatchpatlist = []
    for lexer in get_all_lexers():
        fnmatchpatlist = fnmatchpatlist+[pat for pat in lexer[2]]

    #since one fnmatch pattern can exist in multiple lexers. We need remove duplicates from the fnmatch pattern list
    fnmatchpatlist=set(fnmatchpatlist)

    #combine the match patterns to a single regex
    matchregex = '|'.join([fnmatch.translate(pat) for pat in fnmatchpatlist])
    matchregex = re.compile(matchregex)
    
    rawfilelist = GetDirFileList(dirname)

    filelist = []
    for fname in rawfilelist:
        if (matchregex.match(fname) != None):
            filelist.append(fname)
    return(filelist)

def FindFileInPathList(fname, pathlist, extList=None):
    '''
    search the directories in 'pathlist' one by one to see if fname exists in that
    directory. Search inside a directory is NOT recursive. First 'hit' is returned.
    '''
    patternList = []
    if( extList != None and len(extList) > 0):
        for exten in extList:
            if( exten.startswith('.') == False):
                exten = '.' + exten
            patternList.append(fname + exten)
    else:
        patternList.append(fname)

    
    for fpath in pathlist:
        for pattern in patternList:
            testfname = os.path.join(fpath, pattern)        
            if( os.path.exists(testfname)):
                return(testfname)
    return(None)

def StripAtStart(src, strtostrip):
    if( src.startswith(strtostrip)):
        src = src[len(strtostrip):]
    return(src)    

def readJsText(dirname, filename):
    '''
    read the entire text content of javascript file.
    '''
    jsfile = os.path.join(dirname, *filename)
    
    return open(jsfile, "r").read()

def getJsDirPath():
    '''
    get the javascript directory path based on path of the current script.
    '''
    srcdir = os.path.dirname(os.path.abspath(__file__))
    jsdir = os.path.join(srcdir, '..','thirdparty', 'javascript')
    jsdir = os.path.abspath(jsdir)
    return jsdir

