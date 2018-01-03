#coding: utf-8

import xml.etree.ElementTree as ET

class parseresult(object):
    def __init__(self,file):
        self.file=file
        self.unique_id=1
        self.root=ET.parse(self.file).getroot()
        
    def parse_specified_tc(self,tcname):
        for item in self.root.iterfind('suite/test'):
            if item.attrib['name'] == tcname:
                if self._check_tc_status(item):
                    return self.fetch_pass_tc_info(item)
                else:
                    return self.fetch_fail_tc_info(item)

    def parse_all_tc(self):
        ts_result=[]
        for tc in self.root.iterfind('suite/test'):
            if self._check_tc_status(tc):
                ts_result.append(self.fetch_pass_tc_info(tc))
            else:
                ts_result.append(self.fetch_fail_tc_info(tc))
        return ts_result
    
    def parse_all_tc_gen(self):
        for tc in self.root.findall('suite/test'):
            if self._check_tc_status(tc):
                yield self.fetch_pass_tc_info(tc)
            else:
                yield self.fetch_fail_tc_info(tc)
            
    def _check_tc_status(self,element):
        if len(element.findall('status')) != 1:
            raise Exception('the test case result is not in correct format')
        status_ele=element.findall('status')[0]
        tc_status=status_ele.attrib['status']
        if tc_status == 'PASS':
            return True
        elif tc_status == 'FAIL':
            return False
        else:
            message = 'the test case result %s can not be identified' % tc_status
            raise Exception(message)
                
    def fetch_pass_tc_info(self,element):
        pass_tc_info=[]
        tc_name=element.attrib['name']
        status_ele=element.findall('status')[0]
        tc_status=status_ele.attrib['status']
        pass_tc_info.append(tc_name)
        pass_tc_info.append(tc_status)
        pass_tc_info.append(status_ele.attrib['starttime'])
        pass_tc_info.append(status_ele.attrib['endtime'])
        return pass_tc_info
        
    def fetch_fail_tc_info(self,element):
        fail_tc_info=[]
        tc_name=element.attrib['name']
        status_ele=element.findall('status')[0]
        tc_status=status_ele.attrib['status']
        fail_tc_info.append(tc_name)
        fail_tc_info.append(tc_status)
        fail_tc_info.append(status_ele.attrib['starttime'])
        fail_tc_info.append(status_ele.attrib['endtime'])
        fail_tc_info.append([])
        for kw in element.findall('kw'):
            if not self._check_kw_status(kw):
                fail_tc_info[4].extend(self._fetch_fail_kw_msg(kw))
        return fail_tc_info        
    
    def _check_kw_status(self,element):
        if len(element.findall('status')) != 1:
            raise Exception('the keyword result is not in correct format')
        status_ele=element.findall('status')[0]
        tc_status=status_ele.attrib['status']
        if tc_status == 'PASS':
            return True
        elif tc_status == 'FAIL':
            return False
        else:
            message = 'the keyword result %s can not be identified' % tc_status
            raise Exception(message)
        
            
    def _fetch_fail_kw_msg(self,element):
        fail_kw_msg=[]
        kw_name=element.attrib['name']
        for ele in element.findall('msg'):
            if ele.text and ele.attrib.has_key('timestamp') and ele.attrib.has_key('level'):
                message = kw_name + '/' + ele.attrib['timestamp'] + '/' + ele.attrib['level'] + '/' + ele.text
                fail_kw_msg.append(message)
        return fail_kw_msg
        
    def _walkData(self,root_node, level, result_list):
        temp_list =[self.unique_id, level, root_node.tag, root_node.attrib,root_node.text,root_node.tail]
        result_list.append(temp_list)
        self.unique_id +=1
        
        children_node = root_node.getchildren()
        if len(children_node) == 0: 
            return
        for child in children_node:
            self._walkData(child, level + 1, result_list)
        return  
        
    def getXmlData(self):
        level = 1
        result_list = [] 
        self._walkData(self.root, level, result_list)
        for item in result_list:
            print item

if __name__ == '__main__':
    file='C:/Users/TOSHIBA/Desktop/2012/output.xml'
    result=parseresult(file)
    #temp=result.getXmlData()
    #result.parse_one_tc_1('shoppingwebsite.mainpage.login')
    tmp=result.parse_all_tc_gen()
    for item in tmp:
        print item
    
    print result.parse_specified_tc('shoppingwebsite.mainpage.login2')           