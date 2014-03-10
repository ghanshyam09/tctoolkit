'''
Code Duplication Detector
using the Rabin Karp algorithm to detect duplicates

Copyright (C) 2009 Nitin Bhide (nitinbhide@gmail.com, nitinbhide@thinkingcraftsman.in)

This module is part of Thinking Craftsman Toolkit (TC Toolkit).
and is released under the New BSD License: http://www.opensource.org/licenses/bsd-license.php
TC Toolkit is hosted at http://code.google.com/p/tctoolkit/
'''

from __future__ import with_statement

import sys
import logging

import string, os, datetime
import json
from optparse import OptionParser

from pygments import highlight
from pygments.formatters import HtmlFormatter

from tctoolkitutil.common import *
from thirdparty.templet import *
from codedupdetect import CodeDupDetect

class HtmlWriter(object):
    '''
    class to output the duplication information in html format
    '''
    def __init__(self, cddapp):
        self.cddapp = cddapp
        self.formatter = HtmlFormatter(encoding='utf-8')

    def getCssStyle(self):
        return self.formatter.get_style_defs('.highlight')

    def getMatches(self):
        return self.cddapp.getMatches()

    def write(self, fname):
        with open(fname, "w") as outf:
            outf.write(self.output())

    def getCooccuranceData(self):
        '''
        create a co-occurance data in JSON format.
        '''
        groups, nodes, links = self.cddapp.getCooccuranceData()
        nodelist = [None]* len(nodes)
        linklist = list()
        #create a list of node dictionaries
        assert(len(nodelist) == len(nodes))
        for node, index in nodes.iteritems():
            groupname = os.path.dirname(node)
            nodelist[index] = {'name':node, 'group':groups[groupname] }
        #create a list of link dictionaries
        for link, value in links.iteritems():
            source = link[0]
            target = link[1]
            linklist.append({ 'source':nodes[source], 'target':nodes[target], 'value':value})

        return json.dumps({ 'nodes':nodelist, 'links' : linklist})

    @stringfunction
    def outputCooccurenceMatrix(self):
        '''
        // Co-occurance matrix
        function drawCooccurrence(cooc_mat) {
            var margin = {top: 80, right: 0, bottom: 10, left: 80};                
            var width = cooc_mat.nodes.length*10;
            var height = width;

            var x = d3.scale.ordinal().rangeBands([0, width]),
                z = d3.scale.linear().domain([0, 4]).clamp(true),
                c = d3.scale.category10().domain(d3.range(10));

            var svg = d3.select("body").append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .style("margin-left", -margin.left + "px")
              .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
            
              var matrix = [],
                  nodes = cooc_mat.nodes,
                  n = nodes.length;

              // Compute index per node.
              nodes.forEach(function(node, i) {
                node.index = i;
                node.count = 0;
                matrix[i] = d3.range(n).map(function(j) { return {x: j, y: i, z: 0}; });
              });

              // Convert links to matrix; count character occurrences.
              cooc_mat.links.forEach(function(link) {
                matrix[link.source][link.target].z += link.value;
                matrix[link.target][link.source].z += link.value;
                matrix[link.source][link.source].z += link.value;
                matrix[link.target][link.target].z += link.value;
                nodes[link.source].count += link.value;
                nodes[link.target].count += link.value;
              });

              // Precompute the orders.
              var orders = {
                name: d3.range(n).sort(function(a, b) { return d3.ascending(nodes[a].name, nodes[b].name); }),
                count: d3.range(n).sort(function(a, b) { return nodes[b].count - nodes[a].count; }),
                group: d3.range(n).sort(function(a, b) { return nodes[b].group - nodes[a].group; })
              };

              // The default sort order.
              x.domain(orders.name);

              svg.append("rect")
                  .attr("class", "background")
                  .attr("width", width)
                  .attr("height", height);

              var row = svg.selectAll(".row")
                  .data(matrix)
                .enter().append("g")
                  .attr("class", "row")
                  .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
                  .each(row);

              row.append("line")
                  .attr("x2", width);

              row.append("text")
                  .attr("x", -6)
                  .attr("y", x.rangeBand() / 2)
                  .attr("dy", ".32em")
                  .attr("text-anchor", "end")
                  .text(function(d, i) { return nodes[i].name; });

              var column = svg.selectAll(".column")
                  .data(matrix)
                .enter().append("g")
                  .attr("class", "column")
                  .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });

              column.append("line")
                  .attr("x1", -width);

              column.append("text")
                  .attr("x", 6)
                  .attr("y", x.rangeBand() / 2)
                  .attr("dy", ".32em")
                  .attr("text-anchor", "start")
                  .text(function(d, i) { return nodes[i].name; });

              function row(row) {
                var cell = d3.select(this).selectAll(".cell")
                    .data(row.filter(function(d) { return d.z; }))
                  .enter().append("rect")
                    .attr("class", "cell")
                    .attr("x", function(d) { return x(d.x); })
                    .attr("width", x.rangeBand())
                    .attr("height", x.rangeBand())
                    .style("fill-opacity", function(d) { return z(d.z); })
                    .style("fill", function(d) { return nodes[d.x].group == nodes[d.y].group ? c(nodes[d.x].group) : null; })
                    .on("mouseover", mouseover)
                    .on("mouseout", mouseout);
              }

              function mouseover(p) {
                d3.selectAll(".row text").classed("active", function(d, i) { return i == p.y; });
                d3.selectAll(".column text").classed("active", function(d, i) { return i == p.x; });
              }

              function mouseout() {
                d3.selectAll("text").classed("active", false);
              }

              d3.select("#order").on("change", function() {
                clearTimeout(timeout);
                order(this.value);
              });

              function order(value) {
                x.domain(orders[value]);

                var t = svg.transition().duration(2500);

                t.selectAll(".row")
                    .delay(function(d, i) { return x(i) * 4; })
                    .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
                  .selectAll(".cell")
                    .delay(function(d) { return x(d.x) * 4; })
                    .attr("x", function(d) { return x(d.x); });

                t.selectAll(".column")
                    .delay(function(d, i) { return x(i) * 4; })
                    .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });
              }

              /*
              var timeout = setTimeout(function() {
                order("group");
                d3.select("#order").property("selectedIndex", 2).node().focus();
              }, 5000);
              */
            };

            //duplication co-occurance data
            var dupData = ${self.getCooccuranceData()};
            drawCooccurrence(dupData);
        '''
        #duplication co-occurance matrix data.
        # similar to http://bost.ocks.org/mike/miserables/

    @stringfunction
    def output(self):
        '''<!DOCTYPE html>
        <html>
            <head>
                <meta http-equiv="content-type" content="text/html;charset=utf-8">
                <style type="text/css">${self.getCssStyle()}</style>
                <script src="./thirdparty/javascript/d3js/d3.js"></script>
            </head>
            <body>
                <div>
                 ${[self.getMatchLink(i, match) for i, match in enumerate(self.getMatches())]}
                </div>
                <div>
                    ${[self.getMatchHtml(i, match) for i, match in enumerate(self.getMatches())]}
                </div>
            </body>
            <script>
            ${self.outputCooccurenceMatrix()}
            </script>
        </html>
        '''
    
    @stringfunction
    def getMatchLink(self, i, matchset):
        '''<a href="#match_$i">Match ${i+1}&nbsp;</a>'''

    @stringfunction
    def getMatchHtml(self, i, matchset):
        '''<div id="match_$i">
                <h1>MATCH ${i+1}</h1>
               <ul>
               ${[self.getMatchInfo(m) for m in matchset]}
               </ul>
               <div class="highlight">               
                    ${self.getSyntaxHighlightedSource(matchset)}
                    <a href="#">Up</a>
               </div>
           </div>
        '''

    @stringfunction
    def getMatchInfo(self, match):
        '''<li>${match.srcfile()}:${match.getStartLine()}-${match.getStartLine()+match.getLineCount()}</li>'''

    def getSyntaxHighlightedSource(self, matchset):                
        return  highlight(''.join(matchset.getMatchSource()),matchset.getSourceLexer(), self.formatter, outfile=None)
        

