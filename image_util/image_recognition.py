import requests
from PIL import Image
from transformers import AutoProcessor, BlipForQuestionAnswering
from translate import Translator

from openai_util.function_call.openaifunc_decorator import openai_func

translator = Translator(to_lang='en', from_lang='zh')

model = None
processor = None


@openai_func
def answer_by_image_url_and_text(image: str, prompt: str):
    """
    Answer according to the user's description and picture url or picture path.
    the prompt must be in English

    :param image:URL of the picture
    :param prompt:user tips. must use english
    :return:generated description
    """
    global model, processor
    if not model:
        model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")
    if not processor:
        processor = AutoProcessor.from_pretrained("Salesforce/blip-vqa-base")
    if str.startswith(image, 'http'):
        image = Image.open(requests.get(image, stream=True).raw)
    else:
        image = Image.open(image)
    inputs = processor(images=image, text=translator.translate(prompt), return_tensors="pt")
    return processor.decode(model.generate(**inputs, max_length=4000)[0], skip_special_tokens=True)

# print(answer_by_image_url_and_text("temp.jpg", "what am i holding"))
