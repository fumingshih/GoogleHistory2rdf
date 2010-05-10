'''
Created on Apr 22, 2010
This will read the meta table from a sqlite file of firefox3 browser, and create ontology file 
and also the triple file
@author: fuming
'''

from sqlalchemy import create_engine
from sqlite3 import dbapi2 as sqlite
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from surf import *
from rdflib.URIRef import URIRef
from rdflib.Graph import Graph
from rdflib.Literal import Literal
import os,sys
from getopt import getopt

engine = create_engine('sqlite:///places.sqlite', module=sqlite)
Base = declarative_base()


Session = sessionmaker(bind=engine)
session = Session()
places = []
histories = []

# The path of the output folder to save the triples
outdir = "output/"
    
store = Store(  reader='rdflib',
                writer='rdflib',
                rdflib_store = 'IOMemory')
    
ns.register(bhistory='http://foolme.csail.mit.edu/ns/browser-history#')
ns.register(bplace='http://foolme.csail.mit.edu/ns/browser-place#')
ns.register(bbehavior='http://foolme.csail.mit.edu/ns/browsing-behavior#')
ns.register(bplace_data='http://foolme.csail.mit.edu/lod/browser-place#')
ns.register(bhistory_data='http://foolme.csail.mit.edu/lod/browser-history#')

def queryAll():
#
#    for place in session.query(Place).all():
#        places.append(place)

    for history in session.query(History).all():
        histories.append(history)
  

def createPlaceTriples():
    
    store.clear()
    #store.add_triple(ns.HISTORY.s1,ns.RDF.about,ns.BROW_HISTORY)
    #print store.writer.graph.serialize(format="n3")
#    place = places[0]
    for place in places:
        id = str(place.id)
        store.add_triple(ns.BPLACE_DATA[id],ns.RDF['about'], ns.BPLACE['place'])
        store.add_triple(ns.BPLACE_DATA[id],ns.BPLACE['url'], Literal(place.url))
        store.add_triple(ns.BPLACE_DATA[id],ns.BPLACE['title'], Literal(place.title))
        store.add_triple(ns.BPLACE_DATA[id],ns.BPLACE['visitCount'], Literal(place.visit_count))
        store.add_triple(ns.BPLACE_DATA[id],ns.BPLACE['hidden'], Literal(place.hidden))
        store.add_triple(ns.BPLACE_DATA[id],ns.BPLACE['typed'], Literal(place.typed))
        store.add_triple(ns.BPLACE_DATA[id],ns.BPLACE['lastVisitDate'], Literal(place.last_visit_date))
 
 
    triples = store.writer.graph.serialize(format="n3")
    print "done with serialization"
    
    triples =  "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> ." + triples
    triples = triples.replace("<http://www.w3.org/2001/XMLSchema#long>","xsd:long")
    triples = triples.replace("<http://www.w3.org/2001/XMLSchema#integer","xsd:integer")
   
    #I don't like the long namespace, and don't know why rdflib only substitue pred. with shorter ns naming in the triple
    writeTriples(triples,"browser_place_data.n3")


def createHistoryTriples():
    store.clear()
    
    for history in histories:
        id = str(history.id)
        store.add_triple(ns.BHISTORY_DATA[id],ns.RDF['about'], ns.BHISTORY['history'])
        store.add_triple(ns.BHISTORY_DATA[id],ns.BHISTORY['from'], 
                         ns.BHISTORY_DATA[str(history.from_visit)])
        #if the history.form_visit is 0, then it means it's not from any other link, not a follow through link
        store.add_triple(ns.BHISTORY_DATA[id],ns.BHISTORY['place_id'], ns.BPLACE_DATA[str(history.place_id)])
        store.add_triple(ns.BHISTORY_DATA[id],ns.BHISTORY['visit_date'], Literal(history.visit_date))
        store.add_triple(ns.BHISTORY_DATA[id], getVisitRelation(history.visit_type), ns.BPLACE_DATA[str(history.place_id)])
        
    triples = store.writer.graph.serialize(format="n3")
    print "done with serialization"
    
    triples =  "@prefix xsd: <http://www.w3.org/2001/XMLSchema#>." + triples
    triples = triples.replace("<http://www.w3.org/2001/XMLSchema#long>","xsd:long")
    triples = triples.replace("<http://www.w3.org/2001/XMLSchema#integer","xsd:integer")

    writeTriples(triples,"browser_history_data.n3")


def getVisitRelation(visit_type):

    types = {
             1:ns.BBEHAVIOR['followed'],
             2:ns.BBEHAVIOR['fromhistory'],
             3:ns.BBEHAVIOR['bookmark'],
             4:ns.BBEHAVIOR['embedded'],
             5:ns.BBEHAVIOR['redirect'],
             6:ns.BBEHAVIOR['tmpRedirect'],
             7:ns.BBEHAVIOR['download']             
             }

    return types[visit_type]
    
    
    
        
def writeTriples(triples,filename):
    print "writing to file"
    
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    file = open(outdir+ filename,'w')
    file.write(triples)
    file.close()

class Place(Base):
    __tablename__ = 'moz_places'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    title =  Column(String)
    rev_host = Column(String)
    visit_count = Column(Integer)
    hidden = Column(Integer)
    typed = Column(Integer)
    favicon_id = Column(Integer)
    frecency = Column(Integer)
    last_visit_date = Column(Integer)
    
    def __init__(self,url,title,rev_host,visit_count,hidden,typed,favicon_id,\
                 frecency,last_visit_date):
        self.url = url
        self.title = title
        self.rev_host = rev_host
        self.visit_count = visit_count
        self.hidden = hidden
        self.typed = typed
        self.favicon_id = favicon_id
        self.frecency = frecency
        self.last_visit_date = last_visit_date
        
    def __repr__(self):
        return "<Places('%s','%s','%s','%s','%s','%s','%s','%s','%s')>" %\
                (self.url,self.title,self.rev_host,self.visit_count,self.hidden,\
                 self.typed,self.favicon_id,self.frecency,self.last_visit_date)
 
class History(Base):
    print ";"
    __tablename__ = 'moz_historyvisits'
    id = Column(Integer, primary_key=True)
    from_visit = Column(Integer)
    place_id = Column(Integer)
    visit_date = Column(Integer)
    visit_type = Column(Integer)
    session = Column(Integer)
    
    def __init__(self,from_visit,place_id,visit_date,visit_type,session):
        self.from_visit = from_visit
        self.place_id = place_id
        self.visit_date = visit_date
        self.visit_type = visit_type
        self.session = session
    def __repr__(self):
        return "<Hisotry('%s','%s','%s','%s','%s')>"%\
                (self.from_visit,self.place_id,self.visit_date,self.visit_type,self.session) 


def main(argv=None):
    global outdir
    if argv is None : argv = sys.argv
    try:
        opts, argvs = getopt(sys.argv[1:], 'ho:', ['start=', 'end=',])
        if opts :
            for o, a in opts :
                if o == '-h' :
                    print '''options 
            -h help
            -o <output folder> The output folder to store the triples. If omitted, it will save the triples to output/ folder'''
                elif o=='-o':
                    outdir = a
                    queryAll()
                    createHistoryTriples()
            
            
                    
        else:
            print 'type -h for help'
        
    except Exception, err:
        print err


if __name__ == '__main__':
    main()
