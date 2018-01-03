#coding: utf-8

import os.path
import sys
import re
from .dataprocess import DataParser,TSScriptToTL,TCScriptToTL
from .dataprocess import FileWriter,TCInfoProcess,TSInfoProcess
from . import cachedecorate
import time
from .parseresult import parseresult as XMLResultPaser
import wx
from .tracebackextend import full_exc_info
import traceback


def judge_dir(dir):
    if dir.endswith('/'):
        return dir
    else:
        return dir+'/'

def process_dir(dir):
    pattern=re.compile(r'[\\]+')
    repl='/'
    result=pattern.sub(repl,dir)
    return result

def process_tsname(ts_name):
    ts_temp_name=ts_name.strip()
    pattern=re.compile(r'[ ]+')
    repl='_'
    result=pattern.sub(repl,ts_temp_name)
    return result

class ParaError(Exception):
    pass

class LinkError(Exception):
    pass

class BuildException(Exception):
    pass

class PlatFormNameException(Exception):
    pass


class Node(object):
    nodes=[]
    def __init__(self,ts_id,ts_name,deep,node_dir,parent=None):
        self.parent=parent
        self.ts_id=ts_id
        self.ts_name=ts_name
        self.children=[]
        self.deep=deep
        self.isprojectroot=False
        self.node_dir=node_dir
        Node._add_node(self)
        
    def __str__(self):
        if self.ts_name:
            if self.deep == 0:
                return self.ts_name+'('+self.node_dir+')'
            return self.deep*4*'-'+'|'+self.ts_name+'('+self.node_dir+')'
        else:
            raise ParaError('No testsuite name, please the response from testlink')
 
    @classmethod
    def _add_node(cls,node):
        for item in cls.nodes:
            if node.ts_name == item.ts_name:
                return
        cls.nodes.append(node)
    
    @classmethod
    def clearAllNodes(cls):
        while cls.nodes:
            cls.nodes.pop()
            

 
class NodeProcessForProject(object):
    def __init__(self,projectname,ts_lists):
        self.ts_lists=ts_lists
        self.projectname=projectname
        
        if not self.ts_lists:
            raise ParaError('Can not get the testsuite lists')
        
    
    '''
    the method is for create root Node for projectname
    ts_lists is get by getTestSuitesForTestPlan
    '''   
    def create_rootnode(self):
        ts_id_list=[]
        for ts_list in self.ts_lists:
            ts_id_list.append(ts_list['id'])
            
        for ts_list in self.ts_lists:
            if ts_list['parent_id'] in ts_id_list:
                continue
            else:
                ts_root_id = ts_list['parent_id']
                ts_root_name=self.projectname
                ts_root_dir=process_tsname(self.projectname)+'/'
                break
        
        root_Node=Node(ts_root_id,ts_root_name,0,ts_root_dir)
        root_Node.isprojectroot=True
        return root_Node
    
    '''
    node can be projectname node and ts_lists will be get by getTestSuitesForTestPlan
    '''    
    def create_childnode(self,node,ts_lists):
        if not isinstance(node, Node) or not ts_lists:
            raise ParaError('testsuite info error, can not create the testsuites tree')
            
        for ts_list in ts_lists:
            if node.ts_id == ts_list['parent_id']:
                deep=node.deep+1
                current_node_tsid=ts_list['id']
                current_node_name=ts_list['name']
                current_node_dir=node.node_dir+process_tsname(current_node_name)+'/'
                childnode=Node(current_node_tsid,current_node_name,deep,current_node_dir,node)
                node.children.append(childnode)
                self.create_childnode(childnode, ts_lists)       
    
    '''
    node_list as [node.ts_name,[]]
    '''            
    def create_ts_tree(self,node,node_list):
        if not node.children:
            return
        for childnode in node.children:
            if not childnode.children:
                node_list[1].append(childnode.ts_name)
            else:
                current_list=[childnode.ts_name,[]]
                self.create_ts_tree(childnode,current_list)
                node_list[1].append(current_list)           

   
