import json 
import re

def fine_tune_data(json_file):
    prompts_and_completions = []
    for obj in json_file:
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
    with open("scraped_prompts1.json", "w", encoding="utf8") as file:
        json.dump(prompts_and_completions, file, ensure_ascii=False, indent=1)

# get the scraped data
with open("scraped.json", "r", encoding="utf8") as file:
    json_object = json.load(file)

# creates a json file containing {prompts:completions}
fine_tune_data(json_object)
