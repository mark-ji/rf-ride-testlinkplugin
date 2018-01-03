#coding: utf-8

from codecs import BOM_UTF8
import re
from . import cachedecorate
from _sqlite3 import Row

CRLF = u'\x0D\x0A'
SP=u'\x20'
NBSP = u'\xA0'


def is_string(item):
    return isinstance(item, basestring)


class FileReader(object):

    def __init__(self, path_or_file):
        if is_string(path_or_file):
            self._file = open(path_or_file, 'rb')
            self._close = True
        else:
            self._file = path_or_file
            self._close = False
        # IronPython handles BOM incorrectly if file not opened in binary mode:
        # https://ironpython.codeplex.com/workitem/34655
        if hasattr(self._file, 'mode') and self._file.mode != 'rb':
            raise ValueError('Only files in binary mode accepted.')

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if self._close:
            self._file.close()

    def read(self):
        return self._decode(self._file.read())

    def readlines(self):
        for index, line in enumerate(self._file.readlines()):
            yield self._decode(line, remove_bom=index == 0)

    def _decode(self, content, remove_bom=True):
        if remove_bom and content.startswith(BOM_UTF8):
            content = content[len(BOM_UTF8):]
        return content.decode('UTF-8')
    
class DataParser(object):
    
    def __init__(self,file):
        self.state=None
        self.file=file
        self.settings=[]
        self.variables=[]
        self.testcases=[]
        self.keywords=[]
        self.currentTC={}
    
    def read(self):
        for row in FileReader(self.file).readlines():
            if row.startswith('***'):
                if row.startswith('*** Settings ***'):
                    self.state='setting'
                elif row.startswith('*** Variables ***'):
                    self.state='variable'
                elif row.startswith('*** Test Cases ***'):
                    self.state='testcase'
                elif row.startswith('*** Keywords ***'):
                    self.state='keyword'
            elif self.state=='setting':
                self.settings.append(self._process_row(row))
            elif self.state=='variable':
                self.variables.append(self._process_row(row))
            elif self.state=='testcase':
                self._process_testcase(row)
            elif self.state=='keyword':
                self.keywords.append(self._process_row(row))
            else:
                continue
        return self.settings,self.variables,self.testcases,self.keywords
    
    def _process_testcase(self,row):
        if not row.startswith(4*' '):
            row=self._process_tc_row(row)
            if self.currentTC:
                self.testcases.append(self.currentTC)
            self.currentTC={}
            if row:
                self.currentTC['name']=row
                self.currentTC['scripts']=[]
        else:
            row=self._process_tc_row(row)
            if row and self.currentTC and self.currentTC.has_key('name'):
                self.currentTC['scripts'].append(self._scriptwithmark(row))
                
                
    def _scriptwithmark(self,script):
        return '<p>'+script+'</p>'

    def _process_tc_row(self, row):
        if NBSP in row:
            row = row.replace(NBSP, ' ')
        return row.strip()
    
    def _process_row(self, row):
        if NBSP in row:
            row = row.replace(NBSP, ' ')
        return row.rstrip() 
           
class FileWriter(object):
    def __init__(self,file,settings=None,variables=None,testcases=None,keywords=None):
        if not settings:
            settings=[]
        if not variables:
            variables=[]
        if not testcases:
            testcases=[]
        if not keywords:
            keywords=[]
        self.tcnum=0
            
        if not isinstance(settings,list) or not isinstance(variables,list) or not isinstance(keywords,list) or not isinstance(testcases,list):
            raise Exception('The para for FileWriter is not correct')
        
        if is_string(file):
            self._file = open(file, 'wb')
            self._close = True
        else:
            self._file = file
            self._close = False
        # IronPython handles BOM incorrectly if file not opened in binary mode:
        # https://ironpython.codeplex.com/workitem/34655
        if hasattr(self._file, 'mode') and self._file.mode != 'wb':
            raise ValueError('Only files in binary mode accepted.')
        
        try:
            self._writevariable(self._file, variables)
            self._writesetting(self._file, settings)
            self._writetestcase(self._file, testcases)
            self._writekeyword(self._file, keywords)
        except Exception,e:
            if self._close:
                self._file.close()
            print str(e)
            raise Exception('Error to write the testscripts to file')
        
        if self._close:
                self._file.close()
                    
    def _encode(self, content):
        return content.encode('UTF-8')
    
    def _writesetting(self,file,settings):
        if not settings:
            return
        SettingsHead='*** Settings ***'
        file.write(self._encode(SettingsHead))
        file.write(CRLF)
        for setting in settings:
            file.write(self._encode(setting))
            file.write(CRLF)
        file.write(CRLF)
        
    def _writevariable(self,file,variables):
        if not variables:
            return
        VariablesHead='*** Variables ***'
        file.write(self._encode(VariablesHead))
        file.write(CRLF)
        for variable in variables:
            file.write(self._encode(variable))
            file.write(CRLF)
        file.write(CRLF)
            
    def _writekeyword(self,file,keywords):
        if not keywords:
            return
        KeywordsHead='*** Keywords ***'
        file.write(self._encode(KeywordsHead))
        file.write(CRLF)
        for keyword in keywords:
            file.write(self._encode(keyword))
            file.write(CRLF)
        file.write(CRLF)
            
    def _writetestcase(self,file,testcases):
        if not testcases:
            return
        TestcasesHead='*** Test Cases ***'
        file.write(self._encode(TestcasesHead))
        file.write(CRLF)
        for testcase in testcases:
            file.write(self._encode(testcase['name']))
            file.write(CRLF)
            for script in testcase['scripts']:
                script=4*' '+script
                file.write(self._encode(script))
                file.write(CRLF)
            file.write(CRLF)
            self.tcnum += 1   
                
