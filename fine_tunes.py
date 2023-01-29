import os
import openai
openai.api_key = "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"
openai.Model.delete("davinci:ft-yellow-team:full-success-center-with-titles-2023-01-25-00-20-38")
all_fine_tunes = openai.FineTune.list()
print(all_fine_tunes)



# first_dataset = openai.FineTune.retrieve(id="ft-54WMWGqODA0lAddI4a8kJ5jW")
# print(first_dataset)

# second_dataset = openai.FineTune.retrieve(id="ft-I9KoB8XI9gf9cf8UnJ2u8SBf")
# print(second_dataset)