class CDDApp(object):
    def __init__(self, dirname, options):
        self.dirname=dirname
        self.options = options
        self.filelist = None
        self.matches = None
        self.dupsInFile = None

    def getFileList(self):
        if( self.filelist == None):
            if( self.options.pattern ==''):
                self.filelist = PreparePygmentsFileList(self.dirname)
            else:
                rawfilelist = GetDirFileList(self.dirname)
                self.filelist = fnmatch.filter(rawfilelist,self.options.pattern)
                
        return(self.filelist)

    def run(self):
        filelist = self.getFileList()        
        self.cdd = CodeDupDetect(filelist,self.options.minimum, fuzzy=self.options.fuzzy, min_lines=self.options.min_lines)
        
        if self.options.format.lower() == 'html':
            #self.cdd.html_output(self.options.filename)
            htmlwriter = HtmlWriter(self)            
            htmlwriter.write(self.options.filename)

        else:
            #assume that format is 'txt'.
            self.printDuplicates(self.options.filename)
            
        if self.options.comments:
            self.cdd.insert_comments(self.dirname)        
        
    def printDuplicates(self, filename):
        with FileOrStdout(filename) as output:
            exactmatch = self.cdd.printmatches(output)
            tm2 = datetime.datetime.now()            

    def foundMatches(self):
        '''
        return true if there is atleast one match found.
        '''
        matches = self.getMatches()
        return( len(matches) > 0)        
            
    def getMatches(self):
        if( self.matches == None):
            exactmatches = self.cdd.findcopies()
            self.matches = sorted(exactmatches,reverse=True,key=lambda x:x.matchedlines)
        return(self.matches)
    
    def getCooccuranceData(self):
        return self.cdd.getCooccuranceData(self.dirname)

                                  
