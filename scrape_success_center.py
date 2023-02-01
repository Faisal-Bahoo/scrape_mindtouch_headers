
import requests
import re
from bs4 import BeautifulSoup, NavigableString
import xml.etree.ElementTree as ET
import json
import time
import os.path

session = requests.Session()
headers = {
    'Content-Type': 'application/json', 
}
query = {
    # success center
    'authtoken': 'eyJhbGciOiJIUzI1NiIsImtpZCI6Imh0dHBzOi8vbWluZHRvdWNoLmNvbS9hdXRodG9rZW4vZGVraS84MTIiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJodHRwczovL3N1Y2Nlc3MubWluZHRvdWNoLmNvbSIsImV4cCI6MTY3NTYxMTE4NCwiaWF0IjoxNjc1MDQ5NTg0LCJzdWIiOjgxMiwiaXNzIjoiaHR0cHM6Ly9zdWNjZXNzLm1pbmR0b3VjaC5jb20vQGFwaS9kZWtpL3NlcnZpY2VzLzMifQ.E2Lzls8uiCEHsv3_knq7leQZUjgurZ11hLKMqV3Rtg4'
    #  me
    # 'authtoken': "eyJhbGciOiJIUzI1NiIsImtpZCI6Imh0dHBzOi8vbWluZHRvdWNoLmNvbS9hdXRodG9rZW4vZGVraS8xIiwidHlwIjoiSldUIn0.eyJhdWQiOiJodHRwczovL2ZhaXNhbC1iYWhvby10Lm1pbmR0b3VjaC51cyIsImV4cCI6MTY3NTA1MDAzNywiaWF0IjoxNjc0NDg4NDM3LCJzdWIiOjEsImlzcyI6Imh0dHBzOi8vZmFpc2FsLWJhaG9vLXQubWluZHRvdWNoLnVzL0BhcGkvZGVraS9zZXJ2aWNlcy8xIn0.aQu77GqwCCHeBUCN6iIEow1HjdOGlHyUx1CSNBiTL-Q"
}
def generate_prompts_file():
    check_file = os.path.isfile("./scraped.json")
    if check_file:
        # open the scraped file
        with open("scraped.json", "r", encoding="utf8") as file:
            json_objects = json.load(file)
        # get the prompts and completions        
        prompts_and_completions = []
        for obj in json_objects:
            for page_id in obj:
                if len(obj[page_id]["training_data"]) != 0:
                    for dict in obj[page_id]["training_data"]:
                        for key in dict:                                
                            x = {}  
                            check_duplicate = re.match("^<- ", key)
                            if check_duplicate:
                                k = k.replace("<- ", "")
                            else: k = key                
                            x["prompt"] = k + " ->"
                            x["completion"] = dict[key] + "\n\n###\n\n"
                            if dict[key] != "":
                                prompts_and_completions.append(x)

    # save data to a json file
    with open("scraped_prompts.json", "w", encoding="utf8") as file:
        json.dump(prompts_and_completions, file, ensure_ascii=False, indent=1)

def check_dict_duplicates(myPrompt, a, duplicates):
    if myPrompt in a:   
        duplicates += 1
        myPrompt = f"{'<- '*duplicates}" + myPrompt
    return myPrompt, duplicates

# Get text before the first header tag on a page
def pre_heading_text(soup):
    pre_heading_text = {}
    # find the first header tag
    for el in soup.find(re.compile("^h[1-6]")).previous_elements:
        if el.text != soup.find(re.compile("^h[1-6]")).parent.text and el.text not in pre_heading_text:
            pre_heading_text[el.text.replace("\xa0", " ")] = 0
    pre_heading_text = list(pre_heading_text.keys())
    pre_heading_text.reverse()
    pre_heading_text = ' '.join(pre_heading_text).strip()
    return pre_heading_text

