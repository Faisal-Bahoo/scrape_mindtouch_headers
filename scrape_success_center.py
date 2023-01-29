
import requests
import re
from bs4 import BeautifulSoup, NavigableString, Tag
import xml.etree.ElementTree as ET
import json
import time

session = requests.Session()
headers = {
    'Content-Type': 'application/json', 
}
query = {
    # success center
    # 'authtoken': 'eyJhbGciOiJIUzI1NiIsImtpZCI6Imh0dHBzOi8vbWluZHRvdWNoLmNvbS9hdXRodG9rZW4vZGVraS84MTIiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJodHRwczovL3N1Y2Nlc3MubWluZHRvdWNoLmNvbSIsImV4cCI6MTY3NTA0OTE1OSwiaWF0IjoxNjc0NDg3NTU5LCJzdWIiOjgxMiwiaXNzIjoiaHR0cHM6Ly9zdWNjZXNzLm1pbmR0b3VjaC5jb20vQGFwaS9kZWtpL3NlcnZpY2VzLzMifQ.dylUISbVe5jlowCqW2Jj0ZK9z43LwatZdrk1f51amzw'
    #  me
    'authtoken': "eyJhbGciOiJIUzI1NiIsImtpZCI6Imh0dHBzOi8vbWluZHRvdWNoLmNvbS9hdXRodG9rZW4vZGVraS8xIiwidHlwIjoiSldUIn0.eyJhdWQiOiJodHRwczovL2ZhaXNhbC1iYWhvby10Lm1pbmR0b3VjaC51cyIsImV4cCI6MTY3NTA1MDAzNywiaWF0IjoxNjc0NDg4NDM3LCJzdWIiOjEsImlzcyI6Imh0dHBzOi8vZmFpc2FsLWJhaG9vLXQubWluZHRvdWNoLnVzL0BhcGkvZGVraS9zZXJ2aWNlcy8xIn0.aQu77GqwCCHeBUCN6iIEow1HjdOGlHyUx1CSNBiTL-Q"
}



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
    return myPrompt, myCompletion

# get prompts and completions 
def prompts_version2(page_title,soup):
    headers = soup.find_all(re.compile("^h[1-6]"))
    curr = headers[0]
    curr_header_size = int(str(headers[0])[-2:-1])
    previous_header = None
    myPrompt = page_title
    myCompletion = ""
    a = {}
    saved = ""
    while curr:
        # print(curr)
        next_header = curr.find_next(re.compile("^h[1-6]"))
        if next_header == None: 
            myPrompt, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            a[myPrompt] = myCompletion.strip()
            return a
        else: 
            next_header_size = int(str(next_header)[-2:-1])
          
        if not previous_header:
            saved = myPrompt
            

        if  previous_header != None and curr_header_size < next_header_size:
            myPrompt, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            a[myPrompt] = myCompletion.strip()
            curr = next_header

        elif previous_header != None and curr_header_size == next_header_size:
            myPrompt, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header)
            a[myPrompt] = myCompletion.strip()
            saved = myPrompt
            myPrompt = page_title
            myCompletion = ""
            curr = next_header


        elif  previous_header != None and curr_header_size > next_header_size:
            # myPrompt = page_title + " - " + next_header.text
            myPrompt, myCompletion = prompt_completion_helper(saved, curr, next_header, previous_header)
            a[myPrompt] = myCompletion.strip()
            myPrompt = page_title
            myCompletion = ""
            curr = next_header
            curr_header_size = next_header_size

        
        previous_header = curr

def prompts_version1(page_title,soup):
    headers = soup.find_all(re.compile("^h[1-6]"))
    curr = headers[0]
    largest_header_size = int(str(headers[0])[-2:-1])
    previous_header = None
    myPrompt = page_title
    myCompletion = ""
    myCompletionFull = ""
    a = {}
    while curr:
        next_header = curr.find_next(re.compile("^h[1-6]"))
        if next_header == None: 
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header, "")
            a[temp] = myCompletionFull.strip() + myCompletion
            return a
        else: 
            next_header_size = int(str(next_header)[-2:-1])

        if largest_header_size < next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header, "")
            if myPrompt == page_title:
                myPrompt = temp
            myCompletionFull +=  myCompletion.strip() + " " + next_header.text + " "
            # a[myPrompt] = myCompletion.strip()
            
            curr = next_header

        elif largest_header_size == next_header_size:
            temp, myCompletion = prompt_completion_helper(myPrompt, curr, next_header, previous_header, "")
            print(temp, largest_header_size, next_header_size)
            myCompletionFull += myCompletion
            if not previous_header:
                a[temp] = myCompletionFull.strip()
            else:
                a[myPrompt] = myCompletionFull.strip()
            myPrompt = page_title
            myCompletionFull = ""
            curr = next_header

        elif largest_header_size > next_header_size:
            curr = next_header
        
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
            # start_page = requests.get(('https://success.mindtouch.com/@api/deki/pages/{start_page}/subpages').format(start_page=key), headers=headers, params=query)
            start_page = requests.get(('https://faisal-bahoo-t.mindtouch.us/@api/deki/pages/{start_page}/subpages').format(start_page=key), headers=headers, params=query)
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
                # page_text = requests.get(('https://success.mindtouch.com/@api/deki/pages/{start_page}/contents').format(start_page=key), headers=headers, params=query)
                page_text = requests.get(('https://faisal-bahoo-t.mindtouch.us/@api/deki/pages/{start_page}/contents').format(start_page=key), headers=headers, params=query)
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
                    training_data = prompts_version2(page_title, soup)
                    dictionary[key]['training_data'].append(training_data)


    # save to json file
    # with open("dicts.json", "w", encoding="utf8") as file:
    #     json.dump(dicts, file, ensure_ascii=False, indent=1)
    with open("tests.json", "w", encoding="utf8") as file:
        json.dump(dicts, file, ensure_ascii=False, indent=1)

