
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
                            x["completion"] = dict[key]
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

def prompt_completion_helper(myPrompt, curr, next_header, previous_header):
    if previous_header:
        myPrompt += " - " + previous_header.text
    else:
        myPrompt += " - " + curr.text
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
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            lst = temp.split(" - ")
            myPrompt = lst[0] + " - " + lst[-1]
            if len(lst) > 2: myPrompt = lst[0] + " - " + lst[1] + " - " + lst[-1] 
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletion
            return a
        else: 
            next_header_size = int(str(next_header)[2])
          
        if not previous_header:
            saved = myPrompt

        if  previous_header != None and curr_header_size < next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            lst = temp.split(" - ")
            myPrompt = lst[0] + " - " + lst[-1]
            if len(lst) > 2: myPrompt = lst[0] + " - " + lst[1] + " - " + lst[-1] 
            myPrompt, duplicates = check_dict_duplicates(myPrompt,a,duplicates)
            a[myPrompt] = myCompletion
            curr = next_header

        elif previous_header != None and curr_header_size == next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            lst = temp.split(" - ")
            myPrompt = lst[0] + " - " + lst[-1]
            if len(lst) > 2: myPrompt = lst[0] + " - " + lst[1] + " - " + lst[-1] 
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
                myPrompt += " - " + curr.text
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
<h2>hi</h2><p>sexy</p>

'''

# soup = BeautifulSoup(tt, "html.parser")
# training_data = prompts_version2("page_title", soup)


# with open("tests.json", "w", encoding="utf8") as file:
#     json.dump(training_data, file, ensure_ascii=False, indent=1)