def prompt_completion_helper(myPrompt, curr, next_header, previous_header,version3):
    if previous_header and version3:
        myPrompt += " ^&* " + previous_header.text
    elif not previous_header and version3:
        myPrompt += " ^&* " + curr.text
    elif previous_header and not version3:
        myPrompt += " " + previous_header.text
    else:
        myPrompt += " " + curr.text
    myCompletion = ""
    while curr.next_element and curr.next_element != next_header:
        if isinstance(curr.next_element, NavigableString):
            if curr.next_element.text != curr.text:
               myCompletion += curr.next_element.text
        curr.next_element = curr.next_element.next_element

    myCompletion = re.sub(r'\n+', " ", myCompletion)
    myCompletion = re.sub(r'\s+', " ", myCompletion)
    return myPrompt, myCompletion.strip()

# get prompts and completions 
def prompts_version3(page_title,soup):
    headers = soup.find_all(re.compile("^h[1-6]"))
    curr = headers[0]
    curr_header_size = int(str(headers[0])[2])
    previous_header = None
    myPrompt = page_title
    myCompletion = ""
    a = {}
    saved = ""
    duplicates = 0
    while curr:
        next_header = curr.find_next(re.compile("^h[1-6]"))
        if next_header == None: 
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header, True)
            lst = temp.split(" ^&* ")
            myPrompt = lst[0] + " ^&* " + lst[-1]
            if len(lst) > 2: myPrompt = lst[0] + " ^&* " + lst[1] + " ^&* " + lst[-1] 
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            z = myPrompt.replace(" ^&* ", " ")
            a[z] = myCompletion
            return a
        else: 
            next_header_size = int(str(next_header)[2])
          
        if not previous_header:
            saved = myPrompt

        if  previous_header != None and curr_header_size < next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header, True)
            lst = temp.split(" ^&* ")
            myPrompt = lst[0] + " ^&* " + lst[-1]
            if len(lst) > 2: myPrompt = lst[0] + " ^&* " + lst[1] + " ^&* " + lst[-1] 
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            z = myPrompt.replace(" ^&* ", " ")
            a[z] = myCompletion
            curr = next_header

        elif previous_header != None and curr_header_size == next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header, True)
            lst = temp.split(" ^&* ")
            myPrompt = lst[0] + " ^&* " + lst[-1]
            if len(lst) > 2: myPrompt = lst[0] + " ^&* " + lst[1] + " ^&* " + lst[-1] 
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            z = myPrompt.replace(" ^&* ", " ")
            a[z] = myCompletion
            saved = myPrompt
            myPrompt = page_title
            myCompletion = ""
            curr = next_header

        elif  previous_header != None and curr_header_size > next_header_size:
            myPrompt, myCompletion = prompt_completion_helper(saved, curr, next_header, previous_header, True)
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            myPrompt = myPrompt.replace(" ^&* ", " ")
            a[myPrompt] = myCompletion
            myPrompt = page_title
            myCompletion = ""
            curr = next_header
            curr_header_size = next_header_size
        
        previous_header = curr

def prompts_version2(page_title,soup):
    headers = soup.find_all(re.compile("^h[1-6]"))
    curr = headers[0]
    curr_header_size = int(str(headers[0])[2])
    previous_header = None
    myPrompt = page_title
    myCompletion = ""
    a = {}
    saved = ""
    duplicates = 0

    while curr:
        next_header = curr.find_next(re.compile("^h[1-6]"))
        if next_header == None: 
            myPrompt, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletion
            return a
        else: 
            next_header_size = int(str(next_header)[2])
          
        if not previous_header:
            saved = myPrompt

        if  previous_header != None and curr_header_size < next_header_size:
            myPrompt, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletion
            curr = next_header

        elif previous_header != None and curr_header_size == next_header_size:
            myPrompt, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletion
            saved = myPrompt
            myPrompt = page_title
            myCompletion = ""
            curr = next_header

        elif  previous_header != None and curr_header_size > next_header_size:
            myPrompt, myCompletion = prompt_completion_helper(saved, curr, next_header, previous_header)
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletion
            myPrompt = page_title
            myCompletion = ""
            curr = next_header
            curr_header_size = next_header_size
        
        previous_header = curr

