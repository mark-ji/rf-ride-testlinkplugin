#coding: utf-8

import xlrd
import os
from codecs import BOM_UTF8
import StringIO
import testlink
import re

MANDATORY=1
OPTIONAL=0

LEVEL='level'
TS_NAME='test-suite name'
TS_DETAIL='test-suite details'
TS_ORDER='test-suite order'
TC_NAME='testcase name'
TC_IMPORTANCE='testcase importance'
TC_INTERNALID='testcase id'
TC_SUMMARY='testcase summary'
TC_PRECONDITION='testcase preconditions'
TC_STEP='testcase steps'
TC_RESULT='testcase expected result'
TC_EXECUTIONTYPE='testcase executiontype'
TC_ORDER='testcase order'
TC_STATUS='testcase status'
TC_AUTHOR='testcase authorlogin'
TC_CHECKDUP='testcase checkduplicatedname'
TC_ACTIONDUP='testcase actiononduplicatedname'
TC_ESTIMATETIME='testcase estimatedduration'
TC_TITLE=0
TS_ROW=1
TC_ROW=2


ALLPROPERTY={LEVEL: MANDATORY,TS_NAME: MANDATORY,TS_DETAIL: MANDATORY,TS_ORDER:OPTIONAL,
             TC_NAME: MANDATORY,TC_IMPORTANCE: OPTIONAL,TC_INTERNALID: OPTIONAL,
             TC_SUMMARY: OPTIONAL,TC_PRECONDITION: OPTIONAL, TC_STEP: MANDATORY,TC_RESULT:OPTIONAL,
             TC_EXECUTIONTYPE: OPTIONAL,TC_ORDER:OPTIONAL,TC_STATUS: OPTIONAL,TC_AUTHOR:MANDATORY,
             TC_CHECKDUP: OPTIONAL,TC_ACTIONDUP: OPTIONAL,TC_ESTIMATETIME: OPTIONAL}

MANDATORYPROP=[key for key in ALLPROPERTY if ALLPROPERTY[key] == MANDATORY]
TS_MANDATORYPROP=[key for key in ALLPROPERTY if ALLPROPERTY[key] == MANDATORY and (key.startswith('test-suite') or key == LEVEL)]
TC_MANDATORYPROP=[key for key in ALLPROPERTY if ALLPROPERTY[key] == MANDATORY and (key.startswith('testcase') or key == LEVEL)]

TSINTERFACE2PROP={'testsuitename':TS_NAME, 'details':TS_DETAIL,'order':TS_ORDER }
TCINTERFACE2PROP={'testcasename':TC_NAME,'authorlogin':TC_AUTHOR, 'summary':TC_SUMMARY, 
                  'steps':TC_STEP,'results':TC_RESULT,'preconditions':TC_PRECONDITION, 'importance':TC_IMPORTANCE, 
                  'executiontype':TC_EXECUTIONTYPE, 'order':TC_ORDER, 'internalid':TC_INTERNALID,
                   'checkduplicatedname':TC_CHECKDUP, 'actiononduplicatedname':TC_ACTIONDUP,
                 'status':TC_STATUS, 'estimatedexecduration':TC_ESTIMATETIME}

TESTCASE_STATUS={'draft':1,'readyForReview':2,'reviewInProgress':3, 'rework':4,
                 'obsolete':5, 'future':6, 'final':7,'default':1}
TESTCASE_IMPORTANCE_LEVEL={'low':1,'medium':2,'high':3,'default':1}
TESTCASE_EXECUTION_TYPE={'manual':1,'automatic':2,'default':1}
ORDER={'destination position top':1,'destination position bottom':2,'default':2}

class IndexOutofRange(Exception):
    pass

class RowIndexOutofRange(Exception):
    pass

class TitleDuplication(Exception):
    pass

class RowValueInvalid(Exception):
    pass

class TitlesNotFull(Exception):
    pass

class TestCaseItemNotFull(Exception):
    pass

class TestSuiteItemNotFull(Exception):
    pass

class TCLevelError(Exception):
    pass

class TSLevelError(Exception):
    pass

class TSPARAException(Exception):
    pass

class TCPARAException(Exception):
    pass

class TCRSPException(Exception):
    pass

class TSRSPException(Exception):
    pass

class TSDuplication(Exception):
    pass

