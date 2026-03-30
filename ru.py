from eng_to_ru import Translator


translator = Translator()
text = "Your English text here..."
translated_text = translator.run(text)
print(translated_text)