class NodeProcessForTS(object):
    def __init__(self,testlinkAPI,ts_name,workspace):
        self.testlinkAPI=testlinkAPI
        self.ts_name=ts_name
        self.workspace=workspace
        self.work_dir=None
        self.work_file=None
        self._gettsdirandfile()
        self.projectID=self._get_project_ID()
        self.projectName=self._get_project_Name()
        
    def _get_project_ID(self):
        return Node.nodes[0].ts_id
    
    def _get_project_Name(self):
        return Node.nodes[0].ts_name

    def _getnodeforname(self):
        for node in Node.nodes:
            if self.ts_name == node.ts_name:
                return node
        return None
    
    def _gettsidforname(self):
        node=self._getnodeforname()
        if node:
            return node.ts_id
        return None

    def _gettsdirandfile(self):
        node=self._getnodeforname()
        if node:
            self.work_dir=judge_dir(self.workspace)+node.node_dir
            self.work_file=self.work_dir+process_tsname(node.ts_name)+'.txt'
    
    def _create_dir(self):
        if self.work_dir:
            if os.path.exists(self.work_dir):
                return True
            else:
                try:
                    os.makedirs(self.work_dir)
                except Exception:
                    return False
                return True
        else:
            return False
    
    def _check_file_exist(self):
        if self.work_file:
            if os.path.exists(self.work_file) and os.path.isfile(self.work_file):
                return True
            return False
        else:
            return False
    
    def _getTCFromID(self,tc_id):
        TC_info=self.testlinkAPI.getTestCase(tc_id)
        return TC_info
    
    #decorate, get the full external id from the cache.otherwise get it from the testlink
    @cachedecorate.fetchcache        
    def get_tcfullextid(self,tc_name):
        tc_full_extid=self._get_tcfullextid_fromname(tc_name)
        return tc_full_extid
            
    #decorate,save the name and the full external id in the dictionary structure           
    def _get_tcfullextid_fromname(self,tc_name):
        #in different testsuites with the same testcase name
        #or in different project with the same testsuite name and the same testcase name
        tc_id=self.testlinkAPI.getTestCaseIDByName(tc_name,testsuitename=self.ts_name,testprojectname=self.projectName)[0]['id']
        tc_info=self._getTCFromID(tc_id)
        return TCInfoProcess(tc_info).parseinfo()[2]
                
class LoadScriptFromTS(NodeProcessForTS):
    def __init__(self,testlinkAPI,ts_name,workspace):
        NodeProcessForTS.__init__(self,testlinkAPI,ts_name,workspace)
        self.tc_id_lists=[]
        self.tcnum=0
    
    def _getTCIDfromTS(self):
        node=self._getnodeforname()
        if node:
            self.tc_id_lists=self.testlinkAPI.getTestCasesForTestSuite(testsuiteid=node.ts_id,deep=False,details='only_id')
                
        
    def _getautomatic(self,tc_info):
        if tc_info[0]['execution_type'] == '2':
            return True
        for step in tc_info[0]['steps']:
            if step['execution_type']=='2':
                return True
        return False
    
    #type(ts_info)=dict                
    def _getTSdetailsForID(self,ts_id):
        ts_info=self.testlinkAPI.getTestSuiteByID(ts_id)
        return ts_info
         
    def process(self):
        tsid=self._gettsidforname()
        tsinfo=self._getTSdetailsForID(tsid)
        settings,variables,keywords=TSInfoProcess(tsinfo).parsedetail()
        testcases=[]
        
        self._getTCIDfromTS()
        if not self.tc_id_lists:
            print 'the test-suite %s has no test-cases, return' % self.ts_name
            return
        for tc_id in self.tc_id_lists:
            tc_info=self._getTCFromID(tc_id)
            if self._getautomatic(tc_info):
                testcases.append(TCInfoProcess(tc_info).getScripts())
        
        if self._create_dir():
            if self._check_file_exist() and False:
                #according to the checkbox chosen
                pass
            else:
                fwprocess=FileWriter(self.work_file,settings=settings,variables=variables,testcases=testcases,keywords=keywords)
                self.tcnum=fwprocess.tcnum
                