class TCInfoProcess(object):
    def __init__(self,testcaseinfo):
        #self.testcaseinfo=self._decode(testcaseinfo)
        self.testcaseinfo=testcaseinfo
    
    #decorate,save the name and the full external id in the dictionary structure
    @cachedecorate.storecache    
    def parseinfo(self):
        name=self.testcaseinfo[0]['name']
        id=self.testcaseinfo[0]['id']
        external_id=self.testcaseinfo[0]['full_tc_external_id']
        summary=self.testcaseinfo[0]['summary']
        return name,id,external_id,summary
    
    def getScripts(self):
        testcase={}
        name,id,external_id,summary=self.parseinfo()
        testcase['name']=name
        testcase['scripts']=self._scriptswithoutmark(summary)
        return testcase
    
    def _scriptswithoutmark(self,content):
        scriptsHead='<p>Scripts:</p>'
        headlen=len(scriptsHead)
        scripts=[]
        if not content:
            return []
        pos = content.find(scriptsHead)
        if pos == -1:
            return []
        script_content=content[pos+headlen:]
        pattern=re.compile(r'<p>(.*?)</p>')
        scripts=pattern.findall(script_content)
        return scripts
           
    def _decode(self, content):
        return content.decode('UTF-8')        

class TSInfoProcess(object):
    def __init__(self,tsinfo):
        self.ts_details=''
        if tsinfo.has_key('details'):
            #self.ts_details=tsinfo['details'].decode('UTF-8')
            self.ts_details=tsinfo['details']
        else:
            raise Exception('wrong test suite information')
        
        
    def parsedetail(self):
        settings=[]
        variables=[]
        keywords=[]
        scripts=[]
        state=''
        scripts_pos=self.ts_details.find('<p>Scripts:</p>')
        if scripts_pos == -1:
            return settings,variables,keywords
        scripts=self._getmembers(self.ts_details[scripts_pos:])
        for script in scripts:
            if script.strip() == '***Settings***':
                state='S'
            elif script.strip() == '***Variables***':
                state='V'
            elif script.strip() == '***Keywords***':
                state='K'
            elif state=='S':
                settings.append(script.strip())
            elif state=='V':
                variables.append(script.strip())
            elif state=='K':
                keywords.append(script.strip())
            else:
                continue
        return settings,variables,keywords

    def _getmembers(self,str):
        members=[]
        pattern=re.compile(r'<p>(.*?)</p>')
        members=pattern.findall(str)
        return members

class TSScriptToTL(object):
    #list to scripts string
    def __init__(self,settings=None,variables=None,keywords=None):
        if settings:
            self.settings=settings
        else:
            self.settings=[]
        if variables:
            self.variables=variables
        else:
            self.variables=[]
        if keywords:
            self.keywords=keywords
        else:
            self.keywords=[]
    
    def OrginizeTSScripts(self):
        scripts=''
        scriptshead='<p>Scripts:</p>'
        settingshead='<p>***Settings***</p>'
        variableshead='<p>***Variables***</p>'
        keywordshead='<p>***Keywords***</p>'
        settingscript=''
        variablescript=''
        keywordscript=''
        
        for setting in self.settings:
            settingscript += self._stringwithmark(setting)
            
        for variable in self.variables:
            variablescript += self._stringwithmark(variable)
            
        for keyword in self.keywords:
            keywordscript += self._stringwithmark(keyword)
            
        scripts = scriptshead + settingshead + settingscript + variableshead + variablescript + keywordshead + keywordscript
        return scripts   
        
    def _stringwithmark(self,str):
        return '<p>'+str+'</p>'        
    
class TCScriptToTL(object):
    #list to scripts string
    def __init__(self,teststeps=None):
        if teststeps:
            self.teststeps=teststeps
        else:
            self.teststeps=[]
        
    def OrginizeTCScripts(self):
        scriptshead='<p>Scripts:</p>'
        scripts=''
        for teststep in self.teststeps:
            scripts += teststep
        
        if scripts:
            scripts = scriptshead + scripts
        return scripts
       
                
                
    