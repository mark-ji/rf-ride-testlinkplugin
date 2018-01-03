#coding: utf-8

import wx
from robotide.pluginapi import Plugin,ActionInfo,SeparatorInfo
from testlinkplugin.apidialog import ConfDialog,TestInfoDialog,UpdateInfoDialog,UpdateProgressDialog,ImportProgressDialog
from testlinkplugin.apidialog  import ID_DIALOG_IMPORT_NOT_FINISH
from testlinkplugin.testlinkapiforplugin import Node, NodeProcessForProject,LoadScriptFromTS,UpLoadScriptToTS,UpdateResultToTS
from testlinkplugin.testlinkapiforplugin import judge_dir
import testlink
import threadpool
from testlinkplugin.threadkiller import ThreadWithExc
import sys
import traceback
from testlinkplugin.tracebackextend import full_exc_info

def makerequest_noargs(callable_, callback=None,
        exc_callback=threadpool._handle_thread_exception):
    request=threadpool.WorkRequest(callable_, callback=callback,
                    exc_callback=exc_callback)
    return request

def makerequest_sameargs(callable_, arg=None, callback=None,
        exc_callback=threadpool._handle_thread_exception):
    if not arg:
        request=makerequest_noargs(callable_, callback,exc_callback)
        
    else:
        args=[arg]
        request=threadpool.WorkRequest(callable_, args,callback=callback,
                    exc_callback=exc_callback)
                    
    return request

def handle_exception(request, exc_info):
    traceback.print_exception(*exc_info)