class UpLoadScriptToTS(NodeProcessForTS):
    def __init__(self,testlinkAPI,ts_name,workspace):
        NodeProcessForTS.__init__(self,testlinkAPI,ts_name,workspace)
        self.tcnum=0
        self.ftcnum=0
        
    def process(self):
        if self._check_file_exist():
            settings,variables,testcases,keywords=DataParser(self.work_file).read()
            tsscript = TSScriptToTL(settings=settings,variables=variables,keywords=keywords).OrginizeTSScripts()
            self._UpdateScriptsToTS(tsscript)
            
            #testcases = [{name:script},]
            for testcase in testcases:
                name=testcase['name']
                scripts=TCScriptToTL(testcase['scripts']).OrginizeTCScripts()
                try:
                    self._UpdateScriptsToTC(name, scripts)
                    self.tcnum += 1
                except:
                    etype, value, tb=full_exc_info()
                    traceback.print_exception(etype, value, tb)
                    self.ftcnum += 1
        else:
            print 'the test-suite %s has no scripts file in the direcotry' % self.ts_name

    def process_with_feedback(self,dialog):
        if self._check_file_exist():
            settings,variables,testcases,keywords=DataParser(self.work_file).read()
            tsscript = TSScriptToTL(settings=settings,variables=variables,keywords=keywords).OrginizeTSScripts()
            self._UpdateScriptsToTS(tsscript)
            
            #testcases = [{name:script},]
            for testcase in testcases:
                name=testcase['name']
                scripts=TCScriptToTL(testcase['scripts']).OrginizeTCScripts()
                try:
                    self._UpdateScriptsToTC(name, scripts)
                    self.tcnum += 1
                    wx.CallAfter(dialog.RecordEInfo,name,'Success to update script')
                except:
                    etype, value, tb=full_exc_info()
                    traceback.print_exception(etype, value, tb)
                    reason=' '.join(traceback.format_exception_only(etype, value))
                    self.ftcnum += 1
                    wx.CallAfter(dialog.RecordEInfo,name,reason)
            wx.CallAfter(dialog.RecordEInfo,self.ts_name,'Finish to update script')
            wx.CallAfter(dialog.Update,1,0,0,self.tcnum,self.ftcnum)  
        else:
            print 'the test-suite %s has no scripts file in the direcotry' % self.ts_name
            wx.CallAfter(dialog.RecordEInfo,self.ts_name,'Skip to update script')
            wx.CallAfter(dialog.Update,1,0,0,0,0)
                
    def _UpdateScriptsToTS(self,scripts):
        self.testlinkAPI.updateTestSuite(self._gettsidforname(),testprojectid=self.projectID,details=scripts)
    
    def _UpdateScriptsToTC(self,tc_name,scripts):
        tc_full_extid=self.get_tcfullextid(tc_name)
        if tc_full_extid:
            self.testlinkAPI.updateTestCase(tc_full_extid,summary=scripts)
            
    def __call__(self,dialog=None):
        return self.process_with_feedback(dialog)    
        