def prompts_version1(page_title,soup):
    curr = soup.find(re.compile("^h[1-6]"))
    largest_header_size = int(str(curr)[2])
    previous_header = None
    myPrompt = page_title
    myCompletion = ""
    myCompletionFull = ""
    a = {}
    duplicates = 0
    while curr:
        next_header = curr.find_next(re.compile("^h[1-6]"))
        temp = myPrompt
        if next_header == None: 
            temp, myCompletion = prompt_completion_helper(temp, curr, next_header, previous_header)
            if myPrompt != page_title:
                myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
                a[myPrompt] = myCompletionFull + myCompletion
            else:
                temp, duplicates = check_dict_duplicates(temp,a,duplicates)
                a[temp] = myCompletionFull + myCompletion
            return a
        else: 
            next_header_size = int(str(next_header)[2])

        if previous_header != None and largest_header_size < next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            if myPrompt == page_title:
                myPrompt = temp
            myCompletionFull +=  myCompletion 
            curr = next_header

        elif previous_header != None and largest_header_size == next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            myCompletionFull += myCompletion
            if myPrompt == page_title:
                myPrompt += " " + curr.text
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletionFull
            myPrompt = page_title
            myCompletionFull = ""
            curr = next_header

        elif previous_header != None and largest_header_size > next_header_size:
            myPrompt, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletion
            myPrompt = page_title
            myCompletion = ""
            curr = next_header
            largest_header_size = next_header_size
        
        previous_header = curr



# get each subpage if it has subpages
def getTrueSubpages(pid):
    page_id_dictionary = {"page_restrictions": "", "page_tags":"", "subpages":"","page_title":"","page_content":"", "training_data":[]}
    dicts = [{pid: page_id_dictionary}]
    for i,dictionary in enumerate(dicts):
        print("page count:", i+1)
        if i+1 % 1000 == 0: time.sleep(30)
        for key in dictionary:
            print("page_id: ", key)
            # The page to check
            start_page = requests.get(('https://success.mindtouch.com/@api/deki/pages/{start_page}/subpages').format(start_page=key), headers=headers, params=query)
            # start_page = requests.get(('https://faisal-bahoo-t.mindtouch.us/@api/deki/pages/{start_page}/subpages').format(start_page=key), headers=headers, params=query)
            tree = ET.fromstring(start_page.content)

            # get subpages
            for page in tree.findall('page.subpage'):
                subpages_value = page.get('subpages')
                page_id = int(page.get('id'))
                page_restrictions = page.find("restriction").text
                page_tags = page.find("article").text
                dicts.append({page_id: {"page_restrictions": page_restrictions, "page_tags":page_tags, "subpages":str(subpages_value),"page_title":"","page_content":"", "training_data":[]}})        

            # get page title and content for articles
            if (dictionary[key]['page_restrictions'] == "Public" or dictionary[key]['page_restrictions'] == "Semi-Public") and (dictionary[key]['page_tags'] == "topic" or dictionary[key]['page_tags'] == "howto" or dictionary[key]['page_tags'] == "reference"):
                page_text = requests.get(('https://success.mindtouch.com/@api/deki/pages/{start_page}/contents').format(start_page=key), headers=headers, params=query)
                # page_text = requests.get(('https://faisal-bahoo-t.mindtouch.us/@api/deki/pages/{start_page}/contents').format(start_page=key), headers=headers, params=query)
                contents_tree = ET.fromstring(page_text.content)
                soup = BeautifulSoup(contents_tree.find("body").text, features="html.parser")
                page_title = contents_tree.attrib["title"]
                page_content = re.sub(r'\n+', ' ', soup.get_text()).replace(u"\u00a0", " ").strip()
                page_content = re.sub(r'\s+', " ", page_content)
                dictionary[key]['page_title'] = page_title
                dictionary[key]['page_content'] = page_content
                #check if theres any header tags on the page
                headings = soup.find_all("div", class_="mt-section")
                if page_content == "": continue
                if not headings:
                    dictionary[key]['training_data'] = [{page_title:page_content}]                    
                else:
                    # get the text above the first header as {page_title:text}
                    top_text = pre_heading_text(soup)
                    if top_text != "":
                        dictionary[key]['training_data'] = [{page_title:top_text}]
                    # get headers sections
                    training_data = prompts_version3(page_title, soup)
                    dictionary[key]['training_data'].append(training_data)


    # save to json file
    with open("scraped.json", "w", encoding="utf8") as file:
        json.dump(dicts, file, ensure_ascii=False, indent=1)

