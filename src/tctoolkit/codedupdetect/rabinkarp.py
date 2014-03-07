'''
rabinkarp.py
experimental code to search duplicate strings using Rabin Karp algorithm

reference : http://code.google.com/p/rabinkarp/source/browse/trunk/RK.cpp

Copyright (C) 2009 Nitin Bhide (nitinbhide@gmail.com, nitinbhide@thinkingcraftsman.in)

This module is part of Thinking Craftsman Toolkit (TC Toolkit) and is released under the
New BSD License: http://www.opensource.org/licenses/bsd-license.php
TC Toolkit is hosted at http://code.google.com/p/tctoolkit/

'''

from collections import deque
from itertools import izip
import operator
import hashlib
import tokenizer

HASH_BASE = 256
HASH_MOD =16777619;  #make sure it is a prime

#TOKEN_HASHBASE=HASH_BASE
#TOKEN_MOD = 251   # make sure it is prime and less than 256

#read the FNV has wikipedia entry for the details of these constants.
#http://en.wikipedia.org/wiki/Fowler_Noll_Vo_hash
FNV_OFFSET_BASIS=2166136261
FNV_PRIME=16777619

def int_mod(a, b):
    return (a % b + b) % b

def FNV8_hash(str):
    '''
    8 bit FNV hash created by XOR folding the FNV32 hash of the string
    '''
    fhash = FNV_OFFSET_BASIS
    for ch in str:
        fhash = fhash ^ ord(ch)
        fhash = fhash * FNV_PRIME
        fhash = fhash & 0xFFFFFFFF #ensure that hash remains 32 bit.
    #now fold it with XOR folding
    #print "token hash ", hash
    fhash = (fhash >> 16) ^ (fhash & 0xFFFF)
    fhash = (fhash >> 8) ^ (fhash & 0xFF)
    #print "hash after folding ", hash
    return(fhash)
    
class RabinKarp(object):
    def __init__(self, patternsize, matchstore, fuzzy=False):
        self.patternsize = patternsize
        self.matchstore = matchstore
        self.fuzzy=fuzzy
        self.tokenqueue = deque()
        self.tokenizers = dict()
        self.token_hash = dict()
        self.__rollhashbase =1
        for i in xrange(0, patternsize-1):
            self.__rollhashbase = (self.__rollhashbase*HASH_BASE) % HASH_MOD;

    def getTokenHash(self,token):
        #if token size is only one charater (i.e. tokens like '{', '+' etc)
        #then don't call FNV hash. Just use the single character.
        if( len(token) > 1):
            thash =FNV8_hash(token)
        else:
            thash = ord(token[0])
##        for ch in token:
##            thash = int_mod(thash * TOKEN_HASHBASE, TOKEN_MOD)
##            thash = int_mod(thash + ord(ch), TOKEN_MOD)
##        #print "token : %s hash:%d" % (token,thash)
        return(thash)

    #def getTokenHash(self, token):
    #    '''
    #    check if the token exists in the token_hash dictionary. If yes, return
    #    the value. If not, then add a new integer as token hash.
    #    NOTE : for some reason this hash value misses some of the duplicates.
    #    I am not sure why.
    #    '''
    #    if(len(token) == 1):
    #        thash = ord(token[0])
    #    if token in self.token_hash:
    #        thash = self.token_hash[token]            
    #    else:
    #        thash = len(self.token_hash) + 1 + 256;
    #        self.token_hash[token] = thash
    #    return thash 
        
    def addAllTokens(self,srcfile):
        curhash =0
        matchlen=0
        #empty the tokenqueue since we are starting a new file
        self.tokenqueue.clear()
        tknzr = self.getTokanizer(srcfile)
        for token in tknzr:
            curhash,matchlen = self.rollCurHash(tknzr,curhash,matchlen)
            curhash = self.addToken(curhash,token)

    def rollCurHash(self,tknzr,curhash,pastmatchlen):
        matchlen=pastmatchlen
        if(len(self.tokenqueue) >= self.patternsize):
            '''
            if the number of tokens are reached patternsize then
            then remove hash value of first token from the rolling hash
            '''            
            (thash, firsttoken) = self.tokenqueue.popleft()            
            #add the current hash value in hashset
            if(matchlen==0):                
                matchlen=self.findMatches(curhash,firsttoken,tknzr)
            else:
                matchlen=matchlen-1
                
            self.matchstore.addHash(curhash, firsttoken)
            curhash = int_mod(curhash - int_mod(thash* self.__rollhashbase, HASH_MOD), HASH_MOD)
        return(curhash,matchlen)    
        
    def addToken(self, curhash, tokendata):
        thash = self.getTokenHash(tokendata[3])
        curhash = int_mod(curhash * HASH_BASE, HASH_MOD)
        curhash = int_mod(curhash + thash, HASH_MOD)
        self.tokenqueue.append((thash,tokendata))
        return(curhash)

    def findMatches(self,curhash,tokendata1,tknzr):
        maxmatchlen=0
        matches = self.matchstore.getHashMatch(curhash)
        if( matches!= None):
            #print "queue string %s" % ' '.join([tkn[1][3] for tkn in self.tokenqueue])
            #print "hash =%d match count = %d" % (curhash, len(matches))
            #print "curpos = %s" % str(tokendata1)
            assert(tknzr.srcfile== tokendata1[0])
            
            for tokendata2 in matches:
                matchlen,sha1_hash,match_end1,match_end2 =self.findMatchLength(tknzr,tokendata1,tokendata2)
                
                if(matchlen >= self.patternsize):
                    #add the exact match to match store.
                    self.matchstore.addExactMatch(matchlen,sha1_hash,tokendata1,match_end1,tokendata2,match_end2)
                    maxmatchlen =max(maxmatchlen,matchlen)
        return(maxmatchlen)
        
    def findMatchLength(self, tknzr1,tokendata1, tokendata2):
        matchend1 = None
        matchend2 = None
        matchlen = 0
        sha1_hash = None

        #make a basic sanity check token value is same
        #if the filename is same then distance between the token positions has to be at least patternsize
        #   and the line numbers cannot be same
        if( tokendata1[3] == tokendata2[3]
                and (tokendata1[0]!=tokendata2[0]
                     or ((abs(tokendata1[2]-tokendata2[2])>self.patternsize) and tokendata1[1]>tokendata2[1]))):

            tknzr2 = tknzr1
                
            if( tokendata2[0] != tokendata1[0]): #filenames are different, get the different tokenizer
                srcfile2 = tokendata2[0]
                tknzr2 = self.getTokanizer(srcfile2)

            assert(tknzr1.srcfile== tokendata1[0])
            assert(tknzr2.srcfile== tokendata2[0])
            sha1 = hashlib.sha1()
                        
            for matchdata1, matchdata2 in izip(tknzr1.get_tokens_frompos(tokendata1[2]),tknzr2.get_tokens_frompos(tokendata2[2])):
                if( matchdata1[3] != matchdata2[3]):                    
                    break
                sha1.update(matchdata1[3])
                matchend1 = matchdata1
                matchend2 = matchdata2
                matchlen = matchlen+1
            sha1_hash = sha1.digest()
            
        return(matchlen,sha1_hash, matchend1,matchend2)

    
    def getTokanizer(self,srcfile):
        '''
        get the tokenizer for the given source file.
        '''
        tknizer = self.tokenizers.get(srcfile)
        if(tknizer == None):
            tknizer = tokenizer.Tokenizer(srcfile, fuzzy=self.fuzzy)
            self.tokenizers[srcfile] = tknizer
        assert(tknizer.srcfile == srcfile)
        return(tknizer)
    
            
        
        