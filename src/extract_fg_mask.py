import argparse
import json
import os
import time
import cv2
import numpy as np
import skimage
import random
import supervisely_lib as sly
import constants as const

#@TODO: for debug
random.seed(7)


def update_progress(api, task_id, percentage):
    api.task.set_data(task_id, payload=int(percentage), field="{}.{}".format(const.DATA, const.PROGRESS))


def extract_foreground():
    api = sly.Api.from_env()
    task_id = int(os.getenv("TASK_ID"))

    state = api.task.get_data(task_id, field=const.STATE)

    project = api.task.get_data(task_id, field="{}.projects[{}]".format(const.DATA, state["projectIndex"]))
    project_id = project["id"]

    # sample images
    all_images = []
    for dataset in api.dataset.get_list(project_id):
        images = api.image.get_list(dataset.id)
        image_dataset = [dataset] * len(images)
        all_images.extend(zip(images, image_dataset))

    # read sample count
    if state[const.SAMPLE_FLAG]:
        cnt_images = state[const.SAMPLE_COUNT]
        assert cnt_images <= len(all_images)
        random.shuffle(all_images)
        all_images = all_images[:cnt_images]

    sly.fs.mkdir(const.CACHE_DIR)
    for idx, (image_info, dataset_info) in enumerate(all_images):
        image_id = image_info.id
        image_path = os.path.join(const.CACHE_DIR, "{}.png".format(image_id))
        if not sly.fs.file_exists(image_path):
            api.image.download_path(image_id, image_path, )
        image = sly.image.read(image_path, remove_alpha_channel=False)

        if image.shape[2] != 4:
            sly.logger.warning("Image (id = {}) is skipped: it does not have alpha channel".format(image_id))
            continue

        time.sleep(2)
        if (idx % const.NOTIFY_EVERY == 0 and idx != 0) or idx == len(all_images) - 1:
            update_progress(api, task_id, (idx + 1) * 100 / len(all_images))
            need_stop = api.task.get_data(task_id, field="{}.{}".format(const.STATE, const.NEED_STOP))
            if need_stop is True:
                update_progress(api, task_id, -1)
                sly.logger.info("SCRIPT IS STOPPED")
                exit(0)



    # #state = api.ta
    #
    # # args = parser.parse_args()
    # sly.logger.info("arguments", extra={"cmd_args": vars(args)})
    #
    # sly.fs.mkdir(args.cache_dir)
    # sly.fs.mkdir(args.vis_dir)
    # sly.fs.clean_dir(args.vis_dir)
    #
    # api = sly.Api.from_env()
    #
    # image_path = os.path.join(args.cache_dir, "{}.png".format(args.image_id))
    # if not sly.fs.file_exists(image_path):
    #     api.image.download_path(args.image_id, image_path)
    # image = sly.image.read(image_path, remove_alpha_channel=False)
    # if image.shape[2] != 4:
    #     sly.logger.critical("Image (id = {}) does not have alpha channel".format(args.image_id))
    # if args.debug_vis:
    #     sly.image.write(os.path.join(args.vis_dir, '000_image.png'), image, remove_alpha_channel=False)
    #
    # alpha = image[:, :, 3]
    # mask = (alpha >= args.fg_alpha_threshold).astype(np.uint8) * 255
    # if args.debug_vis:
    #     sly.image.write(os.path.join(args.vis_dir, '001_alpha.png'), mask)
    #
    # labeled_image, num_cc = skimage.measure.label(mask, background=0, return_num=True)
    # sly.logger.info("{} connected components".format(num_cc))
    # if args.debug_vis:
    #     vis = skimage.color.label2rgb(labeled_image, bg_label=0)
    #     sly.image.write(os.path.join(args.vis_dir, '002_components.png'), vis * 255)
    #
    # area_pixels = int(labeled_image.shape[0] * labeled_image.shape[1] / 100  * args.min_area_percent)
    # cleaned_mask = skimage.morphology.remove_small_objects(labeled_image, area_pixels)
    # if args.debug_vis:
    #     vis = skimage.color.label2rgb(cleaned_mask, bg_label=0)
    #     sly.image.write(os.path.join(args.vis_dir, '003_components_cleared.png'), vis * 255)
    #
    # final_mask, num_cc = skimage.measure.label(cleaned_mask, background=0, return_num=True)
    # if args.debug_vis:
    #     vis = skimage.color.label2rgb(final_mask, bg_label=0)
    #     sly.image.write(os.path.join(args.vis_dir, '004_final_mask.png'), vis * 255)
    #
    # _total_sum = 0
    # cc_area = []
    # for i in range(num_cc + 1):
    #     area = np.count_nonzero(final_mask == i)
    #     cc_area.append((i, area))
    #     _total_sum += area
    #
    # image_pixels_count = mask.shape[0] * mask.shape[1]
    # if _total_sum != image_pixels_count:
    #     raise RuntimeError("Some pixels are missed. Processed {} of {}".format(_total_sum, image_pixels_count))
    #
    # cc_area = sorted(cc_area, key=lambda tup: tup[1])
    # cc_area = cc_area[:args.num_objects_per_image]
    #
    # #TODO: count background value
    #
    # # create masks in supervisely format
    # fg_class = sly.ObjClass("fg", sly.Bitmap, color=[0, 255, 0])
    # meta = sly.ProjectMeta(obj_classes=[fg_class])
    #
    # sly_labels = []
    # sly.logger.info("Number of extracted objects: {}".format(len(cc_area)))
    # for idx, (cc_color, area) in enumerate(cc_area):
    #     object_mask = (final_mask == cc_color)
    #     if args.debug_vis:
    #         sly.image.write(os.path.join(args.vis_dir, '005_object_{}.png'.format(idx)), object_mask.astype(np.uint8) * 255)
    #     sly_geometry = sly.Bitmap(data=object_mask)
    #     sly_label = sly.Label(sly_geometry, fg_class)
    #     sly_labels.append(sly_label)
    #
    # ann = sly.Annotation(mask.shape[:2], labels=sly_labels)
    # if args.debug_vis:
    #     render = np.zeros(ann.img_size + (3,), dtype=np.uint8)
    #     ann.draw(render)
    #     sly.image.write(os.path.join(args.vis_dir, '006_sly_ann_vis.png'), render)
    # #TODO: ann method for visualizing instances to annotation

    sly.logger.info("SCRIPT EXECUTED")


if __name__ == "__main__":
    sly.main_wrapper('EXTRACT_FG_MASK', extract_foreground)