class TestLinkPlugin(Plugin):
    MENU_NAME = 'TestLinkPlugin'
    INSTALLATION_URL = 'http://www.baidu.com'
    VERSION = '0.0.1'
    metadata = {'Version': VERSION,
                'Author': 'mark'}
    
    menu = [
        {"name": "TestLink API Configure","action": "OnConfigure"},
        {"name": "Import TestCases From TestLink", "action": "OnImport_NEW_THD"},
        {"name": "Update TestCases To TestLink", "action": "OnUpdate"},
        {"name": None},
        {"name": "About", "action":"OnAbout" }]
    
    def __init__(self, application=None):
        Plugin.__init__(self, application, metadata=self.metadata)
        self.apiurl=''
        self.apikey=''
        self.workspace=''
        self.projectname=''
        self.testplanname=''
        self.tester=''
        #self.testlinkAPI=None
        self.root_node=None
        self.chosenTS=[]
        self.isloadscript=True
        #self.isupdateTC=False
        self.isrefreshscript=False
        #self.updateall=False
        self.appendscript=False
        self.updateresult=False
        self.updatescript=True
  
    def enable(self):
        self.add_testlink_menu()
        
    def disable(self):
        self.remove_testlink_menu()
        
    def remove_testlink_menu(self):
        self.unregister_actions()
        
    def add_testlink_menu(self):
        self.unregister_actions()
        for menuItem in self.menu:
            if menuItem['name'] is None:
                self.register_action(SeparatorInfo(self.MENU_NAME))
            else:
                action_info = ActionInfo(self.MENU_NAME, name=menuItem['name'],
                                         action=self.create_callable(menuItem['action']))
                self.register_action(action_info)
                
    def create_callable(self,action):
        return getattr(self, action)
  
    def OnConfigure(self,event):
        dlg=ConfDialog(workspace=self.workspace,apiurl=self.apiurl,devkey=self.apikey,projectname=self.projectname,testplanname=self.testplanname,tester=self.tester)
        if dlg.ShowModal() == wx.ID_OK:
            self.apiurl=dlg.apiurl
            self.apikey=dlg.devkey
            self.workspace=dlg.workspace
            self.projectname=dlg.projectname
            self.testplanname=dlg.testplanname
            self.tester=dlg.tester
            try:
                self.tl_helper=testlink.TestLinkHelper(self.apiurl,self.apikey)
                self.TestLinkClient=self.tl_helper.connect(testlink.TestlinkAPIClient)
                self.plan_id=self.TestLinkClient.getTestPlanByName(self.projectname,self.testplanname)[0]['id']
                self.ts_lists=self.TestLinkClient.getTestSuitesForTestPlan(self.plan_id)
            except Exception as e:
                err_dlg=wx.MessageDialog(self, str(e), 'Error Message',wx.OK|wx.ICON_ERROR)
                err_dlg.ShowModal()
                err_dlg.Destroy()
                return
            
            Node.clearAllNodes()
            self.ts_process=NodeProcessForProject(self.projectname,self.ts_lists)
            self.root_node=self.ts_process.create_rootnode()
            self.ts_process.create_childnode(self.root_node,self.ts_lists)
 
        dlg.Destroy()
        
    @staticmethod
    def createimporttask(ts_names,TestLinkClient,workspace,progressdlg):
        for ts_name in ts_names:
            try:
                loadfromts=LoadScriptFromTS(TestLinkClient,ts_name,workspace)
                loadfromts.process()

                wx.CallAfter(progressdlg.Update,1,loadfromts.tcnum,0)
                #progressdlg.Update(1,loadfromts.tcnum,0)
                wx.CallAfter(progressdlg.RecordEInfo,ts_name, 'Successed!')
                #progressdlg.RecordEInfo(ts_name, 'Successed!')
            except not SystemExit:
                etype,value,tb = sys.exc_info()
                #progressdlg.Update(1,loadfromts.tcnum,0)
                wx.CallAfter(progressdlg.Update,1,loadfromts.tcnum,0)
                reason=':'.join(traceback.format_exception_only(etype, value))
                #progressdlg.RecordEInfo(ts_name, reason)
                wx.CallAfter(progressdlg.RecordEInfo,ts_name, reason)
                
    def OnImport_NEW_THD(self,event):
        if not self.root_node:
            err_dlg=wx.MessageDialog(self, "Please finish the testlink configure correctly", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
            err_dlg.ShowModal()
            err_dlg.Destroy()
            return
                        
        dlg=TestInfoDialog(self.root_node,chosenTS=self.chosenTS,loadscript=self.isloadscript,refreshscript=self.isrefreshscript)
        if dlg.ShowModal() == wx.ID_OK:
            self.chosenTS=dlg.chosenTS
            self.isloadscript=dlg.loadscript
            self.isrefreshscript=dlg.refreshscript
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        if not self.chosenTS:
            noTS_dlg= wx.MessageDialog(self, "No TestSuite, please check the configure or the TestLink ", 'Error Message', wx.OK|wx.ICON_ERROR)
            noTS_dlg.ShowModal()
            noTS_dlg.Destroy()
            return
        
        tsnum=len(self.chosenTS)
        progressdlg = ImportProgressDialog(plugin=self)
        progressdlg.SetRange(tsnum)
        
        self.thd_import = ThreadWithExc(target=self.createimporttask,args=(self.chosenTS,self.TestLinkClient,self.workspace,progressdlg))
        self.thd_import.setDaemon(True)
        self.thd_import.start()
        
        #progressdlg.Destroy()
        if progressdlg.ShowModal() == ID_DIALOG_IMPORT_NOT_FINISH:
            print 'the import thread can not be killed, and has closed the dialog,should wait'
        progressdlg.Destroy()
        self.thd_import.join()
        projectpath=judge_dir(self.workspace) + self.root_node.node_dir
        self.frame.open_suite(projectpath)
    
    def OnUpdate_MAIN_THD(self,event):
        if not self.root_node:
            err_dlg=wx.MessageDialog(self, "Please finish the testlink configure correctly", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
            err_dlg.ShowModal()
            err_dlg.Destroy()
            return
        dlg=UpdateInfoDialog(self.root_node,chosenTS=self.chosenTS)
        if dlg.ShowModal() == wx.ID_OK:
            self.chosenTS=dlg.chosenTS
            self.appendscript=dlg.appendscript
            self.updateresult=dlg.updateresult
            self.updatescript=dlg.updatescript
            self.pf_name=dlg.pf_name
            self.build_name=dlg.build_name
        else:
            return
        dlg.Destroy()
        if not self.chosenTS:
            noTS_dlg= wx.MessageDialog(self, "No TestSuite, please check the configure or the TestLink ", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
            noTS_dlg.ShowModal()
            noTS_dlg.Destroy()
            return
        
        if self.updatescript:
            for ts_name in self.chosenTS:
                print 'begin to update scripts to the test suites %s ' % ts_name
                UpLoadScriptToTS(self.TestLinkClient,ts_name,self.workspace).process()
                
        if self.updateresult:
            for ts_name in self.chosenTS:
                print 'begin to update result to the test suites %s ' % ts_name
                UpdateResultToTS(self.TestLinkClient,ts_name,self.workspace,self.testplanname,self.plan_id).process()
                
                        
        
    def OnUpdate(self,event):
        if not self.root_node:
            err_dlg=wx.MessageDialog(self, "Please finish the testlink configure correctly", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
            err_dlg.ShowModal()
            err_dlg.Destroy()
            return
        dlg=UpdateInfoDialog(self.root_node,chosenTS=self.chosenTS)
        if dlg.ShowModal() == wx.ID_OK:
            self.chosenTS=dlg.chosenTS
            self.appendscript=dlg.appendscript
            self.updateresult=dlg.updateresult
            self.updatescript=dlg.updatescript
            self.pf_name=dlg.pf_name
            self.build_name=dlg.build_name
        else:
            return
        dlg.Destroy()
        if not self.chosenTS:
            noTS_dlg= wx.MessageDialog(self, "No TestSuite, please check the configure or the TestLink ", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
            noTS_dlg.ShowModal()
            noTS_dlg.Destroy()
            return
        
        mainprocess=threadpool.ThreadPool(1)
        progressdialog=UpdateProgressDialog(plugin=self)
        if self.updatescript:
            rangevalue=len(self.chosenTS)
        if self.updateresult:
            rangevalue= len(self.chosenTS) * 2
        progressdialog.progress.SetRange(rangevalue)

        for ts_name in self.chosenTS:
            if self.updatescript:
                uploadscript=UpLoadScriptToTS(self.TestLinkClient,ts_name,self.workspace)
                request=makerequest_sameargs(uploadscript,progressdialog,exc_callback=handle_exception)
                mainprocess.putRequest(request)
            if self.updateresult:
                updateresult=UpdateResultToTS(self.TestLinkClient,ts_name,self.workspace,self.testplanname,self.plan_id)
                request=makerequest_sameargs(updateresult,progressdialog,exc_callback=handle_exception)
                mainprocess.putRequest(request)
        
        if progressdialog.ShowModal() == wx.ID_OK or wx.ID_CANCEL:
            if mainprocess.workers:
                mainprocess.dismissWorkers(len(mainprocess.workers),do_join=True)
            
            
        progressdialog.Destroy()
                
    
    def OnAbout(self,event):
        pass
               
        
    