'''
Token Tag Cloud (TTC)
Create tag cloud of tokens used in source files. Tag size is based on the number of times token is used
and tag color is based on the type of token.

Copyright (C) 2009 Nitin Bhide (nitinbhide@gmail.com, nitinbhide@thinkingcraftsman.in)

This module is part of Thinking Craftsman Toolkit (TC Toolkit) and is released under the
New BSD License: http://www.opensource.org/licenses/bsd-license.php
TC Toolkit is hosted at http://code.google.com/p/tctoolkit/

'''

import string
import sys

from optparse import OptionParser

from thirdparty.templet import stringfunction
from tokentagcloud.tokentagcloud import *
from tctoolkitutil import readJsText,getJsDirPath,FileOrStdout

@stringfunction
def OutputTagCloud(tagcld, d3js_text, d3cloud_text):
    '''<!DOCTYPE html>
    <html>        
    <head>
    <meta charset="utf-8">
    <script>
        // Embedd the text of d3.js
        $d3js_text
    </script>
    <script>
        // Embedd the text of d3.layout.cloudjs
        $d3cloud_text
    </script>
    <style type="text/css">    
    .tagcloud { display:inline-block;}
    .colorscale { display:inline-block;vertical-align:top;}
    </style>
    </head>
    <body>
    <div>
        <h2 align="center">Language Keyword Tag Cloud</h2>
        <div>
            <div class="colorscale"></div>
            <div id="keyword" class="tagcloud"></div>        
        </div>
    </div>
    <hr/>
    <div>
        <h2 align="center">Names (classname, variable names) Tag Cloud</h2>
        <div>
            <div class="colorscale"></div>
            <div id="names" class="tagcloud"></div>
        </div>
    </div>
    <hr/>
    <div>
        <h2 align="center">Class Name/Function Name Tag Cloud</h2>
        <div>
            <div class="colorscale"></div>
            <div id="classnames" class="tagcloud"></div>
        </div>
    </div>
    <hr/>
    <div id="colorscale">
    </div>    
    <script>
        var minColor = 0, maxColor=0;
        // color scale is reversed ColorBrewer RdYlBu
        var colors =  ["#a50026", "#d73027","#f46d43","#fdae61","#fee090","#ffffbf",
                        "#e0f3f8","#abd9e9","#74add1","#4575b4","#313695"];
        console.log(colors);
        colors.reverse();
        var fill =  d3.scale.linear();
        fill.range(colors);
        
        function drawTagCloud(wordsAndFreq, selector, width, height)
        {
            //console.log("selector is " + selector);
            // Font size is calculated based on word frequency
            var minFreq = d3.min(wordsAndFreq, function(d) { return d.size});
            var maxFreq = d3.max(wordsAndFreq, function(d) { return d.size});
            
            var fontSize = d3.scale.log();
            fontSize.domain([minFreq, maxFreq]);
            fontSize.range([10,100])
            // color is calculated based on how many files the word is found
            minColor = d3.min(wordsAndFreq, function(d) { return d.color});
            maxColor = d3.max(wordsAndFreq, function(d) { return d.color});
            var step = (Math.log(maxColor+1)-Math.log(minColor))/colors.length;            
            fill.domain(d3.range(Math.log(minColor), Math.log(maxColor+1), step));
          
            d3.layout.cloud().size([width, height])
                .words(wordsAndFreq)
                .padding(5)            
                .font("Impact")
                .rotate(function() { return 0})
                .fontSize(function(d) { return fontSize(+d.size); })
                .on("end", draw)
                .start();
          
            function draw(words) {
               // console.log("calling draw");
              d3.select('body').select(selector).append("svg")
                  .attr("width", width)
                  .attr("height", height)
                .append("g")
                  .attr("transform", "translate("+width/2+","+height/2+")")
                .selectAll("text")
                  .data(words)
                .enter().append("text")
                  .style("font-size", function(d) { return d.size + "px"; })
                  .style("font-family", "Impact")
                  .style("fill", function(d, i) {
                    return fill(Math.log(d.color)); })
                  .attr("text-anchor", "middle")
                  .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                   })
                  .text(function(d) { return d.text;});
            }
        }
        
        function drawColorScale(clrscaleDivs, fill)
        {            
            var clrScale = clrscaleDivs.append('div').append('ul').style("list-style-type","none").style("margin",0).style("padding",0)
            clrScale = clrScale.selectAll();
            var range = fill.range().slice(0); // deep copy returned array
            range.reverse(); // show blue at bottom to red at top.            
             var legend = clrScale.data(range)
                .enter().append("li")                    
                    .style("background-color", function(d, i){return range[i];} )
                    .html('&nbsp;&nbsp;&nbsp;');
        }
        
        var width=900;
        var height = width*3.0/4.0;
        // Show the tag cloud for keywords
        var keywordsAndFreq = ${ tagcld.getJSON(filterFunc=KeywordFilter)};        
        drawTagCloud(keywordsAndFreq, "#keyword",width, height);
        // Show the tag cloud for names (class names, function names and variable names)
        var namesAndFreq = ${ tagcld.getJSON(filterFunc=NameFilter) }    ;        
        drawTagCloud(namesAndFreq, "#names",width, height);
        // Show the tag cloud for class names and function names only
        var classNamesAndFreq = ${ tagcld.getJSON(filterFunc=ClassFuncNameFilter) };        
        drawTagCloud(classNamesAndFreq, "#classnames",width, height);
        
        var clrScaleDivs = d3.select('body').selectAll('.colorscale');
        drawColorScale(clrScaleDivs, fill);
        
      </script>

    </body>
    </html>
    '''    