def RunMain():
    usage = "usage: %prog [options] <directory name>"
    description = """Code Duplication Detector. (C) Nitin Bhide nitinbhide@thinkingcraftsman.in
    Uses RabinKarp algorithm for finding exact duplicates. Fuzzy duplication detection support is
    experimental.
    """
    parser = OptionParser(usage,description=description)

    parser.add_option("-p", "--pattern", dest="pattern", default='',
                      help="find duplications with files matching the pattern")
    parser.add_option("-c", "--comments", action="store_true", dest="comments", default=False,
                      help="Mark duplicate patterns in-source with c-style comment.")
    parser.add_option("-r", "--report", dest="report", default=None,
                      help="Output html to given filename.This is essentially combination '-f html -o <filename>")
    parser.add_option("-o", "--out", dest="filename", default=None,
                      help="output file name. This is simple text file")
    parser.add_option("-f", "--fmt", dest="format", default=None,
                      help="output file format. If not specified, determined from outputfile extension. Supported : txt, html")
    parser.add_option("-m", "--minimum", dest="minimum", default=100, type="int",
                      help="Minimum token count for matched patterns.")
    parser.add_option("", "--lines", dest="min_lines", default=3, type="int",
                      help="Minimum line count for matched patterns.")
    parser.add_option("-z", "--fuzzy", dest="fuzzy", default=False, action="store_true",
                      help="Enable fuzzy matching (ignore variable names, function names etc).")
    parser.add_option("-g", "--log", dest="log", default=False, action="store_true",
                      help="Enable logging. Log file generated in the current directory as cdd.log")
    (options, args) = parser.parse_args()
    
    if options.report != None:
        options.format = 'html'
        options.filename = options.report

    if options.format == None:
        #auto detect the format based on the out file extension.
        options.format = 'txt'
        if options.filename:
            name, ext = os.path.splitext(options.filename)
            if ext in set(['.html', '.htm', '.xhtml']):
                options.format = 'html'

    if( len(args) < 1):
        print "Invalid number of arguments. Use cdd.py --help to see the details."
    else:
        if options.log == True:
            logging.basicConfig(filename='cdd.log',level=logging.INFO)
            
        dirname = args[0]
        app = CDDApp(dirname, options)
        with TimeIt(sys.stdout, "Time to calculate the duplicates") as timer:
            app.run()
            
if(__name__ == "__main__"):    
    RunMain()
    