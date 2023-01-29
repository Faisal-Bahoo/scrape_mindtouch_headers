import json 

def fine_tune_data(json_file):
    prompts_and_completions = []
    for obj in json_file:
        for page_id in obj:
            # ########################################## #
            #  {prompt: none, completion: page_content}  #
            # ########################################## #
            # if obj[page_id]["page_content"] != "":
            #     x = {}
            #     x["prompt"] = ""
            #     x["completion"] = obj[page_id]["page_content"]
            #     prompts_and_completions.append(x)

            # ################################################ #
            #  {prompt: page_title, completion: page_content}  #
            # ################################################ #
            # if obj[page_id]["page_content"] != "":
            #     x = {}
            #     x["prompt"] = obj[page_id]["page_title"]
            #     x["completion"] = obj[page_id]["page_content"]
            #     prompts_and_completions.append(x)

            # ################################################ #
            #  {prompt: header tags, completion: text under }  #
            # ################################################ #
            if len(obj[page_id]["training_data"]) != 0:
                for i,dict in enumerate(obj[page_id]["training_data"]):
                    # print(list(dict.keys())[0])
                    for i,key in enumerate(dict):                    
                        x = {}  
                        x["prompt"] = key + " ->"
                        x["completion"] = dict[key]
                        if dict[key] != "":
                            prompts_and_completions.append(x)

    # save data to a json file
    with open("whitney.json", "w", encoding="utf8") as file:
        json.dump(prompts_and_completions, file, ensure_ascii=False, indent=1)

# get the scraped data
with open("version1.json", "r", encoding="utf8") as file:
    json_object = json.load(file)

# creates a json file containing {prompts:completions}
fine_tune_data(json_object)