class UpdateResultToTS(NodeProcessForTS):
    def __init__(self,testlinkAPI,ts_name,workspace,plan_name,plan_id,pf_name=None,build_name=None,user=None,overwrite=True):
        NodeProcessForTS.__init__(self,testlinkAPI,ts_name,workspace)
        self.plan_name=plan_name
        self.plan_id=plan_id
        #if build_name not present Build with higher internal ID will be used
        self.build_name=build_name
        self.pf_name=pf_name
        #if user is None,it will be used when writing execution
        self.user=user
        
        #currently , only support overwrite the content
        self.overwrite=overwrite
        self.tcnum=0
        self.ftcnum=0
            

    def _getbuildsforplan(self):
        builds=[]
        rsp=self.testlinkAPI.getBuildsForTestPlan(self.plan_id)
        if not rsp:
            return builds
        else:
            for item in rsp:
                if item['is_open'] == '1' and item['active'] == '1':
                    builds.append(item['name'])
            return builds
        
    def _getbuildidforname(self):
        rsp=self.testlinkAPI.getBuildsForTestPlan(self.plan_id)
        if rsp:
            for item in rsp:
                if item['name'] == self.build_name:
                    return item['id']
        
        return self._createbuildwithname(self.build_name)


    def _getlastestbuildforplan(self):
        try:
            rsp=self.testlinkAPI.getLatestBuildForTestPlan(self.plan_id)
        except:
            etype, value, tb=full_exc_info()
            traceback.print_exception(etype, value, tb)
            return None
        else:
            if not rsp:
                return None
            else:
                if rsp['is_open'] == '1' and rsp['active'] == '1':
                    return rsp['id']
                else:
                    return None

    
    def _checkplatform(self):
        #getTestPlanPlatforms,Returns the list of platforms associated to a given test plan
        rsp=self.testlinkAPI.getTestPlanPlatforms(self.plan_id)
        if rsp:
            for item in rsp:
                if item['name'] == self.pf_name:
                    return True
            raise PlatFormNameException('the platfrom is not in the test plan')
        else:
            #if no platform in the specific test plan, the platform name can be any.
            return True
                
    def process_with_feedback(self,dialog):
        result_file=self.work_dir+'output.xml'
        if os.path.exists(result_file) and os.path.isfile(result_file):
            try:
                result=XMLResultPaser(result_file).parse_all_tc()
                self._reportresult(result)
            except Exception as reason:
                traceback.print_exc()
                wx.CallAfter(dialog.Update,1,self.tcnum,self.ftcnum,0,0)
                wx.CallAfter(dialog.RecordEInfo,self.ts_name,str(reason))
            else:
                wx.CallAfter(dialog.Update,1,self.tcnum,self.ftcnum,0,0)
                wx.CallAfter(dialog.RecordEInfo,self.ts_name,'Success!')
        else:
            info='No result file in the directory,skip it'
            wx.CallAfter(dialog.Update,1,0,0,0,0)
            wx.CallAfter(dialog.RecordEInfo,self.ts_name,info)
            
    def process(self):
        result_file=self.work_dir+'output.xml'
        
        if os.path.exists(result_file) and os.path.isfile(result_file):
            try:
                result=XMLResultPaser(result_file).parse_all_tc()
                self._reportresult(result)
            except:
                etype, value, tb=full_exc_info()
                traceback.print_exception(etype, value, tb)     
        else:
            print 'the test suite %s has no result. skip it' % self.ts_name

    def _reportresult(self,tc_result):
        for item in tc_result:
            tcname=item[0]
            testcaseexternalid=self.get_tcfullextid(tcname)
            if item[1] == 'PASS':
                status='p'
                notes=''
            else:
                status='f'
                notes=''
                if item[4]:
                    notes='\r\n'.join(item[4])
            buildid=self._getbuild()
            if self._checkplatform():
                platformname=self.pf_name
                
            rsp=self.testlinkAPI.reportTCResult(testplanid=self.plan_id,status=status, testcaseexternalid=testcaseexternalid, buildid=buildid,overwrite=self.overwrite,platformname=platformname,notes=notes)
            self._parseRSPresult(rsp)
          
    def _parseRSPresult(self,rsp):
        try:
            if rsp[0]['status']:     
                self.tcnum += 1
            else:
                self.ftcnum +=1
        except Exception as e:
            self.ftcnum +=1
            print str(e)
        
    def _getbuildwithoutname(self):
        build_id=self._getlastestbuildforplan()
        if build_id:
            return build_id 
        else:
            build_id=self._createbuild()
            return build_id
    
    def _getbuild(self):
        if not self.build_name:
            return self._getbuildwithoutname()
        else:
            return self._getbuildidforname()
     
    def _createbuild(self):
        build_name=self.plan_name+'-'+time.asctime(time.localtime())
        rsp=self.testlinkAPI.createBuild(testplanid=self.plan_id,buildname=build_name)
        if rsp[0]['status']:
            return rsp[0]['id']
        else:
            raise BuildException('Create the builds error')
    
    def _createbuildwithname(self,build_name):
        rsp=self.testlinkAPI.createBuild(testplanid=self.plan_id,buildname=build_name)
        if rsp[0]['status']:
            return rsp[0]['id']
        else:
            raise BuildException('Create the builds error')

    def __call__(self,dialog):
        return self.process_with_feedback(dialog)
        
        
            
                
             
                