class ExcelReader(object):
    def __init__(self,filepath):
        self.filepath=filepath
        self.data=self._open_excel()
        
    def _open_excel(self):
        data=xlrd.open_workbook(self.filepath)
        return data
        
    def _open_sheet_index(self,index):
        if index > self.data.nsheets:
            raise IndexOutofRange('The sheet index is out of range')
        return self.data.sheet_by_index(index)
    
    def read_one_row(self,sheetindex,row_index):
        sheetdata=self._open_sheet_index(sheetindex)
        return self._read_row(sheetdata, row_index)
        
    def _read_row(self,sheetdata,row_index):
        nrows=sheetdata.nrows
        ncols=sheetdata.ncols
        
        if row_index > (nrows-1):
            raise RowIndexOutofRange('The Row Index Value is out of range')
        return sheetdata.row_values(row_index,start_colx=0,end_colx=ncols)
        
    def read_all_row(self,sheet_index,beginrow):
        sheetdata=self._open_sheet_index(sheet_index)
        nrows=sheetdata.nrows
        if beginrow > (nrows-1):
            raise RowIndexOutofRange('The Row Index Value is out of range') 
        for row in range(beginrow,nrows):
            yield self._read_row(sheetdata,row)
                  
    def process_title_seq(self,sheet_index):
        titles=self.read_one_row(sheet_index,0)
        title_seq={}
        for col in range(0,len(titles)):
            #if chars, str.lower()
            #else mandarin, str._decode('utf-8')
            titlevalue=self._decode(titles[col])
            if ALLPROPERTY.has_key(titlevalue):
                if not title_seq.has_key(titlevalue):
                    title_seq[titlevalue]=col
                else:
                    raise TitleDuplication('Some Titles in Excel file duplicated, please check')
        
        for item in MANDATORYPROP:
            if not title_seq.has_key(item):
                str='the item [%s] are missing, please check' % item
                raise TitlesNotFull(str)
        return title_seq
        
    def _decode(self, content):
        return content.decode('UTF-8')

class RowProcess(object):
    def __init__(self,row_value,title_seq):
        self.row_value=row_value
        self.title_seq=title_seq
        self.rowinfo=self._check_Info()
        
        if TS_ROW == self.rowinfo:
            self._check_mandatory_forts()
        else:
            self._check_mandatory_fortc()
             
    def _check_Info(self):
        tsnamecolindex=self.title_seq[TS_NAME]
        tcnamecolindex=self.title_seq[TC_NAME]
        
        if self.row_value[tsnamecolindex] and not self.row_value[tcnamecolindex]:
            return TS_ROW
        
        elif not self.row_value[tsnamecolindex] and self.row_value[tcnamecolindex]:
            return TC_ROW
        
        else:
            raise RowValueInvalid('The row value is invalid,abort')
        
    def _check_mandatory_fortc(self):
        for item in TC_MANDATORYPROP:
            item_index=self.title_seq[item]
            if not self.row_value[item_index]:
                str='The testcase has not [%s] item value' % item
                raise TestCaseItemNotFull(str)
        return True
        
    def _check_mandatory_forts(self):
        for item in TS_MANDATORYPROP:
            item_index=self.title_seq[item]
            if not self.row_value[item_index]:
                str='The testsuite has not [%s] item value' % item
                raise TestSuiteItemNotFull(str)
        return True
    
    def getleveldeep(self):
        index=self.title_seq[LEVEL]
        #check the level value
        return len(self.row_value[index])
            
    def gettsdetails(self):
        index=self.title_seq[TS_DETAIL]
        return self.row_value[index]
    
    def gettsname(self):
        index=self.title_seq[TS_NAME]
        return self.row_value[index]
    
    #steps is a list with dictionaries
    def gettcsteps(self):
        step_result=[]
        steps=self.gettcitemvalue('steps')
        results=self.gettcitemvalue('results')
        steps_list=self._strtolist(steps)
        results_list=self._strtolist(results)
        steps_list_len=len(steps_list)
        results_list_len=len(results_list)
        for index in range(len(steps_list)):
            step_index={}
            step_index['step_number']=index+1
            step_index['actions']=steps_list[index]
            if index+1 > results_list_len:
                step_index['expected_results']=''
            else:
                step_index['expected_results']=results_list[index]
            step_index['execution_type']=self.gettcexecutiontype()
            step_result.append(step_index)
        if steps_list_len < results_list_len:
            step_result[steps_list_len-1]['expected_results'] += (';'+';'.join(results_list[steps_list_len:]))
        return step_result
            
    @staticmethod        
    def _strtolist(str):
        tmp_list=[]
        if str:
            buf = StringIO.StringIO(str)
            for line in buf.readlines():
                tmp_list.append(line.strip())
        return tmp_list
                
    def gettcimportance(self):
        result=self.gettcitemvalue('importance')
        if result:
            if TESTCASE_IMPORTANCE_LEVEL.has_key(result):
                return TESTCASE_IMPORTANCE_LEVEL[result]
        return TESTCASE_IMPORTANCE_LEVEL['default']

    def gettcstatus(self):
        result=self.gettcitemvalue('status')
        if result:
            if TESTCASE_STATUS.has_key(result):
                return TESTCASE_STATUS[result]
        return TESTCASE_STATUS['default']
    
    def gettcexecutiontype(self):
        result=self.gettcitemvalue('executiontype')
        if result:
            if TESTCASE_EXECUTION_TYPE.has_key(result):
                return TESTCASE_EXECUTION_TYPE[result]
        return TESTCASE_STATUS['default']
    
    def gettcorder(self):
        result=self.gettcitemvalue('order')
        if result:
            if ORDER.has_key(result):
                return ORDER[result]
        return ORDER['default']
    
    def gettsorder(self):
        result=self.gettsitemvalue('order')
        if result:
            if ORDER.has_key(result):
                return ORDER[result]
        return ORDER['default']
    
    def gettsitemvalue(self,tsitem):
        if not TSINTERFACE2PROP.has_key(tsitem):
            raise TSPARAException('The item name is not correctly')
        item=TSINTERFACE2PROP[tsitem]
        if not self.title_seq.has_key(item):
            return ''
        index=self.title_seq[item]
        return self.row_value[index]
    
    def gettcitemvalue(self,tcitem):
        if not TCINTERFACE2PROP.has_key(tcitem):
            raise TCPARAException('The item name is not correctly')
        item=TCINTERFACE2PROP[tcitem]
        if not self.title_seq.has_key(item):
            return ''
        index=self.title_seq[item]
        return self.row_value[index]