class D3SourceTagCloud(SourceCodeTagCloud):
    '''
    Generate source code tag cloud in HTML format
    '''    
    def __init__(self, dirname, pattern='*.c', lang=None):
        super(D3SourceTagCloud, self).__init__(dirname, pattern, lang)
                
    def getJSON(self, numWords=100, filterFunc=None):
        tagJsonStr = ''

        tagWordList = self.getTags(numWords, filterFunc)
                
        if( len(tagWordList) > 0):                                    
            #change the font size between "-2" to "+8" relative to current font size
            tagJsonStr = ','.join(["{text:'%s',size:%d, color:%d}" % (w, freq, self.getFileCount(w)) for w, freq in tagWordList])
        tagJsonStr = "[%s]" % tagJsonStr
        
        return(tagJsonStr)
    
    

def RunMain():
    usage = "usage: %prog [options] <directory name>"
    description = '''Token Tag Cloud (C) Nitin Bhide
    Token Tag cloud parses the source code files and displays three tag clouds.
    (1) Tag cloud of keyword
    (2) Tag cloud of class names and variable names
    (3) Tag cloud of class names and function names    
    The size of word is based on number of occurances of that 'token' in the various source code files
    The color of word is based on number of files that 'token' is found.
    '''
    parser = OptionParser(usage,description=description)

    parser.add_option("-p", "--pattern", dest="pattern", default='*.c',
                      help="create tag cloud of files matching the pattern. Default is '*.c' ")
    parser.add_option("-o", "--outfile", dest="outfile", default=None,
                      help="outfile name. Output to stdout if not specified")
    parser.add_option("-l", "--lang", dest="lang", default=None,
                      help="programming language. Pattern will be ignored if language is defined")
    
    (options, args) = parser.parse_args()
    
    if( len(args) < 1):
        parser.error( "Invalid number of arguments. Use ttc.py --help to see the details.")
    else:        
        dirname = args[0]
            
        tagcld = D3SourceTagCloud(dirname, pattern=options.pattern, lang=options.lang)
        jsdir = getJsDirPath()
        
        with FileOrStdout(options.outfile) as outf:
            #read the text of d3js file
            d3jstext = readJsText(jsdir, ["d3js", "d3.min.js"]);
            d3cloud_text = readJsText(jsdir, ["d3js", "d3.layout.cloud.js"]);
            outf.write(OutputTagCloud(tagcld,d3jstext, d3cloud_text))
                
        
if(__name__ == "__main__"):
    RunMain()
    
    