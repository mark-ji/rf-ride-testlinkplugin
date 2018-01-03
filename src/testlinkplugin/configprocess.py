#-*- encoding=utf8 -*-

import ConfigParser
import os
import traceback
import chardet,codecs
import locale

CONFIG_FILE_DIRECTORY=os.path.dirname(os.path.realpath(__file__)) + '/'
CONFIG_FILE_NAME='config.ini'
CONFIG_INFO={'API_URL':('TestLinkAPI',str),'API_DEVKEY':('TestLinkAPI',str),'WORKSPACE':('TestLinkAPI',str),
             'PROXY':('TestLinkAPI',str),'ProjectName':('ProjectInfo',str),'TestPlanName':('ProjectInfo',str),
             'Tester':('ProjectInfo',str),'LoadScript':('ImportTCInfo',bool),'RefreshScript':('ImportTCInfo',bool),
             'ThreadNum':('UpdateTCInfo',int),'UpdateScript':('UpdateTCInfo',bool),'UpdateResult':('UpdateTCInfo',bool),
             'BuildName':('UpdateTCInfo',str),'PlatFormName':('UpdateTCInfo',str)}

def readFile(filePath):
    finput = open(filePath, "r")  
    str = finput.readline() + finput.readline() 
    codeType = chardet.detect(str)["encoding"]   
    finput.seek(0)
    if codeType == "UTF-8":  
        bom = codecs.BOM_UTF8[:].decode("utf-8")
        content = [line.decode(codeType)   
                   if line.decode(codeType)[:1] != bom  
                   else line.decode(codeType)[1:]   
                   for line in finput]
    elif codeType == 'ascii':
        currentType=locale.getpreferredencoding()
        content = [line.decode(currentType) for line in finput] 

    else:  
        content = [line.decode(codeType) for line in finput]  
    finput.close()  
    return ''.join(content)

class configprocess(object): 
    def __init__(self):
        self.file=CONFIG_FILE_DIRECTORY + CONFIG_FILE_NAME
        self.conf=ConfigParser.ConfigParser()
        if not self._configfile_is_exist():
            self._create_config_file()
        try:
            self._remove_config_BOM()
            self.read_config()
        except:
            traceback.print_exc()
            os.remove(self.conf)
            self._create_config_file()
            self.read_config()
    
    def _remove_config_BOM(self):
        with open(self.file,'r') as f:
            content=f.read()
        if content.startswith(codecs.BOM_UTF8):
            content=content[len(codecs.BOM_UTF8):]
            with open(self.file,'w+') as f:
                f.write(content)
                
        
    def _configfile_is_exist(self):
        return os.path.exists(self.file) and os.path.isfile(self.file)
        
    def read_config(self):
        self.conf.read(self.file)
        
    def read_item(self,item):
        if CONFIG_INFO.has_key(item):
            section=CONFIG_INFO[item][0]
            type=CONFIG_INFO[item][1]
            try:
                if type == str:
                    value=self.conf.get(section,item)
                elif type == int:
                    value=self.conf.getint(section,item)
                elif type == bool:
                    value=self.conf.getboolean(section,item)
                elif type == float:
                    value=self.conf.getfloat(section,item)
                else:
                    value=None
            except:
                traceback.print_exc()
                value=None
        else:
            print 'the item %s is not defined,cannot read from configure file' % item
            value=None
        return value

    def write_item(self,item,value):
        if CONFIG_INFO.has_key(item):
            section=CONFIG_INFO[item][0]
            if self.conf.has_section(section):
                self.conf.set(section,item,str(value))
            else:
                self.conf.add_section(section)
                self.conf.set(section,item,str(value))
            with open(self.file, 'w+') as configfile:
                self.conf.write(configfile)
        else:
            print 'the item %s is not defined,cannot write to configure file' % item

    def _create_config_file(self):
        sections=[]
        with open(self.file,'w+') as configfile:
            for key,value in CONFIG_INFO.items():
                if value[0] not in sections:
                    section_header='['+value[0]+']'
                    configfile.write(section_header)
                    configfile.write('\n')
                    sections.append(value[0])
                else:
                    continue
                
if __name__=='__main__':
    path='C:/Users/TOSHIBA/Desktop/2012/config.ini'
    print readFile(path)
    conftest=configprocess()
    value=conftest.read_item('API_URL')
    print value
    conftest.write_item('WORKSPACE','/12/12/12/12')
    print '' or conftest.read_item('WORKSPACE')
    conftest.write_item('WORKSPACE','/23/23/23/23')
    print conftest.read_item('WORKSPACE')