class ImportTSandTC(object):
    def __init__(self,testlinkAPI,path,sheetindex,projectname):
        self.excel=ExcelReader(path)
        self.title_seq=self.excel.process_title_seq(sheetindex)
        self.testlinkAPI=testlinkAPI
        self.sheetindex=sheetindex
        self.projectname=projectname
        self.projectid=self._getProjectIDforName()
        self.currentTS=[]
        
    def _ImportTS(self,rowobj):
        parentid=self._find_parent_for_ts(rowobj)
        tsname=rowobj.gettsitemvalue('testsuitename')
        details=rowobj.gettsitemvalue('details')
        order=rowobj.gettsorder()
        if parentid == '':
            rsp=self.testlinkAPI.createTestSuite(self.projectid,tsname,details,order=order,checkduplicatedname=True)
        else:
            rsp=self.testlinkAPI.createTestSuite(self.projectid,tsname,details,parentid=parentid,order=order,checkduplicatedname=True)
        return self._parse_ts_rsp(rsp)
    
    def _ImportTC(self,rowobj):
        parentid=self._find_parent_for_tc(rowobj)
        tcname=rowobj.gettcitemvalue('testcasename')
        author=rowobj.gettcitemvalue('authorlogin')
        summary=rowobj.gettcitemvalue('summary')
        steps=rowobj.gettcsteps()
        precondition=rowobj.gettcitemvalue('preconditions')
        importance=rowobj.gettcimportance()
        executiontype=rowobj.gettcexecutiontype()
        order=rowobj.gettcorder()
        checkduplicatedname=rowobj.gettcitemvalue('checkduplicatedname')
        actiononduplicatedname=rowobj.gettcitemvalue('actiononduplicatedname')
        status=rowobj.gettcstatus()
        estimatedexecduration=rowobj.gettcitemvalue('estimatedexecduration')
        rsp=self.testlinkAPI.createTestCase(tcname,parentid,self.projectid,author,summary,
                                            steps=steps,preconditions=precondition,importance=importance,
                                            executiontype=executiontype,order=order,checkduplicatedname=checkduplicatedname,
                                            actiononduplicatedname=actiononduplicatedname,status=status,estimatedexecduration=estimatedexecduration)
        return self._parse_tc_rsp(rsp)
    
    #decorate
    def _getTSIDforName(self,ts_name):
        rsp=self.testlinkAPI.getTestProjectByName(self.projectname)
        prefix=rsp['prefix']
        ts_id=self.testlinkAPI.getTestSuite(ts_name,prefix)[0]['id']
        return ts_id
    
    def _getProjectIDforName(self):
        rsp=self.testlinkAPI.getTestProjectByName(self.projectname)
        project_id=rsp['id']
        return project_id
    
    def process(self):
        index=1
        for row in self.excel.read_all_row(self.sheetindex, 1):
            try:
                rowobj=RowProcess(row,self.title_seq)
                if rowobj.rowinfo == TS_ROW:
                    self._ImportTS(rowobj)
                    index=index+1
                elif rowobj.rowinfo == TC_ROW:
                    self._ImportTC(rowobj)
                    index=index+1
            except (IndexOutofRange,RowIndexOutofRange,TitlesNotFull,
                    TestSuiteItemNotFull,TSLevelError,TSPARAException,RowValueInvalid,TSRSPException),reason:
                print 'the %s row,the failed reason to abort the process: %s' % (index,reason)
                break
            
            except (TSDuplication,TestCaseItemNotFull,TCLevelError,TCPARAException,TCRSPException),reason:
                index = index + 1
                print 'the %s row,the failed reason to continue the next row: %s' % (index,reason)
                continue
            
            except Exception,reason:
                print 'the %s row,the other failed reason to abort the process: %s' % (index,reason)
                break
            
        
    def _fetch_parentid_for_ts(self,ts_name):
        if not self.currentTS:
            self.currentTS.append(ts_name)
            parent_id=''
        else:
            parentts=self.currentTS[-1]
            parent_id=self._getTSIDforName(parentts)
            self.currentTS.append(ts_name)
        return parent_id
    
   
    def _find_parent_for_ts(self,row):
        tsdeep=row.getleveldeep()
        if tsdeep > len(self.currentTS) + 1:
            raise TSLevelError('The testsuite level is wrong, abort')
        elif tsdeep == len(self.currentTS) + 1:
            return self._fetch_parentid_for_ts(row.gettsname())
        elif tsdeep <= len(self.currentTS):
            self._pop_list(self.currentTS, (len(self.currentTS)-tsdeep+1))
            return self._fetch_parentid_for_ts(row.gettsname())
                
    def _find_parent_for_tc(self,row):
        if (row.getleveldeep() != len(self.currentTS) + 1 ) or not self.currentTS:
                raise TCLevelError('The testcase level is wrong, skip it')
        parentts=self.currentTS[-1]
        parent_id=self._getTSIDforName(parentts)
        return parent_id
    
    def _find_parent_for_row(self,row):
        parentid=''
        if row.rowinfo == TC_ROW:
            parentid=self._find_parent_for_tc(row)
        elif row.rowinfo == TS_ROW:
            parentid=self._find_parent_for_ts(row)
        return parentid
    
    @staticmethod            
    def _pop_list(tmplist,num):
        while num:
            tmplist.pop()
            num = num -1
        return tmplist
            
            
    def _parse_tc_rsp(self,rsp):
        if isinstance(rsp, list):
            if rsp[0]['status'] and rsp[0]['message'].startswith('Success'):
                return True
            else:
                raise TCRSPException('While import the testcase,the error response from testlink')
        elif isinstance(rsp,dict) and rsp.has_key('msg'):
            str=rsp['msg']
            raise TCRSPException(str)
        else:
            raise TCRSPException('While import the testcase,the error response from testlink')
    
    def _parse_ts_rsp(self,rsp):
        if isinstance(rsp,list):
            if rsp[0]['status'] and rsp[0].has_key('id'):
                ts_id=rsp[0]['id']
                #save the ts_id to the cache
                return True
        if isinstance(rsp,dict) and rsp.has_key('msg'):
            str=rsp['msg']
            return TSDuplication(str)
            #raise TSRSPException(str)
        raise TSRSPException('While import the testsuite,the error response from testlink,abort')
            
            

if __name__=='__main__':
    path='C:/Users/TOSHIBA/Desktop/2012/testcaseexample-1.xls'
    '''
    reader=ExcelReader(path)
    print MANDATORYPROP
    print TC_MANDATORYPROP
    print TS_MANDATORYPROP
    gen=reader.read_all_row(0,0)
    for text in gen:
        print text
    print reader.process_title_seq(0)
    '''
    os.environ['TESTLINK_API_PYTHON_SERVER_URL'] = "http://192.168.1.200/testlink/lib/api/xmlrpc/v1/xmlrpc.php"
    os.environ['TESTLINK_API_PYTHON_DEVKEY'] = "63a71a1af47e7df26ed40e8533bb54da"
    project_name='test_for_autoupdate'
    tl_helper=testlink.TestLinkHelper()
    rf2testlinker=tl_helper.connect(testlink.TestlinkAPIClient)
    task=ImportTSandTC(rf2testlinker,path,0,project_name)
    task.process()
    
    
    
        
            
        
    