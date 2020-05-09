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
from supervisely_lib.annotation.json_geometries_map import GET_GEOMETRY_FROM_STR

#@TODO: for debug
random.seed(7)


def update_progress(api, task_id, percentage):
    api.task.set_data(task_id, payload=int(percentage), field="{}.{}".format(const.DATA, const.PROGRESS))


def count_instances_area(mask, cc_count):
    _total_sum = 0
    cc_area = []
    for i in range(cc_count + 1):
        area = np.count_nonzero(mask == i)
        cc_area.append((i, area))
        _total_sum += area
    image_pixels_count = mask.shape[0] * mask.shape[1]
    if _total_sum != image_pixels_count:
        raise AssertionError("Some pixels are missed. Processed {} of {}".format(_total_sum, image_pixels_count))
    cc_area = sorted(cc_area, key=lambda tup: tup[1])
    return cc_area


def extract_foreground():
    api = sly.Api.from_env()
    task_id = int(os.getenv("TASK_ID"))

    state = api.task.get_data(task_id, field=const.STATE)

    project = api.task.get_data(task_id, field="{}.projects[{}]".format(const.DATA, state[const.PROJECT_INDEX]))
    project_id = project["id"]

    workspace_id = api.project.get_info_by_id(project_id).workspace_id
    team_id = api.workspace.get_info_by_id(workspace_id).team_id

    processed_items = []
    api.task.set_data(task_id, payload=processed_items, field="{}.{}".format(const.DATA, const.TABLE))

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

    fg_class = sly.ObjClass(state[const.FG_NAME],
                            GET_GEOMETRY_FROM_STR(state[const.FG_SHAPE]),
                            color=sly.color.hex2rgb(state[const.FG_COLOR]))
    st_class = sly.ObjClass(state[const.ST_NAME],
                            GET_GEOMETRY_FROM_STR(state[const.ST_SHAPE]),
                            color=sly.color.hex2rgb(state[const.ST_COLOR]))
    meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection([fg_class, st_class]))
    api.project.update_meta(project_id, sly.ProjectMeta().to_json())  # clear previous labels and classes
    api.project.update_meta(project_id, meta.to_json())

    sly.fs.mkdir(const.CACHE_DIR)
    for idx, (image_info, dataset_info) in enumerate(all_images):
        table_row = {}

        image_id = image_info.id
        table_row['id'] = image_id

        image_url = api.image.url(team_id, workspace_id, project_id, dataset_info.id, image_id)
        table_row['name'] = '<a href="{0}" rel="noopener noreferrer" target="_blank">{1}</a>' \
                            .format(image_url, image_info.name)

        image_path = os.path.join(const.CACHE_DIR, "{}.png".format(image_id))
        if not sly.fs.file_exists(image_path):
            api.image.download_path(image_id, image_path, )
        image = sly.image.read(image_path, remove_alpha_channel=False)

        if image.shape[2] != 4:
            sly.logger.warning("Image (id = {}) is skipped: it does not have alpha channel".format(image_id))
            continue

        alpha = image[:, :, 3]
        mask = (alpha >= state[const.ALPHA_THRESHOLD]).astype(np.uint8) * 255
        mask_instances, num_cc = skimage.measure.label(mask, background=0, return_num=True)
        area_pixels = int(mask_instances.shape[0] * mask_instances.shape[1] / 100 * state[const.AREA_THRESHOLD])
        mask_cleaned = skimage.morphology.remove_small_objects(mask_instances, area_pixels)
        mask_cleaned, num_cc = skimage.measure.label(mask_cleaned, background=0, return_num=True)


        cc_area = count_instances_area(mask_cleaned, num_cc)
        cc_area = cc_area[:state[const.MAX_NUMBER_OF_OBJECTS]]

        table_row['objects count'] = len(cc_area)

        labels = []
        sly.logger.debug("image_id = {}, number of extracted objects: {}".format(image_id, len(cc_area)))
        for cc_color, area in cc_area:
            object_mask = (mask_cleaned == cc_color)
            geometry = sly.Bitmap(data=object_mask)
            label = sly.Label(geometry, fg_class)
            labels.append(label)

        #find gray zone
        gray_zone = np.logical_and(alpha != 0, alpha != 255)
        gray_geometry = sly.Bitmap(data=gray_zone)
        gray_label = sly.Label(gray_geometry, st_class)
        labels.append(gray_label)

        ann = sly.Annotation(mask.shape[:2], labels=labels)

        # debug anotation
        # print(json.dumps(ann.to_json()))
        # render = np.zeros(ann.img_size + (3,), dtype=np.uint8)
        # ann.draw(render)
        # sly.image.write('/workdir/src/0.png', render)

        api.annotation.upload_ann(image_id, ann)

        processed_items.append(table_row)

        if (idx % const.NOTIFY_EVERY == 0 and idx != 0) or idx == len(all_images) - 1:
            api.task.set_data(task_id, payload=processed_items, field="{}.{}".format(const.DATA, const.TABLE), append=True)
            processed_items = []
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
