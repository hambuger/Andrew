import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from openai_util.function_call.openaifunc_decorator import openai_func

model_id = "stabilityai/stable-diffusion-2-1"

pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
# pipe = pipe.to("cuda")


@openai_func
def text_to_image(text: str):
    """
    generate image from text with english
    :param text: the text use english, for example: "a phone of a dog"
    """
    image = pipe(text).images[0]
    image.save(f"""/tmp/{text}.png""")
    return f"""/tmp/{text}.png"""