startTime = time.time()
getTrueSubpages(1)
elapsedTime = time.time() - startTime
generate_prompts_file()
elapsedTime = time.strftime("%H:%M:%S", time.gmtime(elapsedTime))
print("Elapsed Time: " + str(elapsedTime))

# testing
tt = '''
<div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section" id="section_1"><span id="Release_2016-10-06"></span><h2 class="editable">Release 2016-10-06</h2> <div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section" id="section_2"><span id="Feature_enhancements"></span><h3 class="editable">Feature enhancements</h3> <header style="display:block"> <ul> <li>Responsive tables in&nbsp;MindTouch&nbsp;4 <ul> <li>Tables in MindTouch&nbsp;4 now have the option to be set to responsive.&nbsp;</li> <li>Tables existing prior to this feature implementation can be made responsive through the table's properties.</li> <li>Feature requires the latest version of DekiScript.&nbsp;<a target="_blank" title="Submit case" href="https://success.mindtouch.com/Admin/Contact/Submit_case" rel="internal">Contact Support</a>&nbsp;if you would like to enable the latest version of DekiScript.</li> </ul> </li> </ul> <div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Bug_fixes"></span><h3 class="editable">Bug fixes</h3> <ul> <li><strong>File attachment ID</strong><br /> Copying&nbsp;pages with embedded files was not changing the file's&nbsp;attachment IDs. Copied files on copied pages now&nbsp;reference their correct file IDs.</li> <li><strong>Contextual help on IOS&nbsp;devices</strong><br /> Fixed an issue where users could not scroll&nbsp;through&nbsp;contextual help content on IOS&nbsp;devices.</li> <li><strong>HTTPS and /@api/deki/ endpoints</strong><br /> HTTPS is now properly&nbsp;enforced&nbsp;for the /@api/deki/ endpoint.</li> </ul> </div><div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Release_2016-10-13"></span><h2 class="editable">Release 2016-10-13</h2> <div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Security_enhancements"></span><h3 class="editable">Security enhancements</h3> <ul> <li><strong><strong>X-XSS-Protection&nbsp;HTTP&nbsp;header enabled</strong></strong><br /> We've enhanced our existing protection against cross site scripting by enabling this web server configuration. This prevents malicious code from being executed in the users browser.</li> <li><strong><strong>X-Content-Type-Options HTTP header enabled</strong></strong><br /> We've enabled&nbsp;this web server configuration&nbsp;to ensure that the file type&nbsp;delivered is the file type it executes. This is to prevent a browser security vulnerability in which malicious content is accessed as long as it had a valid file type.</li> </ul> </div><div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Bug_fixes_2"></span><h3 class="editable">Bug fixes</h3> <ul> <li><strong><strong>Find and replace search experience</strong></strong><br /> Finding and replacing text through the editor no longer forces the browser to scroll to the top of the page, regardless of where the text is located.</li> <li><strong><strong>Spell check suggestions</strong></strong><br /> Spell check suggestions for words&nbsp;that are lower case are now accurately displayed as such in the&nbsp;suggestion menu.</li> <li><strong><strong>Color selector options</strong></strong><br /> Fixed an issue&nbsp;where&nbsp;colors were not displaying correctly in the editor&nbsp;via the&nbsp;<strong><strong>Text color&nbsp;</strong></strong>&gt;&nbsp;<strong><strong>More Colors</strong></strong>&nbsp;option.</li> </ul> </div></div><div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Release_2016-10-20"></span><h2 class="editable">Release 2016-10-20</h2> <div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Feature_enhancements_2"></span><h3 class="editable">Feature enhancements</h3> <ul> <li><strong><strong>Minor jQuery upgrade</strong></strong><br /> We have&nbsp;upgraded&nbsp;from version 1.11.3 to version 2.2.4 for minor bug fixes. While this appears to be a giant version leap, this upgrade will not have any substantial changes to the user experience.&nbsp;This&nbsp;upgrades the base library and does not affect&nbsp;jQuery UI.</li> </ul> </div><div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Bug_fixes_3"></span><h3 class="editable">Bug fixes</h3> <ul> <li><strong><strong>Anchor scroll position</strong></strong><br /> Fixed an issue where the browser did not scroll to the correct anchor position on page load. This was due to content loading above the anchor, after it had already scrolled to the anchor prior.</li> </ul> </div><div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Upcoming_feature_upgrade"></span><h3 class="editable">Upcoming feature upgrade</h3> <ul> <li><strong><strong>Attachment streaming</strong></strong><br /> We are in the process of changing the way we stream attachments in MindTouch so we can increase the speed of serving them to our customers across the world. Current links to attachments will not require code changes on your part. In the coming weeks we will be testing out this change internally and with a select group of beta testers. When we are finished testing, we will announce a release date and documentation that will explain the details of this new functionality.</li> </ul> </div></div><div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Release_2016-10-27"></span><h2 class="editable">Release 2016-10-27</h2> <div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Feature_enhancements_3"></span><h3 class="editable">Feature enhancements</h3> <ul> <li><strong><strong>Dashboard update</strong></strong><br /> We have removed obsolete MindTouch Success Center links from the Dashboard.</li> <li><strong><strong>Revision history quick links</strong></strong><br /> In MindTouch 4, on revision history, comparison, and view pages, the quick links for&nbsp;<strong><strong>view current revision</strong></strong>&nbsp;and&nbsp;<strong><strong>view revision history</strong></strong>&nbsp;that appeared in the right tray have been moved over into the content container near the page title.</li> </ul> <h3bug fixes=""> <ul> <li><strong><strong>Editor dialog hovers</strong></strong><br /> Fixed the background color of the anchor, table properties, and paste dialogs in the editor that were changing when a mouse hovered over them.</li> </ul> <div mt-section-origin="Admin/Release_Notes/2016/10-October" class="mt-section"><span id="Upcoming_feature_upgrade_2"></span><h3 class="editable">Upcoming feature upgrade</h3> <ul> <li><strong><strong>Attachment streaming</strong></strong><br /> We are in the process of changing the way we stream attachments in MindTouch so we can increase the speed of serving them to our customers across the world. Current links to attachments will not require code changes on your part. In the coming weeks, we will be testing out this change internally and with a select group of beta testers. When we are finished testing, we will announce a release date and documentation that will explain the details of this new functionality.</li> <li><strong><strong>HelpRequest data</strong></strong><br /> You may have&nbsp;<a href="https://mindtouch.com/ninjas/customer-insights-powered-new-data/" rel="external nofollow" target="_blank">read about how</a>&nbsp;we&rsquo;ve enhanced the way we compute and power the terabytes of data coming through MindTouch. Soon we will be providing the ability to download HelpRequest data. HelpRequests are an atomic unit of help delivered to a user across multiple channels such as your success center (page views, searches, etc) and in-product contextual help. Soon you will be able to take a look at the raw information to help you gain even more insights into how your site is being used.</li> </ul> </div></h3bug></div></div></header> </div></div>
'''

# soup = BeautifulSoup(tt, "html.parser")
# training_data = prompts_version3("page_title", soup)


# with open("tests.json", "w", encoding="utf8") as file:
#     json.dump(training_data, file, ensure_ascii=False, indent=1)