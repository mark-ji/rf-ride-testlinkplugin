#coding: utf-8

import wx
import testlink
from .testlinkapiforplugin import process_dir
import wx.lib.agw.customtreectrl as CT
import os
import threading
import sys
import traceback
from . import configprocess

ID_DIALOG_IMPORT_NOT_FINISH=123456700
ID_DIALOG_UPDATE_NOT_FINISH=123456701


user_EVT_GAUGE_FINISH=wx.NewEventType()
EVT_GAUGE_FINISH = wx.PyEventBinder(user_EVT_GAUGE_FINISH, 1)
class GAUGEFINISHEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.eventArgs = ""
    def GetEventArgs(self):
        return self.eventArgs
    def SetEventArgs(self, args):
        self.eventArgs = args

class ConfDialog(wx.Dialog):
    def __init__(self,title=u'TestLink API Configure',parent=None, size=None, style=None,workspace=None,apiurl=None,devkey=None,proxy=None,projectname=None,testplanname=None,tester=None):
        parent = parent or wx.GetTopLevelWindows()[0]
        #parent=parent
        size=size or (-1,-1)
        style=style or wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        
        self.configparser=configprocess.configprocess()
        
        self.workspace=workspace or self.configparser.read_item('WORKSPACE')
        self.apiurl=apiurl or self.configparser.read_item('API_URL')
        self.devkey=devkey or self.configparser.read_item('API_DEVKEY')
        self.proxy=proxy or self.configparser.read_item('PROXY')
        self.projectname=projectname or self.configparser.read_item('ProjectName')
        self.testplanname=testplanname or self.configparser.read_item('TestPlanName')
        self.tester=tester or self.configparser.read_item('Tester')
        
        self.isChecked=False
        
        self.CenterOnParent()
        
        self.panel=wx.Panel(self,-1,style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN | wx.FULL_REPAINT_ON_RESIZE)
        self.gbsizer=wx.GridBagSizer(hgap=10,vgap=10)
        
        #testlink xmlrpc url
        self.urllabel=wx.StaticText(self.panel,-1,label=u'URL:')
        self.urltext=wx.TextCtrl(self.panel,-1,size=(200,25))
        if not self.apiurl:
            self.urltext.SetValue('')
        else:
            self.urltext.SetValue(self.apiurl)
        self.gbsizer.Add(self.urllabel,pos=(0,0),span=(1,1),flag=wx.TOP |wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer.Add(self.urltext,pos=(0,1),span=(1,1),flag=wx.TOP|wx.EXPAND,border=5)
        
        #testlink xmlrpc devkey
        self.keylabel=wx.StaticText(self.panel,-1,label=u'devKey:')
        self.keytext=wx.TextCtrl(self.panel,-1,size=(200,25))
        if not self.devkey:
            self.keytext.SetValue('')
        else:
            self.keytext.SetValue(self.devkey)
        self.gbsizer.Add(self.keylabel,pos=(1,0),span=(1,1),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.gbsizer.Add(self.keytext,pos=(1,1),span=(1,1),flag=wx.EXPAND)
        
        #the prpxy between testlink and robotframework
        self.proxylabel=wx.StaticText(self.panel,-1,label=u'Proxy:')
        self.proxytext=wx.TextCtrl(self.panel,-1,size=(200,25))
        if not self.proxy:
            self.proxytext.SetValue('')
        else:   
            self.proxytext.SetValue(self.proxy)
        self.gbsizer.Add(self.proxylabel,pos=(2,0),span=(1,1),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.gbsizer.Add(self.proxytext,pos=(2,1),span=(1,1),flag=wx.EXPAND)
        
        #the robotframwork project workspace
        self.workspacelabel=wx.StaticText(self.panel,-1,label=u'WORKSPACE:')
        self.workspacepath=wx.TextCtrl(self.panel,-1,size=(200,25),style=wx.TE_READONLY)
        if not self.workspace:
            self.workspacepath.SetValue('')
        else:
            self.workspacepath.SetValue(self.workspace)
        self.pathbtn=wx.Button(self.panel,-1,label=u'...',size=(30,25),style=wx.BU_LEFT|wx.NO_BORDER)
        self.gbsizer.Add(self.workspacelabel,pos=(3,0),span=(1,1),flag=wx.LEFT | wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer.Add(self.workspacepath,pos=(3,1),span=(1,1),flag=wx.EXPAND)
        self.gbsizer.Add(self.pathbtn,pos=(3,2),span=(1,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL)
        
        #the project name in testlink
        self.projectlabel=wx.StaticText(self.panel,-1,label=u'Project Name:')
        self.projecttext=wx.TextCtrl(self.panel,-1,size=(200,25))
        if not self.projectname:
            self.projecttext.SetValue('')
        else:    
            self.projecttext.SetValue(self.projectname)
        self.gbsizer.Add(self.projectlabel,pos=(4,0),span=(1,1),flag=wx.LEFT |wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer.Add(self.projecttext,pos=(4,1),span=(1,1),flag=wx.EXPAND)
        
        #the testplan name in testlink
        self.planlabel=wx.StaticText(self.panel,-1,label=u'TestPlan Name:')
        self.plantext=wx.TextCtrl(self.panel,-1,size=(200,25))
        if not self.testplanname:
            self.plantext.SetValue('')
        else:
            self.plantext.SetValue(self.testplanname)
        self.gbsizer.Add(self.planlabel,pos=(5,0),span=(1,1),flag=wx.LEFT |wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer.Add(self.plantext,pos=(5,1),span=(1,1),flag=wx.EXPAND)
        
        #the test engineer in testlink
        self.testerlabel=wx.StaticText(self.panel,-1,label=u'Test Engineer:')
        self.testertext=wx.TextCtrl(self.panel,-1,size=(200,25))
        if not self.tester:
            self.testertext.SetValue('')
        else:
            self.testertext.SetValue(self.tester)
        self.gbsizer.Add(self.testerlabel,pos=(6,0),span=(1,1),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.gbsizer.Add(self.testertext,pos=(6,1),span=(1,1),flag=wx.EXPAND)
        
        
        self.checkbtn=wx.Button(self.panel,-1,label=u'CHECK')
        self.okbtn=wx.Button(self.panel,-1,label=u'OK')
        if not self.isChecked:
            self.okbtn.Disable()
        self.resetbtn=wx.Button(self.panel,-1,label=u'RESET')
        self.gbsizer.Add(self.checkbtn,pos=(7,0),span=(1,1),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.gbsizer.Add(self.okbtn,pos=(7,1),span=(1,1),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        self.gbsizer.Add(self.resetbtn,pos=(7,2),span=(1,1),flag=wx.RIGHT|wx.ALIGN_LEFT,border=5)
        
        
        self.SetClientSize((390,290))
        self.panel.SetSizerAndFit(self.gbsizer)
        #self.gbsizer.SetSizeHints(self.panel)
        
        self.Bind(wx.EVT_BUTTON,self.OnPathbtn, self.pathbtn)
        self.Bind(wx.EVT_BUTTON,self.OnCheckbtn, self.checkbtn)
        self.Bind(wx.EVT_BUTTON,self.OnOKbtn, self.okbtn)
        self.Bind(wx.EVT_BUTTON,self.OnRESETbtn, self.resetbtn)
        self.Bind(wx.EVT_TEXT,self.OnChangeApi,self.urltext)
        self.Bind(wx.EVT_TEXT,self.OnChangeApi,self.keytext)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
    
    def OnClose(self,event):
        if self.isChecked:
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_CANCEL)

    def OnChangeApi(self,event):
        self.okbtn.Disable()
        self.isChecked=False
        
        
    def OnPathbtn(self,event):
        dirdialog=wx.DirDialog(self, message="Choose a directory", 
                     defaultPath="",style=wx.DD_DEFAULT_STYLE, pos = wx.DefaultPosition, 
                     size = wx.DefaultSize,name="wxDirCtrl")
        if dirdialog.ShowModal() == wx.ID_OK:
            chosenpath=dirdialog.GetPath()
            if chosenpath:
                #self.workspace=process_dir(chosenpath)
                self.workspacepath.Clear()
                self.workspacepath.AppendText(process_dir(chosenpath))
                #self.configparser.write_item('WORKSPACE', self.workspace)
            else:
                self.workspacepath.Clear()
                self.workspacepath.AppendText(self.workspace)
        dirdialog.Destroy()        
    
    
    def OnCheckbtn(self,event):
        api_temp_url=self.urltext.GetValue()
        api_temp_key=self.keytext.GetValue()
        api_temp_proxy=self.proxytext.GetValue()
        
        if not api_temp_proxy:
            if api_temp_url and api_temp_key:
                #check the link to testlink
                try:
                    tl_helper=testlink.TestLinkHelper(api_temp_url,api_temp_key)
                    rf2testlinker=tl_helper.connect(testlink.TestlinkAPIClient)
                except Exception,e:
                    dlg=wx.MessageDialog(self, str(e), 'Error Message',wx.OK|wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return
                try:
                    checkresult=rf2testlinker.checkDevKey(api_temp_key)
                except Exception,e:
                    dlg=wx.MessageDialog(self, str(e), 'Error Message',wx.OK|wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return
                if checkresult:
                    self.isChecked=True
                    self.okbtn.Enable()
                    dlg=wx.MessageDialog(self, 'The testlink xmlrpc api can be connect successfully', 'Feedback',wx.OK)
                    dlg.ShowModal()
                    dlg.Destroy()
            else:
                dlg=wx.MessageDialog(self, "URL and devKey are mandatory,please configure them correctly.", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
        else:
            if api_temp_url and api_temp_key:
                #check the link to testlink
                pass
            else:
                dlg=wx.MessageDialog(self, "URL and devKey are mandatory,please configure them correctly.", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
   
    def OnOKbtn(self,event):
        self.apiurl=self.urltext.GetValue()
        self.devkey=self.keytext.GetValue()
        self.proxy=self.proxytext.GetValue()
        self.projectname=self.projecttext.GetValue()
        self.testplanname=self.plantext.GetValue()
        self.tester=self.testertext.GetValue()
        self.workspace=self.workspacepath.GetValue()
        
        
        if not self.apiurl or not self.devkey or not self.workspace or not self.projectname or not self.testplanname:
            dlg=wx.MessageDialog(self, "URL/devKey/workspace/project name/plan name are mandatory,please configure them correctly.", 
                     'Error Message',wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.configparser.write_item('WORKSPACE', self.workspace)
            self.configparser.write_item('API_URL', self.apiurl)
            self.configparser.write_item('API_DEVKEY', self.devkey)
            self.configparser.write_item('PROXY', self.proxy)
            self.configparser.write_item('ProjectName', self.projectname)
            self.configparser.write_item('TestPlanName', self.testplanname)
            self.configparser.write_item('Tester', self.tester)
            self.EndModal(wx.ID_OK)
        
    def OnRESETbtn(self,event):
        '''
        self.workspace=''
        self.apiurl=''
        self.devkey=''
        self.proxy=''
        self.projectname=''
        self.testplanname=''
        self.tester=''
        '''
        self.urltext.Clear()
        self.keytext.Clear()
        self.proxytext.Clear()
        self.workspacepath.Clear()
        self.projecttext.Clear()
        self.testertext.Clear()
        self.plantext.Clear()
        self.okbtn.Disable()
    

class TestInfoDialog(wx.Dialog):
    def __init__(self,node,title=u'Test Info. Configure',parent=None, size=None, style=None,chosenTS=None,loadscript=True,refreshscript=False):
        #parent = parent or wx.GetTopLevelWindows()[0]
        parent=parent
        size=size or (-1,-1)
        style=style or wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER
        self.root_node=node
        if chosenTS == None:
            self.chosenTS = []
        else:
            self.chosenTS=chosenTS
        self.loadscript=loadscript
        self.refreshscript=refreshscript
        
        if not self.chosenTS:
            self.tsname=''
        else:
            self.tsname=';'.join(self.chosenTS)
        
        wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        self.CenterOnParent()
        
        self.panel=wx.Panel(self,-1,style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN | wx.FULL_REPAINT_ON_RESIZE)
        self.gbsizer=wx.GridBagSizer(hgap=10,vgap=10)

        #the testsuites name
        self.testsuitlabel=wx.StaticText(self.panel,-1,label=u'TestSuite Name:')
        self.testsuittext=wx.TextCtrl(self.panel,-1,size=(250,25))
        self.testsuittext.SetValue(self.tsname)
        self.tsbtn=wx.Button(self.panel,-1,label=u'...',size=(30,25),style=wx.BU_LEFT|wx.NO_BORDER)
        self.gbsizer.Add(self.testsuitlabel,pos=(0,0),span=(1,1),flag=wx.TOP|wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer.Add(self.testsuittext,pos=(0,1),span=(1,1),flag=wx.TOP|wx.EXPAND,border=5)
        self.gbsizer.Add(self.tsbtn,pos=(0,2),span=(1,1),flag=wx.TOP|wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        
        
        self.loadscriptcb=wx.CheckBox(self.panel,-1,label=u'Load Scripts')
        self.loadscriptcb.SetValue(self.loadscript)
        self.gbsizer.Add(self.loadscriptcb,pos=(1,0),span=(1,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        
        self.updatescriptcb=wx.CheckBox(self.panel,-1,label=u'Update Existed')
        self.updatescriptcb.SetValue(self.refreshscript)
        self.gbsizer.Add(self.updatescriptcb,pos=(2,0),span=(1,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        
        self.exportbtn=wx.Button(self.panel,-1,label=u'LOAD')
        self.resetbtn=wx.Button(self.panel,-1,label=u'RESET')
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.exportbtn)
        btnSizer.Add(self.resetbtn)
 
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.gbsizer, 0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add(btnSizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        self.SetClientSize((430,150))
        self.panel.SetSizerAndFit(mainSizer)
        
        self.Bind(wx.EVT_BUTTON,self.OnExportbtn, self.exportbtn)
        self.Bind(wx.EVT_BUTTON,self.OnResetbtn, self.resetbtn)
        self.Bind(wx.EVT_BUTTON,self.OnChosentsbtn, self.tsbtn)
        
        
    def OnExportbtn(self,event):
        self.loadscript=self.loadscriptcb.IsChecked()
        self.refreshscript=self.updatescriptcb.IsChecked()
        self.EndModal(wx.ID_OK)    
        

    def OnResetbtn(self,event):
        self.tsname=''
        self.chosenTS=[]
        self.loadscript=True
        self.refreshscript=False
        
        self.testsuittext.Clear()
        self.loadscriptcb.SetValue(True)
        self.updatescriptcb.SetValue(False)
     
    def OnChosentsbtn(self,event):
        dlg=ChosenTSDialog(self.root_node,chosenTS=self.chosenTS)
        if dlg.ShowModal() == wx.ID_OK:
            self.chosenTS=dlg.chosenTS
            dlg.Destroy()
        self.tsname=';'.join(self.chosenTS)
        self.testsuittext.SetValue(self.tsname)
    
class ChosenTSDialog(wx.Dialog):
    def __init__(self,node,title=u'Choose TestSuites',chosenTS=None,parent=None, size=None, style=None):
        #parent = parent or wx.GetTopLevelWindows()[0]
        parent=parent
        size=size or (-1,-1)
        style=style or wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER
        if chosenTS == None:
            self.chosenTS = []
        else:
            self.chosenTS=chosenTS
        wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        self.CenterOnParent()
        
        self.panel=wx.Panel(self,-1,style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN | wx.FULL_REPAINT_ON_RESIZE)
        
        #self.CTtree = wx.TreeCtrl(self,size=(275,350),style=wx.TR_DEFAULT_STYLE|wx.TR_MULTIPLE)
        self.CTtree = CT.CustomTreeCtrl(self.panel, size=(300,350),agwStyle=wx.TR_DEFAULT_STYLE|CT.TR_AUTO_CHECK_CHILD|wx.TR_MULTIPLE)
        self.CTroot = self.CTtree.AddRoot(node.ts_name, ct_type=1)
        #root = self.CTtree.AddRoot(node.ts_name)
        self._AddTreeNodes(self.CTroot, node)
        
        self.CTtree.Expand(self.CTroot)
        
        
        self.choosebtn=wx.Button(self.panel,-1,pos=(140,360),label=u'CHOOSE')
        self.resetbtn=wx.Button(self.panel,-1,pos=(220,360),label=u'RESET')
        
        self.SetClientSize((300,400))        
        
        self.Bind(wx.EVT_BUTTON,self.OnChooseBtn, self.choosebtn)
        self.Bind(wx.EVT_BUTTON,self.OnResetbtn, self.resetbtn)
        
        
        
        
        if self.chosenTS:
            self.CTtree.SetAGWWindowStyleFlag(agwStyle=wx.TR_DEFAULT_STYLE|wx.TR_MULTIPLE)
            for ts in self.chosenTS:
                self._setCheckedItem(ts,self.CTroot)
            self.CTtree.SetAGWWindowStyleFlag(agwStyle=wx.TR_DEFAULT_STYLE|CT.TR_AUTO_CHECK_CHILD|wx.TR_MULTIPLE)
             

            
    def AddTreeNodes(self, parentItem, items):
        for item in items:
            if type(item) == str:
                self.tree.AppendItem(parentItem, item)
            else:
                newItem = self.tree.AppendItem(parentItem, item[0])
                self.AddTreeNodes(newItem, item[1])
    

    def _AddTreeNodes(self, parentItem, node):
        for childnode in node.children:
            if not childnode.children:
                self.CTtree.AppendItem(parentItem, childnode.ts_name,ct_type=1)
                #self.CTtree.AppendItem(parentItem, childnode.ts_name)
            else:
                newItem = self.CTtree.AppendItem(parentItem, childnode.ts_name,ct_type=1)
                #newItem = self.CTtree.AppendItem(parentItem, childnode.ts_name)
                self._AddTreeNodes(newItem, childnode)

    def OnChooseBtn(self,event):
        self.chosenTS=[]
        self._getCheckedItem(self.CTroot)
        self.EndModal(wx.ID_OK)
    
    def _getChild(self,item):
        item_list = item.GetChildren()
        return item_list

    
    def _getCheckedItem(self,item):
        if item != self.CTroot and item.IsChecked():
            self.chosenTS.append(item.GetText()) 
        for childitem in self._getChild(item):
            self._getCheckedItem(childitem)
            
    def OnResetbtn(self,event):
        self.chosenTS=[]
        self._unCheckItems(self.CTroot)

    def _setCheckedItem(self,ts_name,item,):
        if item.GetText() == ts_name:
            self.CTtree.CheckItem(item, checked=True)
        for childitem in self._getChild(item):
            self._setCheckedItem(ts_name, childitem)
            
        
    def _unCheckItems(self,item):
        self.CTtree.CheckItem(item, checked=False)
        for childitem in self._getChild(item):
            self._unCheckItems(childitem)

class UpdateInfoDialog(wx.Dialog):
    def __init__(self,node,title=u'Update Configure',parent=None, size=None, style=None,chosenTS=None,updatescript=True,appendscript=False,updateresult=False):
        #parent = parent or wx.GetTopLevelWindows()[0]
        parent=parent
        size=size or (-1,-1)
        style=style or wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER
        self.root_node=node
        if chosenTS == None:
            self.chosenTS=[]
        else:
            self.chosenTS=chosenTS
        self.appendscript=appendscript
        self.updateresult=updateresult
        self.updatescript=updatescript
        self.build_name=None
        self.pf_name=None
        
        if not self.chosenTS:
            self.tsname=''
        else:
            self.tsname=';'.join(self.chosenTS)
        
        wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        self.CenterOnParent()
        
        self.panel=wx.Panel(self,-1,style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN | wx.FULL_REPAINT_ON_RESIZE)
        self.gbsizer=wx.GridBagSizer(hgap=10,vgap=10)

        #the testsuites name
        self.testsuitlabel=wx.StaticText(self.panel,-1,label=u'TestSuite Name:')
        #self.testsuittext=wx.TextCtrl(self.panel,-1,size=(250,25))
        self.testsuittext=wx.TextCtrl(self.panel,-1)
        self.testsuittext.SetValue(self.tsname)
        self.tsbtn=wx.Button(self.panel,-1,label=u'...',size=(30,25),style=wx.BU_LEFT|wx.NO_BORDER)
        self.gbsizer.Add(self.testsuitlabel,pos=(0,0),span=(1,1),flag=wx.TOP|wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer.Add(self.testsuittext,pos=(0,1),span=(1,1),flag=wx.TOP|wx.EXPAND,border=5)
        self.gbsizer.Add(self.tsbtn,pos=(0,2),span=(1,1),flag=wx.TOP|wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        
        
        self.updateallcb=wx.CheckBox(self.panel,-1,label=u'Append Scripts After the TestCase Summary Info')
        self.updateallcb.SetValue(self.appendscript)
        self.gbsizer.Add(self.updateallcb,pos=(1,1),span=(1,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        
        self.updatescriptcb=wx.CheckBox(self.panel,-1,label=u'Update TestCase Script')
        self.updatescriptcb.SetValue(self.updatescript)
        self.gbsizer.Add(self.updatescriptcb,pos=(2,1),span=(1,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL,border=5)
            
        self.updateresultcb=wx.CheckBox(self.panel,-1,label=u'Update TestCase Result')
        self.updateresultcb.SetValue(self.updateresult)
        self.gbsizer.Add(self.updateresultcb,pos=(3,1),span=(1,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        
        #some conf with Updating the result
        
        
        self.buildlabel=wx.StaticText(self.panel,-1,label=u'Build Name:')
        self.buildtext=wx.TextCtrl(self.panel,-1,size=(300,25))
        self.platformlabel=wx.StaticText(self.panel,-1,label=u'PlatForm Name:')
        self.platformtext=wx.TextCtrl(self.panel,-1,size=(300,25))
        
        self.gbsizer2=wx.GridBagSizer(hgap=10,vgap=10)
        self.gbsizer2.Add(self.buildlabel,pos=(0,0),span=(1,1),flag=wx.TOP|wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer2.Add(self.buildtext,pos=(0,1),span=(1,1),flag=wx.TOP|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL,border=5)
        self.gbsizer2.Add(self.platformlabel,pos=(1,0),span=(1,1),flag= wx.ALIGN_CENTRE_VERTICAL)
        self.gbsizer2.Add(self.platformtext,pos=(1,1),span=(1,1),flag= wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL)
        
        sbox=wx.StaticBox(self.panel,-1,label=u'Build Info')
        self.sbsizer=wx.StaticBoxSizer(sbox,orient=wx.VERTICAL)
        self.sbsizer.Add(self.gbsizer2,proportion=0,flag=wx.EXPAND,border=5)
        
        self.updatebtn=wx.Button(self.panel,-1,label=u'UPDATE')
        self.resetbtn=wx.Button(self.panel,-1,label=u'RESET')
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.updatebtn)
        btnSizer.Add(self.resetbtn)
 
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.gbsizer, 0, wx.EXPAND|wx.ALL, 10)
        self.mainSizer.Add(self.sbsizer, 0, wx.EXPAND|wx.ALL, 10)
        self.mainSizer.Add(btnSizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        
        if self.updateresult:
            self.mainSizer.Show(self.sbsizer)
            self.SetClientSize((460,260))
        else:
            self.mainSizer.Hide(self.sbsizer)
            self.SetClientSize((460,160))
        self.panel.SetSizerAndFit(self.mainSizer)
        
        self.Bind(wx.EVT_BUTTON,self.OnUpdatebtn, self.updatebtn)
        self.Bind(wx.EVT_BUTTON,self.OnResetbtn, self.resetbtn)
        self.Bind(wx.EVT_BUTTON,self.OnChosentsbtn, self.tsbtn)
        self.Bind(wx.EVT_CHECKBOX,self.Oncheck,self.updateresultcb)
        
    def Oncheck(self,event):
        if self.updateresultcb.IsChecked():
            self.mainSizer.Show(self.sbsizer)
            self.SetClientSize((460,260))
            
        else:
            self.mainSizer.Hide(self.sbsizer)
            self.SetClientSize((460,160))
            
        self.mainSizer.Layout()
             
    def OnUpdatebtn(self,event):
        self.appendscript=self.updateallcb.IsChecked()
        self.updateresult=self.updateresultcb.IsChecked()
        self.updatescript=self.updatescriptcb.IsChecked()
        if self.updateresult:
            self.build_name=self.buildtext.GetValue()
            self.pf_name=self.platformtext.GetValue()
        self.EndModal(wx.ID_OK)    
      

    def OnResetbtn(self,event):
        self.tsname=''
        self.chosenTS=None
        self.appendscript=False
        self.updateresult=False
        self.updatescript=True
        
        
        self.testsuittext.Clear()
        self.updateallcb.SetValue(False)
        self.updateresultcb.SetValue(False)
        self.updatescriptcb.SetValue(True)
        
     
    def OnChosentsbtn(self,event):
        dlg=ChosenTSDialog(self.root_node,chosenTS=self.chosenTS)
        if dlg.ShowModal() == wx.ID_OK:
            self.chosenTS=dlg.chosenTS
            dlg.Destroy()
        self.tsname=';'.join(self.chosenTS)
        self.testsuittext.SetValue(self.tsname)               

class UpdateProgressDialog(wx.Dialog):
    def __init__(self,plugin,title=u'Update Result',parent=None, size=None, style=None):
        #parent = parent or wx.GetTopLevelWindows()[0]
        self.plugin=plugin
        parent=parent
        size=size or (-1,-1)
        style=style or wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        self.CenterOnParent()
        self.panel=wx.Panel(self,-1,style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN | wx.FULL_REPAINT_ON_RESIZE)
        self.progresslabel=wx.StaticText(self.panel,-1,label=u'Update Progress:')
        self.progress=wx.Gauge(self.panel,-1)
        
        #update result StaticBoxSizer
        sbox=wx.StaticBox(self.panel,-1,label=u'Update Result:')
        self.updatesbsizer=wx.StaticBoxSizer(sbox,orient=wx.HORIZONTAL)
        
        self.resultslabel=wx.StaticText(self.panel,-1,label=u'Success:')
        self.resultstext=wx.TextCtrl(self.panel,-1)
        self.resultstext.SetValue('0')
        self.resultsnum=0
        self.resultflabel=wx.StaticText(self.panel,-1,label=u'Failed:')
        self.resultftext=wx.TextCtrl(self.panel,-1)
        self.resultftext.SetValue('0')
        self.resultfnum=0
        
        self.resultsizer=wx.BoxSizer(wx.HORIZONTAL)
        self.resultsizer.Add(self.resultslabel, 0, wx.EXPAND|wx.ALL, 10)
        self.resultsizer.Add(self.resultstext, 0, wx.EXPAND|wx.ALL, 10)
        self.resultsizer.Add(self.resultflabel, 0, wx.EXPAND|wx.ALL, 10)
        self.resultsizer.Add(self.resultftext, 0, wx.EXPAND|wx.ALL, 10)
        
        self.updatesbsizer.Add(self.resultsizer,proportion=0,flag=wx.EXPAND,border=5)
        
        #upload  script StaticBoxSizer
        sbox1=wx.StaticBox(self.panel,-1,label=u'Upload Scripts:')
        self.uploadsbsizer=wx.StaticBoxSizer(sbox1,orient=wx.HORIZONTAL)
        
        self.scriptslabel=wx.StaticText(self.panel,-1,label=u'Success:')
        self.scriptstext=wx.TextCtrl(self.panel,-1)
        self.scriptstext.SetValue('0')
        self.scriptsnum=0
        self.scriptflabel=wx.StaticText(self.panel,-1,label=u'Failed:')
        self.scriptftext=wx.TextCtrl(self.panel,-1)
        self.scriptftext.SetValue('0')
        self.scriptfnum=0
        
        self.scriptsizer=wx.BoxSizer(wx.HORIZONTAL)
        self.scriptsizer.Add(self.scriptslabel, 0, wx.EXPAND|wx.ALL, 10)
        self.scriptsizer.Add(self.scriptstext, 0, wx.EXPAND|wx.ALL, 10)
        self.scriptsizer.Add(self.scriptflabel, 0, wx.EXPAND|wx.ALL, 10)
        self.scriptsizer.Add(self.scriptftext, 0, wx.EXPAND|wx.ALL, 10)
        
        self.uploadsbsizer.Add(self.scriptsizer,proportion=0,flag=wx.EXPAND,border=5)
        
        #listctrl to show the error message
        self.feedback=wx.ListCtrl(self.panel,size=(350,230),style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
        self.feedback.InsertColumn(0, 'Item Name')
        self.feedback.InsertColumn(1, 'Error Message') 
        self.feedback.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        self.feedback.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)

        
        #two buttons
        self.abortbtn=wx.Button(self.panel,-1,label=u'ABORT')
        self.finishbtn=wx.Button(self.panel,-1,label=u'FINISH')
        self.finishbtn.Disable()
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((10,10), 1)
        btnSizer.Add(self.abortbtn)
        btnSizer.Add(self.finishbtn)
        
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.progresslabel, 0, wx.EXPAND|wx.TOP|wx.LEFT, 5)
        self.mainSizer.Add(self.progress, 0, wx.EXPAND|wx.ALL, 5)
        self.mainSizer.Add(self.updatesbsizer, 0, wx.EXPAND|wx.ALL, 5)
        self.mainSizer.Add(self.uploadsbsizer, 0, wx.EXPAND|wx.ALL, 5)
        self.mainSizer.Add(self.feedback, 0, wx.EXPAND|wx.ALL, 5)
        self.mainSizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetClientSize((380,490))
        self.SetSizerAndFit(self.mainSizer)
        
        self.Bind(wx.EVT_BUTTON,self.OnAbort, self.abortbtn)
        self.Bind(wx.EVT_BUTTON,self.OnFinish, self.finishbtn)
        self.Bind(EVT_GAUGE_FINISH,self.OnGaugeFinish)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.lock=threading.Lock()

        self.Show()
    
    def OnClose(self,event):
        self.Destroy()

    def OnAbort(self,event):
        self.abortbtn.Disable()
        
    def OnFinish(self,event):
        self.EndModal(wx.ID_OK)
        
    def Update_With_Lock(self,value,results,resultf,scripts,scriptf):
        if self.lock.acquire():
            newvalue=self.progress.GetValue() + value
            self.progress.SetValue(newvalue)
            self.resultsnum = self.resultsnum + results
            self.resultfnum = self.resultfnum + resultf
            self.scriptsnum = self.scriptsnum + scripts
            self.scriptfnum = self.scriptfnum + scriptf
            self.resultstext.SetValue(str(self.resultsnum))
            self.resultftext.SetValue(str(self.resultfnum))
            self.scriptstext.SetValue(str(self.scriptsnum))
            self.scriptftext.SetValue(str(self.scriptfnum))
            self.lock.release()
    
    def Update(self,value,results,resultf,scripts,scriptf):
        newvalue=self.progress.GetValue() + value
        self.progress.SetValue(newvalue)
        self.resultsnum = self.resultsnum + results
        self.resultfnum = self.resultfnum + resultf
        self.scriptsnum = self.scriptsnum + scripts
        self.scriptfnum = self.scriptfnum + scriptf
        self.resultstext.SetValue(str(self.resultsnum))
        self.resultftext.SetValue(str(self.resultfnum))
        self.scriptstext.SetValue(str(self.scriptsnum))
        self.scriptftext.SetValue(str(self.scriptfnum))
        if self.progress.GetValue() == self.progress.GetRange():
            evt = GAUGEFINISHEvent(user_EVT_GAUGE_FINISH, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)
    
    def OnGaugeFinish(self,event):
        self.abortbtn.Disable()
        self.finishbtn.Enable()    
    
    def SetRange(self,value):
        self.progress.SetRange(value)
        
    def RecordEInfo(self,ts_name,reason):
        index=self.feedback.InsertStringItem(sys.maxint, ts_name)
        self.feedback.SetStringItem(index, 1, reason)
               
class ImportProgressDialog(wx.Dialog):
    def __init__(self,plugin,title=u'Update Result',parent=None, size=None, style=None):
        #parent = parent or wx.GetTopLevelWindows()[0]
        self.plugin=plugin
        parent=parent
        size=size or (-1,-1)
        style=style or wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        self.CenterOnParent()
        self.panel=wx.Panel(self,-1,style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN | wx.FULL_REPAINT_ON_RESIZE)
        self.progresslabel=wx.StaticText(self.panel,-1,label=u'Import Progress:')
        self.progress=wx.Gauge(self.panel,-1)
        
        #update result StaticBoxSizer
        sbox=wx.StaticBox(self.panel,-1,label=u'Import Result:')
        self.updatesbsizer=wx.StaticBoxSizer(sbox,orient=wx.HORIZONTAL)
        
        self.resultslabel=wx.StaticText(self.panel,-1,label=u'Success:')
        self.resultstext=wx.TextCtrl(self.panel,-1)
        self.resultstext.SetValue('0')
        self.resultsnum=0
        self.resultflabel=wx.StaticText(self.panel,-1,label=u'Failed:')
        self.resultftext=wx.TextCtrl(self.panel,-1)
        self.resultftext.SetValue('0')
        self.resultfnum=0
        
        self.resultsizer=wx.BoxSizer(wx.HORIZONTAL)
        self.resultsizer.Add(self.resultslabel, 0, wx.EXPAND|wx.ALL, 10)
        self.resultsizer.Add(self.resultstext, 0, wx.EXPAND|wx.ALL, 10)
        self.resultsizer.Add(self.resultflabel, 0, wx.EXPAND|wx.ALL, 10)
        self.resultsizer.Add(self.resultftext, 0, wx.EXPAND|wx.ALL, 10)
        
        self.updatesbsizer.Add(self.resultsizer,proportion=0,flag=wx.EXPAND,border=5)
        
        #listctrl to show the error message
        self.feedback=wx.ListCtrl(self.panel,size=(350,230),style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
        self.feedback.InsertColumn(0, 'Item Name')
        self.feedback.InsertColumn(1, 'Error Message') 
        self.feedback.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        self.feedback.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)

        
        #two buttons
        self.abortbtn=wx.Button(self.panel,-1,label=u'ABORT')
        self.finishbtn=wx.Button(self.panel,-1,label=u'FINISH')
        self.finishbtn.Disable()
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.abortbtn)
        btnSizer.Add(self.finishbtn)
        
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.progresslabel, 0, wx.EXPAND|wx.TOP|wx.LEFT, 5)
        self.mainSizer.Add(self.progress, 0, wx.EXPAND|wx.ALL, 5)
        self.mainSizer.Add(self.updatesbsizer, 0, wx.EXPAND|wx.ALL, 5)
        self.mainSizer.Add(self.feedback, 0, wx.EXPAND|wx.ALL, 5)
        self.mainSizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetClientSize((380,490))
        self.SetSizerAndFit(self.mainSizer)
        
        self.Bind(wx.EVT_BUTTON,self.OnAbort, self.abortbtn)
        self.Bind(wx.EVT_BUTTON,self.OnFinish, self.finishbtn)
        self.Bind(EVT_GAUGE_FINISH,self.OnGaugeFinish)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.lock=threading.Lock()
        self.Show()
    
    def OnClose(self,event):
        if self.progress.GetValue() == self.progress.GetRange():
            self.EndModal(wx.ID_CANCEL)
            
        elif not self.plugin.thd_import.is_alive():
            self.EndModal(wx.ID_CANCEL)
        
        else:
            try:
                self.plugin.thd_import.raiseExc(SystemExit)
            except:
                print traceback.print_exc()
                self.EndModal(ID_DIALOG_IMPORT_NOT_FINISH)
            else:
                self.EndModal(wx.ID_CANCEL)

    def OnAbort(self,event):
        try:
            self.plugin.thd_import.raiseExc(SystemExit)
        except:
            print traceback.print_exc()
        else:
            self.abortbtn.Disable()
            self.finishbtn.Enable()

    def OnFinish(self,event):
        self.EndModal(wx.ID_OK)
        
    def Update_With_Lock(self,value,results,resultf):
        if self.lock.acquire():
            newvalue=self.progress.GetValue() + value
            self.progress.SetValue(newvalue)
            self.resultsnum = self.resultsnum + results
            self.resultfnum = self.resultfnum + resultf
            self.resultstext.SetValue(str(self.resultsnum))
            self.resultftext.SetValue(str(self.resultfnum))
            self.lock.release()
    
    def Update(self,value,results,resultf):
        newvalue=self.progress.GetValue() + value
        self.progress.SetValue(newvalue)
        self.resultsnum = self.resultsnum + results
        self.resultfnum = self.resultfnum + resultf
        self.resultstext.SetValue(str(self.resultsnum))
        self.resultftext.SetValue(str(self.resultfnum))
        if self.progress.GetValue() == self.progress.GetRange():
            evt = GAUGEFINISHEvent(user_EVT_GAUGE_FINISH, self.GetId())
            self.GetEventHandler().ProcessEvent(evt)
    
    def OnGaugeFinish(self,event):
        self.abortbtn.Disable()
        self.finishbtn.Enable()
                           
    def SetRange(self,value):
        self.progress.SetRange(value)    
            
    
    def RecordEInfo(self,ts_name,reason):
        index=self.feedback.InsertStringItem(sys.maxint, ts_name)
        self.feedback.SetStringItem(index, 1, reason)
            

if __name__ == "__main__":
    import time
    #process=rftestlinkinterface.TS_Process()
    #root=process.find_ts_root()
    #process.process_childnode(root, process.ts_lists)
    os.environ['TESTLINK_API_PYTHON_SERVER_URL'] = "http://192.168.1.200/testlink/lib/api/xmlrpc/v1/xmlrpc.php"
    os.environ['TESTLINK_API_PYTHON_DEVKEY'] = "63a71a1af47e7df26ed40e8533bb54da"
    project_name='test_for_automaticimport'
    plan_name='automatic_import_1'
    root_node=None
    '''
    tl_helper=testlink.TestLinkHelper()
    rf2testlinker=tl_helper.connect(testlink.TestlinkAPIClient)
    plan_id=rf2testlinker.getTestPlanByName(project_name,plan_name)[0]['id']
    ts_lists=rf2testlinker.getTestSuitesForTestPlan(plan_id)
    ts_process=NodeProcessForProject(project_name,ts_lists)
    root_node=ts_process.create_rootnode()
    ts_process.create_childnode(root_node,ts_lists)
    '''
    class Mywin(wx.Frame):
        def __init__(self, parent, title): 
            super(Mywin, self).__init__(parent, title = title, size = (300,200))  
            self.InitUI()
            
        def InitUI(self):    
            panel = wx.Panel(self) 
            btn = wx.Button(panel, label = "UpdateInfoDialog", pos = (75,10)) 
            btn1 = wx.Button(panel, label = "TestInfoDialog", pos = (75,40)) 
            btn2 = wx.Button(panel, label = "UpdateProgressDialog", pos = (75,70))
            btn3 = wx.Button(panel, label = "ImportProgressDialog", pos = (75,100))  
            btn.Bind(wx.EVT_BUTTON, self.OnUpdate)
        
            btn1.Bind(wx.EVT_BUTTON, self.OnTestInfo) 
            btn2.Bind(wx.EVT_BUTTON, self.OnProgress)
            btn3.Bind(wx.EVT_BUTTON, self.OnImport) 
            self.Centre() 
            self.Show(True) 
            
        def OnUpdate(self,event):
            dialog=UpdateInfoDialog(root_node,updateresult=False)
            if dialog.ShowModal() == wx.ID_OK:
                print "You entered: UpdateInfoDialog" 
            dialog.Destroy()
            
        def OnTestInfo(self,event):
            dialog=TestInfoDialog(root_node)
            if dialog.ShowModal() == wx.ID_OK:
                print "You entered: %s" % dialog.GetValue()
            dialog.Destroy()
        
        def OnImport(self,event):
            dialog=ImportProgressDialog(plugin=None)
        
            
        def OnProgress(self,event):
            dialog=UpdateProgressDialog(parent=self)
            #dialog.Show()
            #dialog.Destroy()
            
            dialog.progress.SetRange(100)
            
            def SlowFib(n):
                if n == 0:
                    return 0
                elif n == 1:
                    return 1
                else:
                    return SlowFib(n-1) + SlowFib(n-2)

            def showprocess(i,dlg):
                while True:
                    wx.CallAfter(dlg.progress.SetValue,i)
                    if i >=100:
                        break
                    i=i+10
                    wx.CallAfter(SlowFib,30)
            #showprocess(0,dialog)      
    app = wx.PySimpleApp()
    Mywin(None,'Dialog Demo') 
    app.MainLoop()
    
