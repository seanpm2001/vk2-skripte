'''
Created on Jan 16, 2014

@author: mendt
'''
import logging, shutil, uuid, os
import xml.etree.ElementTree as ET
from settings import sqlalchemy_engine
from settings import templates, gn_settings
from src.csw.Namespaces import Namespaces
from src.csw.CswTransactionBinding import gn_transaction_insert
from src.models.Meta import initializeDb
from src.models.Messtischblatt import Messtischblatt
from src.models.MetadatenCore import MetadatenCore

def createServiceDescription(template, db, logger):
    logger.debug('Start creating service description')
    
    # create tempory copy
    mdServiceFile = os.path.join( os.path.dirname(template), str(uuid.uuid4()) + '.xml')
    shutil.copyfile(template, mdServiceFile)

    # Helper method which define the prefix of the namespaces
    for key in Namespaces:
        ET.register_namespace(key, Namespaces[key].strip('}').strip('{'))
        
    # parse xml template file
    xmlTree = ET.parse(mdServiceFile)
    xmlElementRoot = xmlTree.getroot()
    
    # search xml element srv:SV_ServiceIdentification
    searchHierarchy = [Namespaces['gmd']+'identificationInfo', Namespaces['srv']+'SV_ServiceIdentification']
    xmlElementServiceId = xmlElementRoot.find('/'.join(searchHierarchy))
        
    # get all messtischblaetter
    i = 0
    messtischblaetter = Messtischblatt.all(db)
    logger.debug('Start appending new messtischblatt resources')
    for messtischblatt in messtischblaetter:
        metadata_core = MetadatenCore.by_id(messtischblatt.id, db)
        appendCoupledResource(rootElement = xmlElementServiceId, resourceId = messtischblatt.dateiname, resourceTitle = metadata_core.titel)
        
        # break condition for testing
#         if i == 10:
#             break
#         i += 1

    logger.debug('Save modified file in %s.'%mdServiceFile)        
    
    #print 'Service document'
    #print '================'
    #print ET.tostring(xmlElementRoot, encoding='utf-8', method='xml')
    
    xmlTree.write(mdServiceFile, encoding="utf-8", xml_declaration=True)
    return mdServiceFile
            
    
   
def appendCoupledResource(rootElement, resourceId, resourceTitle):
    # at first create srv:coupledResource
    coupledResource = ET.Element(Namespaces['srv']+'coupledResource')
    sv_coupledresource = ET.Element(Namespaces['srv']+'SV_CoupledResource')
    
    operationName = ET.Element(Namespaces['srv']+'operationName')
    operationNameVale = ET.Element(Namespaces['gco']+'CharacterString')
    operationNameVale.text = resourceTitle
    
    identifier = ET.Element(Namespaces['srv']+'identifier')
    identifierValue = ET.Element(Namespaces['gco']+'CharacterString')
    identifierValue.text = resourceId
        
    operationName.append(operationNameVale)
    identifier.append(identifierValue)
    sv_coupledresource.append(operationName)
    sv_coupledresource.append(identifier)
    coupledResource.append(sv_coupledresource)
    rootElement.append(coupledResource)
    
    # at last create and append srv:operatesOn
    operatesOn = ET.Element(Namespaces['srv']+'operatesOn', attrib = {'uuidref':resourceId})
    rootElement.append(operatesOn)   
    return rootElement

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    dbSession = initializeDb(sqlalchemy_engine)
    logger = logging.getLogger('sqlalchemy.engine')
    response = createServiceDescription(templates['service'], dbSession, logger)
    
    print 'Insert service file %s ...'%response
    gn_transaction_insert(response, gn_settings['gn_username'], gn_settings['gn_password'], logger)