# getTrueSubpages(282)



# testing
tt = '''
<div class="mt-page-summary"><div class="mt-page-overview"></div></div> <a class="new" href="https://faisal-bahoo-t.mindtouch.us/Template:Custom/List_Subpages_If_Exists" rel="internal">List Subpages If Exists</a> <p>Introductory remarks and summary of the article below. Optionally this could&nbsp;be a page summary, depending on how clients are formatting things.</p> <p>Our company is at the forefront of the Artificial Intelligence testing industry. We strive to offer the highest quality and most accurate testing results. Our cutting-edge AI testing technology is revolutionizing the AI testing industry and providing our customers with unprecedented accuracy and performance. With our innovative and visionary approach, we are able to stay ahead of the curve and deliver the best possible results to our customers.</p> <p>We are proud to be a market leader in the AI testing industry, providing our customers with the most accurate and cutting-edge testing solutions. Our visionary approach ensures that we remain ahead of the curve and continue to provide the best possible results to our clients.</p> <div mt-section-origin="Testing/category_test_for_wiki/another_guide_here/article_stuff_test" class="mt-section" id="section_1"><span id="Luminary_Vision"></span><h1 class="editable">Luminary Vision</h1> <p>Some information pertaining to this Luminary Vision. This is mission critical to delivering value to our customers! Below is&nbsp;a 2-point plan on how we'll rapidly execute on this vision.</p> <div mt-section-origin="Testing/category_test_for_wiki/another_guide_here/article_stuff_test" class="mt-section" id="section_2"><span id="Transformation"></span><h3 class="editable">Transformation</h3> <p>Transformation involves an 2-pronged approach: Extraction, and Transformation.</p> <div mt-section-origin="Testing/category_test_for_wiki/another_guide_here/article_stuff_test" class="mt-section" id="section_3"><span id="Extract"></span><h4 class="editable">Extract</h4> <p>Customers need to give us the data. It's going to suck, so next we need to...</p> <p>Here's a bullet list of the various ways to supply terrible data, just to drive home how easy it is to deliver garbage:</p> <ul> <li>CSV data that contains commas in cell contents</li> <li>CSV data with a separator other than commas, and no notice of the new separator value</li> <li>Supplying an XLSX file when we requested a CSV</li> <li>Sending a zip file of 1000's of txt files</li> </ul> </div><div mt-section-origin="Testing/category_test_for_wiki/another_guide_here/article_stuff_test" class="mt-section" id="section_4"><span id="Transform"></span><h4 class="editable">Transform</h4> <p>Technical mumbo jumbo...</p> <pre class="brush: python; collapse: false; first-line: 1; gutter: true; ruler: false; toolbar: true; wrap-lines: true; "> def CodeToBeIgnored(): cheese = &quot;String_Cheese&quot; cheeseTokens = cheese.split('_') # return list of cheese tokens </pre> </div></div><div mt-section-origin="Testing/category_test_for_wiki/another_guide_here/article_stuff_test" class="mt-section" id="section_5"><span id="Deliver"></span><h3 class="editable">Deliver</h3> <p>At our company, we are proud to offer rapid value delivery with our cutting-edge AI testing technology. We strive to stay ahead of the curve by providing our customers with the most accurate and efficient results. Our innovative and visionary approach ensures that our customers can stay ahead of the competition and get the highest quality results in the shortest amount of time. Our AI testing solutions are revolutionizing the industry and providing our customers with unprecedented accuracy and performance.</p> </div></div><div mt-section-origin="Testing/category_test_for_wiki/another_guide_here/article_stuff_test" class="mt-section" id="section_6"><span id="Stagnant_Vision"></span><h2 class="editable">Stagnant Vision</h2> <p>Alternate vision for the company. Just included to make Section 1 the obvious choice, but to allow decision makers to feel like the contributed to the project. Below is a streamlined 1-part plan on how to execute this vision.</p> <div mt-section-origin="Testing/category_test_for_wiki/another_guide_here/article_stuff_test" class="mt-section" id="section_7"><span id="Ignore_Customers"></span><h3 class="editable">Ignore Customers</h3> <p>Our AI testing technology is designed to provide our customers with the most accurate and efficient results without sacrificing quality. Our cutting-edge technology allows us to deliver rapid value without having to wait for customer feedback. By leveraging the latest AI technology, we are able to provide our customers with the highest quality results in the shortest amount of time. Our innovative and visionary approach ensures that our customers get the best results without having to wait for customer feedback. With our AI testing technology, our customers can stay ahead of the competition and get the highest quality results without having to wait for customer feedback.</p> </div></div>
'''

soup = BeautifulSoup(tt, "html.parser")
training_data = prompts_version2("page_title", soup)


with open("tests.json", "w", encoding="utf8") as file:
    json.dump(training_data, file, ensure_ascii=False, indent=1)