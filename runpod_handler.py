import os
import uuid
import torch
import runpod
import tempfile
import traceback
from diffusers.utils import load_image
from huggingface_hub import hf_hub_download
from diffusers import EulerDiscreteScheduler, DDIMScheduler

from photomaker import PhotoMakerStableDiffusionXLPipeline
from firebase_manager import upload_file_to_firebase

# gloal variable
base_model_path = 'SG161222/RealVisXL_V3.0'
device = "cuda"

def run(job):
    try:
        # Check if 'input' key exists in the job object
        if "input" not in job:
            return {"error": "Input data is missing 'input' key"}

        photomaker_ckpt = hf_hub_download(
            repo_id="TencentARC/PhotoMaker", filename="photomaker-v1.bin", repo_type="model"
        )
        pipe = PhotoMakerStableDiffusionXLPipeline.from_pretrained(
            base_model_path, torch_dtype=torch.bfloat16, use_safetensors=True, variant="fp16"
        ).to(device)
        pipe.load_photomaker_adapter(
            os.path.dirname(photomaker_ckpt),
            subfolder="",
            weight_name=os.path.basename(photomaker_ckpt),
            trigger_word=job["input"].get("trigger_word", "img"),
        )
        pipe.id_encoder.to(device)
        # pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        # pipe.fuse_lora()
        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
        # pipe.set_adapters(["photomaker"], adapter_weights=[1.0])
        pipe.fuse_lora()

        # define and show the input ID images
        input_id_images = []
        for image_path in job["input"].get("input_image_urls", []):
            print(f"Adding image to list: {image_path}")
            input_id_images.append(load_image(image_path))

        ## Note that the trigger word `img` must follow the class word for personalization
        prompt = job["input"].get("prompt")
        negative_prompt = job["input"].get("negative_prompt")

        if not prompt or not input_id_images:
            return {"error": "Missing prompt or invalid image URLs"}

        generator = torch.Generator(device=device).manual_seed(42)

        ## Parameter setting
        num_steps = int(job["input"].get("num_steps", 50))
        style_strength_ratio = int(job["input"].get("style_strength_ratio", 20))
        start_merge_step = int(float(style_strength_ratio) / 100 * num_steps)
        if start_merge_step > 30:
            start_merge_step = 30

        images = pipe(
            prompt=prompt,
            input_id_images=input_id_images,
            negative_prompt=negative_prompt,
            num_images_per_prompt=4,
            num_inference_steps=num_steps,
            start_merge_step=start_merge_step,
            generator=generator,
        ).images

        print("Uploading images to Firebase.")
        image_urls = []
        file_id = uuid.uuid4().hex[:6]
        with tempfile.TemporaryDirectory() as temp_dir:
            for idx, image in enumerate(images):
                filename = f"{file_id}_{idx:02d}.png"
                filepath = os.path.join(temp_dir, filename)
                uploadpath = f"PhotoMaker/outputs/{filename}"
                image.save(filepath)
                image_urls.append(f"{upload_file_to_firebase(filepath, uploadpath)}?alt=media")

        print("Images successfully uploaded to Firebase")
        result = {"message": "Image generation completed successfully", "image_urls": image_urls}
        return result
    except Exception as e:
        error_message = f"Error running inference: {e}"
        return {"error": error_message, "traceback": traceback.format_exc()}


runpod.serverless.start({"handler": run})
