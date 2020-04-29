import argparse
import json
import os
import cv2
import numpy as np
import skimage
import supervisely_lib as sly

parser = argparse.ArgumentParser(description='Recalculate foreground label')
parser.add_argument('--image-id', action="store", type=int, required=True)
parser.add_argument('--state', action="store", type=json.loads, default={}, required=True)

parser.add_argument('--fg-alpha-threshold', action="store", type=sly.color.validate_channel_value, default=250,
                    help="0 means fully transparent, 255  - no transparency."
                         "keep all pixels with transparency great or equal (>=)")

parser.add_argument('--min-area-percent', action="store", type=sly._utils.validate_percent, default=5,
                    help="remove all objects with small area (%)")

parser.add_argument('--cache-dir', action="store", type=str, default="/sly_task_data/cache", required=False)
parser.add_argument('--vis-dir', action="store", type=str, default="/sly_task_data/vis", required=False)
parser.add_argument('--debug-vis', action="store_true", default=False, required=False)

# example
# --image-id 339 --state "{\"key\":\"val\"}" --debug-vis
#363


def extract_foreground():
    args = parser.parse_args()
    sly.logger.info("arguments", extra={"cmd_args": vars(args)})

    sly.fs.mkdir(args.cache_dir)
    sly.fs.mkdir(args.vis_dir)
    sly.fs.clean_dir(args.vis_dir)

    api = sly.Api.from_env()

    image_path = os.path.join(args.cache_dir, "{}.png".format(args.image_id))
    if not sly.fs.file_exists(image_path):
        api.image.download_path(args.image_id, image_path)
    image = sly.image.read(image_path, remove_alpha_channel=False)
    if image.shape[2] != 4:
        sly.logger.critical("Image (id = {}) does not have alpha channel".format(args.image_id))
    if args.debug_vis:
        sly.image.write(os.path.join(args.vis_dir, '000_image.png'), image, remove_alpha_channel=False)

    alpha = image[:, :, 3]
    mask = (alpha >= args.fg_alpha_threshold).astype(np.uint8) * 255
    if args.debug_vis:
        sly.image.write(os.path.join(args.vis_dir, '001_alpha.png'), mask)

    labeled_image, num_cc = skimage.measure.label(mask, background=0, return_num=True)
    sly.logger.info("find {} connected components".format(num_cc))
    if args.debug_vis:
        vis = skimage.color.label2rgb(labeled_image, bg_label=0)
        sly.image.write(os.path.join(args.vis_dir, '002_components.png'), vis * 255)

    area_pixels = int(labeled_image.shape[0] * labeled_image.shape[1] / 100  * args.min_area_percent)
    cleaned_mask = skimage.morphology.remove_small_objects(labeled_image, area_pixels)
    if args.debug_vis:
        vis = skimage.color.label2rgb(cleaned_mask, bg_label=0)
        sly.image.write(os.path.join(args.vis_dir, '003_components_cleared.png'), vis * 255)



    # total_sum = 0
    # for i in range(num + 1):
    #     comp_mask = (labeled_image == i).astype(np.uint8)
    #     cv2.imwrite(os.path.join(args.vis_dir, "comp_{}.png".format(i)),  comp_mask * 255)
    #     total_sum += comp_mask.sum()
    #     print(comp_mask.sum())
    #
    # sly.logger.info("SCRIPT EXECUTED")
    # print('total_sum = ', total_sum, '; total pixels = ', alpha.shape[0] * alpha.shape[1])




if __name__ == "__main__":
    sly.main_wrapper('EXTRACT_FG_MASK', extract_foreground)
