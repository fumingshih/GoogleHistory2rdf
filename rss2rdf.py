'''
Created on Apr 29, 2010
 
    This helps to tranform the rss search history into a RDF file
 
@author: fuming
'''
import feedparser  
from surf import *
from rdflib.URIRef import URIRef
from rdflib.Graph import Graph
from rdflib.Literal import Literal
import re
from datetime import datetime
from time import mktime
import os,sys
from getopt import getopt

store = Store(  reader='rdflib',
        writer='rdflib',
        rdflib_store = 'IOMemory')

ns.register(history='http://foolme.csail.mit.edu/ns/search-history#')
ns.register(ghistory='http://foolme.csail.mit.edu/lod/google-search#')

outdir = "data/"
indir = "./"

def rss2rdf(rsscontent):
    print "1"

    store.clear()
    query_guids = getAllQuery_guid(rsscontent)

    d = feedparser.parse(rsscontent)
    
    _idx = 0 # for accessing query_guid
    for item in d['entries']:
        print "*"
        title = _str(item.title)
        print "**"
        t = datetime.strptime(item.updated,"%a, %d %b %Y %H:%M:%S GMT") # get a datetime object
        unixtime = int(mktime(t.timetuple())+1e-6*t.microsecond)
        category = item.tags[0].term # this is the value of category in google's rss feed, specify if the time is a query or a result
        description = item.summary_detail.value
        print "***"
        id = str(item.id)
        link = item.link
        
        sourceURI = URIRef("http://foolme.csail.mit.edu/lod/google-search#"+id)
        # add common terms
        store.add_triple(sourceURI, ns.RDF['about'], ns.HISTORY['history'])
        store.add_triple(sourceURI, ns.HISTORY['link'], Literal(link))
        store.add_triple(sourceURI, ns.HISTORY['date'], Literal(unixtime))      
        print "****"
        # add term specific to query
        if(category == 'web query'):
            store.add_triple(sourceURI, ns.RDF['about'], ns.HISTORY['query'])
            store.add_triple(sourceURI, ns.HISTORY['queryTerm'], Literal(title))
            store.add_triple(sourceURI, ns.HISTORY['resultClicked'], Literal(description[0]))
            print "*****"
        if(category == 'web result'):
            store.add_triple(sourceURI, ns.RDF['about'], ns.HISTORY['result'])
            store.add_triple(sourceURI, ns.HISTORY['resultTitle'], Literal(title))
            smh_guid = query_guids[_idx]
            store.add_triple(sourceURI, ns.HISTORY['from'], ns.GHISTORY[smh_guid])
            _idx += 1
            print "*****--"
    print "2"
    triples = store.writer.graph.serialize(format="n3")

    print triples
    return triples

def _str(str):
    
    return str.encode('utf-8')

def writeFile(filename,triples):
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    file = open(outdir+'/%s.nt'%filename,'w')
    file.write(triples)
    file.close()

def getAllQuery_guid(rsscontent):
    '''
    If the feed item is a search result, it will contain something call <smh:query_guid>xxx</smh:query_guid>
    We try to parse them out independently, because feedparser does not provide this 
    
    '''
#    teststring = 'blahlah<smh:query_guid>pmyaRY30C6egsALC0cWBDw</smh:query_guid>blah blah\
#                blahblahblah<smh:query_guid>vNyYRbmRAZWgsALf8fWADw</smh:query_guid>blahblahhadsf'
#                    
    pattern = re.compile('<smh:query_guid>\S+</smh:query_guid>')
    
    query_guids = []
    results = re.findall(pattern,rsscontent)
    for r in results:
        r = r[r.find('>')+1:]
        r = r[:r.find('<')]
        query_guids.append(r)
    return query_guids;
    
def read_from_folder(indir):
    
    files  = os.listdir(indir)
    if not files:
        print "no file under this folder"
    for f in files:

        if(f[0]=='_'):
            break
        else:
            file = open(indir+f,'r')
            raw_data = file.read()
            triples = rss2rdf(raw_data)
            print 'write file%s: '%f
            writeFile(f[0:f.find('.xml')],triples)
            file.close()
            srcf = indir+f
            newf = indir+'_'+f
            os.rename(srcf,newf)
            print 'done'
            

def main(argv = None):

 
    global indir, outdir

    if argv is None : argv = sys.argv
    try:
        opts, argvs = getopt(sys.argv[1:], 'hf:o:', ['start=', 'end=',])
        if opts :
            for o, a in opts :
                if o == '-h' :
                    print '''options 
            -h help
            -f <folder> The folder to get rss google history. If omitted, it will search the current folder. 
            -o <output folder> The output folder to store the triples. If omitted, it will save the triples to data/ folder'''
                elif o=='-f' :
                    indir = a
                    read_from_folder(indir)
                elif o=='-o':
                    outdir = a
                    read_from_folder(indir)
            
            
                    
        else:
            print 'type -h for help'
        
    except Exception, err:
        print err
        
        


if __name__ == '__main__':
    main()

 
    
    
    

        