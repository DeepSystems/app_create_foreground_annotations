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
                    help="object will be removed if area is less than argument value (%)")

parser.add_argument('--num-objects-per-image', action="store", type=int, default=1,
                    help="how many objects will be extracted from image (with maximum area)")

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

    final_mask, num_cc = skimage.measure.label(cleaned_mask, background=0, return_num=True)
    if args.debug_vis:
        vis = skimage.color.label2rgb(final_mask, bg_label=0)
        sly.image.write(os.path.join(args.vis_dir, '004_final_mask.png'), vis * 255)

    _total_sum = 0
    cc_area = []
    for i in range(num_cc + 1):
        area = np.count_nonzero(final_mask == i)
        cc_area.append((i, area))
        _total_sum += area

    image_pixels_count = mask.shape[0] * mask.shape[1]
    if _total_sum != image_pixels_count:
        raise RuntimeError("Some pixels are missed. Processed {} of {}".format(_total_sum, image_pixels_count))

    cc_area = sorted(cc_area, key=lambda tup: tup[1])
    cc_area = cc_area[:args.num_objects_per_image]

    #TODO: count background value

    # create masks in supervisely format
    fg_class = sly.ObjClass("fg", sly.Bitmap, color=[0, 255, 0])
    meta = sly.ProjectMeta(obj_classes=[fg_class])

    sly_labels = []
    sly.logger.info("Number of extracted objects: {}".format(len(cc_area)))
    for idx, (cc_color, area) in enumerate(cc_area):
        object_mask = (final_mask == cc_color)
        if args.debug_vis:
            sly.image.write(os.path.join(args.vis_dir, '005_object_{}.png'.format(idx)), object_mask.astype(np.uint8) * 255)
        sly_geometry = sly.Bitmap(data=object_mask)
        sly_label = sly.Label(sly_geometry, fg_class)
        sly_labels.append(sly_label)

    ann = sly.Annotation(mask.shape[:2], labels=sly_labels)
    if args.debug_vis:
        render = np.zeros(ann.img_size + (3,), dtype=np.uint8)
        ann.draw(render)
        sly.image.write(os.path.join(args.vis_dir, '006_sly_ann_vis.png'), render)


    sly.logger.info("SCRIPT EXECUTED")


if __name__ == "__main__":
    sly.main_wrapper('EXTRACT_FG_MASK', extract_foreground)
